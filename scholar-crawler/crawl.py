#!/usr/bin/env python3
"""Google Scholar profile crawler.

Scrapes citation stats for a Google Scholar profile and writes:

  hindex.txt     -- one stat per line, same order as the profile stats table:
                    citations (all), citations (recent), h-index (all),
                    h-index (recent), i10-index (all), i10-index (recent)
  citations.txt  -- "year,count" per line for the citations-per-year chart

Design goals (this replaces a fragile Rust scraper):
  * stdlib only -- nothing to install, nothing to compile
  * retries with exponential backoff across several Scholar mirrors
  * correct year/count pairing (bars with zero citations are missing from
    the chart HTML, so naive zipping of labels and bars mispairs data;
    we use each bar's z-index, which counts from the right edge)
  * never overwrite good data with bad data: output files are only written
    after the parsed data passes sanity checks
  * if Scholar blocks us (common from CI IPs) we keep the old data and exit
    successfully with a warning, so the workflow stays green and the site
    keeps serving the last known-good numbers. Set STRICT=1 to fail instead.
"""

import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Optional, Tuple

SCHOLAR_USER = os.environ.get("SCHOLAR_USER", "XHeNA_8AAAAJ")
STRICT = os.environ.get("STRICT", "") == "1"
MAX_ATTEMPTS = int(os.environ.get("MAX_ATTEMPTS", "6"))

REPO_ROOT = Path(__file__).resolve().parent.parent
CITATIONS_PATH = REPO_ROOT / "citations.txt"
HINDEX_PATH = REPO_ROOT / "hindex.txt"

MIRRORS = [
    f"https://scholar.google.com/citations?user={SCHOLAR_USER}&hl=en",
    f"https://scholar.google.ca/citations?user={SCHOLAR_USER}&hl=en",
    f"https://scholar.google.de/citations?user={SCHOLAR_USER}&hl=en",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def log(msg: str) -> None:
    print(msg, flush=True)


def warn(msg: str) -> None:
    # ::warning:: renders as an annotation in GitHub Actions
    print(f"::warning::{msg}" if os.environ.get("GITHUB_ACTIONS") else f"WARNING: {msg}", flush=True)


def fetch_profile() -> Optional[str]:
    """Fetch the profile page, rotating mirrors with exponential backoff."""
    for attempt in range(MAX_ATTEMPTS):
        url = MIRRORS[attempt % len(MIRRORS)]
        log(f"[{attempt + 1}/{MAX_ATTEMPTS}] GET {url}")
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            if "gsc_rsb_std" in html:
                return html
            log("  -> got a page without stats (CAPTCHA / block page?)")
        except urllib.error.HTTPError as e:
            log(f"  -> HTTP {e.code}")
        except Exception as e:  # noqa: BLE001 - we want to retry on anything
            log(f"  -> {type(e).__name__}: {e}")
        if attempt < MAX_ATTEMPTS - 1:
            delay = min(2 ** attempt, 30) + random.uniform(0, 2)
            log(f"  retrying in {delay:.1f}s")
            time.sleep(delay)
    return None


def parse_stats(html: str) -> List[int]:
    """Return the six stats-table numbers (citations/h-index/i10, all+recent)."""
    stats = [int(m) for m in re.findall(r'class="gsc_rsb_std">(\d+)</td>', html)]
    if not stats:
        stats = [int(m) for m in re.findall(r'class="gsc_rsb_std">(\d+)<', html)]
    return stats


def parse_chart(html: str) -> List[Tuple[int, int]]:
    """Return [(year, citations)] for the per-year chart, zeros filled in.

    Year labels:  <span class="gsc_g_t" ...>2019</span>
    Bars:         <a ... class="gsc_g_a" style="...z-index:N"><span class="gsc_g_al">42</span></a>
    A bar's z-index N means it belongs to the N-th year counting from the
    RIGHT of the label list. Years with zero citations have no bar at all.
    """
    years = [int(y) for y in re.findall(r'class="gsc_g_t"[^>]*>(\d{4})</span>', html)]
    if not years:
        return []

    counts = {y: 0 for y in years}
    bar_re = re.compile(
        r'class="gsc_g_a"[^>]*z-index:(\d+)[^>]*>\s*'
        r'<span[^>]*class="gsc_g_al"[^>]*>(\d+)</span>',
    )
    for z, count in bar_re.findall(html):
        idx = len(years) - int(z)
        if 0 <= idx < len(years):
            counts[years[idx]] = int(count)
        else:
            warn(f"chart bar with out-of-range z-index {z} ignored")
    return sorted(counts.items())


def sanity_check(stats: List[int], chart: List[Tuple[int, int]]) -> Optional[str]:
    """Return an error string if the parsed data looks wrong, else None."""
    if len(stats) < 6:
        return f"expected 6 stats values, got {len(stats)}: {stats}"
    citations_all, _, hindex_all = stats[0], stats[1], stats[2]
    if citations_all <= 0:
        return f"total citations is {citations_all}, refusing to publish"
    if hindex_all <= 0 or hindex_all > citations_all:
        return f"h-index {hindex_all} is implausible for {citations_all} citations"
    if not chart:
        return "citations-per-year chart is empty"
    if sum(c for _, c in chart) > citations_all:
        return "per-year chart sums to more than total citations"
    return None


def main() -> int:
    html = fetch_profile()
    if html is None:
        msg = f"Google Scholar unreachable/blocked after {MAX_ATTEMPTS} attempts; keeping existing data"
        if STRICT:
            log(f"ERROR: {msg}")
            return 1
        warn(msg)
        return 0

    stats = parse_stats(html)
    chart = parse_chart(html)

    error = sanity_check(stats, chart)
    if error:
        msg = f"scraped data failed sanity check ({error}); keeping existing data"
        if STRICT:
            log(f"ERROR: {msg}")
            return 1
        warn(msg)
        return 0

    HINDEX_PATH.write_text("".join(f"{s}\n" for s in stats[:6]), encoding="utf-8")
    CITATIONS_PATH.write_text(
        "".join(f"{year},{count}\n" for year, count in chart), encoding="utf-8"
    )

    log(f"OK: citations={stats[0]} h-index={stats[2]} i10={stats[4]}")
    log(f"OK: chart covers {chart[0][0]}-{chart[-1][0]} ({len(chart)} years)")
    log(f"wrote {HINDEX_PATH} and {CITATIONS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
