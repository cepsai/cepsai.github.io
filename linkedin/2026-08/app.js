const THEMES = {
  "AI builders": ["AI Engineer", "AI Specialist", "Datacenter Technician"],
  "Founders and owners": ["Founder", "Co-Founder", "Owner"],
  "Design and content": ["UX Designer", "UI Designer", "Interface Specialist", "Frontend Developer", "Copywriter", "Technical Writer", "Comms Manager", "Comms Assistant", "Community Manager"],
  "Data and tech": ["IT Analyst", "IT Consultant", "System Engineer", "Software Engineer", "Project Engineer", "Data Analyst", "QA Specialist"],
  "Project and admin coordination": ["Project Manager", "Project Associate", "Project Management Specialist", "Program Specialist", "Product Manager", "Office Assistant", "Direction Assistant", "Operations Associate", "Event Specialist"],
  "Sales and marketing": ["Business Development Manager", "Sales Specialist", "Sales Manager", "Salesperson", "Account Executive", "Account Manager", "Head of Sales", "Manager of Sales", "Sales Development Representative", "Sales Assistant", "Customer Associate", "Retail Associate", "Real Estate Agent", "Growth Specialist", "Campus Ambassador", "Marketing Assistant", "Product Marketing Manager", "Digital Marketing Specialist"],
  "Other": ["Principal", "Board Member", "Business Specialist", "Teacher", "Teaching Assistant", "Postdoc Researcher", "Research Assistant", "Law Clerk", "Legal Associate", "Accountant", "Payroll Accountant", "Finance Specialist", "HR Manager", "Employment Consultant", "Nurse Practitioner", "Pharmacist", "Chef", "Bartender"]
};

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

const DATA_URL = "data/top5.csv";
const DATASETS = {
  top5: "top5.csv",
  talent: "p5_finance_ai_talent.csv",
  allJobs: "p2_entry_overall.csv"
};
const MODES = {
  real: { base: "data/", extra: {} },
  mock: { base: "data/mock/", extra: { talentFields: "p5_ai_talent_by_field.csv" } }
};
const TALENT_BASE_FIELD = "Finance";
const TALENT_FIELDS = {
  real: [TALENT_BASE_FIELD],
  mock: [TALENT_BASE_FIELD, "ICT", "Manufacturing", "Professional services", "Health", "Education", "Retail", "Public administration"]
};
const MOCK_SOURCE = "Mockup data";
const MOCK_DEFAULT_EXTRA = ["Spain", "Italy", "Japan"];
const ISO2 = {
  ARG: "AR", AUS: "AU", AUT: "AT", BEL: "BE", BRA: "BR", BGR: "BG", CAN: "CA", CHL: "CL", COL: "CO", HRV: "HR",
  CZE: "CZ", DNK: "DK", EGY: "EG", EST: "EE", FIN: "FI", FRA: "FR", DEU: "DE", GRC: "GR", HUN: "HU", IND: "IN",
  IDN: "ID", IRL: "IE", ISR: "IL", ITA: "IT", JPN: "JP", KEN: "KE", LTU: "LT", MYS: "MY", MEX: "MX", NLD: "NL",
  NZL: "NZ", NGA: "NG", NOR: "NO", PER: "PE", PHL: "PH", POL: "PL", PRT: "PT", QAT: "QA", ROU: "RO", SAU: "SA",
  SGP: "SG", SVK: "SK", ZAF: "ZA", ESP: "ES", SWE: "SE", CHE: "CH", TUR: "TR", ARE: "AE", GBR: "UK", USA: "US"
};
const REGION_PRESETS = [
  { id: "EU27", label: "EU27", regions: ["EU27"] },
  { id: "Europe", label: "Europe", regions: ["EU27", "Europe (non-EU)"] },
  { id: "Americas", label: "Americas", regions: ["Americas"] },
  { id: "Asia-Pacific", label: "Asia-Pacific", regions: ["Asia-Pacific"] },
  { id: "all", label: "All", regions: null },
  { id: "real", label: "LinkedIn 5", real: true }
];
const D3PLUS_URL = "https://cdn.jsdelivr.net/npm/d3plus-hierarchy@1";
const DEFAULT_TAB = "matrix";
const TABS = ["matrix", "strip", "themes", "treemap", "pairs", "bump", "countries"];
const FILTER_OFF = {};
const REAL_COUNTRIES = ["France", "Germany", "India", "United Kingdom", "United States"];
let COUNTRIES = REAL_COUNTRIES.slice();
const COUNTRY_SHORT = { "France": "FR", "Germany": "DE", "India": "IN", "United Kingdom": "UK", "United States": "US" };
const COUNTRY_COLOR = { "France": "#2756d3", "Germany": "#f59e0b", "India": "#10b981", "United Kingdom": "#8b5cf6", "United States": "#E53229" };
const LEVELS = ["overall", "entry"];
const LEVEL_LABEL = { overall: "Overall", entry: "Entry" };
const LEVEL_LONG = { overall: "Overall", entry: "Entry-level" };
const LEVEL_COLOR = { overall: "#10b981", entry: "#2756d3" };
const DIR_LABEL = { growing: "Fastest growing", declining: "Fastest declining" };
const THEME_ORDER = Object.keys(THEMES);

const GROW_LIGHT = "#e3f5e8", GROW_DARK = "#146c2e";
const DECL_LIGHT = "#fde4e1", DECL_DARK = "#b42318";
const ZERO_COLOR = "#eef1f5";
const RAMP_MAX = 60;
const RAMP_FLOOR = 0.14;
const RAMP_GAMMA = 0.85;

const COL_GAP = 2;
const ROW_GAP = 1;
const SECTION_GAP = 16;
const MATRIX_MIN_CELL = 32;
const MATRIX_MIN_CELL_PHONE = 24;
const MAX_CELL_W = 90;

const STRIP_BREAK_AT = 100;
const STRIP_MIN_ROW = 78;
const PAIRS_FRAMING = "axes";
const PAIRS_LABELS = "flank";
const PAIRS_GAP_HEADROOM = 0.06;
const LABEL_FS = 12;
const LABEL_FS_MIN = 9;
const SHOW_TOOLTIP = 1;
const TREEMAP_GROUP_STROKE = "#fff";
const TREEMAP_DURATION = 600;


const BREAKPOINT_COMPACT = 500;
const BREAKPOINT_PHONE = 560;

function parseNum(value) {
  if (value == null || value === "") return 0;
  const n = Number(String(value).replace(/,/g, ""));
  return Number.isFinite(n) ? n : 0;
}

function smartFormat(v) {
  if (!isFinite(v)) return "N/A";
  if (Math.abs(v) >= 1e9) return d3.format(".1f")(v / 1e9) + "B";
  if (Math.abs(v) >= 1e6) return d3.format(".1f")(v / 1e6) + "M";
  if (Math.abs(v) >= 1e3 && Math.floor(v) === v) return d3.format(",")(v);
  if (Math.floor(v) === v) return d3.format(",")(v);
  return d3.format(",.1f")(v);
}

const signed = v => (v > 0 ? "+" : v < 0 ? "−" : "") + smartFormat(Math.abs(v));
const pct = v => signed(v) + "%";
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const isPhone = () => window.innerWidth < BREAKPOINT_PHONE;
const cname = c => isPhone() ? COUNTRY_SHORT[c] : c;
const EXTRA_COLORS = ["#06b6d4", "#f97316", "#db2777"];
const MUTED = "#c3c9d2";
const MAX_COLOURED = 8;
const colourSlots = new Map();
function colourOf(c) {
  if (COUNTRY_COLOR[c]) return COUNTRY_COLOR[c];
  return colourSlots.get(c) || "#64748b";
}
function syncColourSlots() {
  Array.from(colourSlots.keys()).forEach(c => { if (!selectedCountries.has(c)) colourSlots.delete(c); });
  selCountries().forEach(c => {
    if (COUNTRY_COLOR[c] || colourSlots.has(c)) return;
    const used = new Set(colourSlots.values());
    const free = EXTRA_COLORS.find(x => !used.has(x));
    if (free) colourSlots.set(c, free);
  });
}

function rampT(v) {
  const t = Math.pow(Math.min(1, Math.abs(v) / RAMP_MAX), RAMP_GAMMA);
  return RAMP_FLOOR + (1 - RAMP_FLOOR) * t;
}
function valToColor(v) {
  if (v === 0) return ZERO_COLOR;
  const t = rampT(v);
  return v > 0 ? d3.interpolateRgb(GROW_LIGHT, GROW_DARK)(t) : d3.interpolateRgb(DECL_LIGHT, DECL_DARK)(t);
}
const valText = v => v !== 0 && rampT(v) > 0.52 ? "#fff" : "#0f172a";

const themeOf = (() => {
  const m = new Map();
  THEME_ORDER.forEach(t => THEMES[t].forEach(o => m.set(o, t)));
  return o => m.get(o) || "Other";
})();

let tooltip;
function tipShow(e, html) {
  if (!SHOW_TOOLTIP) return;
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
const row = (k, v, c) => `<span class="t-row"><span class="t-k">${k}</span><span class="t-v"${c ? ` style="color:${c}"` : ""}>${v}</span></span>`;
function tipFor(d) {
  return `<span class="t-name">${esc(d.occupation)}</span>` +
    `<span class="t-q">${esc(d.country)} / ${LEVEL_LONG[d.level]}</span>` +
    row("List", DIR_LABEL[d.direction]) +
    row("Rank", d.rank) +
    row("YoY hiring", pct(d.yoy), d.yoy > 0 ? GROW_DARK : d.yoy < 0 ? DECL_DARK : null) + mockTag(d);
}

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

let DATA = [], OCC = [], PAIRS = [];
const DS = {};
const selectedCountries = new Set(COUNTRIES);
let dataMode = "real";
const META = new Map();
const savedSelection = {};
const modeCache = {};
let talentField = TALENT_BASE_FIELD;
let bumpSelected = null;
let activeTab = DEFAULT_TAB;
let sortState = { mode: "count" };
let themeView = "avg";
let treemapInstance = null;
let tmLegendInitialized = false;
let tmBusy = false, tmPending = false;
const COLS = [];
function buildCols() {
  COLS.length = 0;
  COUNTRIES.forEach(c => LEVELS.forEach(l => COLS.push({ key: c + "|" + l, country: c, level: l })));
}
buildCols();

function prepare(rows) {
  DATA = rows.map(r => ({
    country: r.country.trim(),
    level: r.level.trim(),
    direction: r.direction.trim(),
    rank: parseNum(r.rank),
    occupation: r.occupation.trim(),
    yoy: parseNum(r.yoy_pct),
    mock: parseNum(r.mock) === 1
  }));
  OCC = Array.from(d3.group(DATA, d => d.occupation), ([name, items]) => {
    const cells = {};
    items.forEach(d => { cells[d.country + "|" + d.level] = d; });
    return { name, items, cells, count: items.length, mean: d3.mean(items, d => d.yoy) };
  });
  PAIRS = [];
  COUNTRIES.forEach(c => {
    const ov = DATA.filter(d => d.country === c && d.level === "overall");
    const en = DATA.filter(d => d.country === c && d.level === "entry");
    ov.forEach(o => {
      const e = en.find(x => x.occupation === o.occupation);
      if (e) PAIRS.push({ id: COUNTRY_SHORT[c] + " " + o.occupation, country: c, occupation: o.occupation, overall: o, entry: e, gap: e.yoy - o.yoy });
    });
  });
}

const fmt1 = v => d3.format(".1f")(v);
const pct1 = v => (v > 0 ? "+" : v < 0 ? "−" : "") + fmt1(Math.abs(v)) + "%";
const pts1 = v => (v > 0 ? "+" : v < 0 ? "−" : "") + fmt1(Math.abs(v)) + " pts";
const share1 = v => fmt1(v) + "%";
const selCountries = () => COUNTRIES.filter(c => selectedCountries.has(c));
const filterOff = () => !!(FILTER_OFF[activeTab] && FILTER_OFF[activeTab]());
const EXTRA = {};

function prepareExtra() {
  const lvl = r => r.level.trim().toLowerCase();
  const mk = r => parseNum(r.mock) === 1;
  const talentRow = (r, field) => ({ country: r.country.trim(), field, year: parseNum(r.year), value: parseNum(r.share_finance_members_ai_talent_pct), mock: mk(r) });
  EXTRA.talent = DS.talent.map(r => talentRow(r, TALENT_BASE_FIELD))
    .concat((DS.talentFields || []).map(r => talentRow(r, r.field.trim())));
  EXTRA.allJobs = DS.allJobs.map(r => ({ country: r.country.trim(), facet: "All jobs", level: lvl(r), value: parseNum(r.yoy_hiring_rate_pct), mock: mk(r) }));
  EXTRA.bumpByField = new Map();
}

function talentFields() {
  return TALENT_FIELDS[dataMode].filter(f => EXTRA.talent.some(d => d.field === f));
}

function bumpFor(field) {
  if (EXTRA.bumpByField.has(field)) return EXTRA.bumpByField.get(field);
  const src = EXTRA.talent.filter(d => d.field === field);
  const years = Array.from(new Set(src.map(d => d.year))).sort(d3.ascending);
  let prev = null;
  const bump = new Map(COUNTRIES.map(c => [c, []]));
  years.forEach(yr => {
    const rows = src.filter(d => d.year === yr);
    rows.sort((a, b) => b.value - a.value || (prev ? prev.get(a.country) - prev.get(b.country) : 0) || COUNTRIES.indexOf(a.country) - COUNTRIES.indexOf(b.country));
    const now = new Map();
    rows.forEach((d, i) => {
      now.set(d.country, i + 1);
      const tied = rows.filter(o => o !== d && o.value === d.value).map(o => o.country);
      if (bump.has(d.country)) bump.get(d.country).push({ year: yr, rank: i + 1, value: d.value, field, tied, mock: d.mock });
    });
    prev = now;
  });
  const out = { years, bump };
  EXTRA.bumpByField.set(field, out);
  return out;
}

function buildFieldMenu() {
  const dd = document.getElementById("field-dd");
  const menu = dd.querySelector(".selector-dropdown-menu");
  const toggle = dd.querySelector(".selector-dropdown-toggle");
  const fields = talentFields();
  if (!fields.includes(talentField)) talentField = TALENT_BASE_FIELD;
  document.getElementById("field-ctx").classList.toggle("field-off", fields.length < 2);
  menu.innerHTML = "";
  fields.forEach(f => {
    const b = document.createElement("button");
    b.className = "selector-dropdown-option";
    b.textContent = f;
    b.dataset.field = f;
    b.setAttribute("role", "option");
    b.addEventListener("click", () => {
      talentField = f;
      menu.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
      bumpSelected = null;
      render();
    });
    menu.appendChild(b);
  });
  if (dd.dataset.wired) return;
  dd.dataset.wired = "1";
  toggle.addEventListener("click", e => {
    e.stopPropagation();
    const open = menu.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(open));
  });
  document.addEventListener("click", e => {
    if (!dd.contains(e.target)) { menu.classList.remove("open"); toggle.setAttribute("aria-expanded", "false"); }
  });
}

function updateFieldMenu() {
  const dd = document.getElementById("field-dd");
  dd.querySelector(".selector-dropdown-toggle").textContent = `Field: ${talentField}`;
  dd.querySelectorAll(".selector-dropdown-option").forEach(b => {
    const on = b.dataset.field === talentField;
    b.classList.toggle("active", on);
    b.setAttribute("aria-selected", String(on));
  });
}

function toggleCountry(c) {
  if (selectedCountries.has(c)) { if (selectedCountries.size > 1) selectedCountries.delete(c); }
  else selectedCountries.add(c);
  render();
}

function buildCountryFilter() {
  const el = document.getElementById("country-filter");
  el.innerHTML = "";
  if (dataMode === "mock") { buildCountryDropdown(el); return; }
  COUNTRIES.forEach(c => {
    const item = document.createElement("div");
    item.className = "legend-item interactive active";
    item.dataset.country = c;
    item.setAttribute("role", "button");
    item.setAttribute("tabindex", "0");
    item.setAttribute("aria-pressed", "true");
    item.innerHTML = `<span class="legend-square" style="background:${colourOf(c)}"></span><span class="cf-name"></span>`;
    item.addEventListener("click", () => toggleCountry(c));
    item.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggleCountry(c); } });
    el.appendChild(item);
  });
}

function buildCountryDropdown(el) {
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
  REGION_PRESETS.forEach(p => {
    const b = document.createElement("button");
    b.textContent = p.label;
    b.addEventListener("click", e => {
      e.stopPropagation();
      const pick = p.real ? REAL_COUNTRIES.filter(c => META.has(c)) : COUNTRIES.filter(c => !p.regions || p.regions.includes(META.get(c).region));
      if (!pick.length) return;
      selectedCountries.clear();
      pick.forEach(c => selectedCountries.add(c));
      render();
    });
    presets.appendChild(b);
  });
  COUNTRIES.forEach(c => {
    const o = document.createElement("button");
    o.className = "selector-dropdown-option";
    o.dataset.country = c;
    o.setAttribute("role", "option");
    o.innerHTML = `<span class="cf-box"></span><span>${esc(c)}</span><span class="cf-region">${esc(COUNTRY_SHORT[c])}</span>`;
    o.addEventListener("click", e => { e.stopPropagation(); toggleCountry(c); });
    list.appendChild(o);
  });
  search.addEventListener("input", () => {
    const q = search.value.trim().toLowerCase();
    list.querySelectorAll(".selector-dropdown-option").forEach(o => {
      const c = o.dataset.country, m = META.get(c);
      o.style.display = !q || c.toLowerCase().includes(q) || COUNTRY_SHORT[c].toLowerCase().includes(q) || (m && m.region.toLowerCase().includes(q)) ? "" : "none";
    });
  });
  menu.addEventListener("click", e => e.stopPropagation());
  toggle.addEventListener("click", e => {
    e.stopPropagation();
    const open = menu.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(open));
    if (open) search.focus();
  });
  if (!buildCountryDropdown.wired) {
    buildCountryDropdown.wired = true;
    document.addEventListener("click", e => {
      const d = document.querySelector(".cf-dd");
      if (d && !d.contains(e.target)) {
        d.querySelector(".selector-dropdown-menu").classList.remove("open");
        d.querySelector(".selector-dropdown-toggle").setAttribute("aria-expanded", "false");
      }
    });
  }
}

function updateCountryFilter() {
  const el = document.getElementById("country-filter");
  el.classList.toggle("off", filterOff());
  const dd = el.querySelector(".cf-dd");
  if (dd) {
    dd.querySelector(".selector-dropdown-toggle").textContent = `Countries: ${selectedCountries.size} of ${COUNTRIES.length}`;
    dd.querySelectorAll(".cf-list .selector-dropdown-option").forEach(o => {
      const c = o.dataset.country, on = selectedCountries.has(c);
      o.classList.toggle("active", on);
      o.setAttribute("aria-selected", String(on));
      const box = o.querySelector(".cf-box");
      box.style.background = on ? colourOf(c) : "transparent";
      box.style.borderColor = on ? colourOf(c) : "#cbd5e1";
    });
    return;
  }
  el.querySelectorAll(".legend-item").forEach(item => {
    const c = item.dataset.country, on = selectedCountries.has(c);
    item.classList.toggle("active", on);
    item.classList.toggle("dim", !on);
    item.setAttribute("aria-pressed", String(on));
    item.title = on && selectedCountries.size === 1 ? "At least one country stays selected" : "";
    item.querySelector(".cf-name").textContent = cname(c);
  });
}

function loadMode(mode) {
  if (!modeCache[mode]) {
    const m = MODES[mode];
    const files = Object.assign({}, DATASETS, m.extra);
    const keys = Object.keys(files);
    modeCache[mode] = Promise.all(keys.map(k => d3.csv(m.base + files[k]))).then(list => {
      const out = {};
      keys.forEach((k, i) => { out[k] = list[i]; });
      return out;
    });
    modeCache[mode].catch(() => { delete modeCache[mode]; });
  }
  return modeCache[mode];
}

function applyMode(mode, bundle, redraw) {
  if (COUNTRIES.length) savedSelection[dataMode] = Array.from(selectedCountries);
  dataMode = mode;
  META.clear();
  bundle.top5.concat(bundle.allJobs).forEach(r => {
    const c = r.country.trim();
    if (!META.has(c)) META.set(c, { iso3: (r.iso3 || "").trim(), region: (r.region || "").trim(), mock: parseNum(r.mock) === 1 });
  });
  const others = Array.from(META.keys()).filter(c => !REAL_COUNTRIES.includes(c)).sort(d3.ascending);
  COUNTRIES = REAL_COUNTRIES.filter(c => META.has(c)).concat(others);
  others.forEach(c => { const i3 = META.get(c).iso3; COUNTRY_SHORT[c] = ISO2[i3] || i3 || c.slice(0, 2).toUpperCase(); });
  const keep = (savedSelection[mode] || (mode === "mock" ? REAL_COUNTRIES.concat(MOCK_DEFAULT_EXTRA) : COUNTRIES)).filter(c => META.has(c));
  selectedCountries.clear();
  (keep.length ? keep : COUNTRIES).forEach(c => selectedCountries.add(c));
  colourSlots.clear();
  Object.keys(DS).forEach(k => delete DS[k]);
  Object.assign(DS, bundle);
  prepare(bundle.top5);
  prepareExtra();
  buildCols();
  buildSortMenu();
  if (sortState.mode === "col" && !COLS.some(c => c.key === sortState.key)) sortState = { mode: "count" };
  bumpSelected = null;
  buildFieldMenu();
  buildCountryFilter();
  document.querySelectorAll("#data-mode .selector-button").forEach(b => b.classList.toggle("active", b.dataset.mode === mode));
  const dm = document.getElementById("data-mode");
  if (dm) positionPill(dm);
  document.querySelector(".viz-grid").classList.toggle("wide-source", mode === "mock");
  setSourceBody(redraw);
  if (redraw) render();
}

function sourceHTML() {
  if (dataMode === "mock") return `Source: ${esc(MOCK_SOURCE)}`;
  return `Source: <a href="https://economicgraph.linkedin.com/" target="_blank" rel="noopener">LinkedIn</a>`;
}

function setSourceBody(animate) {
  const el = document.getElementById("source-body");
  if (!el) return;
  const html = sourceHTML();
  if (el.innerHTML === html) return;
  if (!animate) { if (!el.classList.contains("slide-out")) el.innerHTML = html; return; }
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

function switchMode(mode) {
  if (mode === dataMode) return;
  document.querySelectorAll("#data-mode .selector-button").forEach(b => b.classList.toggle("active", b.dataset.mode === mode));
  positionPill(document.getElementById("data-mode"));
  loadMode(mode).then(bundle => applyMode(mode, bundle, true)).catch(err => {
    console.error(err);
    document.querySelectorAll("#data-mode .selector-button").forEach(b => b.classList.toggle("active", b.dataset.mode === dataMode));
    positionPill(document.getElementById("data-mode"));
  });
}

function setTab(tab, push) {
  if (!TABS.includes(tab)) tab = DEFAULT_TAB;
  activeTab = tab;
  document.querySelectorAll("#tabs .selector-button").forEach(b => {
    const on = b.dataset.tab === tab;
    b.classList.toggle("active", on);
    b.setAttribute("aria-selected", String(on));
  });
  document.querySelectorAll(".panel").forEach(p => p.classList.toggle("active", p.dataset.tab === tab));
  document.querySelectorAll(".ctx").forEach(c => c.classList.toggle("show", c.dataset.for === tab));
  if (push) history.replaceState(null, "", "#" + tab);
  render();
  SELECTOR_GROUPS.forEach(positionPill);
}

function setLegend(items) {
  document.getElementById("legend").innerHTML = items.join("");
}

function render() {
  if (!DATA.length) return;
  tipHide();
  syncColourSlots();
  setSourceBody(false);
  updateCountryFilter();
  ({ matrix: renderMatrix, strip: renderStrip, themes: renderThemes, treemap: renderTreemap, pairs: renderPairs,
     bump: renderBump, countries: renderCountries })[activeTab]();
}

function panelSize(el) {
  const cs = getComputedStyle(el);
  return {
    w: el.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight),
    h: el.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom)
  };
}

function heatmap(host, cfg) {
  const phone = isPhone();
  host.innerHTML = "";
  const main = document.createElement("div");
  main.className = "hm-main";
  main.innerHTML = `<div class="hm-wrapper"><div class="hm-inner"><div class="row-bands"></div><div class="y-axis"></div><div class="sections"></div></div></div>` +
    `<div class="hm-legend"><div class="hm-legend-title">${cfg.legend.title}</div><div class="hm-legend-body"><div class="hm-legend-bar"></div><div class="hm-legend-ticks">${cfg.legend.ticks.map(t => `<span class="legend-tick">${t}</span>`).join("")}</div></div>` +
    (cfg.legend.hatch ? `<div class="hm-hatch"><i></i><span>${cfg.legend.hatch}</span></div>` : "") + `</div>`;
  host.appendChild(main);
  const wrapper = main.querySelector(".hm-wrapper");
  const inner = main.querySelector(".hm-inner");
  const yAxis = main.querySelector(".y-axis");
  const sectionsEl = main.querySelector(".sections");
  const legend = main.querySelector(".hm-legend");
  const legendBar = main.querySelector(".hm-legend-bar");
  const bands = main.querySelector(".row-bands");
  inner.style.setProperty("--row-gap", ROW_GAP + "px");
  inner.style.setProperty("--col-gap", COL_GAP + "px");

  const yHead = document.createElement("div");
  yHead.className = "y-head";
  yAxis.appendChild(yHead);
  const yLabels = cfg.rows.map(r => {
    const l = document.createElement("div");
    l.className = "y-label";
    l.innerHTML = `<span>${esc(r.label)}</span>`;
    if (cfg.yMaxW) l.style.maxWidth = cfg.yMaxW + "px";
    if (cfg.wrapY) l.firstChild.style.whiteSpace = "normal";
    l.title = r.label;
    yAxis.appendChild(l);
    return l;
  });

  const cells = [], xLabels = [], seps = [], heads = [];
  let totalCols = 0, totalSeparators = 0;
  cfg.sections.forEach(sec => {
    const s = document.createElement("div");
    s.className = "section";
    const head = document.createElement("div");
    head.className = "section-head";
    if (sec.title) head.innerHTML = `<div class="section-title">${esc(sec.title)}</div><div class="section-rule"></div>`;
    s.appendChild(head);
    heads.push(head);
    const xTop = document.createElement("div");
    xTop.className = "x-top";
    if (cfg.xTop) head.appendChild(xTop);
    const grid = document.createElement("div");
    grid.className = "section-grid";
    sec.groups.forEach((grp, gi) => {
      if (gi > 0) {
        const sep = document.createElement("div");
        sep.className = "group-separator";
        grid.appendChild(sep);
        seps.push(sep);
        totalSeparators++;
        if (cfg.xTop) { const sp = document.createElement("div"); sp.style.width = "17px"; xTop.appendChild(sp); }
      }
      const gb = document.createElement("div");
      gb.className = "group-block";
      grp.forEach(col => {
        totalCols++;
        const cb = document.createElement("div");
        cb.className = "col-block";
        cfg.rows.forEach((r, ri) => {
          const c = r.cells[col.key];
          const cell = document.createElement("div");
          cell.className = "cell" + (c ? "" : " empty");
          if (c) {
            cell.style.background = c.bg;
            cell.style.color = c.fg;
            cell.innerHTML = c.html;
          }
          const tip = c ? c.tip : cfg.emptyTip(r, col);
          cell.addEventListener("mousemove", e => tipShow(e, tip));
          cell.addEventListener("mouseleave", tipHide);
          cb.appendChild(cell);
          cells.push(cell);
        });
        const xl = document.createElement("div");
        xl.className = "x-label" + (cfg.onHeader ? " sortable" : "") + (cfg.sortedKey === col.key ? " sorted" : "");
        xl.textContent = col.label;
        if (cfg.onHeader) xl.addEventListener("click", () => cfg.onHeader(col.key));
        if (cfg.xTop) xTop.appendChild(xl); else cb.appendChild(xl);
        xLabels.push(xl);
        gb.appendChild(cb);
      });
      grid.appendChild(gb);
    });
    s.appendChild(grid);
    sectionsEl.appendChild(s);
  });

  const nRows = cfg.rows.length;
  const nSections = cfg.sections.length;
  const sectionGap = phone ? 6 : SECTION_GAP;
  sectionsEl.style.gap = sectionGap + "px";

  const pageW = panelSize(host).w;
  const pageH = panelSize(host).h;
  const wrapperW = phone ? pageW : pageW - legend.offsetWidth - 30;
  const wrapperH = phone ? pageH - legend.offsetHeight - 8 : pageH;
  const yAxisW = yAxis.offsetWidth;
  const headH = Math.max(0, ...heads.map(h => h.offsetHeight));
  const xLabelH = cfg.xTop ? 0 : Math.max(12, ...xLabels.map(l => l.offsetHeight)) + 6;
  const colGaps = cfg.sections.reduce((s, sec) => s + sec.groups.reduce((s2, g) => s2 + (g.length - 1) * COL_GAP, 0), 0);
  const totalGaps = (nSections - 1) * sectionGap + totalSeparators * (phone ? 10 : 17) + colGaps;
  const maxW = Math.floor((wrapperW - yAxisW - totalGaps - 2) / totalCols);
  const maxH = Math.floor((wrapperH - headH - xLabelH - (nRows - 1) * ROW_GAP) / nRows);
  const minCell = cfg.minCell || 6;
  const cellSize = Math.max(Math.min(minCell, maxW), Math.min(maxW, maxH, cfg.maxCell || MAX_CELL_W), cfg.scrollMin || 0);
  const fontPx = Math.max(8.5, Math.min(15, cellSize * (cfg.fontRatio || 0.36)));

  cells.forEach(c => { c.style.width = cellSize + "px"; c.style.height = cellSize + "px"; c.style.fontSize = fontPx + "px"; });
  xLabels.forEach(l => { l.style.width = cellSize + "px"; l.style.fontSize = Math.max(9, Math.min(13, cellSize * 0.34)) + "px"; });
  yLabels.forEach(l => { l.style.height = cellSize + "px"; });
  const gridH = nRows * cellSize + (nRows - 1) * ROW_GAP;
  seps.forEach(s => { s.style.height = gridH + "px"; });
  const sectionEls = Array.from(sectionsEl.querySelectorAll(".section"));
  if (cfg.lockSections) {
    const titles = Array.from(sectionsEl.querySelectorAll(".section-title"));
    const maxTitleW = Math.max(0, ...titles.map(t => t.scrollWidth));
    const colsPer = totalCols / nSections;
    const sectionW = colsPer * cellSize + (colsPer - 1) * COL_GAP;
    const slack = wrapperW - yAxisW - nSections * sectionW;
    const gapPx = Math.max(sectionGap, Math.min(Math.floor(slack / Math.max(1, nSections - 1)), maxTitleW - sectionW + 12));
    sectionsEl.style.gap = gapPx + "px";
    sectionEls.forEach(se => { se.style.width = sectionW + "px"; });
    const lastTitle = titles[titles.length - 1];
    if (lastTitle) sectionsEl.style.paddingRight = Math.max(0, Math.ceil((lastTitle.scrollWidth - sectionW) / 2) + 4) + "px";
  }
  const headH2 = Math.max(0, ...heads.map(h => h.offsetHeight));
  yHead.style.height = headH2 + "px";
  yHead.style.marginBottom = -ROW_GAP + "px";

  wrapper.style.maxWidth = wrapperW + "px";
  wrapper.style.maxHeight = wrapperH + "px";

  if (cfg.bands) {
    const pitch = cellSize + ROW_GAP;
    bands.style.top = headH2 + "px";
    bands.style.height = gridH + "px";
    bands.style.background = `repeating-linear-gradient(to bottom,rgba(15,23,42,0.05) 0 ${pitch}px, transparent ${pitch}px ${pitch * 2}px)`;
  }

  const visGridH = Math.min(gridH, wrapperH - headH2);
  const stops = d3.range(25).map(i => {
    const t = i / 24;
    return `${cfg.legend.color(phone ? t : 1 - t)} ${(t * 100).toFixed(1)}%`;
  }).join(",");
  legendBar.style.background = `linear-gradient(to ${phone ? "right" : "bottom"},${stops})`;
  const body = main.querySelector(".hm-legend-body");
  if (phone) {
    legendBar.style.width = Math.min(200, pageW * 0.5) + "px";
    legendBar.style.height = "12px";
    body.style.height = "auto";
  } else {
    const barH = Math.max(120, Math.min(320, Math.round(visGridH * 0.6)));
    legendBar.style.height = barH + "px";
    legendBar.style.width = "14px";
    body.style.height = barH + "px";
  }
}

function occFor(cs) {
  const set = new Set(cs);
  return OCC.map(o => {
    const items = o.items.filter(d => set.has(d.country));
    if (!items.length) return null;
    const cells = {};
    items.forEach(d => { cells[d.country + "|" + d.level] = d; });
    return { name: o.name, items, cells, count: items.length, mean: d3.mean(items, d => d.yoy) };
  }).filter(Boolean);
}

function sortedOcc(list) {
  const base = (list || OCC).slice();
  const byCount = (a, b) => b.count - a.count || b.mean - a.mean || d3.ascending(a.name, b.name);
  if (sortState.mode === "name") return base.sort((a, b) => d3.ascending(a.name, b.name));
  if (sortState.mode === "col" && selectedCountries.has(sortState.key.split("|")[0])) {
    const k = sortState.key, dir = sortState.dir;
    return base.sort((a, b) => {
      const va = a.cells[k], vb = b.cells[k];
      if (va && vb) return dir * (vb.yoy - va.yoy) || byCount(a, b);
      if (va) return -1;
      if (vb) return 1;
      return byCount(a, b);
    });
  }
  return base.sort(byCount);
}

function sortLabel() {
  if (sortState.mode === "count") return "Sort: most lists";
  if (sortState.mode === "name") return "Sort: name";
  const c = COLS.find(x => x.key === sortState.key);
  if (!c || !selectedCountries.has(c.country)) return "Sort: most lists";
  return `Sort: ${COUNTRY_SHORT[c.country]} ${LEVEL_LABEL[c.level].toLowerCase()} ${sortState.dir > 0 ? "high" : "low"} first`;
}

function buildSortMenu() {
  const dd = document.getElementById("sort-dd");
  const menu = dd.querySelector(".selector-dropdown-menu");
  const toggle = dd.querySelector(".selector-dropdown-toggle");
  menu.innerHTML = "";
  const opts = [{ id: "count", label: "Most lists" }, { id: "name", label: "Name A to Z" }]
    .concat(COLS.map(c => ({ id: c.key, label: `${c.country}, ${LEVEL_LABEL[c.level].toLowerCase()}` })));
  opts.forEach(o => {
    const b = document.createElement("button");
    b.className = "selector-dropdown-option";
    b.textContent = o.label;
    b.dataset.id = o.id;
    b.addEventListener("click", () => {
      sortState = (o.id === "count" || o.id === "name") ? { mode: o.id } : { mode: "col", key: o.id, dir: 1 };
      menu.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
      renderMatrix();
    });
    menu.appendChild(b);
  });
  if (dd.dataset.wired) return;
  dd.dataset.wired = "1";
  toggle.addEventListener("click", e => {
    e.stopPropagation();
    const open = menu.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(open));
  });
  document.addEventListener("click", e => {
    if (!dd.contains(e.target)) { menu.classList.remove("open"); toggle.setAttribute("aria-expanded", "false"); }
  });
}

function renderMatrix() {
  const host = document.getElementById("matrix");
  const phone = isPhone();
  const dd = document.getElementById("sort-dd");
  dd.querySelector(".selector-dropdown-toggle").textContent = sortLabel();
  const activeId = sortState.mode === "col" ? sortState.key : sortState.mode;
  dd.querySelectorAll(".selector-dropdown-option").forEach(b => {
    b.classList.toggle("active", b.dataset.id === activeId);
    const k = b.dataset.id.split("|");
    b.style.display = k.length === 2 && !selectedCountries.has(k[0]) ? "none" : "";
  });
  const cs = selCountries();

  const rows = sortedOcc(occFor(cs)).map(o => {
    const cells = {};
    COLS.forEach(c => {
      const d = o.cells[c.key];
      if (d) cells[c.key] = { bg: valToColor(d.yoy), fg: valText(d.yoy), html: signed(d.yoy), tip: tipFor(d) };
    });
    return { label: o.name, cells, occ: o };
  });
  const arrow = k => sortState.mode === "col" && sortState.key === k ? (sortState.dir > 0 ? " ↓" : " ↑") : "";
  heatmap(host, {
    rows,
    sections: cs.map(c => ({
      title: cs.length > 6 ? COUNTRY_SHORT[c] : cname(c),
      groups: [LEVELS.map(l => ({ key: c + "|" + l, label: (l === "overall" ? "Ovr" : "Ent") + arrow(c + "|" + l) }))]
    })),
    xTop: true,
    bands: true,
    lockSections: true,
    minCell: phone ? MATRIX_MIN_CELL_PHONE : MATRIX_MIN_CELL,
    scrollMin: cs.length > 6 ? (phone ? MATRIX_MIN_CELL_PHONE : MATRIX_MIN_CELL) : 0,
    maxCell: 56,
    fontRatio: 0.36,
    yMaxW: phone ? 86 : 210,
    sortedKey: sortState.mode === "col" ? sortState.key : null,
    onHeader: k => {
      sortState = (sortState.mode === "col" && sortState.key === k) ? { mode: "col", key: k, dir: -sortState.dir } : { mode: "col", key: k, dir: 1 };
      renderMatrix();
    },
    emptyTip: (r, col) => `<span class="t-name">${esc(r.label)}</span><span class="t-q">${esc(col.key.split("|")[0])} / ${LEVEL_LONG[col.key.split("|")[1]]}</span><span class="t-note">Not in this top 5 or bottom 5 list</span>`,
    legend: {
      title: phone ? "YoY hiring" : "YoY hiring<br>change",
      color: t => valToColor(Math.abs(t - 0.5) < 0.02 ? 0 : (t - 0.5) * 2 * RAMP_MAX),
      ticks: phone ? [pct(RAMP_MAX), "0%", pct(-RAMP_MAX)] : [pct(RAMP_MAX) + " or more", pct(RAMP_MAX / 2), "0%", pct(-RAMP_MAX / 2), pct(-RAMP_MAX) + " or less"],
      hatch: "Not in that list"
    }
  });
  setLegend([]);
}

function renderThemes() {
  const host = document.getElementById("themes");
  const phone = isPhone();
  const cs = selCountries();
  const tagged = DATA.filter(d => selectedCountries.has(d.country)).map(d => ({ ...d, theme: themeOf(d.occupation) }));
  const colKeys = cs.concat(["All"]);
  const rows = THEME_ORDER.map(t => {
    const cells = {};
    colKeys.forEach(c => {
      const items = tagged.filter(d => d.theme === t && (c === "All" || d.country === c));
      if (!items.length) return;
      const where = c === "All" ? (cs.length === COUNTRIES.length ? (COUNTRIES.length === 5 ? "All five countries" : "All countries") : "All selected countries") : c;
      const list = items.slice().sort((a, b) => b.yoy - a.yoy).map(d => `${esc(d.occupation)} ${pct(d.yoy)} <span style="color:#94a3b8">${COUNTRY_SHORT[d.country]} ${d.level}</span>`).join("<br>");
      if (themeView === "avg") {
        const m = d3.mean(items, d => d.yoy), mr = Math.round(m);
        cells[c] = {
          bg: valToColor(mr), fg: valText(mr),
          html: `${signed(mr)}<small>${items.length} slot${items.length > 1 ? "s" : ""}</small>`,
          tip: `<span class="t-name">${esc(t)}</span><span class="t-q">${esc(where)}</span>` + row("Average YoY", pct(Math.round(m * 10) / 10)) + row("List slots", items.length) + `<span class="t-note">${list}</span>` + anyMock(items)
        };
      } else {
        const g = items.filter(d => d.direction === "growing").length, dcl = items.length - g;
        const net = (g - dcl) / items.length * RAMP_MAX;
        cells[c] = {
          bg: valToColor(net), fg: valText(net),
          html: phone ? `${g} / ${dcl}` : `${g} / ${dcl}<small>up / down</small>`,
          tip: `<span class="t-name">${esc(t)}</span><span class="t-q">${esc(where)}</span>` + row("In growing lists", g) + row("In declining lists", dcl) + `<span class="t-note">${list}</span>` + anyMock(items)
        };
      }
    });
    return { label: t, cells };
  });
  heatmap(host, {
    rows,
    sections: [{ title: "", groups: [cs.map(c => ({ key: c, label: COUNTRY_SHORT[c] })), [{ key: "All", label: "All" }]] }],
    xTop: false,
    bands: false,
    minCell: 30,
    scrollMin: cs.length > 8 || (phone && cs.length > 5) ? 30 : 0,
    maxCell: 110,
    fontRatio: 0.26,
    yMaxW: phone ? 84 : 220,
    wrapY: true,
    emptyTip: (r, col) => `<span class="t-name">${esc(r.label)}</span><span class="t-q">${esc(col.key)}</span><span class="t-note">No list slots in this theme</span>`,
    legend: themeView === "avg" ? {
      title: phone ? "Average YoY" : "Average YoY<br>of the slots",
      color: t => valToColor(Math.abs(t - 0.5) < 0.02 ? 0 : (t - 0.5) * 2 * RAMP_MAX),
      ticks: phone ? [pct(RAMP_MAX), "0%", pct(-RAMP_MAX)] : [pct(RAMP_MAX) + " or more", pct(RAMP_MAX / 2), "0%", pct(-RAMP_MAX / 2), pct(-RAMP_MAX) + " or less"],
      hatch: "No slots"
    } : {
      title: phone ? "Growing / declining slots" : "Growing /<br>declining slots",
      color: t => valToColor(Math.abs(t - 0.5) < 0.02 ? 0 : (t - 0.5) * 2 * RAMP_MAX),
      ticks: ["All growing", "Even", "All declining"],
      hatch: "No slots"
    }
  });
  setLegend([]);
}

function renderStrip() {
  const host = document.getElementById("strip");
  host.innerHTML = "";
  const phone = isPhone();
  host.style.overflowY = "";
  let { w: width, h: height } = panelSize(host);
  if (width <= 0 || height <= 0) return;
  const sc = Math.max(0.6, Math.min(1, Math.min(width / 1080, height / 720)));
  const cs = selCountries();
  const labelW = phone ? 28 : (cs.length > 6 ? 150 : 120);
  const margin = { top: 24, right: 12, bottom: 30, left: labelW + 12 };
  if ((height - margin.top - margin.bottom) / cs.length < STRIP_MIN_ROW) {
    host.style.overflowY = "auto";
    width -= 14;
    height = margin.top + margin.bottom + cs.length * STRIP_MIN_ROW;
  }
  const innerW = Math.max(50, width - margin.left - margin.right);
  const innerH = Math.max(50, height - margin.top - margin.bottom);
  const rowH = innerH / cs.length;
  const r = Math.max(3.5, Math.min(6.4, innerW / 170, rowH / 16));
  const axisFont = Math.max(9, Math.min(13, innerW / 12 * 0.14));

  const vals = DATA.filter(d => selectedCountries.has(d.country)).map(d => d.yoy);
  const mainVals = vals.filter(v => v <= STRIP_BREAK_AT);
  const outVals = vals.filter(v => v > STRIP_BREAK_AT);
  const hasOut = outVals.length > 0;
  const ext = d3.extent(mainVals);
  const pad0 = (ext[1] - ext[0]) * 0.06;
  const xMainNice = d3.scaleLinear().domain([ext[0] - pad0, ext[1] + pad0]).nice();
  const outLane = hasOut ? 56 * sc + 10 : 0;
  const gap = hasOut ? 20 * sc : 0;
  const mainEnd = innerW - outLane - gap;
  const xMain = xMainNice.range([0, mainEnd]);
  const outExt = hasOut ? d3.extent(outVals) : [0, 1];
  const xOut = d3.scaleLinear().domain(outExt[0] === outExt[1] ? [outExt[0] - 1, outExt[1] + 1] : outExt)
    .range([mainEnd + gap + outLane * 0.35, innerW - outLane * 0.35]);
  const x = v => v > STRIP_BREAK_AT ? xOut(v) : xMain(v);

  const svg = d3.select(host).append("svg").attr("width", width).attr("height", height).attr("viewBox", `0 0 ${width} ${height}`);
  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

  const ticks = xMain.ticks(Math.max(4, Math.floor(mainEnd / 110))).filter(t => !hasOut || xMain(t) < mainEnd - 30);
  g.append("g").attr("class", "axis-grid").attr("transform", `translate(0,${innerH})`)
    .call(d3.axisBottom(xMain).tickValues(ticks).tickSize(-innerH).tickFormat(""));
  [["axisBottom", innerH], ["axisTop", 0]].forEach(([fn, ty]) => {
    const ax = g.append("g").attr("class", "axis").attr("transform", `translate(0,${ty})`)
      .call(d3[fn](xMain).tickValues(ticks).tickFormat(v => pct(v)).tickSizeOuter(0));
    ax.selectAll("text").style("font-size", `${axisFont}px`).attr("fill", "#374151");
    ax.select(".domain").attr("stroke", "#9ca3af");
    if (hasOut) {
      const a2 = g.append("g").attr("class", "axis").attr("transform", `translate(0,${ty})`)
        .call(d3[fn](xOut).tickValues(outVals).tickFormat(v => pct(v)).tickSizeOuter(0));
      a2.selectAll("text").style("font-size", `${axisFont}px`).attr("fill", "#374151");
      a2.select(".domain").attr("d", `M${mainEnd + gap},0H${innerW}`).attr("stroke", "#9ca3af");
    }
  });
  if (hasOut) {
    const b0 = mainEnd, b1 = mainEnd + gap, k = 5 * sc;
    [0, innerH].forEach(yy => g.append("path").attr("class", "brk")
      .attr("d", `M${b0 - k * 0.6},${yy + k}L${b0 + k * 0.6},${yy - k}M${b1 - k * 0.6},${yy + k}L${b1 + k * 0.6},${yy - k}`));
  }
  g.append("line").attr("class", "zero-line").attr("x1", xMain(0)).attr("x2", xMain(0)).attr("y1", 0).attr("y2", innerH);

  const annFont = Math.max(9, Math.min(12, LABEL_FS * sc + 1));
  const leaders = g.append("g").attr("class", "leaders");
  const labels = g.append("g").attr("class", "labels");
  const dots = g.append("g").attr("class", "dots");

  cs.forEach((c, i) => {
    const top = i * rowH;
    if (i > 0) g.append("line").attr("class", "row-rule").attr("x1", -labelW - 12).attr("x2", innerW).attr("y1", top).attr("y2", top);
    g.append("text").attr("class", "country-label").attr("x", -12).attr("y", top + rowH / 2).attr("dy", "0.35em")
      .attr("text-anchor", "end").style("font-size", `${phone ? 11 : 13}px`).text(cname(c));

    const laneY = { overall: top + rowH * 0.40, entry: top + rowH * 0.66 };
    const pts = [];
    LEVELS.forEach(l => {
      const items = DATA.filter(d => d.country === c && d.level === l).sort((a, b) => a.yoy - b.yoy);
      const placed = [];
      const step = r * 1.55;
      items.forEach(d => {
        const px = x(d.yoy);
        let py = 0;
        for (const kk of [0, -1, 1, -2, 2, -3, 3]) {
          if (!placed.some(p => Math.hypot(p.x - px, p.y - kk * step) < r * 1.9)) { py = kk * step; break; }
        }
        placed.push({ x: px, y: py });
        pts.push({ d, x: px, y: laneY[l] + py });
      });
    });

    const sym = d3.symbol(d3.symbolDiamond, Math.PI * r * r * 1.3);
    pts.forEach(p => {
      const el = p.d.level === "overall"
        ? dots.append("circle").attr("cx", p.x).attr("cy", p.y).attr("r", r)
        : dots.append("path").attr("d", sym()).attr("transform", `translate(${p.x},${p.y})`);
      el.attr("class", "point-dot").attr("fill", LEVEL_COLOR[p.d.level]).attr("stroke", "#fff").attr("stroke-width", 1.2)
        .datum(p.d)
        .on("mousemove", (e, d) => tipShow(e, tipFor(d))).on("mouseleave", tipHide);
    });

    const extreme = pick => {
      const v = pick(pts.map(p => p.d.yoy));
      const hits = pts.filter(p => p.d.yoy === v);
      return { p: hits[0], names: hits.map(h => h.d.occupation).join(" and ") };
    };
    const topY = top + annFont + 3, botY = top + rowH - 5;
    const draw = (E, anchor, y) => {
      const p = E.p;
      const lx = anchor === "start" ? Math.max(-4, p.x - 4) : Math.min(innerW, p.x + 4);
      const t = labels.append("text").attr("class", "dot-label").attr("x", lx)
        .attr("text-anchor", anchor).style("font-size", `${annFont}px`);
      t.append("tspan").text(E.names + " ");
      t.append("tspan").style("font-weight", 700).attr("fill", p.d.yoy > 0 ? GROW_DARK : DECL_DARK).text(pct(p.d.yoy));
      const ld = leaders.append("path").attr("class", "leader");
      const place = yy => {
        t.attr("y", yy);
        const dotEdge = yy < p.y ? p.y - r - 1 : p.y + r + 1;
        const lineY = yy < p.y ? yy + 3 : yy - annFont + 1;
        ld.attr("d", `M${p.x},${lineY}L${p.x},${dotEdge}`);
      };
      place(y);
      return { t, place };
    };
    const lo = draw(extreme(v => d3.min(v)), "start", topY);
    const hi = draw(extreme(v => d3.max(v)), "end", topY);
    const a = lo.t.node().getBBox(), b = hi.t.node().getBBox();
    if (b.x < a.x + a.width + 8) hi.place(botY);
  });

  const circ = `<svg width="14" height="14"><circle cx="7" cy="7" r="5.5" fill="${LEVEL_COLOR.overall}"/></svg>`;
  const dia = `<svg width="14" height="14"><path d="${d3.symbol(d3.symbolDiamond, 70)()}" transform="translate(7,7)" fill="${LEVEL_COLOR.entry}"/></svg>`;
  setLegend([
    `<div class="legend-item">${circ}<span>Overall</span></div>`,
    `<div class="legend-item">${dia}<span>Entry-level</span></div>`
  ]);
}

function treemapLeaves() {
  return Array.from(d3.group(DATA.filter(d => selectedCountries.has(d.country)), d => d.occupation), ([name, items]) => ({
    parent: themeOf(name),
    name,
    value: items.length,
    avg: d3.mean(items, d => d.yoy),
    lists: items.slice().sort((a, b) => COUNTRIES.indexOf(a.country) - COUNTRIES.indexOf(b.country) || LEVELS.indexOf(a.level) - LEVELS.indexOf(b.level))
  })).filter(d => d.value > 0);
}

function tmTipBody(d) {
  const lists = (d.lists || []).map(x => `${COUNTRY_SHORT[x.country]} ${LEVEL_LONG[x.level].toLowerCase()}, ${DIR_LABEL[x.direction].toLowerCase()} #${x.rank}, ${pct(x.yoy)}${x.mock ? " (Mock)" : ""}`).join("<br>");
  return "<strong>Theme:</strong> " + esc(d.parent) +
    "<br><strong>List slots:</strong> " + d.value +
    "<br><strong>Average YoY:</strong> " + pct(Math.round(d.avg * 10) / 10) +
    "<br><strong>In lists:</strong><br>" + lists + ((d.lists || []).some(x => x.mock) ? "<br><strong>Mock:</strong> includes mock values" : "");
}

function loadD3plus() {
  if (typeof d3plus !== "undefined") return Promise.resolve();
  if (!loadD3plus.p) {
    loadD3plus.p = new Promise((resolve, reject) => {
      const el = document.createElement("script");
      el.src = D3PLUS_URL;
      el.onload = resolve;
      el.onerror = () => { loadD3plus.p = null; reject(); };
      document.head.appendChild(el);
    });
  }
  return loadD3plus.p;
}

const tmLabelH = () => isPhone() ? 16 : 20;

function ensureTreemapInstance(width, height) {
  if (typeof d3plus === "undefined") return null;
  if (!treemapInstance) {
    treemapInstance = new d3plus.Treemap()
      .select("#treemap")
      .groupBy(["parent", "name"])
      .tooltip(!!SHOW_TOOLTIP)
      .tooltipConfig({ title: d => esc(d.name), body: tmTipBody, tbody: [] })
      .sum("value")
      .layoutPadding(2)
      .legend(false)
      .duration(TREEMAP_DURATION)
      .color(d => valToColor(d.avg))
      .shapeConfig({
        rx: 0,
        ry: 0,
        label: d => d.name,
        labelConfig: { fontColor: d => valText(d.avg) },
        stroke: d => d.depth === 0 ? TREEMAP_GROUP_STROKE : "transparent",
        strokeWidth: d => d.depth === 0 ? 3 : 0
      })
      .config({ label: d => d.name });
    const tm = treemapInstance._treemap;
    if (tm && typeof tm.padding === "function" && typeof tm.paddingTop === "function") {
      const basePadding = tm.padding;
      tm.padding = function (p) {
        if (!arguments.length) return basePadding.call(tm);
        basePadding.call(tm, p);
        tm.paddingTop(n => n.depth === 1 ? tmLabelH() : (typeof p === "function" ? p(n) : +p));
        return tm;
      };
    }
  }
  if (width) treemapInstance.width(width);
  if (height) treemapInstance.height(height);
  return treemapInstance;
}

function buildTreemapLegend() {
  if (tmLegendInitialized) return;
  tmLegendInitialized = true;
  const legend = document.getElementById("tm-legend");
  const stops = d3.range(25).map(i => `${valToColor(i === 12 ? 0 : (i / 24 - 0.5) * 2 * RAMP_MAX)} ${(i / 24 * 100).toFixed(1)}%`).join(",");
  legend.innerHTML = `<span class="tm-key"><span>Average YoY ${pct(-RAMP_MAX)}</span><i style="background:linear-gradient(to right,${stops})"></i><span>${pct(RAMP_MAX)}</span></span>`;
}

let tmLeaves = [];

function renderTreemap() {
  const host = document.getElementById("treemap");
  const { w, h } = panelSize(host);
  if (w <= 0 || h <= 0) return;
  buildTreemapLegend();
  setLegend([]);
  if (typeof d3plus === "undefined") {
    if (loadD3plus.waiting) return;
    loadD3plus.waiting = true;
    host.innerHTML = `<div class="error-message">Loading treemap</div>`;
    loadD3plus().then(() => {
      loadD3plus.waiting = false;
      host.innerHTML = "";
      if (activeTab === "treemap") renderTreemap();
    }).catch(() => {
      loadD3plus.waiting = false;
      host.innerHTML = `<div class="error-message">Treemap library failed to load</div>`;
    });
    return;
  }
  const instance = ensureTreemapInstance(w, h);
  if (tmBusy) { tmPending = true; return; }
  tmBusy = true;
  d3.selectAll("#treemap g.tm-groups").remove();
  tmLeaves = treemapLeaves();
  instance.data(tmLeaves).render(() => {
    setTimeout(() => {
      tmBusy = false;
      drawTreemapGroups();
      if (tmPending) { tmPending = false; if (activeTab === "treemap") renderTreemap(); }
    }, TREEMAP_DURATION + 50);
  });
}

function drawTreemapGroups() {
  const layer = d3.select("#treemap g.d3plus-Treemap");
  if (layer.empty()) return;
  const svg = d3.select(layer.node().parentNode);
  svg.selectAll("g.tm-groups").remove();
  const live = new Set(tmLeaves.map(d => d.parent + "|" + d.name));
  const slots = d3.rollup(tmLeaves, v => d3.sum(v, d => d.value), d => d.parent);
  const boxes = new Map();
  layer.selectAll("rect").each(function (d) {
    if (!d || !d.data || !d.parent || d.parent.x0 == null || !live.has(d.data.parent + "|" + d.data.name)) return;
    boxes.set(d.data.parent, d.parent);
  });
  const g = svg.append("g").attr("class", "tm-groups").attr("transform", layer.attr("transform")).style("pointer-events", "none");
  const lh = tmLabelH(), fs = isPhone() ? 10.5 : 12.5;
  boxes.forEach((b, theme) => {
    g.append("rect").attr("x", b.x0 - 1).attr("y", b.y0 - 1).attr("width", b.x1 - b.x0 + 2).attr("height", b.y1 - b.y0 + 2)
      .attr("fill", "none").attr("stroke", TREEMAP_GROUP_STROKE).attr("stroke-width", 3);
    const maxW = b.x1 - b.x0 - 6;
    const t = g.append("text").attr("class", "tm-group-label").attr("x", b.x0 + 3).attr("y", b.y0 + lh - 5).style("font-size", fs + "px");
    t.append("tspan").text(theme);
    const n = slots.get(theme) || 0;
    const tn = t.append("tspan").attr("class", "tm-n").text(` ${n} slot${n === 1 ? "" : "s"}`);
    if (t.node().getComputedTextLength() > maxW) tn.remove();
    const main = t.select("tspan");
    let label = theme;
    while (t.node().getComputedTextLength() > maxW && label.length > 1) {
      label = label.slice(0, -1);
      main.text(label.trimEnd() + "…");
    }
    if (maxW < 14) t.remove();
  });
}

function measureWidth(svg, text, fs, weight) {
  const t = svg.append("text").style("font-size", fs + "px").style("font-weight", weight).text(text);
  const w = t.node().getComputedTextLength();
  t.remove();
  return w;
}

function renderPairs() {
  const host = document.getElementById("pairs");
  host.innerHTML = "";
  const phone = isPhone();
  const { w: width, h: height } = panelSize(host);
  if (width <= 0 || height <= 0) return;
  const sc = Math.max(0.6, Math.min(1, Math.min(width / 1080, height / 720)));
  const PP = PAIRS.filter(p => selectedCountries.has(p.country));
  if (!PP.length) { host.innerHTML = `<div class="error-message">No occupation is in both lists for the selected countries</div>`; setLegend([]); return; }
  const margin = { top: 16, right: 16, bottom: 48, left: phone ? 52 : 70 };
  const availW = Math.max(50, width - margin.left - margin.right);
  const availH = Math.max(50, height - margin.top - margin.bottom);
  const innerW = availW, innerH = availH;

  const xExt = d3.extent(PP, p => p.overall.yoy);
  const xPad = Math.max((xExt[1] - xExt[0]) * 0.10, 1);
  const xDom = d3.scaleLinear().domain([xExt[0] - xPad, xExt[1] + xPad]).nice().domain();
  const gExt = d3.extent(PP.map(p => p.gap).concat([0]));
  const gPad = Math.max((gExt[1] - gExt[0]) * PAIRS_GAP_HEADROOM, 1);
  const yDom = d3.scaleLinear().domain([gExt[0] - gPad, gExt[1] + gPad]).nice().domain();
  const x = d3.scaleLinear().domain(xDom).range([0, innerW]);
  const y = d3.scaleLinear().domain(yDom).range([innerH, 0]);
  const pts = v => (v === 0 ? "0" : signed(v)) + " pts";

  const svg = d3.select(host).append("svg").attr("width", width).attr("height", height).attr("viewBox", `0 0 ${width} ${height}`);
  const root = svg.append("g").attr("class", "plot-area").attr("transform", `translate(${margin.left},${margin.top})`);
  const frame = root.append("g").attr("class", "frame");
  const gridY = root.append("g").attr("class", "axis-grid grid-y");
  const gridX = root.append("g").attr("class", "axis-grid grid-x");
  const axisX = root.append("g").attr("class", "axis axis-x");
  const axisY = root.append("g").attr("class", "axis axis-y");
  const leadersG = root.append("g").attr("class", "leaders");
  const labelsG = root.append("g").attr("class", "labels");
  const dotsG = root.append("g").attr("class", "dots");

  frame.append("rect").attr("x", 0).attr("y", 0).attr("width", innerW).attr("height", y(0)).attr("fill", "rgba(39,86,211,.045)");
  frame.append("rect").attr("x", 0).attr("y", y(0)).attr("width", innerW).attr("height", innerH - y(0)).attr("fill", "rgba(242,169,0,.06)");
  if (x(0) > 0 && x(0) < innerW) frame.append("line").attr("class", "zero-line").attr("x1", x(0)).attr("x2", x(0)).attr("y1", 0).attr("y2", innerH);

  const nT = Math.max(4, Math.floor(innerW / 110));
  const nTy = Math.max(4, Math.floor(innerH / 70));
  gridY.call(d3.axisLeft(y).ticks(nTy).tickSize(-innerW).tickFormat(""));
  gridX.attr("transform", `translate(0,${innerH})`).call(d3.axisBottom(x).ticks(nT).tickSize(-innerH).tickFormat(""));
  axisX.attr("transform", `translate(0,${innerH})`).call(d3.axisBottom(x).ticks(nT).tickFormat(v => pct(v)));
  axisY.call(d3.axisLeft(y).ticks(nTy).tickFormat(v => v === 0 ? "0" : signed(v)));
  frame.append("line").attr("class", "split-line").attr("x1", 0).attr("x2", innerW).attr("y1", y(0)).attr("y2", y(0));
  [axisX, axisY].forEach(a => { a.selectAll("text").attr("font-size", 11).attr("fill", "#374151"); a.select(".domain").attr("stroke", "#9ca3af"); });

  svg.append("text").attr("class", "axis-label").attr("text-anchor", "middle")
    .attr("x", margin.left + innerW / 2).attr("y", height - 10).text("Overall YoY hiring change");
  svg.append("text").attr("class", "axis-label").attr("text-anchor", "middle")
    .attr("transform", `translate(14,${margin.top + innerH / 2}) rotate(-90)`).text(phone ? "Entry minus overall, pts" : "Entry-level minus overall, percentage points");

  const noteFS = Math.max(9, 12 * sc);
  root.append("text").attr("class", "region-note").attr("x", 8 * sc).attr("y", 16 * sc).style("font-size", noteFS + "px").text("Entry-level did better");
  root.append("text").attr("class", "region-note").attr("x", innerW - 8 * sc).attr("y", innerH - 10 * sc).attr("text-anchor", "end").style("font-size", noteFS + "px").text("Entry-level did worse");

  const dotR = Math.max(3.5, Math.min(6.4, innerW / 120));
  const reach = dotR + 5 * sc;
  const xMinText = 2, xMaxText = innerW - 2;
  const labelText = p => `${p.occupation} (${COUNTRY_SHORT[p.country]})`;
  let labelFS = LABEL_FS * Math.max(sc, 0.85), nameW = {};
  for (;;) {
    PP.forEach(p => { nameW[p.id] = measureWidth(svg, labelText(p), labelFS, 400); });
    const stuck = PP.some(p => {
      const cx = x(p.overall.yoy), w = nameW[p.id];
      return cx - reach - w < xMinText && cx + reach + w > xMaxText;
    });
    if (!stuck || labelFS <= LABEL_FS_MIN) break;
    labelFS = Math.max(LABEL_FS_MIN, labelFS - 0.35);
  }
  const same = d3.group(PP, p => p.overall.yoy + "|" + p.entry.yoy);
  const nudge = p => {
    const grp = same.get(p.overall.yoy + "|" + p.entry.yoy);
    if (grp.length < 2) return 0;
    return (grp.indexOf(p) - (grp.length - 1) / 2) * dotR * 1.8;
  };
  const dotsXY = PP.map(p => ({ id: p.id, x: x(p.overall.yoy) + nudge(p), y: y(p.gap) }));
  const hits = (p, sd, cx, cy, w) => {
    const x0 = sd < 0 ? cx - reach - w : cx + reach, x1 = x0 + w, y0 = cy - labelFS * 0.6, y1 = cy + labelFS * 0.6;
    return dotsXY.filter(o => o.id !== p.id && o.x + dotR > x0 && o.x - dotR < x1 && o.y + dotR > y0 && o.y - dotR < y1).length;
  };
  const placed = PP.map(p => {
    const cx = x(p.overall.yoy) + nudge(p), cy = y(p.gap), w = nameW[p.id];
    const prefer = p.gap >= 0 ? -1 : 1;
    const fitsLeft = cx - reach - w >= xMinText;
    const fitsRight = cx + reach + w <= xMaxText;
    let side = prefer < 0 ? (fitsLeft ? -1 : (fitsRight ? 1 : -1)) : (fitsRight ? 1 : (fitsLeft ? -1 : 1));
    if (fitsLeft && fitsRight && hits(p, side, cx, cy, w) > hits(p, -side, cx, cy, w)) side = -side;
    const half = (same.get(p.overall.yoy + "|" + p.entry.yoy).length - 1) / 2 * dotR * 1.8;
    let lx = x(p.overall.yoy) + side * (reach + half);
    lx = side < 0 ? Math.max(lx, xMinText + w) : Math.min(lx, xMaxText - w);
    return { ...p, cx, cy, side, lx };
  });
  [0].forEach(sd => {
    const grp = placed.filter(d => !sd || d.side === sd).sort((a, b) => a.cy - b.cy);
    const ys = declump(grp.map(d => d.cy), 4, innerH - 4, labelFS + 3 * sc);
    grp.forEach((d, i) => { d.ly = ys[i]; });
  });

  placed.forEach(d => {
    const lx = d.lx;
    if (Math.abs(d.ly - d.cy) > 2 || Math.abs(lx - d.cx) > reach + 1) {
      leadersG.append("path").attr("class", "leader hit").attr("data-k", d.id)
        .attr("d", `M${d.cx + d.side * (dotR + 1)},${d.cy}L${lx - d.side * 2},${d.ly}`);
    }
    labelsG.append("text").attr("class", "dot-label hit").attr("data-k", d.id)
      .attr("x", lx).attr("y", d.ly).attr("dy", "0.35em").attr("text-anchor", d.side < 0 ? "end" : "start")
      .style("font-size", labelFS + "px").text(labelText(d))
      .call(t => { if (phone) t.attr("stroke", "#fff").attr("stroke-width", 3).attr("stroke-linejoin", "round").style("paint-order", "stroke"); });
  });
  const tipPair = p => `<span class="t-name">${esc(p.occupation)}</span><span class="t-q" style="color:${colourOf(p.country)}">${esc(p.country)}</span>` +
    row("Overall", pct(p.overall.yoy)) + row("Entry-level", pct(p.entry.yoy)) + row("Entry minus overall", pts(p.gap)) +
    `<span class="t-note">Overall rank ${p.overall.rank} in the ${DIR_LABEL[p.overall.direction].toLowerCase()} list. Entry-level rank ${p.entry.rank} in the ${DIR_LABEL[p.entry.direction].toLowerCase()} list.</span>` + mockTag(p.overall);
  dotsG.selectAll("circle").data(placed, d => d.id).join("circle")
    .attr("class", "point-dot hit").attr("data-k", d => d.id)
    .attr("cx", d => d.cx).attr("cy", d => d.cy).attr("r", dotR)
    .attr("fill", d => colourOf(d.country)).attr("stroke", "#fff").attr("stroke-width", 1.2)
    .on("mouseover", function () { d3.select(this).interrupt().attr("r", dotR + 2); })
    .on("mousemove", (e, d) => tipShow(e, tipPair(d)))
    .on("mouseout", function () { d3.select(this).interrupt().attr("r", dotR); tipHide(); });

  const node = svg.node();
  node.addEventListener("mouseover", e => {
    const hit = e.target.closest("[data-k]");
    node.querySelectorAll(".hovered").forEach(n => n.classList.remove("hovered"));
    if (!hit) { node.classList.remove("dim"); return; }
    node.classList.add("dim");
    node.querySelectorAll(`[data-k="${CSS.escape(hit.dataset.k)}"]`).forEach(n => n.classList.add("hovered"));
  });
  node.addEventListener("mouseleave", () => { node.classList.remove("dim"); node.querySelectorAll(".hovered").forEach(n => n.classList.remove("hovered")); });

  setLegend([`<div class="legend-item"><svg width="22" height="10"><line x1="1" y1="5" x2="21" y2="5" class="split-line"/></svg><span>Same rate</span></div>`]);
}

const mockTag = d => d && d.mock ? `<span class="t-mock">Mock</span>` : "";
const anyMock = rows => rows.some(d => d.mock) ? `<span class="t-mock">Includes mock values</span>` : "";

function renderBump() {
  const host = document.getElementById("bump");
  host.innerHTML = "";
  const phone = isPhone();
  const { w: width, h: height } = panelSize(host);
  if (width <= 0 || height <= 0) return;
  updateFieldMenu();
  const field = talentField;
  const { years, bump } = bumpFor(field);
  const N = COUNTRIES.filter(c => (bump.get(c) || []).length).length;
  const many = N > MAX_COLOURED;
  const series = COUNTRIES.map(c => ({ label: c, values: bump.get(c) || [], on: selectedCountries.has(c) }))
    .filter(d => d.values.length)
    .sort((a, b) => a.on - b.on);
  series.forEach(d => { d.color = d.on ? colourOf(d.label) : MUTED; d.labelled = d.on || !many; });

  const svg = d3.select(host).append("svg").attr("id", "chart").attr("role", "img")
    .attr("aria-label", `Rank of each country by share of members in ${field} with AI engineering talent, by year`)
    .attr("width", width).attr("height", height).attr("viewBox", `0 0 ${width} ${height}`);
  const labelFS = phone ? 10.5 : Math.max(10, Math.min(14, width / 90));
  const labelW = d3.max(series.filter(d => d.labelled), d => measureWidth(svg, cname(d.label), labelFS, 700)) || 0;
  const rankW = measureWidth(svg, "#" + N, 11, 600) + 6;
  const compactH = window.innerHeight < 500;
  const margin = compactH ? { top: 8, right: 8, bottom: 8, left: 8 }
    : { top: 20, right: labelW + 16, bottom: 34, left: rankW + labelW + 16 };
  const x = d3.scalePoint().domain(years).range([margin.left, width - margin.right]).padding(0.5);
  const y = d3.scaleLinear().domain([N + 0.5, 0.5]).range([height - margin.bottom, margin.top]);
  const rankStep = (height - margin.top - margin.bottom) / N;
  const lineWidth = Math.max(1.4, Math.min(3.4, rankStep * 0.28, x.step() * 0.12));
  const pointR = Math.max(2.2, Math.min(7, rankStep * 0.34, x.step() * 0.26));

  svg.append("g").attr("class", "grid-lines").selectAll("line").data(d3.range(1, N + 1)).join("line")
    .attr("x1", margin.left).attr("x2", width - margin.right)
    .attr("y1", d => y(d)).attr("y2", d => y(d))
    .attr("stroke", "rgba(15, 23, 42, 0.08)").attr("stroke-dasharray", "4,4");
  const rankEvery = rankStep >= 12 ? 1 : 5;
  svg.append("g").attr("class", "axis--y").selectAll("text")
    .data(d3.range(1, N + 1).filter(r => r === 1 || r % rankEvery === 0)).join("text")
    .attr("class", "rank-label").attr("x", 4).attr("y", d => y(d)).attr("dy", "0.35em")
    .style("font-size", "11px").text(d => "#" + d);
  const yearEvery = x.step() < 34 ? 2 : 1;
  svg.append("g").attr("class", "axis--x").selectAll("text")
    .data(years.filter((yr, i) => i % yearEvery === 0 || i === years.length - 1)).join("text")
    .attr("class", "rank-label").attr("x", d => x(d)).attr("y", height - margin.bottom + 20)
    .attr("text-anchor", "middle").style("font-size", (phone ? 10 : 12) + "px").text(d => d);

  const lineGen = d3.line().x(d => x(d.year)).y(d => y(d.rank)).curve(d3.curveMonotoneX);
  const groups = svg.append("g").attr("class", "series-group").selectAll(".series").data(series, d => d.label).join("g")
    .attr("class", "series").attr("data-label", d => d.label);
  groups.append("path").attr("class", "series-line").attr("stroke", d => d.color).attr("d", d => lineGen(d.values))
    .style("--lineWidth", d => `${d.on ? lineWidth : Math.max(1, lineWidth * 0.6)}px`);
  groups.selectAll(".series-point").data(d => d.values.map(v => ({ ...v, country: d.label, color: d.color, on: d.on }))).join("circle")
    .attr("class", "series-point").attr("r", d => d.on ? pointR : pointR * 0.7)
    .attr("cx", d => x(d.year)).attr("cy", d => y(d.rank)).attr("fill", d => d.color)
    .on("mousemove", (e, d) => tipShow(e, `<span class="t-name">${esc(d.country)}</span><span class="t-q">${esc(d.field)} / ${d.year}</span>` +
      row("Rank", `#${d.rank} of ${N}`) + row("AI engineering talent", share1(d.value)) +
      (d.tied.length ? `<span class="t-note">Tied with ${d.tied.map(esc).join(", ")}. Order follows the year before.</span>` : "") +
      `<span class="t-note">Share of members in ${esc(d.field)} with AI engineering talent</span>` + mockTag(d)))
    .on("mouseleave", tipHide);
  const firstX = x(years[0]) - 12, lastX = x(years[years.length - 1]) + 12;
  const lab = groups.filter(d => d.labelled);
  const start = lab.append("text").attr("class", "series-label series-label-start").attr("x", firstX)
    .attr("y", d => y(d.values[0].rank)).attr("text-anchor", "end").attr("dy", "0.35em");
  const end = lab.append("text").attr("class", "series-label series-label-end").attr("x", lastX)
    .attr("y", d => y(d.values[d.values.length - 1].rank)).attr("text-anchor", "start").attr("dy", "0.35em");
  [start, end].forEach(sel => sel.attr("fill", d => d.on ? d.color : "#9ca3af").style("font-size", labelFS + "px")
    .style("font-weight", d => d.on ? 700 : 400).text(d => cname(d.label))
    .attr("role", "button").attr("tabindex", 0)
    .on("keydown", (e, d) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); lock(d.label); } }));

  const apply = hover => {
    const hl = bumpSelected || hover;
    groups.classed("highlighted", d => !!hl && d.label === hl).classed("dim", d => !!hl && d.label !== hl);
  };
  const lock = c => { bumpSelected = bumpSelected === c ? null : c; apply(null); };
  if (bumpSelected && !series.some(d => d.label === bumpSelected)) bumpSelected = null;
  groups.on("mouseenter", (e, d) => { if (!bumpSelected) apply(d.label); })
    .on("mouseleave", () => apply(null))
    .on("click", (e, d) => { e.stopPropagation(); lock(d.label); });
  svg.on("click", () => { bumpSelected = null; apply(null); });
  apply(null);
  setLegend([]);
}

const COUNTRIES_FRAMING = "axes";
const COUNTRIES_LABELS = "flank";

function renderCountries() {
  const host = document.getElementById("countries");
  host.innerHTML = "";
  const phone = isPhone();
  const { w: width, h: height } = panelSize(host);
  if (width <= 0 || height <= 0) return;
  const sc = Math.max(0.6, Math.min(1, Math.min(width / 1080, height / 720)));
  const byC = d3.group(EXTRA.allJobs, d => d.country);
  const pts = COUNTRIES.filter(c => byC.has(c)).map(c => {
    const ov = byC.get(c).find(d => d.level === "overall"), en = byC.get(c).find(d => d.level === "entry");
    return ov && en ? { id: c, country: c, overall: ov.value, entry: en.value, gap: en.value - ov.value, mock: ov.mock || en.mock, on: selectedCountries.has(c) } : null;
  }).filter(Boolean);
  if (!pts.length) { host.innerHTML = `<div class="error-message">No data available</div>`; setLegend([]); return; }
  const margin = { top: 16, right: 16, bottom: 48, left: phone ? 52 : 70 };
  const innerW = Math.max(50, width - margin.left - margin.right);
  const innerH = Math.max(50, height - margin.top - margin.bottom);
  const ext = d3.extent(pts.flatMap(p => [p.overall, p.entry]));
  const pad0 = Math.max((ext[1] - ext[0]) * 0.10, 1);
  const dom = d3.scaleLinear().domain([ext[0] - pad0, ext[1] + pad0]).nice().domain();
  const x = d3.scaleLinear().domain(dom).range([0, innerW]);
  const y = d3.scaleLinear().domain(dom).range([innerH, 0]);

  const svg = d3.select(host).append("svg").attr("width", width).attr("height", height).attr("viewBox", `0 0 ${width} ${height}`);
  const root = svg.append("g").attr("class", "plot-area").attr("transform", `translate(${margin.left},${margin.top})`);
  const frame = root.append("g").attr("class", "frame");
  const gridY = root.append("g").attr("class", "axis-grid grid-y");
  const gridX = root.append("g").attr("class", "axis-grid grid-x");
  const axisX = root.append("g").attr("class", "axis axis-x");
  const axisY = root.append("g").attr("class", "axis axis-y");
  const leadersG = root.append("g").attr("class", "leaders");
  const labelsG = root.append("g").attr("class", "labels");
  const dotsG = root.append("g").attr("class", "dots");

  frame.append("path").attr("d", `M0,${y(dom[0])}L0,${y(dom[1])}L${x(dom[1])},${y(dom[1])}Z`).attr("fill", "rgba(39,86,211,.045)");
  frame.append("path").attr("d", `M0,${y(dom[0])}L${x(dom[1])},${y(dom[0])}L${x(dom[1])},${y(dom[1])}Z`).attr("fill", "rgba(242,169,0,.06)");
  if (dom[0] < 0 && dom[1] > 0) {
    frame.append("line").attr("class", "zero-line").attr("x1", x(0)).attr("x2", x(0)).attr("y1", 0).attr("y2", innerH);
    frame.append("line").attr("class", "zero-line").attr("x1", 0).attr("x2", innerW).attr("y1", y(0)).attr("y2", y(0));
  }
  frame.append("line").attr("class", "split-line").attr("x1", x(dom[0])).attr("y1", y(dom[0])).attr("x2", x(dom[1])).attr("y2", y(dom[1]));

  const nT = Math.max(4, Math.floor(innerW / 110));
  const nTy = Math.max(4, Math.floor(innerH / 70));
  gridY.call(d3.axisLeft(y).ticks(nTy).tickSize(-innerW).tickFormat(""));
  gridX.attr("transform", `translate(0,${innerH})`).call(d3.axisBottom(x).ticks(nT).tickSize(-innerH).tickFormat(""));
  axisX.attr("transform", `translate(0,${innerH})`).call(d3.axisBottom(x).ticks(nT).tickFormat(v => pct(v)));
  axisY.call(d3.axisLeft(y).ticks(nTy).tickFormat(v => pct(v)));
  [axisX, axisY].forEach(a => { a.selectAll("text").attr("font-size", 11).attr("fill", "#374151"); a.select(".domain").attr("stroke", "#9ca3af"); });
  svg.append("text").attr("class", "axis-label").attr("text-anchor", "middle")
    .attr("x", margin.left + innerW / 2).attr("y", height - 10).text(phone ? "Overall YoY hiring rate" : "Overall YoY change in LinkedIn hiring rate");
  svg.append("text").attr("class", "axis-label").attr("text-anchor", "middle")
    .attr("transform", `translate(14,${margin.top + innerH / 2}) rotate(-90)`).text(phone ? "Entry-level YoY hiring rate" : "Entry-level YoY change in LinkedIn hiring rate");
  const noteFS = Math.max(9, 12 * sc);
  root.append("text").attr("class", "region-note").attr("x", 8 * sc).attr("y", 16 * sc).style("font-size", noteFS + "px").text("Entry-level did better");
  root.append("text").attr("class", "region-note").attr("x", innerW - 8 * sc).attr("y", innerH - 10 * sc).attr("text-anchor", "end").style("font-size", noteFS + "px").text("Entry-level did worse");

  const many = pts.length > 12;
  const dotR = Math.max(3.5, Math.min(many ? 5.5 : 7, innerW / 110));
  pts.forEach(p => { p.cx = x(p.overall); p.cy = y(p.entry); });
  const minGap = dotR * 2 + 1;
  for (let pass = 0; pass < 6; pass++) {
    for (let i = 0; i < pts.length; i++) for (let j = i + 1; j < pts.length; j++) {
      const a = pts[i], b = pts[j];
      const dx = b.cx - a.cx, dy = b.cy - a.cy, d = Math.hypot(dx, dy);
      if (d >= minGap) continue;
      const ux = d > 0.01 ? dx / d : 1, uy = d > 0.01 ? dy / d : 0, push = (minGap - d) / 2;
      a.cx -= ux * push; a.cy -= uy * push; b.cx += ux * push; b.cy += uy * push;
    }
  }
  const reach = dotR + 5 * sc;
  const xMinText = 2, xMaxText = innerW - 2;
  const labelled = pts.filter(p => p.on);
  const labelText = p => cname(p.country);
  let labelFS = LABEL_FS * Math.max(sc, 0.85), nameW = {};
  for (;;) {
    labelled.forEach(p => { nameW[p.id] = measureWidth(svg, labelText(p), labelFS, 600); });
    const stuck = labelled.some(p => { const cx = p.cx, w = nameW[p.id]; return cx - reach - w < xMinText && cx + reach + w > xMaxText; });
    if (!stuck || labelFS <= LABEL_FS_MIN) break;
    labelFS = Math.max(LABEL_FS_MIN, labelFS - 0.35);
  }
  const hits = (p, sd, cx, cy, w) => {
    const x0 = sd < 0 ? cx - reach - w : cx + reach, x1 = x0 + w, y0 = cy - labelFS * 0.6, y1 = cy + labelFS * 0.6;
    return pts.filter(o => o.id !== p.id && o.cx + dotR > x0 && o.cx - dotR < x1 && o.cy + dotR > y0 && o.cy - dotR < y1).length;
  };
  const placed = labelled.map(p => {
    const cx = p.cx, cy = p.cy, w = nameW[p.id];
    const prefer = p.gap >= 0 ? -1 : 1;
    const fitsLeft = cx - reach - w >= xMinText, fitsRight = cx + reach + w <= xMaxText;
    let side = prefer < 0 ? (fitsLeft ? -1 : (fitsRight ? 1 : -1)) : (fitsRight ? 1 : (fitsLeft ? -1 : 1));
    if (fitsLeft && fitsRight && hits(p, side, cx, cy, w) > hits(p, -side, cx, cy, w)) side = -side;
    let lx = cx + side * reach;
    lx = side < 0 ? Math.max(lx, xMinText + w) : Math.min(lx, xMaxText - w);
    return { ...p, cx, cy, side, lx };
  });
  [-1, 1].forEach(sd => {
    const grp = placed.filter(d => d.side === sd).sort((a, b) => a.cy - b.cy);
    const ys = declump(grp.map(d => d.cy), 4, innerH - 4, labelFS + 3 * sc);
    grp.forEach((d, i) => { d.ly = ys[i]; });
  });
  placed.forEach(d => {
    if (Math.abs(d.ly - d.cy) > 2 || Math.abs(d.lx - d.cx) > reach + 1) {
      leadersG.append("path").attr("class", "leader hit").attr("data-k", d.id)
        .attr("d", `M${d.cx + d.side * (dotR + 1)},${d.cy}L${d.lx - d.side * 2},${d.ly}`);
    }
    labelsG.append("text").attr("class", "dot-label hit").attr("data-k", d.id)
      .attr("x", d.lx).attr("y", d.ly).attr("dy", "0.35em").attr("text-anchor", d.side < 0 ? "end" : "start")
      .style("font-size", labelFS + "px").style("font-weight", 600).text(labelText(d));
  });
  const tip = p => `<span class="t-name">${esc(p.country)}</span><span class="t-q">All jobs, Apr to Jun 2026</span>` +
    row("Entry-level", pct1(p.entry), LEVEL_COLOR.entry) + row("Overall", pct1(p.overall), LEVEL_COLOR.overall) +
    row("Entry minus overall", pts1(p.gap)) + mockTag(p);
  dotsG.selectAll("circle").data(pts.slice().sort((a, b) => a.on - b.on), d => d.id).join("circle")
    .attr("class", "point-dot hit").attr("data-k", d => d.id)
    .attr("cx", d => d.cx).attr("cy", d => d.cy).attr("r", d => d.on ? dotR : dotR * 0.75)
    .attr("fill", d => d.on ? colourOf(d.country) : MUTED).attr("stroke", "#fff").attr("stroke-width", 1.2)
    .on("mouseover", function (e, d) { d3.select(this).interrupt().attr("r", (d.on ? dotR : dotR * 0.75) + 2); })
    .on("mousemove", (e, d) => tipShow(e, tip(d)))
    .on("mouseout", function (e, d) { d3.select(this).interrupt().attr("r", d.on ? dotR : dotR * 0.75); tipHide(); });
  const node = svg.node();
  node.addEventListener("mouseover", e => {
    const hit = e.target.closest("[data-k]");
    node.querySelectorAll(".hovered").forEach(n => n.classList.remove("hovered"));
    if (!hit) { node.classList.remove("dim"); return; }
    node.classList.add("dim");
    node.querySelectorAll(`[data-k="${CSS.escape(hit.dataset.k)}"]`).forEach(n => n.classList.add("hovered"));
  });
  node.addEventListener("mouseleave", () => { node.classList.remove("dim"); node.querySelectorAll(".hovered").forEach(n => n.classList.remove("hovered")); });
  setLegend([`<div class="legend-item"><svg width="22" height="10"><line x1="1" y1="9" x2="21" y2="1" class="split-line"/></svg><span>Same rate</span></div>`]);
}

function init() {
  tooltip = document.createElement("div");
  tooltip.id = "tooltip";
  document.body.appendChild(tooltip);

  SELECTOR_GROUPS.forEach(initPill);
  const themeGroup = document.getElementById("theme-view");
  document.querySelectorAll("#tabs .selector-button").forEach(b => b.addEventListener("click", () => setTab(b.dataset.tab, true)));
  themeGroup.querySelectorAll(".selector-button").forEach(b => b.addEventListener("click", () => {
    themeGroup.querySelectorAll(".selector-button").forEach(x => x.classList.toggle("active", x === b));
    positionPill(themeGroup);
    themeView = b.dataset.view;
    renderThemes();
  }));
  document.querySelectorAll("#data-mode .selector-button").forEach(b => b.addEventListener("click", () => switchMode(b.dataset.mode)));

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

  loadMode("real").then(bundle => {
    applyMode("real", bundle, false);
    const rc = vizEl.getBoundingClientRect();
    lastW = rc.width; lastH = rc.height;
    setTab((location.hash || "").slice(1) || DEFAULT_TAB, false);
  }).catch(err => {
    console.error(err);
    const el = document.createElement("div");
    el.style.cssText = "display:flex;align-items:center;justify-content:center;height:100%;font-family:system-ui,sans-serif;color:#666;";
    el.textContent = "No data available";
    vizEl.appendChild(el);
  });
}

init();
