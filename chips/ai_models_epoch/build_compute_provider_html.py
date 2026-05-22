"""Generate proprietary_compute.html — visualizes which compute provider trained
each proprietary (closed-weight) notable AI model whose training hardware is known.

Source: Epoch AI notable_ai_models.csv (snapshot 2026-04-29)
Output: proprietary_compute.html (self-contained, no network deps except Chart.js CDN)
"""
import json
import pandas as pd
from pathlib import Path

SRC = Path(__file__).parent / "notable_ai_models.csv"
OUT = Path(__file__).parent / "proprietary_compute.html"


def classify_provider(hw: str) -> str:
    """Map a training-hardware string to a single compute-provider label."""
    if not isinstance(hw, str) or not hw.strip():
        return "Unknown"
    parts = [p.strip() for p in hw.split(",")]
    providers = set()
    for p in parts:
        low = p.lower()
        if "nvidia" in low:
            providers.add("NVIDIA")
        elif "google tpu" in low or low.startswith("tpu"):
            providers.add("Google TPU")
        elif "huawei" in low or "ascend" in low:
            providers.add("Huawei Ascend")
        elif "amazon" in low or "trainium" in low or "inferentia" in low:
            providers.add("Amazon Trainium")
        elif "amd" in low or "instinct" in low or "mi300" in low or "mi250" in low:
            providers.add("AMD")
        elif "intel" in low or "gaudi" in low:
            providers.add("Intel Gaudi")
        elif "cerebras" in low:
            providers.add("Cerebras")
        elif "graphcore" in low or "ipu" in low:
            providers.add("Graphcore")
        else:
            providers.add("Other")
    if len(providers) == 1:
        return next(iter(providers))
    return "Mixed (" + " + ".join(sorted(providers)) + ")"


def primary_provider(label: str) -> str:
    """For coloring, collapse 'Mixed (...)' back to a single bucket."""
    if label.startswith("Mixed"):
        return "Mixed"
    return label


df = pd.read_csv(SRC, low_memory=False)

# Filter: proprietary = not open weights
prop = df[df["Open model weights?"].fillna("No") == "No"].copy()
# Known hardware
known = prop[prop["Training hardware"].notna()].copy()

known["provider_full"] = known["Training hardware"].apply(classify_provider)
known["provider"] = known["provider_full"].apply(primary_provider)
known["year"] = pd.to_datetime(known["Publication date"], errors="coerce").dt.year

# Order by date desc
known = known.sort_values("Publication date", ascending=False, na_position="last").reset_index(drop=True)

cols_keep = [
    "Model", "Organization", "Publication date", "year",
    "Training hardware", "Hardware quantity",
    "provider", "provider_full",
    "Model accessibility", "Frontier model",
    "Parameters", "Training compute (FLOP)",
    "Country (of organization)",
    "Link",
]
records = (
    known[cols_keep]
    .where(known[cols_keep].notna(), None)
    .to_dict(orient="records")
)

# Clean NaN → None and convert numpy types
def clean(v):
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    if hasattr(v, "item"):
        try:
            return v.item()
        except Exception:
            pass
    return v


records = [{k: clean(v) for k, v in r.items()} for r in records]

# Year-by-provider counts
year_provider = (
    known.groupby(["year", "provider"]).size().unstack(fill_value=0).sort_index()
)
years = [int(y) for y in year_provider.index if pd.notna(y)]
providers_in_order = ["NVIDIA", "Google TPU", "Huawei Ascend", "Amazon Trainium", "AMD", "Intel Gaudi", "Mixed", "Other"]
providers_in_order = [p for p in providers_in_order if p in year_provider.columns]
series = {p: [int(year_provider.loc[y, p]) if y in year_provider.index else 0 for y in years] for p in providers_in_order}

# Overall counts
overall = known["provider"].value_counts().to_dict()
overall_sorted = sorted(overall.items(), key=lambda kv: -kv[1])

# Chip counts (where Hardware quantity known)
chip_totals = (
    known.dropna(subset=["Hardware quantity"]).groupby("provider")["Hardware quantity"].sum().to_dict()
)

# Provider colors
COLORS = {
    "NVIDIA":          "#76b900",  # NVIDIA green
    "Google TPU":      "#4285F4",  # Google blue
    "Huawei Ascend":   "#e60012",  # Huawei red
    "Amazon Trainium": "#ff9900",  # AWS orange
    "AMD":             "#ED1C24",
    "Intel Gaudi":     "#0071c5",
    "Cerebras":        "#7b3fa0",
    "Graphcore":       "#00b9b6",
    "Mixed":           "#888888",
    "Other":           "#bbbbbb",
}

data_payload = {
    "records": records,
    "years": years,
    "series": series,
    "overall": overall_sorted,
    "chip_totals": chip_totals,
    "colors": COLORS,
    "total_models": len(known),
    "total_proprietary": len(prop),
    "snapshot_date": "2026-04-29",
}

html = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Compute providers behind proprietary AI models</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root {
  --bg: #0f1116;
  --panel: #181b22;
  --panel-2: #1f232c;
  --border: #2a2f3a;
  --text: #e6e8ee;
  --muted: #9097a8;
  --accent: #7aa2f7;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, "SF Pro Text", "Inter", system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  font-size: 13px;
  line-height: 1.5;
}
.wrap { max-width: 1280px; margin: 0 auto; padding: 28px 24px 80px; }
h1 { font-size: 22px; font-weight: 600; margin: 0 0 4px; letter-spacing: -0.01em; }
.subtitle { color: var(--muted); font-size: 13px; margin-bottom: 24px; }
.subtitle code { background: var(--panel-2); padding: 1px 6px; border-radius: 3px; font-size: 11.5px; }

.grid-summary { display: grid; grid-template-columns: 1.2fr 1fr; gap: 16px; margin-bottom: 22px; }
@media (max-width: 880px) { .grid-summary { grid-template-columns: 1fr; } }

.panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px 18px;
}
.panel h2 {
  font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--muted); margin: 0 0 12px;
}

/* Provider chips */
.providers { display: flex; flex-direction: column; gap: 8px; }
.provider-row {
  display: grid; grid-template-columns: 14px 1fr auto auto; gap: 10px; align-items: center;
  padding: 6px 4px; border-radius: 4px;
}
.provider-row.active { background: var(--panel-2); }
.dot { width: 12px; height: 12px; border-radius: 3px; }
.provider-name { font-weight: 500; }
.provider-count { font-variant-numeric: tabular-nums; color: var(--muted); font-size: 12px; }
.provider-bar { width: 140px; height: 6px; background: var(--panel-2); border-radius: 3px; overflow: hidden; }
.provider-bar > span { display: block; height: 100%; }

/* Filter strip */
.filter-strip {
  display: flex; gap: 8px; flex-wrap: wrap; align-items: center;
  margin: 18px 0 12px;
}
.chip {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 11px; border-radius: 999px;
  background: var(--panel); border: 1px solid var(--border);
  cursor: pointer; font-size: 12px;
  user-select: none;
}
.chip .dot { width: 9px; height: 9px; border-radius: 50%; }
.chip.active { border-color: var(--accent); background: var(--panel-2); }
.chip.dim { opacity: 0.35; }
#searchBox {
  margin-left: auto; padding: 6px 10px; background: var(--panel);
  border: 1px solid var(--border); border-radius: 6px; color: var(--text);
  font-size: 12px; width: 220px;
}
#searchBox:focus { outline: none; border-color: var(--accent); }

/* Chart */
.chart-wrap { position: relative; height: 320px; }

/* Table */
.table-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: 8px; }
table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid var(--border); white-space: nowrap; }
th {
  background: var(--panel-2); position: sticky; top: 0;
  font-weight: 600; font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.04em;
  color: var(--muted); cursor: pointer; user-select: none;
}
th .arrow { opacity: 0.4; margin-left: 4px; }
th.sort-asc .arrow, th.sort-desc .arrow { opacity: 1; color: var(--accent); }
tbody tr:hover { background: var(--panel-2); }
td.model { font-weight: 500; max-width: 280px; overflow: hidden; text-overflow: ellipsis; }
td.org { color: var(--muted); max-width: 220px; overflow: hidden; text-overflow: ellipsis; }
td.right { text-align: right; font-variant-numeric: tabular-nums; }
td a { color: var(--accent); text-decoration: none; }
td a:hover { text-decoration: underline; }

/* Provider tag in table */
.tag {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 500;
  border: 1px solid;
}
.tag .tdot { width: 7px; height: 7px; border-radius: 50%; }

/* Frontier badge */
.frontier {
  display: inline-block; padding: 1px 6px; margin-left: 6px;
  font-size: 10px; font-weight: 600; border-radius: 3px;
  background: rgba(122, 162, 247, 0.15); color: var(--accent);
  border: 1px solid rgba(122, 162, 247, 0.3);
}

/* Tooltip (custom, no native title attrs) */
#tip {
  position: fixed; pointer-events: none; opacity: 0; transition: opacity 100ms;
  background: #000; border: 1px solid var(--border); padding: 6px 9px;
  border-radius: 4px; font-size: 11px; color: var(--text); z-index: 1000;
  max-width: 320px; white-space: normal; box-shadow: 0 4px 16px rgba(0,0,0,0.4);
}

footer {
  margin-top: 28px; color: var(--muted); font-size: 11.5px;
  border-top: 1px solid var(--border); padding-top: 12px;
}
</style>
</head>
<body>
<div class="wrap">
  <h1>Compute providers behind proprietary AI models</h1>
  <div class="subtitle">
    <span id="countLine"></span> &middot;
    source <code>notable_ai_models.csv</code> &middot; snapshot <span id="snapDate"></span> (Epoch&nbsp;AI)
    &middot; &ldquo;proprietary&rdquo; = closed weights; &ldquo;known&rdquo; = training hardware reported
  </div>

  <div class="grid-summary">
    <div class="panel">
      <h2>Provider mix (model count)</h2>
      <div class="providers" id="providersList"></div>
    </div>
    <div class="panel">
      <h2>Reported chip-units (sum of hardware quantity, where given)</h2>
      <div class="providers" id="chipsList"></div>
    </div>
  </div>

  <div class="panel">
    <h2>Provider distribution over time (publication year)</h2>
    <div class="chart-wrap"><canvas id="yearChart"></canvas></div>
  </div>

  <div class="filter-strip" id="filterStrip"></div>

  <div class="table-wrap">
    <table id="modelTable">
      <thead><tr>
        <th data-key="Publication date">Date <span class="arrow">&#x25BE;</span></th>
        <th data-key="Model">Model <span class="arrow"></span></th>
        <th data-key="Organization">Organization <span class="arrow"></span></th>
        <th data-key="provider">Provider <span class="arrow"></span></th>
        <th data-key="Training hardware">Hardware <span class="arrow"></span></th>
        <th data-key="Hardware quantity" class="right">Units <span class="arrow"></span></th>
        <th data-key="Model accessibility">Access <span class="arrow"></span></th>
        <th data-key="Country (of organization)">Country <span class="arrow"></span></th>
      </tr></thead>
      <tbody></tbody>
    </table>
  </div>

  <footer>
    Excludes open-weight models. &ldquo;Mixed&rdquo; = trained on hardware from multiple vendors.
    Hover hardware cells for detail; click column headers to sort; click provider chips to filter.
  </footer>
</div>

<div id="tip"></div>

<script>
const DATA = __DATA__;
const COLORS = DATA.colors;

function fmtInt(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return "";
  return Math.round(n).toLocaleString();
}

// Provider summary cards
function renderProviderList(elId, items, formatter, maxVal) {
  const el = document.getElementById(elId);
  el.innerHTML = "";
  const max = maxVal || items.reduce((m, x) => Math.max(m, x[1]), 0);
  items.forEach(([name, n]) => {
    const color = COLORS[name] || "#888";
    const row = document.createElement("div");
    row.className = "provider-row";
    row.innerHTML = `
      <span class="dot" style="background:${color}"></span>
      <span class="provider-name">${name}</span>
      <span class="provider-count">${formatter(n)}</span>
      <span class="provider-bar"><span style="width:${(n/max*100).toFixed(1)}%; background:${color}"></span></span>
    `;
    el.appendChild(row);
  });
}

renderProviderList("providersList", DATA.overall, fmtInt);
const chipItems = Object.entries(DATA.chip_totals).sort((a,b)=>b[1]-a[1]);
renderProviderList("chipsList", chipItems, fmtInt);

document.getElementById("countLine").textContent =
  `${DATA.total_models} proprietary models with known training hardware (of ${DATA.total_proprietary} proprietary in dataset)`;
document.getElementById("snapDate").textContent = DATA.snapshot_date;

// Stacked bar chart
const ctx = document.getElementById("yearChart").getContext("2d");
const datasets = Object.entries(DATA.series).map(([name, vals]) => ({
  label: name,
  data: vals,
  backgroundColor: COLORS[name] || "#888",
  borderColor: COLORS[name] || "#888",
  borderWidth: 0,
  stack: "a",
}));
const yearChart = new Chart(ctx, {
  type: "bar",
  data: { labels: DATA.years, datasets },
  options: {
    responsive: true, maintainAspectRatio: false,
    scales: {
      x: { stacked: true, grid: { display: false }, ticks: { color: "#9097a8" } },
      y: { stacked: true, grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#9097a8" } },
    },
    plugins: {
      legend: { labels: { color: "#e6e8ee", boxWidth: 12, font: { size: 11 } } },
      tooltip: { mode: "index", intersect: false },
    },
  },
});

// Filter chips
const allProviders = DATA.overall.map(([p]) => p);
const filterStrip = document.getElementById("filterStrip");
let activeProviders = new Set(allProviders);

allProviders.forEach(p => {
  const chip = document.createElement("span");
  chip.className = "chip active";
  chip.dataset.provider = p;
  chip.innerHTML = `<span class="dot" style="background:${COLORS[p]||'#888'}"></span>${p}`;
  chip.addEventListener("click", () => {
    if (activeProviders.has(p)) {
      activeProviders.delete(p);
      chip.classList.remove("active");
      chip.classList.add("dim");
    } else {
      activeProviders.add(p);
      chip.classList.add("active");
      chip.classList.remove("dim");
    }
    renderTable();
  });
  filterStrip.appendChild(chip);
});

const allBtn = document.createElement("span");
allBtn.className = "chip";
allBtn.textContent = "Reset";
allBtn.addEventListener("click", () => {
  activeProviders = new Set(allProviders);
  filterStrip.querySelectorAll(".chip").forEach(c => {
    if (c.dataset.provider) { c.classList.add("active"); c.classList.remove("dim"); }
  });
  document.getElementById("searchBox").value = "";
  renderTable();
});
filterStrip.appendChild(allBtn);

const search = document.createElement("input");
search.id = "searchBox";
search.placeholder = "Filter model / org / hardware...";
search.addEventListener("input", renderTable);
filterStrip.appendChild(search);

// Table
let sortKey = "Publication date";
let sortDir = -1; // newest first

function cmp(a, b) {
  const av = a[sortKey], bv = b[sortKey];
  if (av === null || av === undefined) return 1;
  if (bv === null || bv === undefined) return -1;
  if (typeof av === "number" && typeof bv === "number") return (av - bv) * sortDir;
  return String(av).localeCompare(String(bv)) * sortDir;
}

function renderTable() {
  const q = document.getElementById("searchBox").value.toLowerCase().trim();
  const rows = DATA.records.filter(r => {
    if (!activeProviders.has(r.provider)) return false;
    if (!q) return true;
    return (
      (r.Model || "").toLowerCase().includes(q) ||
      (r.Organization || "").toLowerCase().includes(q) ||
      (r["Training hardware"] || "").toLowerCase().includes(q) ||
      (r["Country (of organization)"] || "").toLowerCase().includes(q)
    );
  });
  rows.sort(cmp);

  const tbody = document.querySelector("#modelTable tbody");
  tbody.innerHTML = "";
  const frag = document.createDocumentFragment();
  rows.forEach(r => {
    const color = COLORS[r.provider] || "#888";
    const tr = document.createElement("tr");
    const frontier = r["Frontier model"] === true || r["Frontier model"] === "True" || r["Frontier model"] === "true"
      ? '<span class="frontier">FRONTIER</span>' : "";
    const link = r.Link ? `<a href="${r.Link}" target="_blank" rel="noopener">${r.Model || ""}</a>` : (r.Model || "");
    tr.innerHTML = `
      <td>${r["Publication date"] || ""}</td>
      <td class="model">${link}${frontier}</td>
      <td class="org">${r.Organization || ""}</td>
      <td>
        <span class="tag" style="color:${color}; border-color:${color};">
          <span class="tdot" style="background:${color}"></span>${r.provider_full}
        </span>
      </td>
      <td class="hw" data-hw="${(r["Training hardware"]||"").replace(/"/g,'&quot;')}">${r["Training hardware"] || ""}</td>
      <td class="right">${fmtInt(r["Hardware quantity"])}</td>
      <td>${r["Model accessibility"] || ""}</td>
      <td>${r["Country (of organization)"] || ""}</td>
    `;
    frag.appendChild(tr);
  });
  tbody.appendChild(frag);

  // Update sort indicators
  document.querySelectorAll("#modelTable th").forEach(th => {
    th.classList.remove("sort-asc", "sort-desc");
    const arr = th.querySelector(".arrow");
    if (arr) arr.innerHTML = "";
    if (th.dataset.key === sortKey) {
      th.classList.add(sortDir === 1 ? "sort-asc" : "sort-desc");
      if (arr) arr.innerHTML = sortDir === 1 ? "&#x25B4;" : "&#x25BE;";
    }
  });
}

document.querySelectorAll("#modelTable th").forEach(th => {
  th.addEventListener("click", () => {
    const key = th.dataset.key;
    if (sortKey === key) sortDir = -sortDir;
    else { sortKey = key; sortDir = key === "Publication date" ? -1 : 1; }
    renderTable();
  });
});

// Custom tooltip (replaces native title= per project standards)
const tip = document.getElementById("tip");
document.querySelector("#modelTable tbody").addEventListener("mousemove", (e) => {
  const cell = e.target.closest("td.hw, td.model, td.org");
  if (!cell) { tip.style.opacity = 0; return; }
  let text = "";
  if (cell.classList.contains("hw")) text = cell.dataset.hw;
  else text = cell.textContent.trim();
  if (!text || text.length < 4) { tip.style.opacity = 0; return; }
  tip.textContent = text;
  tip.style.left = (e.clientX + 12) + "px";
  tip.style.top = (e.clientY + 12) + "px";
  tip.style.opacity = 1;
});
document.querySelector("#modelTable tbody").addEventListener("mouseleave", () => { tip.style.opacity = 0; });

renderTable();
</script>
</body>
</html>
"""

html = html.replace("__DATA__", json.dumps(data_payload))
OUT.write_text(html)
print(f"Wrote {OUT}")
print(f"Models: {len(known)} | Providers: {len(overall)}")
for p, n in overall_sorted:
    print(f"  {p}: {n}")
