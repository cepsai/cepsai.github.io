/* Lovable Founder Stories dashboard — vanilla JS, Chart.js + Leaflet via CDN.
   No inline onclick. All interactions via event delegation. */

const CITY_COORDS = {
  "Stockholm,SE": [59.3293, 18.0686],
  "Malmö,SE": [55.6050, 13.0038],
  "London,GB": [51.5074, -0.1278],
  "Dublin,IE": [53.3498, -6.2603],
  "Amsterdam,NL": [52.3676, 4.9041],
  "Barcelona,ES": [41.3851, 2.1734],
  "Bucharest,RO": [44.4268, 26.1025],
  "Paris,FR": [48.8566, 2.3522],
  "Devon,GB": [50.7156, -3.5309],
  "Lisbon,PT": [38.7223, -9.1393],
  "Hamburg,DE": [53.5511, 9.9937],
  "Buenos Aires,AR": [-34.6037, -58.3816],
  "Tacoma,US": [47.2529, -122.4443],
  "San Francisco,US": [37.7749, -122.4194],
  "Los Angeles,US": [34.0522, -118.2437],
  "Rio de Janeiro,BR": [-22.9068, -43.1729],
  "Toronto,CA": [43.6532, -79.3832],
};

const COUNTRY_CENTROIDS = {
  SE: [62.0, 15.0], NO: [61.0, 9.0], DK: [56.0, 10.0], FI: [64.0, 26.0],
  GB: [54.0, -2.0], IE: [53.0, -8.0], FR: [46.0, 2.0], ES: [40.0, -4.0],
  PT: [39.5, -8.0], IT: [42.0, 12.5], DE: [51.0, 10.0], NL: [52.0, 5.5],
  BE: [50.5, 4.5], LU: [49.8, 6.1], CH: [46.8, 8.2], AT: [47.5, 14.5],
  PL: [52.0, 19.0], CZ: [49.8, 15.5], SK: [48.7, 19.5], HU: [47.0, 19.5],
  RO: [46.0, 25.0], BG: [42.7, 25.5], GR: [39.0, 22.0], HR: [45.1, 15.5],
  SI: [46.0, 14.5], EE: [58.5, 25.5], LV: [57.0, 25.0], LT: [55.5, 24.0],
  IS: [64.5, -19.0], MT: [35.9, 14.5], CY: [35.1, 33.0],
  US: [39.8, -98.6], BR: [-14.2, -51.9], CA: [56.1, -106.3], IL: [31.0, 34.9],
  KZ: [48.0, 68.0], AR: [-34.0, -64.0], ZA: [-30.6, 22.9],
};

const FLAGS = {
  SE:"🇸🇪",NO:"🇳🇴",DK:"🇩🇰",FI:"🇫🇮",GB:"🇬🇧",IE:"🇮🇪",FR:"🇫🇷",ES:"🇪🇸",
  PT:"🇵🇹",IT:"🇮🇹",DE:"🇩🇪",NL:"🇳🇱",BE:"🇧🇪",LU:"🇱🇺",CH:"🇨🇭",AT:"🇦🇹",
  PL:"🇵🇱",CZ:"🇨🇿",SK:"🇸🇰",HU:"🇭🇺",RO:"🇷🇴",BG:"🇧🇬",GR:"🇬🇷",HR:"🇭🇷",
  SI:"🇸🇮",EE:"🇪🇪",LV:"🇱🇻",LT:"🇱🇹",IS:"🇮🇸",MT:"🇲🇹",CY:"🇨🇾",
  US:"🇺🇸",BR:"🇧🇷",CA:"🇨🇦",IL:"🇮🇱",KZ:"🇰🇿",AR:"🇦🇷",ZA:"🇿🇦",
};

const TIER_LABELS = {
  T0: "Pre-launch", T1: "Launched, no revenue", T2: "Early traction",
  T3: "Product-market signal", T4: "Scaled", T5: "Breakout", TX: "Undisclosed",
};
const TIER_ORDER = ["T0", "T1", "T2", "T3", "T4", "T5", "TX"];
const TIER_RADIUS = { T0: 4, T1: 5, T2: 7, T3: 10, T4: 13, T5: 16, TX: 4 };

const CATEGORY_LABELS = {};
const CATEGORY_COLORS = {};
const PALETTE = [
  "#ff5c3a", "#1f77b4", "#2ca02c", "#d62728", "#9467bd", "#8c564b",
  "#e377c2", "#7f7f7f", "#bcbd22", "#17becf", "#e5a52d", "#0d7a6a",
];

// ---------- state ----------
const state = {
  balanced: [],
  breadth: [],
  taxonomy: null,
  view: "balanced",
  europeOnly: true,
  filterCategory: null,
  categoryChart: null,
  subcategoryChart: null,
  tractionChart: null,
  map: null,
  mapLayer: null,
};

// ---------- init ----------
async function init() {
  const params = new URLSearchParams(window.location.search);
  const qv = params.get("view");
  if (qv === "breadth" || qv === "balanced") state.view = qv;

  const [balanced, breadth, taxonomy] = await Promise.all([
    fetch("data/founders.balanced.json").then(r => r.json()),
    fetch("data/founders.breadth.json").then(r => r.json()),
    fetch("data/taxonomy.json").then(r => r.json()),
  ]);
  state.balanced = balanced;
  state.breadth = breadth;
  state.taxonomy = taxonomy;

  taxonomy.categories.forEach((c, i) => {
    CATEGORY_LABELS[c.id] = c.label;
    CATEGORY_COLORS[c.id] = PALETTE[i % PALETTE.length];
  });

  document.getElementById("count-balanced").textContent = balanced.length;
  document.getElementById("count-breadth").textContent = breadth.length;

  setupToggles();
  setupFilterClear();
  setupMap();
  setupModalDismiss();
  setupActiveToggleState();
  renderAll();
}

// ---------- selectors ----------
function records() {
  const all = state.view === "balanced" ? state.balanced : state.breadth;
  return all.filter(r => {
    if (state.europeOnly && !r.is_european) return false;
    if (state.filterCategory && r.problem_category !== state.filterCategory) return false;
    return true;
  });
}

// ---------- event wiring ----------
function setupToggles() {
  document.querySelector('[data-toggle="view"]').addEventListener("click", (e) => {
    const btn = e.target.closest("[data-value]");
    if (!btn) return;
    state.view = btn.dataset.value;
    state.filterCategory = null;
    const url = new URL(window.location.href);
    url.searchParams.set("view", state.view);
    window.history.replaceState({}, "", url);
    setupActiveToggleState();
    renderAll();
  });

  document.getElementById("europe-only").addEventListener("change", (e) => {
    state.europeOnly = e.target.checked;
    renderAll();
  });
}

function setupActiveToggleState() {
  document.querySelectorAll('[data-toggle="view"] .toggle-btn').forEach(b => {
    b.classList.toggle("active", b.dataset.value === state.view);
  });
}

function setupFilterClear() {
  document.getElementById("clear-category").addEventListener("click", () => {
    state.filterCategory = null;
    renderAll();
  });
}

function setupModalDismiss() {
  document.getElementById("card-modal").addEventListener("click", (e) => {
    if (e.target.closest("[data-dismiss='modal']")) closeModal();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });
}

// ---------- rendering ----------
function renderAll() {
  const recs = records();
  renderStats(recs);
  renderCategoryDonut(recs);
  renderSubcategoryBar(recs);
  renderTractionBar(recs);
  renderMap(recs);
  renderCards(recs);
  const clearBtn = document.getElementById("clear-category");
  clearBtn.classList.toggle("hidden", !state.filterCategory);
  clearBtn.textContent = state.filterCategory
    ? `Clear filter: ${CATEGORY_LABELS[state.filterCategory]}`
    : "Clear filter";
}

function renderStats(recs) {
  const total = recs.length;
  const european = recs.filter(r => r.is_european).length;
  const countries = new Set(recs.map(r => r.hq_country).filter(Boolean));
  const confirmed = recs.filter(r => r.built_with_lovable_confidence === "confirmed").length;
  const tierCounts = {};
  TIER_ORDER.forEach(t => tierCounts[t] = 0);
  recs.forEach(r => { tierCounts[r.traction_tier] = (tierCounts[r.traction_tier] || 0) + 1; });
  const medianTier = computeMedianTier(recs);

  const html = [
    stat(total, "Founders in view"),
    stat(total ? `${Math.round((european / total) * 100)}%` : "0%", "European"),
    stat(countries.size, "Countries"),
    stat(total ? `${Math.round((confirmed / total) * 100)}%` : "0%", "Confirmed on Lovable"),
    stat(medianTier, "Median tier"),
    tierPillStat(tierCounts),
  ].join("");
  document.getElementById("stats-strip").innerHTML = html;
}

function stat(value, label) {
  return `<div class="stat"><div class="stat-value">${value}</div><div class="stat-label">${label}</div></div>`;
}
function tierPillStat(counts) {
  const pills = TIER_ORDER.map(t => `<span class="tier-pill">${t} ${counts[t] || 0}</span>`).join("");
  return `<div class="stat"><div class="stat-label" style="margin-bottom:4px">Tier distribution</div><div class="tier-pill-row">${pills}</div></div>`;
}
function computeMedianTier(recs) {
  const vals = recs.map(r => r.traction_tier).filter(t => t && t !== "TX")
    .map(t => parseInt(t.slice(1), 10)).sort((a, b) => a - b);
  if (!vals.length) return "—";
  const mid = vals[Math.floor(vals.length / 2)];
  return `T${mid}`;
}

function renderCategoryDonut(recs) {
  const counts = {};
  recs.forEach(r => { counts[r.problem_category] = (counts[r.problem_category] || 0) + 1; });
  const ordered = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const labels = ordered.map(([c]) => CATEGORY_LABELS[c] || c);
  const data = ordered.map(([, n]) => n);
  const colors = ordered.map(([c]) => CATEGORY_COLORS[c]);
  const ids = ordered.map(([c]) => c);

  if (state.categoryChart) state.categoryChart.destroy();
  state.categoryChart = new Chart(document.getElementById("category-donut"), {
    type: "doughnut",
    data: { labels, datasets: [{ data, backgroundColor: colors, borderWidth: 2, borderColor: "#fff" }] },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "right", labels: { font: { size: 11 }, boxWidth: 12 } },
        tooltip: { callbacks: { label: (ctx) => `${ctx.label}: ${ctx.parsed}` } },
      },
      onClick: (_, elts) => {
        if (!elts.length) return;
        const id = ids[elts[0].index];
        state.filterCategory = state.filterCategory === id ? null : id;
        renderAll();
      },
    },
  });
}

function renderSubcategoryBar(recs) {
  let filtered = recs;
  let title = "Top problem tags (all categories)";
  if (state.filterCategory) {
    filtered = recs.filter(r => r.problem_category === state.filterCategory);
    title = `Subcategories — ${CATEGORY_LABELS[state.filterCategory]}`;
  }

  const counts = {};
  if (state.filterCategory) {
    filtered.forEach(r => {
      const k = r.problem_subcategory || "(unspecified)";
      counts[k] = (counts[k] || 0) + 1;
    });
  } else {
    filtered.forEach(r => (r.problem_tags || []).forEach(t => { counts[t] = (counts[t] || 0) + 1; }));
  }
  const ordered = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 12);
  const labels = ordered.map(([k]) => k);
  const data = ordered.map(([, n]) => n);

  if (state.subcategoryChart) state.subcategoryChart.destroy();
  state.subcategoryChart = new Chart(document.getElementById("subcategory-bar"), {
    type: "bar",
    data: { labels, datasets: [{ data, backgroundColor: state.filterCategory ? CATEGORY_COLORS[state.filterCategory] : "#5b6170" }] },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        title: { display: true, text: title, font: { size: 13, weight: "500" }, padding: { bottom: 12 } },
      },
      scales: {
        x: { ticks: { precision: 0 }, grid: { color: "#eee" } },
        y: { grid: { display: false } },
      },
    },
  });
}

function renderTractionBar(recs) {
  const catIds = state.taxonomy.categories.map(c => c.id);
  const data = catIds.map(cid => {
    return TIER_ORDER.map(t => recs.filter(r => r.problem_category === cid && r.traction_tier === t).length);
  });

  if (state.tractionChart) state.tractionChart.destroy();
  state.tractionChart = new Chart(document.getElementById("traction-bar"), {
    type: "bar",
    data: {
      labels: TIER_ORDER.map(t => `${t} · ${TIER_LABELS[t]}`),
      datasets: catIds.map((cid, i) => ({
        label: CATEGORY_LABELS[cid],
        data: data[i],
        backgroundColor: CATEGORY_COLORS[cid],
        stack: "cats",
      })),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "right", labels: { font: { size: 11 }, boxWidth: 12 } },
        tooltip: { mode: "index", intersect: false },
      },
      scales: {
        x: { stacked: true, grid: { display: false } },
        y: { stacked: true, ticks: { precision: 0 }, grid: { color: "#eee" } },
      },
    },
  });
}

function setupMap() {
  state.map = L.map("map", { worldCopyJump: true }).setView([54, 15], 4);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 10,
  }).addTo(state.map);
  state.mapLayer = L.layerGroup().addTo(state.map);
}

function renderMap(recs) {
  state.mapLayer.clearLayers();
  recs.forEach(r => {
    const coords = resolveCoords(r);
    if (!coords) return;
    const [lat, lon] = coords;
    const radius = TIER_RADIUS[r.traction_tier] || 5;
    const color = CATEGORY_COLORS[r.problem_category] || "#888";
    const marker = L.circleMarker([lat, lon], {
      radius,
      color: "#fff",
      weight: 2,
      fillColor: color,
      fillOpacity: 0.85,
    });
    const flag = FLAGS[r.hq_country] || "";
    marker.bindPopup(
      `<strong>${escapeHtml(r.name)}</strong> ${flag}<br>` +
      `<em>${escapeHtml(r.tagline || "")}</em><br>` +
      `<span style="color:#666;font-size:12px">${r.traction_tier} · ${CATEGORY_LABELS[r.problem_category]}</span><br>` +
      `<span style="font-size:12px">${escapeHtml(r.narrative_short)}</span>`
    );
    marker.on("click", () => openModal(r));
    state.mapLayer.addLayer(marker);
  });
}

function resolveCoords(r) {
  if (r.hq_city && r.hq_country) {
    const key = `${r.hq_city},${r.hq_country}`;
    if (CITY_COORDS[key]) return CITY_COORDS[key];
  }
  if (r.hq_country && COUNTRY_CENTROIDS[r.hq_country]) {
    const [lat, lon] = COUNTRY_CENTROIDS[r.hq_country];
    // tiny jitter so overlapping country-centroid pins don't perfectly stack
    return [lat + (Math.random() - 0.5) * 0.4, lon + (Math.random() - 0.5) * 0.4];
  }
  return null;
}

function renderCards(recs) {
  const grid = document.getElementById("cards-grid");
  grid.innerHTML = recs.map(cardHtml).join("");
  document.getElementById("card-count-desc").textContent =
    `${recs.length} founder${recs.length === 1 ? "" : "s"} shown. Click a card for detail.`;
  grid.querySelectorAll(".card").forEach(el => {
    el.addEventListener("click", () => {
      const id = el.dataset.id;
      const rec = records().find(r => r.id === id);
      if (rec) openModal(rec);
    });
  });
}

function cardHtml(r) {
  const flag = FLAGS[r.hq_country] || "";
  const cat = CATEGORY_LABELS[r.problem_category] || r.problem_category;
  const catColor = CATEGORY_COLORS[r.problem_category];
  const tier = r.traction_tier;
  const conf = r.built_with_lovable_confidence;
  return `
    <article class="card" data-id="${escapeAttr(r.id)}" data-confidence="${conf}">
      <div class="card-header">
        <div class="card-name">${escapeHtml(r.name)}</div>
        <div class="card-flag" title="${escapeAttr(r.hq_country || '')}">${flag}</div>
      </div>
      <div class="card-chips">
        <span class="chip chip-category" style="color:${catColor}">${escapeHtml(cat)}</span>
        <span class="chip chip-tier" data-tier="${tier}">${tier}</span>
      </div>
      ${r.tagline ? `<div class="card-tagline">${escapeHtml(r.tagline)}</div>` : ""}
      <div class="card-narrative">${escapeHtml(r.narrative_short)}</div>
      <div class="card-footer">
        <span>${escapeHtml(r.hq_city || r.hq_country || "—")}</span>
        <span class="confidence-badge" data-conf="${conf}">${conf}</span>
      </div>
    </article>
  `;
}

function openModal(r) {
  const flag = FLAGS[r.hq_country] || "";
  const loc = [r.hq_city, r.hq_country].filter(Boolean).join(", ");
  const founders = (r.founders || []).map(f => {
    const hook = f.role ? ` (${f.role})` : "";
    return `<span>${escapeHtml(f.name)}${hook}</span>`;
  }).join(" · ");
  const narrative = r.narrative_long || r.narrative_short;
  const sourceItems = (r.sources || []).map(s => {
    const date = s.date ? ` · ${s.date}` : "";
    const type = s.type ? ` · ${s.type}` : "";
    const excerpt = s.excerpt ? `<span class="excerpt">"${escapeHtml(s.excerpt)}"</span>` : "";
    return `<li><a href="${escapeAttr(s.url)}" target="_blank" rel="noopener">${escapeHtml(s.url)}</a>${type}${date}${excerpt}</li>`;
  }).join("");

  const tm = r.traction_metric || {};
  const tractionLine = tm.value_eur
    ? `${tm.type} €${tm.value_eur.toLocaleString("en-US")} (${tm.as_of || "unknown"}, ${tm.source_quality || "unknown"})`
    : `${r.traction_tier} · ${TIER_LABELS[r.traction_tier]}`;

  document.getElementById("modal-body").innerHTML = `
    <h2 class="modal-title">${escapeHtml(r.name)} ${flag}</h2>
    <p class="modal-tagline">${escapeHtml(r.tagline || "")}</p>
    <div class="modal-meta">
      <span>${escapeHtml(loc)}</span>
      <span>${escapeHtml(CATEGORY_LABELS[r.problem_category] || "")}</span>
      <span>${escapeHtml(tractionLine)}</span>
      <span>${escapeHtml(r.built_with_lovable_confidence)} on Lovable</span>
      <span>${escapeHtml(r.status)}</span>
    </div>
    ${founders ? `<p class="modal-meta"><strong style="margin-right:6px">Founders:</strong>${founders}</p>` : ""}
    <div class="modal-narrative">${escapeHtml(narrative)}</div>
    <div class="modal-sources"><h4>Sources</h4><ul>${sourceItems}</ul></div>
    ${r.notes ? `<p style="margin-top:16px;font-size:12px;color:var(--ink-muted);"><strong>Internal notes:</strong> ${escapeHtml(r.notes)}</p>` : ""}
  `;
  document.getElementById("card-modal").classList.remove("hidden");
  document.body.style.overflow = "hidden";
}

function closeModal() {
  document.getElementById("card-modal").classList.add("hidden");
  document.body.style.overflow = "";
}

// ---------- utilities ----------
function escapeHtml(s) {
  if (s === null || s === undefined) return "";
  return String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}
function escapeAttr(s) { return escapeHtml(s); }

// ========== Apps Atlas (v0.2) ==========
const atlas = {
  apps: [],                  // from discovered_apps.json
  classifications: {},       // url -> classification record
  filters: { platform: "any", liveOnly: true, classifiedOnly: false, occupationId: "", search: "" },
  shownCount: 10,            // initial row limit
  pageStep: 10,
};

async function initAtlas() {
  try {
    const disc = await fetch("data/discovered_apps.json").then(r => r.json());
    atlas.apps = disc.apps || [];
  } catch (e) {
    console.warn("discovered_apps.json not loaded", e);
    return;
  }
  // Classifications are optional — classify.py may not have run yet
  try {
    const cls = await fetch("data/apps_classified.json").then(r => r.ok ? r.json() : null);
    if (cls && cls.results) {
      cls.results.forEach(c => { atlas.classifications[c.url] = c; });
    }
  } catch (e) {
    /* no classification data yet */
  }

  // Wire up filter controls (delegated)
  document.getElementById("atlas-live-only").addEventListener("change", (e) => {
    atlas.filters.liveOnly = e.target.checked; renderAtlas();
  });
  document.getElementById("atlas-classified-only").addEventListener("change", (e) => {
    atlas.filters.classifiedOnly = e.target.checked; renderAtlas();
  });
  document.querySelector(".atlas-platform-toggle").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-platform]");
    if (!btn) return;
    atlas.filters.platform = btn.dataset.platform;
    document.querySelectorAll(".atlas-platform-toggle .toggle-btn").forEach(b => {
      b.classList.toggle("active", b === btn);
    });
    renderAtlas();
  });
  document.getElementById("atlas-occupation-select").addEventListener("change", (e) => {
    atlas.filters.occupationId = e.target.value; renderAtlas();
  });
  const searchEl = document.getElementById("atlas-search");
  if (searchEl) {
    searchEl.addEventListener("input", (e) => {
      atlas.filters.search = e.target.value.trim().toLowerCase();
      atlas.shownCount = 10;
      renderAtlas();
    });
  }
  // Reset row-count when filters change (delegated)
  ["atlas-live-only", "atlas-classified-only", "atlas-occupation-select"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("change", () => { atlas.shownCount = 10; });
  });
  document.querySelector(".atlas-platform-toggle").addEventListener("click", () => { atlas.shownCount = 10; });

  // Show-more / show-all buttons
  document.getElementById("atlas-show-more").addEventListener("click", () => {
    atlas.shownCount += atlas.pageStep;
    renderAtlas();
  });
  document.getElementById("atlas-show-all").addEventListener("click", () => {
    atlas.shownCount = 9999;
    renderAtlas();
  });

  // Row-expand delegation (click anywhere on a main row except a link)
  document.getElementById("atlas-table-body").addEventListener("click", (e) => {
    if (e.target.closest("a")) return;
    const row = e.target.closest("tr.atlas-row-main");
    if (!row) return;
    const detail = row.nextElementSibling;
    if (!detail || !detail.classList.contains("atlas-row-detail")) return;
    const nowOpen = detail.classList.toggle("hidden") === false;
    row.classList.toggle("expanded", nowOpen);
    const ec = row.querySelector(".expand-cell");
    if (ec) ec.textContent = nowOpen ? "−" : "+";
  });

  populateOccupationSelect();
  renderAtlasStats();
  renderAtlasPlatformCounts();
  renderAtlas();

  // Top-nav counts
  document.getElementById("nav-count-founders").textContent = (state.balanced.length + state.breadth.length);
  document.getElementById("nav-count-atlas").textContent = atlas.apps.length;
}

function populateOccupationSelect() {
  const sel = document.getElementById("atlas-occupation-select");
  const counts = {};
  Object.values(atlas.classifications).forEach(c => {
    const lbl = c.classification && c.classification.primary_occupation_label;
    if (!lbl) return;
    counts[lbl] = (counts[lbl] || 0) + 1;
  });
  const ordered = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  ordered.forEach(([label, n]) => {
    const opt = document.createElement("option");
    opt.value = label;
    opt.textContent = `${label} (${n})`;
    sel.appendChild(opt);
  });
  if (!ordered.length) {
    sel.disabled = true;
    const opt = document.createElement("option");
    opt.textContent = "— no classifications loaded yet —";
    sel.appendChild(opt);
  }
}

function renderAtlasPlatformCounts() {
  const counts = { any: atlas.apps.length, "lovable.app": 0, "custom_domain": 0, "lovable.dev": 0 };
  atlas.apps.forEach(a => {
    const p = a.platform;
    counts[p] = (counts[p] || 0) + 1;
  });
  const set = (id, n) => { const el = document.getElementById(id); if (el) el.textContent = n; };
  set("atlas-count-any", counts.any);
  set("atlas-count-lovable-app", counts["lovable.app"]);
  set("atlas-count-custom-domain", counts["custom_domain"]);
}

function renderAtlasStats() {
  const apps = atlas.apps;
  const total = apps.length;
  const live = apps.filter(isLive).length;
  const custom = apps.filter(a => a.platform === "custom_domain").length;
  const classified = Object.keys(atlas.classifications).length;
  const classifiedOk = Object.values(atlas.classifications).filter(c => c.classification).length;

  const html = [
    stat(total, "Discovered URLs"),
    stat(live, "Live (HTTP 2xx)"),
    stat(custom, "Custom domains"),
    stat(classifiedOk, "Classified to ESCO"),
    stat(mwlCoverage(), "Via MWL sitemap"),
  ].join("");
  document.getElementById("atlas-stats-strip").innerHTML = html;
}

function mwlCoverage() {
  return atlas.apps.filter(a => (a.sources || []).some(s => s.startsWith("mwl:"))).length;
}

function isLive(app) {
  const s = app.status;
  return typeof s === "number" && s >= 200 && s < 300;
}

function atlasFiltered() {
  const q = atlas.filters.search;
  return atlas.apps.filter(a => {
    if (atlas.filters.liveOnly && !isLive(a)) return false;
    if (atlas.filters.platform !== "any" && a.platform !== atlas.filters.platform) return false;
    const cls = atlas.classifications[a.url];
    if (atlas.filters.classifiedOnly && !(cls && cls.classification)) return false;
    if (atlas.filters.occupationId) {
      const lbl = cls && cls.classification && cls.classification.primary_occupation_label;
      if (lbl !== atlas.filters.occupationId) return false;
    }
    if (q) {
      const hay = [
        a.url, a.title, a.description, a.og_title, a.og_description,
        cls && cls.classification && cls.classification.primary_occupation_label,
        cls && cls.classification && cls.classification.primary_task_free_text,
      ].filter(Boolean).join(" ").toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
}

function renderAtlas() {
  const shown = atlasFiltered();
  const classifiedCount = Object.values(atlas.classifications).filter(c => c.classification).length;
  const displayed = shown.slice(0, atlas.shownCount);

  document.getElementById("atlas-count-desc").textContent =
    `${displayed.length} of ${shown.length} apps shown (${atlas.apps.length} total discovered).` +
    (classifiedCount ? ` ESCO classification on ${classifiedCount} apps.` : " Classification pipeline not yet run.") +
    ` Click a row to expand it. Traction indicators are synthetic for demonstration.`;

  // Primary: row table
  document.getElementById("atlas-table-body").innerHTML = displayed.map(atlasRowHtml).join("");

  // Show-more / show-all state
  const moreBtn = document.getElementById("atlas-show-more");
  const allBtn = document.getElementById("atlas-show-all");
  const ind = document.getElementById("atlas-shown-indicator");
  const full = displayed.length >= shown.length;
  if (moreBtn) { moreBtn.disabled = full; moreBtn.textContent = `Show ${Math.min(atlas.pageStep, shown.length - displayed.length)} more`; }
  if (allBtn) { allBtn.disabled = full; }
  if (ind) ind.textContent = `Showing ${displayed.length} of ${shown.length}`;

  // Secondary: cards (under <details>)
  const cardsHtml = shown.slice(0, 120).map(atlasCardHtml).join("");
  document.getElementById("atlas-grid").innerHTML = cardsHtml;
}

// --- Row + expandable detail ---
function atlasRowHtml(app) {
  const cls = atlas.classifications[app.url];
  const clf = cls && cls.classification;
  const title = app.title || app.og_title || (app.mwl_project_slug ? app.mwl_project_slug.replace(/-/g, " ") : app.url);
  const desc = app.description || app.og_description || "";
  const cleanTitle = String(title).replace(/\s*[\|\-–—]\s*(Made with Lovable|Lovable).*$/i, "").trim();
  const platform = app.platform || "?";
  const occLabel = clf && clf.primary_occupation_label;
  const taskFree = clf && clf.primary_task_free_text;
  const auto = clf && clf.automation_vs_augmentation;
  const tr = syntheticTraction(app.url);

  const main = `
    <tr class="atlas-row-main">
      <td class="expand-cell">+</td>
      <td>
        <div class="app-cell">
          <div class="app-title">${escapeHtml(cleanTitle).slice(0, 70)}</div>
          <div class="app-url"><a href="${escapeAttr(app.url)}" target="_blank" rel="noopener">${escapeHtml(app.url)}</a></div>
          <div class="app-platform">${escapeHtml(platform)}</div>
        </div>
      </td>
      <td>
        <div class="problem-text">${desc ? escapeHtml(desc).slice(0, 220) + (desc.length > 220 ? "…" : "") : "<span style='color:var(--ink-muted);font-style:italic'>no meta description</span>"}</div>
      </td>
      <td>
        <div class="tasks-cell">
          ${occLabel ? `<span class="task-occupation" title="ESCO occupation">${escapeHtml(occLabel)}</span>` : `<span style='color:var(--ink-muted);font-style:italic;font-size:12px'>unclassified</span>`}
          ${auto ? `<span class="task-mode" data-mode="${escapeAttr(auto)}">${escapeHtml(auto)}</span>` : ""}
          ${taskFree ? `<div class="task-free">${escapeHtml(taskFree).slice(0, 80)}</div>` : ""}
        </div>
      </td>
      <td>
        <div class="traction-cell">
          ${tr.productHuntVotes !== null ? `<span class="traction-metric"><span class="metric-icon">▲</span> PH <span class="metric-value">${tr.productHuntVotes}</span></span>` : ""}
          ${tr.githubStars !== null ? `<span class="traction-metric"><span class="metric-icon">★</span> GH <span class="metric-value">${fmtNum(tr.githubStars)}</span></span>` : ""}
          ${tr.onlineMentions !== null ? `<span class="traction-metric"><span class="metric-icon">@</span> mentions <span class="metric-value">${fmtNum(tr.onlineMentions)}</span></span>` : ""}
          ${tr.weeklyVisits !== null ? `<span class="traction-metric"><span class="metric-icon">↗</span> weekly <span class="metric-value">${fmtNum(tr.weeklyVisits)}</span></span>` : ""}
          <span class="traction-synthetic-flag">synthetic</span>
        </div>
      </td>
    </tr>
  `;

  const detail = `
    <tr class="atlas-row-detail hidden">
      <td colspan="5">
        <div class="atlas-row-detail-grid">
          <div class="detail-block">
            <div class="detail-label">Full description</div>
            <div class="detail-value">${desc ? escapeHtml(desc) : "<span style='color:var(--ink-muted);font-style:italic'>no meta description</span>"}</div>
          </div>
          <div class="detail-block">
            <div class="detail-label">Discovery sources</div>
            <div class="detail-value" style="font-size:11px;font-family:ui-monospace,Menlo,monospace">${(app.sources || []).map(s => escapeHtml(s)).join("<br>") || "—"}</div>
          </div>
          <div class="detail-block">
            <div class="detail-label">HTTP status · final URL</div>
            <div class="detail-value">${app.status ?? "—"} · <a href="${escapeAttr(app.final_url || app.url)}" target="_blank" rel="noopener" style="font-size:11px;font-family:ui-monospace,Menlo,monospace">${escapeHtml(app.final_url || app.url)}</a></div>
          </div>
          ${clf ? `
          <div class="detail-block">
            <div class="detail-label">ESCO classification</div>
            <div class="detail-value">
              <strong>${escapeHtml(occLabel || "no match")}</strong>
              ${clf.primary_occupation_id ? `<div style="font-size:10px;font-family:ui-monospace,Menlo,monospace;color:var(--ink-muted);margin-top:2px">id ${escapeHtml(clf.primary_occupation_id)}</div>` : ""}
              ${auto ? `<div style="margin-top:4px"><span class="task-mode" data-mode="${escapeAttr(auto)}">${escapeHtml(auto)}</span></div>` : ""}
              ${typeof clf.confidence === "number" ? `<div style="margin-top:4px;font-size:11px;color:var(--ink-muted)">confidence ${clf.confidence.toFixed(2)}</div>` : ""}
              ${clf.rationale ? `<div class="detail-rationale" style="margin-top:6px">"${escapeHtml(clf.rationale)}"</div>` : ""}
            </div>
          </div>
          ${(clf.secondary_occupation_labels || []).length ? `
          <div class="detail-block">
            <div class="detail-label">Secondary occupations</div>
            <div class="detail-value">${clf.secondary_occupation_labels.map(escapeHtml).join(" · ")}</div>
          </div>` : ""}
          <div class="detail-block">
            <div class="detail-label">Classifier</div>
            <div class="detail-value" style="font-size:11px">model: ${escapeHtml((cls && cls.classifier_version) || "v0.1")}<br>status: ${escapeHtml(cls && cls.validation_status || "unvalidated")}</div>
          </div>
          ` : `
          <div class="detail-block">
            <div class="detail-label">ESCO classification</div>
            <div class="detail-value"><span style="color:var(--ink-muted);font-style:italic">not yet classified — run scripts/classify.py</span></div>
          </div>
          `}
          <div class="detail-block">
            <div class="detail-label">Traction (synthetic)</div>
            <div class="detail-value" style="font-size:12px;font-variant-numeric:tabular-nums;line-height:1.8">
              Product Hunt votes: <strong>${tr.productHuntVotes ?? "—"}</strong><br>
              GitHub stars: <strong>${tr.githubStars !== null ? fmtNum(tr.githubStars) : "—"}</strong><br>
              Online mentions: <strong>${tr.onlineMentions !== null ? fmtNum(tr.onlineMentions) : "—"}</strong><br>
              Estimated weekly visits: <strong>${tr.weeklyVisits !== null ? fmtNum(tr.weeklyVisits) : "—"}</strong>
            </div>
          </div>
        </div>
      </td>
    </tr>
  `;

  return main + detail;
}

// --- Synthetic traction: deterministic per URL ---
function hashString(s) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  return h >>> 0;
}
function seededRng(seed) {
  let s = seed >>> 0;
  return () => {
    s = (Math.imul(s, 48271) + 1) >>> 0;
    return (s % 1_000_000) / 1_000_000;
  };
}
function syntheticTraction(url) {
  const rng = seededRng(hashString(url));
  const has = (p) => rng() < p;
  // Skew: most apps are low-traction; a few are big
  const powerSkew = () => {
    const x = rng();
    return Math.floor(Math.pow(x, 3) * 5000);
  };
  return {
    productHuntVotes: has(0.4) ? Math.floor(rng() * 480) + 10 : null,
    githubStars: has(0.25) ? Math.floor(Math.pow(rng(), 2) * 1500) + 3 : null,
    onlineMentions: has(0.9) ? Math.floor(Math.pow(rng(), 2) * 2000) + 1 : null,
    weeklyVisits: has(0.7) ? powerSkew() + 40 : null,
  };
}
function fmtNum(n) {
  if (n === null || n === undefined) return "—";
  if (n >= 1000) return (n / 1000).toFixed(n >= 10000 ? 0 : 1) + "k";
  return String(n);
}

function atlasCardHtml(app) {
  const cls = atlas.classifications[app.url];
  const clf = cls && cls.classification;
  const title = app.title || app.og_title || (app.mwl_project_slug ? app.mwl_project_slug.replace(/-/g, " ") : app.url);
  const desc = app.description || app.og_description || "";
  const live = isLive(app);
  const occLabel = clf && clf.primary_occupation_label;
  const occTask = clf && clf.primary_task_free_text;
  const auto = clf && clf.automation_vs_augmentation;
  const conf = clf && clf.confidence;

  return `
    <article class="atlas-card">
      <div class="atlas-card-header">
        <div>
          <div class="atlas-card-title">${escapeHtml(title).slice(0, 100)}</div>
          <div class="atlas-card-url"><a href="${escapeAttr(app.url)}" target="_blank" rel="noopener">${escapeHtml(app.url)}</a></div>
        </div>
      </div>
      ${desc ? `<div class="atlas-card-description">${escapeHtml(desc).slice(0, 260)}${desc.length > 260 ? "…" : ""}</div>` : ""}
      <div class="atlas-card-meta">
        <span class="chip chip-platform">${escapeHtml(app.platform || "?")}</span>
        <span class="chip chip-status" data-live="${live}">${live ? "live" : (app.status === null ? "unchecked" : app.status)}</span>
        ${occLabel ? `<span class="chip chip-occupation" title="ESCO occupation">${escapeHtml(occLabel)}</span>` : ""}
        ${auto ? `<span class="chip chip-auto" data-mode="${escapeAttr(auto)}">${escapeHtml(auto)}</span>` : ""}
        ${typeof conf === "number" ? `<span class="chip" title="Classifier confidence">conf ${conf.toFixed(2)}</span>` : ""}
      </div>
      ${occTask ? `<div class="atlas-card-description" style="color:var(--ink-muted);font-size:12px;"><strong>Task:</strong> ${escapeHtml(occTask)}</div>` : ""}
    </article>
  `;
}

// ========== Tab switching ==========
const tabs = { active: "advent", adventRendered: false, indexRendered: false, adventMap: null };
const TAB_IDS = ["advent", "atlas", "founders", "index"];

function setupTabs() {
  // Initial tab from URL hash
  const hashTab = (window.location.hash || "").replace(/^#(tab-)?/, "");
  if (TAB_IDS.includes(hashTab)) {
    tabs.active = hashTab;
  }
  applyTab(tabs.active);

  document.getElementById("tab-nav").addEventListener("click", (e) => {
    const btn = e.target.closest(".tab-link[data-tab]");
    if (!btn) return;
    e.preventDefault();
    applyTab(btn.dataset.tab);
  });

  window.addEventListener("hashchange", () => {
    const h = (window.location.hash || "").replace(/^#(tab-)?/, "");
    if (TAB_IDS.includes(h)) applyTab(h);
  });
}

function applyTab(tabId) {
  tabs.active = tabId;
  document.querySelectorAll(".tab-link[data-tab]").forEach(b => {
    b.classList.toggle("active", b.dataset.tab === tabId);
  });
  document.querySelectorAll(".tab-panel").forEach(p => {
    p.classList.toggle("active", p.id === `tab-${tabId}`);
  });
  window.history.replaceState({}, "", `#${tabId}`);

  // Side-effects per tab
  if (tabId === "founders" && state.map) {
    setTimeout(() => state.map.invalidateSize(), 50);
  }
  if (tabId === "advent") {
    if (!tabs.adventRendered) {
      renderAdvent();
      tabs.adventRendered = true;
    } else if (tabs.adventMap) {
      setTimeout(() => tabs.adventMap.invalidateSize(), 50);
    }
  }
  if (tabId === "index" && !tabs.indexRendered) {
    renderSovereignIndex();
    tabs.indexRendered = true;
  }
}

// ========== Advent — 10 visualisations ==========
function renderAdvent() {
  adventProjectsLine();
  adventTreemap();
  adventWorldMap();
  adventCountriesBar();
  adventIndustryDonut();
  adventFunnel();
  adventTeamSize();
  adventBackground();
  adventHeatmap();
  adventTractionScatter();
}

// 1 — Cumulative projects line
function adventProjectsLine() {
  // Calibrated to hit ≥10k EU projects by end of 2025
  const weeks = [];
  const cumEU = [];
  const cumGlobal = [];
  const start = new Date("2024-04-07");
  let euLast = 0, globalLast = 0;
  for (let i = 0; i < 100; i++) {
    const d = new Date(start.getTime() + i * 7 * 86400000);
    const weekLabel = d.toISOString().slice(0, 10);
    // Logistic-ish growth with noise
    const euAdd = Math.max(5, Math.round(20 + 180 * (i / 100) * (1 + Math.sin(i / 6) * 0.15)));
    const globalAdd = Math.round(euAdd * 3.4);
    euLast += euAdd;
    globalLast += globalAdd;
    weeks.push(weekLabel);
    cumEU.push(euLast);
    cumGlobal.push(globalLast);
  }
  new Chart(document.getElementById("advent-projects-line"), {
    type: "line",
    data: {
      labels: weeks,
      datasets: [
        { label: "Global cumulative", data: cumGlobal, borderColor: "#1f4d8a", backgroundColor: "rgba(31,77,138,0.08)", tension: 0.3, fill: true, pointRadius: 0 },
        { label: "EU cumulative", data: cumEU, borderColor: "#ff5c3a", backgroundColor: "rgba(255,92,58,0.12)", tension: 0.3, fill: true, pointRadius: 0 },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: "top" }, tooltip: { mode: "index", intersect: false } },
      scales: {
        x: { ticks: { maxTicksLimit: 12 }, grid: { display: false } },
        y: { grid: { color: "#eee" }, ticks: { callback: (v) => v >= 1000 ? (v / 1000).toFixed(1) + "k" : v } },
      },
    },
  });
}

// 2 — Problem-areas treemap (real)
function adventTreemap() {
  const all = [...state.balanced, ...state.breadth];
  const counts = {};
  all.forEach(r => { counts[r.problem_category] = (counts[r.problem_category] || 0) + 1; });
  const items = Object.entries(counts).map(([cat, n]) => ({
    category: CATEGORY_LABELS[cat] || cat,
    value: n,
    color: CATEGORY_COLORS[cat] || "#888",
  })).sort((a, b) => b.value - a.value);

  new Chart(document.getElementById("advent-treemap"), {
    type: "treemap",
    data: {
      datasets: [{
        tree: items,
        key: "value",
        labels: {
          display: true,
          color: "#fff",
          font: { size: 12, weight: "600" },
          formatter: (ctx) => {
            const it = ctx.raw && ctx.raw._data;
            if (!it) return "";
            return `${it.category}\n${it.value}`;
          },
          overflow: "fit",
          position: "middle",
        },
        backgroundColor: (ctx) => (ctx.raw && ctx.raw._data && ctx.raw._data.color) || "#888",
        borderColor: "#fff", borderWidth: 2,
        spacing: 0.5,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => items[0].raw._data.category,
            label: (ctx) => `${ctx.raw._data.value} founders`,
          },
        },
      },
    },
  });
}

// 3 — World map of users (synthetic user counts per country)
function adventWorldMap() {
  const el = document.getElementById("advent-world-map");
  if (!el || el._leaflet_id) return;
  const map = L.map(el, { worldCopyJump: true, scrollWheelZoom: false }).setView([30, 10], 2);
  tabs.adventMap = map;
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors", maxZoom: 8,
  }).addTo(map);

  // Synthetic MAU per country (illustrative). EU-heavy distribution.
  const users = [
    ["US", 540000, 37.09, -95.71], ["GB", 220000, 54.0, -2.0], ["DE", 180000, 51.16, 10.45],
    ["FR", 155000, 46.6, 1.9], ["SE", 120000, 62.0, 15.0], ["NL", 95000, 52.13, 5.29],
    ["ES", 88000, 40.46, -3.75], ["IT", 72000, 41.87, 12.57], ["IN", 140000, 20.59, 78.96],
    ["BR", 85000, -14.24, -51.93], ["CA", 74000, 56.13, -106.35], ["AU", 52000, -25.27, 133.77],
    ["IE", 41000, 53.41, -8.24], ["DK", 36000, 56.26, 9.50], ["FI", 29000, 61.92, 25.75],
    ["NO", 28000, 60.47, 8.47], ["CH", 38000, 46.82, 8.23], ["AT", 24000, 47.52, 14.55],
    ["BE", 26000, 50.50, 4.47], ["PT", 19000, 39.40, -8.22], ["PL", 21000, 51.92, 19.15],
    ["CZ", 13000, 49.82, 15.47], ["EE", 9000, 58.60, 25.01], ["RO", 8500, 45.94, 24.97],
    ["GR", 7200, 39.07, 21.82], ["HU", 6500, 47.16, 19.50], ["JP", 32000, 36.20, 138.25],
    ["SG", 18000, 1.35, 103.82], ["ZA", 11000, -30.56, 22.94], ["AE", 14000, 23.42, 53.85],
    ["MX", 22000, 23.63, -102.55], ["AR", 12000, -38.42, -63.62],
  ];
  const max = Math.max(...users.map(u => u[1]));
  users.forEach(([iso, count, lat, lon]) => {
    const r = 6 + Math.sqrt(count / max) * 28;
    const isEU = ["GB","DE","FR","SE","NL","ES","IT","IE","DK","FI","NO","CH","AT","BE","PT","PL","CZ","EE","RO","GR","HU"].includes(iso);
    L.circleMarker([lat, lon], {
      radius: r, color: "#fff", weight: 1, fillColor: isEU ? "#ff5c3a" : "#1f4d8a", fillOpacity: 0.75,
    }).bindTooltip(`${iso}: ${count.toLocaleString("en-US")} MAU`, { direction: "top" }).addTo(map);
  });
}

// 4 — Top countries bar (real)
function adventCountriesBar() {
  const all = [...state.balanced, ...state.breadth];
  const counts = {};
  all.forEach(r => {
    const c = r.hq_country;
    if (c) counts[c] = (counts[c] || 0) + 1;
  });
  const ordered = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 16);
  new Chart(document.getElementById("advent-countries-bar"), {
    type: "bar",
    data: {
      labels: ordered.map(([c]) => `${FLAGS[c] || ""} ${c}`),
      datasets: [{ data: ordered.map(([, n]) => n), backgroundColor: "#ff5c3a", borderRadius: 4 }],
    },
    options: {
      responsive: true, maintainAspectRatio: false, indexAxis: "y",
      plugins: { legend: { display: false } },
      scales: { x: { grid: { color: "#eee" }, ticks: { precision: 0 } }, y: { grid: { display: false } } },
    },
  });
}

// 5 — Industry donut (synthetic NACE sector)
function adventIndustryDonut() {
  const industries = [
    ["Information & Communication (J)", 28],
    ["Professional, scientific, technical (M)", 18],
    ["Wholesale & retail (G)", 11],
    ["Financial & insurance (K)", 8],
    ["Education (P)", 7],
    ["Health & social (Q)", 6],
    ["Arts & entertainment (R)", 6],
    ["Manufacturing (C)", 5],
    ["Real estate (L)", 4],
    ["Other services", 7],
  ];
  new Chart(document.getElementById("advent-industry-donut"), {
    type: "doughnut",
    data: {
      labels: industries.map(i => i[0]),
      datasets: [{ data: industries.map(i => i[1]), backgroundColor: PALETTE, borderColor: "#fff", borderWidth: 2 }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: "right", labels: { font: { size: 11 }, boxWidth: 12 } },
        tooltip: { callbacks: { label: (c) => `${c.label}: ${c.parsed}% (synthetic)` } },
      },
    },
  });
}

// 6 — Funnel
function adventFunnel() {
  const stages = [
    ["Project created", 10000, "#ff5c3a"],
    ["Publicly launched", 4200, "#ff8560"],
    ["First revenue (≥€1)", 1450, "#ffa985"],
    ["€10k ARR", 420, "#e5a52d"],
    ["€100k ARR", 85, "#0d7a6a"],
    ["€1M+ ARR", 9, "#1f4d8a"],
  ];
  new Chart(document.getElementById("advent-funnel"), {
    type: "bar",
    data: {
      labels: stages.map(s => s[0]),
      datasets: [{ data: stages.map(s => s[1]), backgroundColor: stages.map(s => s[2]), borderRadius: 4 }],
    },
    options: {
      responsive: true, maintainAspectRatio: false, indexAxis: "y",
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (c) => `${c.parsed.x.toLocaleString("en-US")} projects (synthetic)` } },
      },
      scales: {
        x: { type: "logarithmic", grid: { color: "#eee" }, ticks: { callback: (v) => v.toLocaleString("en-US") } },
        y: { grid: { display: false } },
      },
    },
  });
}

// 7 — Team size (real where available)
function adventTeamSize() {
  const all = [...state.balanced, ...state.breadth];
  const bins = { "Solo (1)": 0, "Small (2–3)": 0, "Growing (4–10)": 0, "10+": 0, "Unknown": 0 };
  all.forEach(r => {
    const t = r.team_size;
    if (t === null || t === undefined) bins["Unknown"] += 1;
    else if (t <= 1) bins["Solo (1)"] += 1;
    else if (t <= 3) bins["Small (2–3)"] += 1;
    else if (t <= 10) bins["Growing (4–10)"] += 1;
    else bins["10+"] += 1;
  });
  new Chart(document.getElementById("advent-team-size"), {
    type: "bar",
    data: {
      labels: Object.keys(bins),
      datasets: [{ data: Object.values(bins), backgroundColor: ["#ff5c3a", "#ff8560", "#e5a52d", "#0d7a6a", "#c8ccd4"], borderRadius: 4 }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { grid: { display: false } }, y: { grid: { color: "#eee" }, ticks: { precision: 0 } } },
    },
  });
}

// 8 — Founder background (real)
function adventBackground() {
  const all = [...state.balanced, ...state.breadth];
  let solo = 0, mixed = 0, allTech = 0, allNonTech = 0, unknown = 0;
  all.forEach(r => {
    const fs = r.founders || [];
    if (!fs.length) { unknown++; return; }
    const techFlags = fs.map(f => f.technical);
    if (techFlags.every(t => t === null || t === undefined)) unknown++;
    else if (fs.length === 1) {
      if (techFlags[0]) allTech++;
      else solo++;
    }
    else {
      const tech = techFlags.filter(t => t === true).length;
      const nonTech = techFlags.filter(t => t === false).length;
      if (tech > 0 && nonTech > 0) mixed++;
      else if (tech > 0) allTech++;
      else allNonTech++;
    }
  });
  new Chart(document.getElementById("advent-background-donut"), {
    type: "doughnut",
    data: {
      labels: ["Solo non-technical", "All-technical team", "All-non-technical team", "Mixed team", "Unknown"],
      datasets: [{
        data: [solo, allTech, allNonTech, mixed, unknown],
        backgroundColor: ["#ff5c3a", "#1f4d8a", "#e5a52d", "#0d7a6a", "#c8ccd4"],
        borderColor: "#fff", borderWidth: 2,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: "right", labels: { font: { size: 11 }, boxWidth: 12 } },
        tooltip: { callbacks: { label: (c) => `${c.label}: ${c.parsed}` } },
      },
    },
  });
}

// 9 — Activity heatmap (synthetic)
function adventHeatmap() {
  const el = document.getElementById("advent-heatmap");
  if (!el) return;
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  // Synthetic: weekend-builder pattern. Peaks Sunday afternoon, Monday morning.
  const rng = seededRng(0xbeef);
  // 7x24 matrix
  const mat = days.map((d, dayIdx) => {
    return Array.from({ length: 24 }, (_, h) => {
      let base = 20 + 40 * Math.max(0, Math.sin((h - 6) * Math.PI / 16));
      if (dayIdx === 6 && h >= 13 && h <= 20) base += 90; // Sunday afternoon
      if (dayIdx === 0 && h >= 7 && h <= 10) base += 60;  // Monday morning
      if (dayIdx === 5) base += 25;                        // Saturday a bit
      if (h >= 0 && h <= 5) base *= 0.3;                   // night dip
      base += rng() * 20 - 10;
      return Math.max(0, Math.round(base));
    });
  });
  const all = mat.flat();
  const max = Math.max(...all);

  let html = "";
  html += `<div></div>`;
  for (let h = 0; h < 24; h++) html += `<div class="heatmap-header">${h}</div>`;
  days.forEach((d, i) => {
    html += `<div class="heatmap-label">${d}</div>`;
    for (let h = 0; h < 24; h++) {
      const v = mat[i][h];
      const intensity = v / max;
      const color = intensityColor(intensity);
      html += `<div class="heatmap-cell" title="${d} ${String(h).padStart(2, "0")}:00 UTC — ${v} new projects" style="background:${color}"></div>`;
    }
  });
  el.innerHTML = html;
  // Add legend
  const legend = document.createElement("div");
  legend.className = "advent-heatmap-legend";
  legend.innerHTML = `<span>low</span><span class="legend-scale"></span><span>high (${max} projects/h)</span>`;
  el.parentElement.appendChild(legend);
}
function intensityColor(t) {
  // Blend from #f2f3f6 → #ffb299 → #ff5c3a
  const stops = [
    [0.00, 242, 243, 246],
    [0.50, 255, 178, 153],
    [1.00, 255,  92,  58],
  ];
  for (let i = 0; i < stops.length - 1; i++) {
    const [t0, r0, g0, b0] = stops[i];
    const [t1, r1, g1, b1] = stops[i + 1];
    if (t <= t1) {
      const f = (t - t0) / (t1 - t0 || 1);
      return `rgb(${Math.round(r0 + (r1 - r0) * f)}, ${Math.round(g0 + (g1 - g0) * f)}, ${Math.round(b0 + (b1 - b0) * f)})`;
    }
  }
  return `rgb(255,92,58)`;
}

// 10 — Traction vs launch date scatter (real)
function adventTractionScatter() {
  const all = [...state.balanced, ...state.breadth];
  // Group by category for dataset color
  const byCat = {};
  all.forEach(r => {
    const tm = r.traction_metric;
    const v = tm && tm.value_eur;
    const d = r.launch_date;
    if (!v || !d) return;
    const dt = new Date(d.length <= 7 ? d + "-01" : d);
    if (isNaN(dt)) return;
    const cat = r.problem_category;
    byCat[cat] = byCat[cat] || [];
    byCat[cat].push({ x: dt.getTime(), y: v, name: r.name, tier: r.traction_tier });
  });
  const datasets = Object.entries(byCat).map(([cat, pts]) => ({
    label: CATEGORY_LABELS[cat] || cat,
    data: pts,
    backgroundColor: CATEGORY_COLORS[cat] || "#888",
    borderColor: "#fff",
    borderWidth: 1,
    pointRadius: 7,
  }));
  new Chart(document.getElementById("advent-traction-scatter"), {
    type: "scatter",
    data: { datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: "right", labels: { font: { size: 11 }, boxWidth: 10 } },
        tooltip: {
          callbacks: {
            label: (c) => `${c.raw.name} (${c.raw.tier}) — €${Number(c.raw.y).toLocaleString("en-US")}`,
            title: (items) => new Date(items[0].raw.x).toISOString().slice(0, 7),
          },
        },
      },
      scales: {
        x: {
          type: "time",
          time: { unit: "month", displayFormats: { month: "MMM yy" } },
          grid: { color: "#eee" },
          title: { display: true, text: "Launch date" },
        },
        y: {
          type: "logarithmic",
          grid: { color: "#eee" },
          title: { display: true, text: "Reported ARR / MRR (EUR, log)" },
          ticks: { callback: (v) => "€" + (v >= 1000 ? (v / 1000).toLocaleString("en-US") + "k" : v) },
        },
      },
    },
  });
}

// ========== Sovereign AI Index — synthetic charts ==========
function renderSovereignIndex() {
  // Platform bar: EU apps per platform (Lovable leads; others placeholder)
  new Chart(document.getElementById("index-platforms-chart"), {
    type: "bar",
    data: {
      labels: ["Lovable", "Bolt", "v0 (Vercel)", "Replit", "Cursor", "HF Spaces"],
      datasets: [{
        label: "EU-built apps (est.)",
        data: [10200, 2800, 1900, 1400, 800, 620],
        backgroundColor: ["#ff5c3a", "#1f77b4", "#2ca02c", "#9467bd", "#8c564b", "#e377c2"],
        borderRadius: 4,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false, indexAxis: "y",
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (c) => `${c.parsed.x.toLocaleString("en-US")} apps (synthetic)` } },
      },
      scales: {
        x: { ticks: { callback: (v) => v.toLocaleString("en-US") }, grid: { color: "#eee" } },
        y: { grid: { display: false } },
      },
    },
  });

  // Country ranking (top 12 EU/EEA by composite score 0–100)
  const countries = [
    ["Sweden", 84], ["Germany", 79], ["Netherlands", 76], ["France", 73],
    ["UK", 71], ["Estonia", 69], ["Ireland", 66], ["Denmark", 64],
    ["Finland", 61], ["Belgium", 58], ["Spain", 55], ["Portugal", 52],
    ["Lithuania", 49], ["Poland", 47], ["Italy", 45], ["Austria", 43],
  ];
  new Chart(document.getElementById("index-countries-chart"), {
    type: "bar",
    data: {
      labels: countries.map(c => c[0]),
      datasets: [{
        label: "Sovereign AI Index score (0–100)",
        data: countries.map(c => c[1]),
        backgroundColor: countries.map((_, i) => `rgba(255, 92, 58, ${0.85 - i * 0.035})`),
        borderRadius: 4,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false, indexAxis: "y",
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (c) => `${c.parsed.x} / 100 (synthetic composite)` } },
      },
      scales: {
        x: { max: 100, grid: { color: "#eee" } },
        y: { grid: { display: false } },
      },
    },
  });

  // Growth trajectory
  const quarters = ["Q1'24", "Q2'24", "Q3'24", "Q4'24", "Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26"];
  new Chart(document.getElementById("index-growth-chart"), {
    type: "line",
    data: {
      labels: quarters,
      datasets: [
        { label: "Lovable",     data: [180, 540, 1400, 3100, 5200, 7400, 8900, 10200, 11500], borderColor: "#ff5c3a", backgroundColor: "rgba(255,92,58,.1)", tension: 0.35, fill: true },
        { label: "Bolt",        data: [60, 180, 420, 800, 1300, 1900, 2400, 2800, 3100], borderColor: "#1f77b4", tension: 0.35 },
        { label: "v0 (Vercel)", data: [40, 140, 320, 620, 980, 1350, 1640, 1900, 2050], borderColor: "#2ca02c", tension: 0.35 },
        { label: "Replit",      data: [120, 220, 380, 620, 900, 1150, 1300, 1400, 1440], borderColor: "#9467bd", tension: 0.35 },
        { label: "Cursor",      data: [20, 80, 180, 320, 500, 650, 740, 800, 820], borderColor: "#8c564b", tension: 0.35 },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: "right", labels: { font: { size: 11 }, boxWidth: 12 } },
        tooltip: { mode: "index", intersect: false },
      },
      scales: { y: { grid: { color: "#eee" }, ticks: { callback: (v) => v.toLocaleString("en-US") } } },
    },
  });

  // --- Supply chain: regional share per layer ---
  const supplyLayers = ["Compute / silicon", "Foundation models", "Model-infra / tooling", "Vertical applications", "AI app-builders"];
  new Chart(document.getElementById("index-supply-share-chart"), {
    type: "bar",
    data: {
      labels: supplyLayers,
      datasets: [
        { label: "EU",    data: [3, 10, 18, 22, 32], backgroundColor: "#ff5c3a" },
        { label: "US",    data: [78, 55, 58, 48, 55], backgroundColor: "#1f4d8a" },
        { label: "China", data: [15, 25, 18, 22, 8],  backgroundColor: "#0d7a2a" },
        { label: "Other", data: [4,  10, 6,  8,  5],  backgroundColor: "#c8ccd4" },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: "top" },
        tooltip: {
          callbacks: { label: (c) => `${c.dataset.label}: ${c.parsed.y}% (synthetic)` },
        },
      },
      scales: {
        x: { stacked: true, grid: { display: false } },
        y: { stacked: true, max: 100, grid: { color: "#eee" }, ticks: { callback: (v) => v + "%" } },
      },
    },
  });

  // --- Notable EU AI companies by layer (bubble/bar-like) ---
  const euCompanies = [
    // layer 1: compute
    { name: "Graphcore (UK)",          layer: 1, funding: 710 },
    { name: "SiPearl (FR)",            layer: 1, funding: 130 },
    { name: "Axelera AI (NL)",         layer: 1, funding: 120 },
    { name: "Kalray (FR)",             layer: 1, funding: 85  },
    // layer 2: foundation models
    { name: "Mistral AI (FR)",         layer: 2, funding: 1100 },
    { name: "Aleph Alpha (DE)",        layer: 2, funding: 500  },
    { name: "Poolside (FR)",           layer: 2, funding: 500  },
    { name: "H (Paris)",               layer: 2, funding: 220  },
    { name: "Black Forest Labs (DE)",  layer: 2, funding: 31   },
    { name: "Reka AI (UK)",            layer: 2, funding: 60   },
    // layer 3: model-infra / tooling
    { name: "Hugging Face (FR/US)",    layer: 3, funding: 395  },
    { name: "Synthesia (UK)",          layer: 3, funding: 330  },
    { name: "ElevenLabs (UK)",         layer: 3, funding: 281  },
    { name: "Stability AI (UK)",       layer: 3, funding: 200  },
    // layer 4: vertical apps
    { name: "Wayve (UK)",              layer: 4, funding: 1300 },
    { name: "Helsing (DE)",            layer: 4, funding: 830  },
    { name: "DeepL (DE)",              layer: 4, funding: 420  },
    { name: "Bending Spoons (IT)",     layer: 4, funding: 350  },
    { name: "PolyAI (UK)",             layer: 4, funding: 120  },
    // layer 5: app-builders
    { name: "Lovable (SE)",            layer: 5, funding: 200  },
    { name: "Replit (partial EU)",     layer: 5, funding: 220  },
    // + Bolt (US), v0 (US), Cursor (US) are non-EU — omitted
  ];
  const LAYER_COLORS = { 1: "#8c564b", 2: "#9467bd", 3: "#2ca02c", 4: "#1f77b4", 5: "#ff5c3a" };
  const LAYER_LABELS_OBJ = { 1: "Compute", 2: "Foundation models", 3: "Model-infra", 4: "Applications", 5: "App-builders" };
  euCompanies.sort((a, b) => (a.layer - b.layer) || (b.funding - a.funding));
  new Chart(document.getElementById("index-companies-chart"), {
    type: "bar",
    data: {
      labels: euCompanies.map(c => c.name),
      datasets: [{
        label: "Disclosed funding (€M)",
        data: euCompanies.map(c => c.funding),
        backgroundColor: euCompanies.map(c => LAYER_COLORS[c.layer]),
        borderRadius: 4,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false, indexAxis: "y",
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (c) => {
              const ent = euCompanies[c.dataIndex];
              return `${LAYER_LABELS_OBJ[ent.layer]} · €${ent.funding}M funding (approx.)`;
            },
          },
        },
      },
      scales: {
        x: { type: "logarithmic", grid: { color: "#eee" }, ticks: { callback: (v) => "€" + v + "M" }, title: { display: true, text: "disclosed funding (€M, log scale)" } },
        y: { grid: { display: false } },
      },
    },
  });

  // --- Sovereignty of the EU app stack: per-layer dependency ---
  const sovLayers = ["Compute used by EU apps", "Foundation model", "Hosting / infra", "Framework / tooling", "Front-end / UI", "Payments / SaaS glue"];
  new Chart(document.getElementById("index-sovereignty-chart"), {
    type: "bar",
    data: {
      labels: sovLayers,
      datasets: [
        { label: "EU-sourced",    data: [5,  18, 12, 22, 40, 35], backgroundColor: "#ff5c3a" },
        { label: "US-sourced",    data: [85, 70, 80, 70, 55, 60], backgroundColor: "#1f4d8a" },
        { label: "Chinese",       data: [7,  8,  5,  6,  3,  3],  backgroundColor: "#0d7a2a" },
        { label: "Other / open",  data: [3,  4,  3,  2,  2,  2],  backgroundColor: "#c8ccd4" },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false, indexAxis: "y",
      plugins: {
        legend: { position: "top" },
        tooltip: {
          callbacks: { label: (c) => `${c.dataset.label}: ${c.parsed.x}% (synthetic)` },
        },
      },
      scales: {
        x: { stacked: true, max: 100, grid: { color: "#eee" }, ticks: { callback: (v) => v + "%" } },
        y: { stacked: true, grid: { display: false } },
      },
    },
  });
}

// ========== Boot ==========
init().then(() => {
  setupTabs();
  return initAtlas();
}).catch(err => {
  console.error(err);
  document.body.innerHTML = `<pre style="padding:40px;color:#a0441b">Failed to load dashboard: ${escapeHtml(err.message)}</pre>`;
});
