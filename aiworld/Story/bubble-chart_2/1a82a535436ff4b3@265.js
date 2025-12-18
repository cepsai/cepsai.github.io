import define1 from "./a33468b95d0b15b0@817.js";

function _1(md){return(
md`<div style="color: grey; font: 13px/25.5px var(--sans-serif); text-transform: uppercase;"><h1 style="display: none;">Bubble chart</h1><a href="https://d3js.org/">D3</a> › <a href="/@d3/gallery">Gallery</a></div>

# Bubble chart

Bubble charts are non-hierarchical [packed circles](/@d3/pack/2). The area of each circle is proportional its value (here, file size). The organic appearance of these diagrams can be intriguing, but also consider a [treemap](/@d3/treemap/2) or a humble [bar chart](/@d3/horizontal-bar-chart/2).`
)}

function _key(Swatches,chart){return(
Swatches(chart.scales.color)
)}

function _chart(d3,data)
{
  // Specify the dimensions of the chart.
  const width = 928;
  const height = width;
  const margin = 1; // to avoid clipping the root circle stroke
  const name = d => d.id.split(".").pop(); // "Strings" of "flare.util.Strings"
  const group = d => d.id.split(".")[1]; // "util" of "flare.util.Strings"
  const names = d => name(d).split(/(?=[A-Z][a-z])|\s+/g); // ["Legend", "Item"] of "flare.vis.legend.LegendItems"

  // Specify the number format for values.
  const format = d3.format(",d");

  // Create a categorical color scale.
  const color = d3.scaleOrdinal(d3.schemeTableau10);

  // Create the pack layout.
  const pack = d3.pack()
      .size([width - margin * 2, height - margin * 2])
      .padding(3);

  // Compute the hierarchy from the (flat) data; expose the values
  // for each node; lastly apply the pack layout.
  const root = pack(d3.hierarchy({children: data})
      .sum(d => d.value));

  // Create the SVG container.
  const svg = d3.create("svg")
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", [-margin, -margin, width, height])
      .attr("style", "max-width: 100%; height: auto; font: 10px sans-serif;")
      .attr("text-anchor", "middle");

  // Place each (leaf) node according to the layout’s x and y values.
  const node = svg.append("g")
    .selectAll()
    .data(root.leaves())
    .join("g")
      .attr("transform", d => `translate(${d.x},${d.y})`);

  // Add a title.
  node.append("title")
      .text(d => `${d.data.id}\n${format(d.value)}`);

  // Add a filled circle.
  node.append("circle")
      .attr("fill-opacity", 0.7)
      .attr("fill", d => color(group(d.data)))
      .attr("r", d => d.r);

  // Add a label.
  const text = node.append("text")
      .attr("clip-path", d => `circle(${d.r})`);

  // Add a tspan for each CamelCase-separated word.
  text.selectAll()
    .data(d => names(d.data))
    .join("tspan")
      .attr("x", 0)
      .attr("y", (d, i, nodes) => `${i - nodes.length / 2 + 0.35}em`)
      .text(d => d);

  // Add a tspan for the node’s value.
  text.append("tspan")
      .attr("x", 0)
      .attr("y", d => `${names(d.data).length / 2 + 0.35}em`)
      .attr("fill-opacity", 0.7)
      .text(d => format(d.value));

  return Object.assign(svg.node(), {scales: {color}});
}


async function _data(FileAttachment){return(
(await FileAttachment("flare.csv").csv({typed: true})).filter(({value}) => value !== null)
)}

export default function define(runtime, observer) {
  const main = runtime.module();
  function toString() { return this.url; }
  const fileAttachments = new Map([
    ["flare.csv", {url: new URL("./files/aee5d40e70ea9830c96efe6da03ad32187ff7223ad1b7b84e38c32127ccf6661b576fe0005b42657703e7bfaaefabc74550268cc35f64122a652fc471110c832.csv", import.meta.url), mimeType: "text/csv", toString}]
  ]);
  main.builtin("FileAttachment", runtime.fileAttachments(name => fileAttachments.get(name)));
  main.variable(observer()).define(["md"], _1);
  main.variable(observer("key")).define("key", ["Swatches","chart"], _key);
  main.variable(observer("chart")).define("chart", ["d3","data"], _chart);
  main.variable(observer("data")).define("data", ["FileAttachment"], _data);
  const child1 = runtime.module(define1);
  main.import("Swatches", child1);
  return main;
}
