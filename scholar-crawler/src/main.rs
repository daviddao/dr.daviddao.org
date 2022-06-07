use error_chain::error_chain;
use select::document::Document;
use select::predicate::Class;
use std::fs::File;
use std::io::Write;


error_chain! {
      foreign_links {
          ReqError(reqwest::Error);
          IoError(std::io::Error);
      }
}

#[tokio::main]
async fn main() -> Result<()> {

    let citations_path = "../citations.txt";
    let hindex_path = "../hindex.txt";

    let mut output = File::create(citations_path)?;

    let res = reqwest::get("https://scholar.google.ca/citations?user=XHeNA_8AAAAJ&hl=en")
    .await?
    .text()
    .await?;

    let document = Document::from(res.as_str());

    // Get the citations
    let citations = document
    .select(Class("gsc_g_al"));
    // Zip with the years
    Document::from(res.as_str())
    .select(Class("gsc_g_t"))
    .zip(citations)
    .for_each(|(x,y)| write!(output, "{},{}\n", x.text(), y.text()).unwrap());

    let mut output = File::create(hindex_path)?;

    // Get the stats
    Document::from(res.as_str())
    .select(Class("gsc_rsb_std"))
    .filter_map(|n| Some(n.text()))
    .for_each(|x| write!(output, "{}\n", x).unwrap());

    Ok(())
}
