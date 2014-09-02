function snipvis(div) {

        var genome = [
            {
                    del: 61,
                    hetero: 13568,
                    homo: 30234,
                    name: "1"
}, {
                    del: 70,
                    hetero: 15162,
                    homo: 31016,
                    name: "2"
}, {
                    del: 70,
                    hetero: 12205,
                    homo: 26095,
                    name: "3"
}, {
                    del: 60,
                    hetero: 10704,
                    homo: 23356,
                    name: "4"
}, {
                    del: 51,
                    hetero: 11085,
                    homo: 23579,
                    name: "5"
}, {
                    del: 52,
                    hetero: 11997,
                    homo: 25758,
                    name: "6"
}, {
                    del: 46,
                    hetero: 10109,
                    homo: 20860,
                    name: "7"
}, {
                    del: 50,
                    hetero: 10210,
                    homo: 21352,
                    name: "8"
}, {
                    del: 38,
                    hetero: 9019,
                    homo: 17927,
                    name: "9"
}, {
                    del: 48,
                    hetero: 9381,
                    homo: 20476,
                    name: "10"
}, {
                    del: 43,
                    hetero: 8902,
                    homo: 18980,
                    name: "11"
}, {
                    del: 51,
                    hetero: 8884,
                    homo: 19067,
                    name: "12"
}, {
                    del: 36,
                    hetero: 6460,
                    homo: 14859,
                    name: "13"
}, {
                    del: 24,
                    hetero: 6179,
                    homo: 12512,
                    name: "14"
}, {
                    del: 31,
                    hetero: 5386,
                    homo: 11627,
                    name: "15"
}, {
                    del: 31,
                    hetero: 5543,
                    homo: 11688,
                    name: "16"
}, {
                    del: 23,
                    hetero: 4627,
                    homo: 10572,
                    name: "17"
}, {
                    del: 27,
                    hetero: 5443,
                    homo: 11444,
                    name: "18"
}, {
                    del: 28,
                    hetero: 3522,
                    homo: 6587,
                    name: "19"
}, {
                    del: 27,
                    hetero: 4763,
                    homo: 9611,
                    name: "20"
}, {
                    del: 8,
                    hetero: 2590,
                    homo: 5772,
                    name: "21"
}, {
                    del: 24,
                    hetero: 2812,
                    homo: 5884,
                    name: "22"
}, {
                    del: 40,
                    hetero: 8,
                    homo: 13,
                    name: "X"
}, {
                    del: 2,
                    hetero: 0,
                    homo: 0,
                    name: "Y"
}, {
                    del: 37,
                    hetero: 0,
                    homo: 0,
                    name: "MT"
}];

        var data_res = [];

        for (var k = 0; k < 25; k++) {
                    var data = [{
                        category: "del",
                        number: genome[k].del
            }, {
                        category: "hetero",
                        number: genome[k].hetero
            }, {
                        category: "homo",
                        number: genome[k].homo
            }];


                    var data_wrapper = [{
                        name: genome[k].name,
                        data: data
            }];

                    data_res = data_res.concat(data_wrapper);

        }
         //Parser End


         //Div
        var menu_pane = d3.select(div)
                    .append("div")
                    .append("span")
                    .text("Chromosome:   ");

        var sel = menu_pane
                    .append("select")
                    .on("change", function (d) {

                        if (this.value < 23) {
                            data = data_res[this.value - 1].data;
                        } else {
                            switch (this.value) {
                            case 'X':
                                data = data_res[22].data;
                                break;

                            case 'Y':
                                data = data_res[23].data;
                                break;

                            case 'MT':
                                data = data_res[24].data;
                                break;
                            }
                        }

                        g
                            .data(pie(data))

                        g.select("path")
                            .attr("d", arc)
                            .style("fill", function (d) {
                                return color(d.data.category);
                            });

                        g.select("text")
                            .attr("transform", function (d) {
                                return "translate(" + arc.centroid(d) + ")";
                            })
                            .attr("dy", ".35em")
                            .style("text-anchor", "middle")
                            .text(function (d) {
                                return d.data.category;
                            });
                    });

        for (var d in data_res) {
                    sel
                        .append("option")
                        .attr("value", data_res[d].name)
                        .text(data_res[d].name);
        }
         // The first one is the option selected
        d3.select("option[value='X']")
            .attr("selected", 1);



         //End Div

        var width = 960,
                    height = 500,
                    radius = Math.min(width, height) / 2;

        var color = d3.scale.category10();

        var arc = d3.svg.arc()
                    .outerRadius(radius - 10)
                    .innerRadius(radius - 150);

        var pie = d3.layout.pie()
                    .sort(null)
                    .value(function (d) {
                        return d.number;
                    });

        var svg = d3.select(div).append("svg")
                    .attr("width", width)
                    .attr("height", height)
                    .append("g")
                    .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

        var g = svg.selectAll(".arc")
                    .data(pie(data_res[22].data))
                    .enter().append("g")
                    .attr("class", "arc");

        g.append("path")
            .attr("d", arc)
            .style("fill", function (d) {
                    return color(d.data.category);
                });

        g.append("text")
            .attr("transform", function (d) {
                    return "translate(" + arc.centroid(d) + ")";
                })
            .attr("dy", ".35em")
            .style("text-anchor", "middle")
            .text(function (d) {
                    return d.data.category;
                });

};