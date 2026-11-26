const SHOW_CONTAINER_2 = 1;
const SHOW_CONTAINER_3 = 1;
const SHOW_CONTAINER_4 = 1;
const SHOW_CONTAINER_5 = 0;

(function applyContainerVisibility() {
  const vizGrid = document.querySelector('.viz-grid');
  const c2 = document.getElementById('container2');
  const c3 = document.getElementById('container3');
  const c4 = document.getElementById('container4');
  const c5 = document.getElementById('container5');

  if (!SHOW_CONTAINER_2 && c2) c2.style.display = 'none';
  if (!SHOW_CONTAINER_3 && c3) c3.style.display = 'none';
  if (!SHOW_CONTAINER_4 && c4) c4.style.display = 'none';
  if (c5 && !SHOW_CONTAINER_5) c5.style.display = 'none';

  const row2Visible = SHOW_CONTAINER_5;
  const row3Visible = SHOW_CONTAINER_2;
  const row4Visible = SHOW_CONTAINER_3 || SHOW_CONTAINER_4;

  let gridRows = [];
  let currentRow = 1;
  const chartHeight = 20 - (row2Visible ? 1 : 0) - (row3Visible ? 1 : 0) - (row4Visible ? 1 : 0);
  gridRows.push(`${chartHeight}fr`);

  if (row2Visible) { gridRows.push('1fr'); currentRow++; if (c5) c5.style.gridRow = String(currentRow); }
  if (row3Visible) { gridRows.push('1fr'); currentRow++; if (c2) c2.style.gridRow = String(currentRow); }
  if (row4Visible) {
    gridRows.push('1fr'); currentRow++;
    if (SHOW_CONTAINER_3 && c3) c3.style.gridRow = String(currentRow);
    if (SHOW_CONTAINER_4 && c4) c4.style.gridRow = String(currentRow);
    if (row4Visible && SHOW_CONTAINER_3 && !SHOW_CONTAINER_4 && c3) c3.style.gridColumn = '1 / span 2';
    if (row4Visible && !SHOW_CONTAINER_3 && SHOW_CONTAINER_4 && c4) c4.style.gridColumn = '1 / span 2';
  }

  vizGrid.style.gridTemplateRows = gridRows.join(' ');
  document.getElementById('container1').style.gridRow = '1';
})();

const TABS = ["trend", "change", "tight"];
const DEFAULT_TAB = "trend";
const ACCENT = "#2756d3";
const NEG = "#E53229";
const POS = "#146c2e";
const REF_COLOR = "#94a3b8";
const REF_DASH = { "United States": "7 4", "United Kingdom": "2 3" };
const REFS = ["United States", "United Kingdom"];
const DEFAULT_EU = ["Germany", "France", "Italy", "Spain", "Netherlands", "Belgium", "Poland", "Sweden"];
const PALETTE = ["#2756d3", "#E53229", "#f59e0b", "#10b981", "#8b5cf6", "#06b6d4", "#db2777", "#8c564b", "#f97316", "#65a30d", "#0f766e", "#7c3aed"];
const TIGHT_EU = ["France", "Germany", "Ireland", "Italy", "Netherlands"];
const TIGHT_COLOR = { France: "#2756d3", Germany: "#f59e0b", Ireland: "#10b981", Italy: "#E53229", Netherlands: "#8b5cf6" };
const MEASURE_LONG = { applicants: "Attractive jobs per applicant", applications: "Attractive jobs per application" };
const LINKEDIN = `<a href="https://economicgraph.linkedin.com/" target="_blank" rel="noopener">LinkedIn Economic Graph</a>`;
const BREAKPOINT_PHONE = 560;

const META = new Map();
const LHR = new Map();
const TIGHT = { applicants: new Map(), applications: new Map() };
let EU = [];
let YOY = [], REF_YOY = [], IND = [];
const selected = new Set(DEFAULT_EU);
const colourSlots = new Map();
let activeTab = DEFAULT_TAB;
let changeView = "country";
let tightMeasure = "applicants";
let loaded = false;

const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const isPhone = () => window.innerWidth < BREAKPOINT_PHONE;
const fmt2 = d3.format(".2f");
const pct1 = v => (v > 0 ? "+" : v < 0 ? "−" : "") + d3.format(".1f")(Math.abs(v)) + "%";
const monthDate = m => { const [y, mo] = m.split("-").map(Number); return new Date(Date.UTC(y, mo - 1, 1)); };
const monthLabel = d3.utcFormat("%b %Y");
const short = c => (META.get(c) || {}).iso2 || c;
const cname = c => isPhone() ? short(c) : c;
const isRef = c => REFS.includes(c);
const flagImg = c => { const k = short(c).toLowerCase(); return k ? `<img class="cf-flag" src="https://flagcdn.com/w40/${k === "uk" ? "gb" : k}.png" alt="" loading="lazy">` : ""; };
const row = (k, v, c) => `<span class="t-row"><span class="t-k">${k}</span><span class="t-v"${c ? ` style="color:${c}"` : ""}>${v}</span></span>`;

let tooltip;
function tipShow(e, html) {
  tooltip.innerHTML = html;
  const w = tooltip.offsetWidth, h = tooltip.offsetHeight;
  let x = e.clientX + 14, y = e.clientY - 24;
  if (x + w > window.innerWidth - 8) x = e.clientX - w - 14;
  if (y + h > window.innerHeight - 8) y = window.innerHeight - h - 8;
  if (y < 8) y = 8;
  tooltip.style.left = x + "px";
  tooltip.style.top = y + "px";
  tooltip.style.opacity = "1";
}
function tipHide() { if (tooltip) tooltip.style.opacity = "0"; }

function positionPill(group) {
  const pill = group._pill, btn = group.querySelector(".selector-button.active");
  if (!pill || !btn) return;
  pill.style.width = btn.offsetWidth + "px";
  pill.style.height = btn.offsetHeight + "px";
  pill.style.transform = `translate(${btn.offsetLeft}px,${btn.offsetTop}px)`;
}
function initPill(group) {
  const pill = document.createElement("span");
  pill.className = "selector-pill";
  pill.style.transition = "none";
  group.insertBefore(pill, group.firstChild);
  group._pill = pill;
  positionPill(group);
  requestAnimationFrame(() => { pill.style.transition = ""; });
}
const SELECTOR_GROUPS = Array.from(document.querySelectorAll(".selector-group"));

function declump(ys, lo, hi, pitch) {
  const n = ys.length, out = ys.slice();
  if (!n) return out;
  const p = Math.min(pitch, (hi - lo) / Math.max(1, n - 1));
  out[0] = Math.max(lo, out[0]);
  for (let i = 1; i < n; i++) out[i] = Math.max(out[i], out[i - 1] + p);
  out[n - 1] = Math.min(out[n - 1], hi);
  for (let i = n - 2; i >= 0; i--) out[i] = Math.min(out[i], out[i + 1] - p);
  return out;
}

function panelSize(el) {
  const cs = getComputedStyle(el);
  return {
    w: el.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight),
    h: el.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom)
  };
}

function measureText(text, cls) {
  const svg = d3.select("body").append("svg").style("position", "absolute").style("visibility", "hidden");
  const t = svg.append("text").attr("class", cls).text(text);
  const w = t.node().getComputedTextLength();
  svg.remove();
  return w;
}

function styleAxis(ax, fs) {
  ax.selectAll("text").attr("font-size", fs);
  ax.select(".domain").remove();
  ax.selectAll(".tick line").remove();
}

function timeAxis(g, x, rows, innerW, innerH, phone) {
  const d0 = rows[0].date, d1 = rows[rows.length - 1].date;
  const years = d3.range(d0.getUTCFullYear(), d1.getUTCFullYear() + 1);
  years.forEach(yr => {
    const ys = new Date(Date.UTC(yr, 0, 1));
    if (ys > d0 && ys < d1) g.append("line").attr("class", "year-line").attr("x1", x(ys)).attr("x2", x(ys)).attr("y1", 0).attr("y2", innerH);
  });
  const yearFS = phone ? 11 : Math.max(12, Math.min(16, innerW * 0.016));
  g.append("g").selectAll("text").data(years.map(yr => {
    const a = new Date(Math.max(+d0, Date.UTC(yr, 0, 1))), b = new Date(Math.min(+d1, Date.UTC(yr, 11, 1)));
    return { yr, x: (x(a) + x(b)) / 2, w: x(b) - x(a) };
  })).join("text").attr("class", "year-axis-label")
    .attr("x", d => d.x).attr("y", innerH + 18)
    .attr("text-anchor", "middle").style("font-size", yearFS + "px")
    .text(d => d.w < yearFS * 2.6 ? "’" + String(d.yr).slice(2) : d.yr);
}

function lineChart(host, cfg) {
  host.innerHTML = "";
  const phone = isPhone();
  const { w: width, h: height } = panelSize(host);
  if (width <= 0 || height <= 0) return;
  const series = cfg.series;
  const months = series[0].rows;
  const axisFS = phone ? 10 : 11;
  const labelW = d3.max(series, s => measureText(cname(s.name), "end-label")) + 12;
  const margin = { top: 14, right: Math.min(labelW, width * 0.3), bottom: 30, left: phone ? 40 : 58 };
  const innerW = Math.max(50, width - margin.left - margin.right);
  const innerH = Math.max(50, height - margin.top - margin.bottom);
  const vals = series.flatMap(s => s.rows.map(r => r.v)).concat(cfg.base != null ? [cfg.base] : []);
  const ext = d3.extent(vals), pad = (ext[1] - ext[0]) * 0.05;
  const x = d3.scaleUtc().domain([months[0].date, months[months.length - 1].date]).range([0, innerW]);
  const y = d3.scaleLinear().domain([ext[0] - pad, ext[1] + pad]).nice().range([innerH, 0]);

  const svg = d3.select(host).append("svg").attr("role", "img").attr("aria-label", cfg.aria)
    .attr("width", width).attr("height", height).attr("viewBox", `0 0 ${width} ${height}`);
  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
  const nTy = Math.max(3, Math.floor(innerH / 60));
  g.append("g").attr("class", "axis-grid").call(d3.axisLeft(y).ticks(nTy).tickSize(-innerW).tickFormat(""));
  styleAxis(g.append("g").attr("class", "axis").call(d3.axisLeft(y).ticks(nTy).tickFormat(d3.format(".1f"))), axisFS);
  timeAxis(g, x, months, innerW, innerH, phone);
  svg.append("text").attr("class", "axis-label").attr("text-anchor", "middle")
    .attr("transform", `translate(${phone ? 11 : 14},${margin.top + innerH / 2}) rotate(-90)`)
    .text(phone ? cfg.yShort : cfg.yLabel);
  if (cfg.base != null) {
    g.append("line").attr("class", "base-line").attr("x1", 0).attr("x2", innerW).attr("y1", y(cfg.base)).attr("y2", y(cfg.base));
  }

  const lw = phone ? 1.53 : 2.04;
  const line = d3.line().x(d => x(d.date)).y(d => y(d.v));
  const ordered = series.slice().sort((a, b) => (b.ref ? 1 : 0) - (a.ref ? 1 : 0));
  g.append("g").selectAll("path").data(ordered).join("path")
    .attr("class", d => "series-line" + (d.ref ? " ref-line" : ""))
    .attr("fill", "none").attr("stroke", d => d.color).attr("stroke-width", d => d.ref ? lw * 0.8 : lw)
    .attr("stroke-dasharray", d => d.dash || null)
    .style("opacity", d => d.ref ? 0.95 : 0.9)
    .attr("d", d => line(d.rows));

  if (cfg.base != null) g.append("text").attr("class", "base-label").attr("x", 4).attr("y", y(cfg.base) - 5).text(cfg.baseLabel);

  const ends = series.map(s => ({ s, y: y(s.rows[s.rows.length - 1].v) })).sort((a, b) => a.y - b.y);
  const ly = declump(ends.map(e => e.y), 0, innerH, phone ? 11 : 13);
  g.append("g").selectAll("text").data(ends).join("text")
    .attr("class", d => "end-label" + (d.s.ref ? " ref" : ""))
    .attr("x", innerW + 6).attr("y", (d, i) => ly[i]).attr("dy", "0.35em")
    .attr("fill", d => d.s.ref ? null : d.s.color).text(d => cname(d.s.name));

  const dots = g.append("g").style("pointer-events", "none");
  const focus = g.append("line").attr("class", "focus-line").attr("y1", 0).attr("y2", innerH);
  const bis = d3.bisector(d => d.date).center;
  g.append("rect").attr("width", innerW).attr("height", innerH).attr("fill", "transparent")
    .on("mousemove", function (e) {
      const i = bis(months, x.invert(d3.pointer(e, this)[0]));
      const d = months[i];
      focus.attr("x1", x(d.date)).attr("x2", x(d.date)).style("opacity", 1);
      const pts = series.map(s => ({ s, v: s.rows[i].v })).sort((a, b) => b.v - a.v);
      dots.selectAll("circle").data(pts).join("circle")
        .attr("cx", x(d.date)).attr("cy", p => y(p.v)).attr("r", phone ? 3 : 4)
        .attr("fill", p => p.s.color).attr("stroke", "#fff").attr("stroke-width", 1.2);
      tipShow(e, `<span class="t-name">${monthLabel(d.date)}</span>` +
        pts.map(p => row(esc(p.s.name), fmt2(p.v), p.s.ref ? REF_COLOR : p.s.color)).join("") +
        `<span class="t-note">${esc(cfg.tipNote)}</span>`);
    })
    .on("mouseleave", () => { focus.style("opacity", 0); dots.selectAll("circle").remove(); tipHide(); });
}

function colourOf(c) {
  return colourSlots.get(c) || PALETTE[0];
}
function syncColourSlots() {
  Array.from(colourSlots.keys()).forEach(c => { if (!selected.has(c)) colourSlots.delete(c); });
  EU.filter(c => selected.has(c)).forEach(c => {
    if (colourSlots.has(c)) return;
    const used = new Set(colourSlots.values());
    colourSlots.set(c, PALETTE.find(x => !used.has(x)) || PALETTE[colourSlots.size % PALETTE.length]);
  });
}

function toggleCountry(c) {
  if (selected.has(c)) { if (selected.size > 1) selected.delete(c); }
  else selected.add(c);
  render();
}

function buildCountryFilter() {
  const el = document.getElementById("country-filter");
  el.innerHTML = "";
  const dd = document.createElement("div");
  dd.className = "selector-dropdown cf-dd";
  dd.innerHTML = `<button class="selector-dropdown-toggle" aria-expanded="false" aria-haspopup="listbox"></button>` +
    `<div class="selector-dropdown-menu" role="listbox" aria-multiselectable="true"><input class="cf-search" type="search" placeholder="Search countries" aria-label="Search countries">` +
    `<div class="cf-presets"></div><div class="cf-list"></div></div>`;
  el.appendChild(dd);
  const toggle = dd.querySelector(".selector-dropdown-toggle");
  const menu = dd.querySelector(".selector-dropdown-menu");
  const search = dd.querySelector(".cf-search");
  const presets = dd.querySelector(".cf-presets");
  const list = dd.querySelector(".cf-list");
  [["Default", () => DEFAULT_EU], ["All EU", () => EU]].forEach(([label, pick]) => {
    const b = document.createElement("button");
    b.textContent = label;
    b.addEventListener("click", e => {
      e.stopPropagation();
      selected.clear();
      pick().forEach(c => selected.add(c));
      render();
    });
    presets.appendChild(b);
  });
  EU.forEach(c => {
    const o = document.createElement("button");
    o.className = "selector-dropdown-option";
    o.dataset.country = c;
    o.setAttribute("role", "option");
    o.title = `Data quality: ${META.get(c).tier}`;
    o.innerHTML = `<span class="cf-box"></span>${flagImg(c)}<span>${esc(c)}</span><span class="cf-region">${esc(short(c))}</span>`;
    o.addEventListener("click", e => { e.stopPropagation(); toggleCountry(c); });
    list.appendChild(o);
  });
  search.addEventListener("input", () => {
    const q = search.value.trim().toLowerCase();
    list.querySelectorAll(".selector-dropdown-option").forEach(o => {
      const c = o.dataset.country;
      o.style.display = !q || c.toLowerCase().includes(q) || short(c).toLowerCase().includes(q) ? "" : "none";
    });
  });
  menu.addEventListener("click", e => e.stopPropagation());
  toggle.addEventListener("click", e => {
    e.stopPropagation();
    const open = menu.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(open));
    if (open) search.focus();
  });
  document.addEventListener("click", e => {
    if (!dd.contains(e.target)) {
      menu.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
    }
  });
  REFS.forEach(c => {
    const item = document.createElement("div");
    item.className = "legend-item ref";
    item.innerHTML = `<svg width="22" height="10" aria-hidden="true"><line x1="2" y1="5" x2="20" y2="5" stroke="${REF_COLOR}" stroke-width="2.04" stroke-dasharray="${REF_DASH[c]}"/></svg><span class="cf-name"></span>`;
    item.dataset.country = c;
    el.appendChild(item);
  });
}

function updateCountryFilter() {
  const el = document.getElementById("country-filter");
  const dd = el.querySelector(".cf-dd");
  if (!dd) return;
  dd.querySelector(".selector-dropdown-toggle").textContent = `EU countries: ${selected.size} of ${EU.length}`;
  dd.querySelectorAll(".cf-list .selector-dropdown-option").forEach(o => {
    const c = o.dataset.country, on = selected.has(c);
    o.classList.toggle("active", on);
    o.setAttribute("aria-selected", String(on));
    const box = o.querySelector(".cf-box");
    box.style.background = on ? colourOf(c) : "transparent";
    box.style.borderColor = on ? colourOf(c) : "";
  });
  el.querySelectorAll(".legend-item.ref").forEach(item => {
    item.querySelector(".cf-name").textContent = cname(item.dataset.country);
  });
}

function renderTrend() {
  syncColourSlots();
  updateCountryFilter();
  const series = EU.filter(c => selected.has(c)).map(c => ({ name: c, rows: LHR.get(c), color: colourOf(c) }))
    .concat(REFS.map(c => ({ name: c, rows: LHR.get(c), color: REF_COLOR, dash: REF_DASH[c], ref: true })));
  lineChart(document.getElementById("trend"), {
    series,
    base: 1,
    baseLabel: "2016 = 1",
    yLabel: "LinkedIn Hiring Rate (index, 2016 = 1)",
    yShort: "Hiring rate index",
    tipNote: "Hiring rate index, 2016 = 1, seasonally adjusted",
    aria: "LinkedIn Hiring Rate by country, monthly, January 2017 to October 2026, index with 2016 = 1"
  });
}

function renderTight() {
  const m = TIGHT[tightMeasure];
  const series = TIGHT_EU.map(c => ({ name: c, rows: m.get(c), color: TIGHT_COLOR[c] }))
    .concat(REFS.map(c => ({ name: c, rows: m.get(c), color: REF_COLOR, dash: REF_DASH[c], ref: true })));
  lineChart(document.getElementById("tight"), {
    series,
    yLabel: MEASURE_LONG[tightMeasure] + " (index)",
    yShort: tightMeasure === "applicants" ? "Jobs per applicant" : "Jobs per application",
    tipNote: MEASURE_LONG[tightMeasure] + ", index. Higher means a tighter market.",
    aria: MEASURE_LONG[tightMeasure] + ", monthly, November 2019 to October 2026"
  });
  document.getElementById("legend").innerHTML = series.map(s =>
    `<div class="legend-item"><svg width="22" height="10" aria-hidden="true"><line x1="2" y1="5" x2="20" y2="5" stroke="${s.color}" stroke-width="${s.ref ? 2.04 : 2.55}" stroke-dasharray="${s.dash || ""}" stroke-linecap="${s.ref ? "butt" : "round"}"/></svg><span>${esc(cname(s.name))}</span></div>`).join("");
}

function renderChange() {
  const host = document.getElementById("change");
  host.innerHTML = "";
  const phone = isPhone();
  const { w: width, h: height } = panelSize(host);
  if (width <= 0 || height <= 0) return;
  const byInd = changeView === "industry";
  const items = byInd
    ? IND.map(d => ({ key: d.industry, label: d.industry, v: d.change, n: d.n }))
    : YOY.concat(REF_YOY).map(d => ({ key: d.country, label: phone ? short(d.country) : d.country, v: d.change, d, ref: isRef(d.country) }));
  items.sort((a, b) => a.v - b.v);
  const axisFS = phone ? 10 : 11;
  const anyNeg = items.some(d => d.v < 0), anyPos = items.some(d => d.v > 0);
  const maxLabel = Math.min(width * (phone ? 0.42 : 0.38), d3.max(items, d => measureText(d.label, "bar-label")) + 10);
  const valW = measureText("−00.0%", "bar-value") + 10;
  const margin = {
    top: 24, bottom: 26,
    left: (anyNeg ? valW : 0) + (anyPos ? maxLabel : 0) + 6,
    right: (anyNeg ? maxLabel : 0) + (anyPos ? valW : 0) + 6
  };
  const innerW = Math.max(60, width - margin.left - margin.right);
  const innerH = Math.max(60, height - margin.top - margin.bottom);
  const ext = d3.extent(items.map(d => d.v).concat([0]));
  const x = d3.scaleLinear().domain(ext).nice().range([0, innerW]);
  const yb = d3.scaleBand().domain(items.map(d => d.key)).range([0, innerH]).padding(0.22);

  const svg = d3.select(host).append("svg").attr("role", "img")
    .attr("aria-label", byInd ? "Median change in hiring rate across EU countries by industry, October 2026 vs October 2025" : "Change in hiring rate by EU country, October 2026 vs October 2025")
    .attr("width", width).attr("height", height).attr("viewBox", `0 0 ${width} ${height}`);
  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
  const nTx = Math.max(3, Math.floor(innerW / 80));
  g.append("g").attr("class", "axis-grid").call(d3.axisTop(x).ticks(nTx).tickSize(-innerH).tickFormat(""));
  styleAxis(g.append("g").attr("class", "axis").call(d3.axisTop(x).ticks(nTx).tickFormat(v => v === 0 ? "0%" : pct1(v).replace(".0%", "%"))), axisFS);
  svg.append("text").attr("class", "axis-label").attr("text-anchor", "middle")
    .attr("x", margin.left + innerW / 2).attr("y", height - 6)
    .text(byInd ? (phone ? "Median change, Oct 2026 vs Oct 2025" : "Median change in hiring rate across EU countries, Oct 2026 vs Oct 2025") : (phone ? "Change, Oct 2026 vs Oct 2025" : "Change in hiring rate, Oct 2026 vs Oct 2025"));

  const bars = g.append("g").attr("class", "bars");
  const fs = Math.max(9, Math.min(13, yb.bandwidth() * 0.75));
  const grp = bars.selectAll("g").data(items).join("g");
  grp.append("rect").attr("class", "bar")
    .attr("x", d => x(Math.min(0, d.v))).attr("width", d => Math.abs(x(d.v) - x(0)))
    .attr("y", d => yb(d.key)).attr("height", yb.bandwidth())
    .attr("fill", d => d.ref ? REF_COLOR : d.v < 0 ? NEG : POS)
    .attr("opacity", d => d.ref ? 0.75 : 1);
  grp.append("text").attr("class", d => "bar-label" + (d.ref ? " ref" : ""))
    .attr("x", d => d.v < 0 ? x(0) + 6 : x(0) - 6).attr("text-anchor", d => d.v < 0 ? "start" : "end")
    .attr("y", d => yb(d.key) + yb.bandwidth() / 2).attr("dy", "0.35em").style("font-size", fs + "px")
    .text(d => d.label)
    .each(function () {
      const t = d3.select(this), full = t.text();
      if (this.getComputedTextLength() <= maxLabel - 8) return;
      let s = full;
      while (s.length > 3 && this.getComputedTextLength() > maxLabel - 8) { s = s.slice(0, -1); t.text(s.trimEnd() + "…"); }
    });
  grp.append("text").attr("class", "bar-value")
    .attr("x", d => d.v < 0 ? x(d.v) - 5 : x(d.v) + 5).attr("text-anchor", d => d.v < 0 ? "end" : "start")
    .attr("y", d => yb(d.key) + yb.bandwidth() / 2).attr("dy", "0.35em").style("font-size", Math.max(9, fs - 1) + "px")
    .text(d => pct1(d.v));
  g.append("line").attr("class", "zero-line").attr("x1", x(0)).attr("x2", x(0)).attr("y1", 0).attr("y2", innerH);

  grp.on("mousemove", function (e, d) {
    bars.classed("dim", true);
    grp.selectAll(".bar").classed("hovered", false);
    d3.select(this).select(".bar").classed("hovered", true);
    const html = byInd
      ? `<span class="t-name">${esc(d.key)}</span>` + row("Median change", pct1(d.v), d.v < 0 ? NEG : POS) +
        row("EU countries with data", `${d.n} of ${EU.length}`) +
        `<span class="t-note">Median of the change in each EU country, Oct 2026 vs Oct 2025</span>`
      : `<span class="t-name">${flagImg(d.key)} ${esc(d.key)}</span>` +
        row("Oct 2025", fmt2(d.d.before)) + row("Oct 2026", fmt2(d.d.now)) +
        row("Change", pct1(d.v), d.ref ? null : d.v < 0 ? NEG : POS) +
        `<span class="t-note">Data quality: ${esc(META.get(d.key).tier)}${d.ref ? ". Shown for reference." : ""}</span>`;
    tipShow(e, html);
  }).on("mouseleave", () => { bars.classed("dim", false); grp.selectAll(".bar").classed("hovered", false); tipHide(); });
}

function sourceHTML() {
  return `Source: ${LINKEDIN}`;
}

function setSourceBody(animate) {
  const el = document.getElementById("source-body");
  const html = sourceHTML();
  if (el.innerHTML === html) return;
  if (!animate) { el.innerHTML = html; return; }
  el.classList.add("slide-out");
  clearTimeout(setSourceBody.t);
  setSourceBody.t = setTimeout(() => {
    el.innerHTML = sourceHTML();
    el.classList.remove("slide-out");
    el.classList.add("slide-in");
    el.getBoundingClientRect();
    el.classList.remove("slide-in");
  }, 320);
}

function render(animateSource) {
  if (!loaded) return;
  tipHide();
  setSourceBody(!!animateSource);
  ({ trend: renderTrend, change: renderChange, tight: renderTight })[activeTab]();
}

function setTab(tab, push) {
  if (!TABS.includes(tab)) tab = DEFAULT_TAB;
  const changed = tab !== activeTab;
  activeTab = tab;
  document.querySelectorAll("#tabs .selector-button").forEach(b => {
    const on = b.dataset.tab === tab;
    b.classList.toggle("active", on);
    b.setAttribute("aria-selected", String(on));
  });
  document.querySelectorAll(".panel").forEach(p => p.classList.toggle("active", p.dataset.tab === tab));
  document.querySelectorAll(".ctx").forEach(c => c.classList.toggle("show", c.dataset.for.split(" ").includes(tab)));
  if (push) history.replaceState(null, "", "#" + tab);
  render(changed && push);
  SELECTOR_GROUPS.forEach(positionPill);
}

function wireToggle(id, set) {
  const grp = document.getElementById(id);
  grp.querySelectorAll(".selector-button").forEach(b => b.addEventListener("click", () => {
    grp.querySelectorAll(".selector-button").forEach(x => x.classList.toggle("active", x === b));
    positionPill(grp);
    set(b.dataset.value);
    render(true);
  }));
}

function seriesFrom(rows, valKey) {
  const out = new Map();
  d3.group(rows, d => d.country).forEach((xs, c) => {
    out.set(c, xs.map(d => ({ month: d.month, date: monthDate(d.month), v: +d[valKey] })).sort((a, b) => a.date - b.date));
  });
  return out;
}

function prepare([countries, hiring, yoy, refYoy, ind, tight]) {
  countries.forEach(d => META.set(d.country, { iso2: d.iso2, group: d.group, tier: d.tier }));
  EU = countries.filter(d => d.group === "EU").map(d => d.country).sort(d3.ascending);
  seriesFrom(hiring, "lhr").forEach((v, k) => LHR.set(k, v));
  const yo = d => ({ country: d.country, before: +d.lhr_2025_10, now: +d.lhr_2026_10, change: +d.change_pct });
  YOY = yoy.map(yo);
  REF_YOY = refYoy.map(yo);
  IND = ind.map(d => ({ industry: d.industry, change: +d.median_change_pct, n: +d.n_countries }));
  ["applicants", "applications"].forEach(m => seriesFrom(tight.filter(d => d.measure === m), "value").forEach((v, k) => TIGHT[m].set(k, v)));
  DEFAULT_EU.concat(REFS).forEach(c => { if (!LHR.has(c)) throw new Error("No hiring data for " + c); });
  TIGHT_EU.concat(REFS).forEach(c => { if (!TIGHT.applicants.has(c) || !TIGHT.applications.has(c)) throw new Error("No tightness data for " + c); });
}

function init() {
  tooltip = document.createElement("div");
  tooltip.id = "tooltip";
  document.body.appendChild(tooltip);
  SELECTOR_GROUPS.forEach(initPill);
  document.querySelectorAll("#tabs .selector-button").forEach(b => b.addEventListener("click", () => setTab(b.dataset.tab, true)));
  wireToggle("change-view", v => { changeView = v; });
  wireToggle("tight-measure", v => { tightMeasure = v; });

  const vizEl = document.getElementById("viz");
  let resizeTimer, lastW = 0, lastH = 0;
  const onResize = () => {
    SELECTOR_GROUPS.forEach(gr => {
      const p = gr._pill; if (p) p.style.transition = "none";
      positionPill(gr);
      requestAnimationFrame(() => { if (p) p.style.transition = ""; });
    });
    const rc = vizEl.getBoundingClientRect();
    if (Math.abs(rc.width - lastW) < 1 && Math.abs(rc.height - lastH) < 1) return;
    lastW = rc.width; lastH = rc.height;
    render();
  };
  window.addEventListener("resize", () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(onResize, 120); });
  if (typeof ResizeObserver !== "undefined") {
    new ResizeObserver(() => { clearTimeout(resizeTimer); resizeTimer = setTimeout(onResize, 120); }).observe(vizEl);
  }

  Promise.all(["countries", "hiring_rate", "eu_hiring_yoy", "ref_hiring_yoy", "eu_industry_yoy", "tightness"].map(f => d3.csv(`data/${f}.csv`)))
    .then(files => {
      prepare(files);
      loaded = true;
      buildCountryFilter();
      const rc = vizEl.getBoundingClientRect();
      lastW = rc.width; lastH = rc.height;
      activeTab = null;
      setTab((location.hash || "").slice(1) || DEFAULT_TAB, false);
    })
    .catch(err => {
      console.error(err);
      const el = document.createElement("div");
      el.className = "error-message";
      el.textContent = "No data available";
      vizEl.appendChild(el);
    });
}

init();
