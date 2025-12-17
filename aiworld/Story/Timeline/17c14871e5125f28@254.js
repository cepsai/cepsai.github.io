function _1(md){return(
md`# Timeline with Observable Plot`
)}

function _2(Plot,fontSizeInt,width,height,sideMargins,preparedData,tickHeight){return(
Plot.plot({
  style: {
    fontSize: fontSizeInt + "px",
    fontFamily: "Lato"
  },
  width,
  height,
  marginLeft: sideMargins,
  marginRight: sideMargins,
  x: { axis: null },
  y: { axis: null, domain: [-height / 2, height / 2] },
  marks: [
    Plot.ruleY([0]),
    Plot.ruleX(preparedData, {
      x: "year",
      y: (d, i) => (i % 2 === 0 ? tickHeight : -tickHeight)
    }),
    Plot.dot(preparedData, { x: "year", fill: "#fff", stroke: "#000" }),
    Plot.text(preparedData, {
      x: "year",
      y: (d, i) => (i % 2 === 0 ? -fontSizeInt / 2 - 4 : fontSizeInt / 2 + 4),
      text: (d) => d.year.toString()
    }),
    Plot.text(preparedData, {
      x: "year",
      y: (d, i) =>
        i % 2 === 0
          ? tickHeight + d.numberOfLines * fontSizeInt * 0.5
          : -tickHeight - d.numberOfLines * fontSizeInt * 0.5,
      text: "text"
    })
  ]
})
)}

function _height(Inputs){return(
Inputs.range([100, 500], {
  label: "Height",
  step: 10,
  value: 200
})
)}

function _tickHeight(Inputs){return(
Inputs.range([10, 50], {
  label: "Tick Height",
  step: 5,
  value: 25
})
)}

function _fontSizeInt(Inputs){return(
Inputs.range([8, 24], {
  label: "Font Size",
  step: 2,
  value: 16
})
)}

function _lineLength(Inputs){return(
Inputs.range([10, 30], {
  label: "Maximum Character Length of Each Line",
  step: 1,
  value: 15
})
)}

function _sideMargins(Inputs){return(
Inputs.range([10, 120], {
  label: "Left and Right Margins",
  step: 5,
  value: 70
})
)}

function _data(){return(
[
  {
    year: 1788,
    composition: `Symphony No. 41 "Jupiter"`,
    composer: "Wolfgang Amadeus Mozart",
    link: "https://en.wikipedia.org/wiki/Symphony_No._41_(Mozart)"
  },
  {
    year: 1894,
    composition: "Prelude to the Afternoon of a Faun",
    composer: "Claude Debussy",
    link: "https://en.wikipedia.org/wiki/Pr%C3%A9lude_%C3%A0_l%27apr%C3%A8s-midi_d%27un_faune"
  },
  {
    year: 1805,
    composition: `Symphony No. 3 "Eroica"`,
    composer: "Ludwig van Beethoven",
    link: "https://en.wikipedia.org/wiki/Symphony_No._3_(Beethoven)"
  },
  {
    year: 1913,
    composition: "Rite of Spring",
    composer: "Igor Stravinsky",
    link: "https://en.wikipedia.org/wiki/The_Rite_of_Spring"
  },
  {
    year: 1741,
    composition: "Goldberg Variations",
    composer: "Johann Sebastian Bach",
    link: "https://en.wikipedia.org/wiki/Goldberg_Variations"
  },
  {
    year: 1881,
    composition: "Piano Concerto No. 2",
    composer: "Johannes Brahms",
    link: "https://en.wikipedia.org/wiki/Piano_Concerto_No._2_(Brahms)"
  },
  {
    year: 1826,
    composition: `A Midsummer Night's Dream "Overture"`,
    composer: "Felix Mendelssohn",
    link: "https://en.wikipedia.org/wiki/A_Midsummer_Night%27s_Dream_(Mendelssohn)"
  }
]
)}

function _preparedData(data,wrapText,lineLength,d3){return(
data
  .map(function (d) {
    const composerShort = d.composer.split(" ").slice(-1);
    const { text, numberOfLines } = wrapText(
      `${d.composition} (${composerShort})`,
      lineLength
    );
    return { ...d, text, numberOfLines };
  })
  .sort((a, b) => d3.ascending(a.year, b.year))
)}

function _wrapText(){return(
function wrapText(inputString, segmentLength) {
  const words = inputString.split(" ");
  let result = "";
  let currentLineLength = 0;
  let numberOfLines = 0;

  for (const word of words) {
    if (currentLineLength + word.length + 1 <= segmentLength) {
      // Add the word and a space to the current line
      result += (result === "" ? "" : " ") + word;
      currentLineLength += word.length + 1;
    } else {
      // Start a new line with the word
      result += "\n" + word;
      currentLineLength = word.length;
      numberOfLines++;
    }
  }

  // Count the last line
  if (result !== "") {
    numberOfLines++;
  }

  return {
    text: result,
    numberOfLines: numberOfLines
  };
}
)}

function _11(htl){return(
htl.html`<style>
@import url('https://fonts.googleapis.com/css2?family=Lato&display=swap');

</style>`
)}

export default function define(runtime, observer) {
  const main = runtime.module();
  main.variable(observer()).define(["md"], _1);
  main.variable(observer()).define(["Plot","fontSizeInt","width","height","sideMargins","preparedData","tickHeight"], _2);
  main.variable(observer("viewof height")).define("viewof height", ["Inputs"], _height);
  main.variable(observer("height")).define("height", ["Generators", "viewof height"], (G, _) => G.input(_));
  main.variable(observer("viewof tickHeight")).define("viewof tickHeight", ["Inputs"], _tickHeight);
  main.variable(observer("tickHeight")).define("tickHeight", ["Generators", "viewof tickHeight"], (G, _) => G.input(_));
  main.variable(observer("viewof fontSizeInt")).define("viewof fontSizeInt", ["Inputs"], _fontSizeInt);
  main.variable(observer("fontSizeInt")).define("fontSizeInt", ["Generators", "viewof fontSizeInt"], (G, _) => G.input(_));
  main.variable(observer("viewof lineLength")).define("viewof lineLength", ["Inputs"], _lineLength);
  main.variable(observer("lineLength")).define("lineLength", ["Generators", "viewof lineLength"], (G, _) => G.input(_));
  main.variable(observer("viewof sideMargins")).define("viewof sideMargins", ["Inputs"], _sideMargins);
  main.variable(observer("sideMargins")).define("sideMargins", ["Generators", "viewof sideMargins"], (G, _) => G.input(_));
  main.variable(observer("data")).define("data", _data);
  main.variable(observer("preparedData")).define("preparedData", ["data","wrapText","lineLength","d3"], _preparedData);
  main.variable(observer("wrapText")).define("wrapText", _wrapText);
  main.variable(observer()).define(["htl"], _11);
  return main;
}
