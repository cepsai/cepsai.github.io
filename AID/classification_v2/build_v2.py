"""Regenerate published AID HTMLs with v3.1 ensemble classification data.

Reads priority_target_v3_1_classified_ensemble.csv, derives the per-country
DATA JSON the published HTMLs expect, and writes patched copies to
classification_v2/. The 4-way v3.1 taxonomy maps into the existing 3-way UI
slots: gov = digital_governance_and_rights, inc = digital_human_development,
inf = hard_infrastructure. non_digital rows are dropped.
"""
import json, re, sys
from collections import defaultdict, Counter
from pathlib import Path
import pandas as pd

AID = Path("/Users/robertpraas/Documents/GitHub/cepsai.github.io/AID")
OUT = AID / "classification_v2"
NEW_CSV = Path("/Users/robertpraas/CEPS-DST Dropbox/Robert Praas/5-taiwan/experiments_v2/results_v3_1/priority_target_v3_1_classified_ensemble.csv")
OLD_HTML = AID / "tech_overview.html"

DEDUP_KEYS = ["year","donor_name","recipient_name","project_title",
              "short_description","tech_category","usd_commitment","usd_disbursement"]

CAT_MAP = {
    "digital_governance_and_rights": "gov",
    "digital_human_development":     "inc",
    "hard_infrastructure":           "inf",
}

# Naive keyword taxonomy — same 16 themes the v1 pipeline used (THEMES_TODO.md).
# Match substrings against tech_reason + short_description.
THEME_KEYWORDS = {
    "e-government":         ["e-government", "e-gov", "digital government", "egovernment", "public sector digital"],
    "digital skills":       ["digital skills", "digital literacy", "ict skills", "ict training"],
    "capacity building":    ["capacity building", "capacity development", "training"],
    "media & journalism":   ["media", "journalism", "journalist", "press freedom"],
    "connectivity":         ["connectivity", "broadband", "fiber", "internet access", "last mile"],
    "digital platform":     ["digital platform", "online platform", "web platform"],
    "e-learning":           ["e-learning", "elearning", "online learning", "digital learning"],
    "mobile services":      ["mobile", "sms", "mobile phone", "mobile money"],
    "cybersecurity":        ["cyber", "cybersecurity", "information security", "cyber security"],
    "civil society":        ["civil society", "ngo", "cso"],
    "digital health":       ["digital health", "telemedicine", "ehealth", "e-health", "health information system"],
    "e-commerce":           ["e-commerce", "ecommerce", "online commerce", "digital trade"],
    "digital identity":     ["digital identity", "digital id", "biometric id"],
    "open data":            ["open data", "data portal"],
    "financial inclusion":  ["financial inclusion", "fintech", "digital finance", "mobile money"],
    "GIS / mapping":        ["gis", "mapping", "geospatial", "remote sensing"],
}

def extract_themes(rows):
    """Count theme hits across a country's digital rows."""
    counts = {}
    texts = (rows["tech_reason"].fillna("") + " " +
             rows["short_description"].fillna("") + " " +
             rows["description"].fillna("")).str.lower()
    for theme, kws in THEME_KEYWORDS.items():
        mask = pd.Series(False, index=texts.index)
        for kw in kws:
            mask |= texts.str.contains(re.escape(kw), regex=True, na=False)
        n = int(mask.sum())
        if n:
            counts[theme] = n
    return dict(sorted(counts.items(), key=lambda x: -x[1]))

def extract_old_meta():
    """Pull region + type per country from the current published tech_overview.html."""
    with open(OLD_HTML) as f:
        for line in f:
            if line.lstrip().startswith("var DATA ="):
                m = re.match(r"\s*var DATA = (\{.*\});\s*$", line)
                return {k: {"region": v["region"], "type": v["type"]}
                        for k, v in json.loads(m.group(1)).items()}
    raise RuntimeError("Could not find old DATA block")

def build_projects(g_country):
    """Collapse CRS rows for one country into 'project groups' keyed by (title, cat).
    Matches the schema the profile HTMLs expect (projects[] with members[])."""
    out = []
    # Rows with no title can't form a stable group; drop them.
    gg = g_country[g_country["project_title"].fillna("").str.strip() != ""].copy()
    for (title, cat_raw), grp in gg.groupby(["project_title","tech_category"], sort=False):
        donors = grp["donor_name"].value_counts()
        top_donor = donors.index[0]
        years = grp["year"].astype(int)
        members = [{
            "year": int(r["year"]),
            "donor": r["donor_name"],
            "sector": r.get("sector_name") or "",
            "uc": round(float(r["usd_commitment"] or 0), 3),
            "ud": round(float(r["usd_disbursement"] or 0), 3),
            "cb": int(r["confidence"] or 0),
            "ct": int(r["tech_confidence"] or 0),
        } for _, r in grp.iterrows()]
        # Pick the modal non-empty description/sector/reason to represent the group.
        def mode_nonempty(series):
            s = series.fillna("").astype(str)
            s = s[s.str.strip() != ""]
            if s.empty: return ""
            return s.mode().iat[0]
        out.append({
            "title": str(title),
            "cat": cat_raw,
            "donor": top_donor,
            "n_donors": int(donors.shape[0]),
            "desc": mode_nonempty(grp["short_description"]),
            "long": mode_nonempty(grp["description"]),
            "sector": mode_nonempty(grp["sector_name"]),
            "reason": mode_nonempty(grp["tech_reason"]),
            "conf_bin": int(grp["confidence"].fillna(0).astype(float).mean()),
            "conf_tech": int(grp["tech_confidence"].fillna(0).astype(float).mean()),
            "total_commit": round(float(grp["usd_commitment"].fillna(0).sum()), 3),
            "total_disb":   round(float(grp["usd_disbursement"].fillna(0).sum()), 3),
            "n_entries": int(len(grp)),
            "year_range": f"{years.min()}-{years.max()}" if years.min()!=years.max() else f"{years.min()}",
            "year_first": int(years.min()),
            "year_last":  int(years.max()),
            "members": members,
        })
    # Sort newest-first, biggest-pledge tiebreak.
    out.sort(key=lambda p: (-p["year_last"], -p["total_commit"]))
    return out


def build_non_digital(df):
    """Lightweight non-digital project groups per country (no members[] — too large).

    Schema matches what the project-view cards need (title/donor/desc/sector/year_range/
    totals/n_entries/cat), minus members[] (we synthesize a dummy empty array so the
    tooltip can short-circuit on it)."""
    nd = df[(df["tech_category"] == "non_digital") &
            (df["project_title"].fillna("").str.strip() != "")].copy()
    out = defaultdict(list)
    for (country, title), grp in nd.groupby(["recipient_name", "project_title"], sort=False):
        donors = grp["donor_name"].value_counts()
        years = grp["year"].astype(int)
        def mode_nonempty(series):
            s = series.fillna("").astype(str)
            s = s[s.str.strip() != ""]
            if s.empty: return ""
            return s.mode().iat[0]
        # Cap description length so the 171K-row payload stays ~17 MB.
        desc = mode_nonempty(grp["short_description"])[:240]
        out[country].append({
            "title": str(title)[:200],
            "cat": "non_digital",
            "donor": donors.index[0],
            "n_donors": int(donors.shape[0]),
            "desc": desc,
            "long": "",
            "sector": mode_nonempty(grp["sector_name"]),
            "reason": "",
            "conf_bin": 0,
            "conf_tech": 0,
            "total_commit": round(float(grp["usd_commitment"].fillna(0).sum()), 3),
            "total_disb":   round(float(grp["usd_disbursement"].fillna(0).sum()), 3),
            "n_entries": int(len(grp)),
            "year_range": f"{years.min()}-{years.max()}" if years.min()!=years.max() else f"{years.min()}",
            "year_first": int(years.min()),
            "year_last":  int(years.max()),
            "members": [],
        })
    for c in out:
        out[c].sort(key=lambda p: (-p["year_last"], -p["total_commit"]))
    return dict(out)

def build_data(df, meta):
    """Aggregate digital rows into the DATA schema the HTMLs expect."""
    d = df[df["tech_category"].isin(CAT_MAP)].copy()
    d["cat"] = d["tech_category"].map(CAT_MAP)
    d_unique = d.drop_duplicates(DEDUP_KEYS)

    out = {}
    for country, g in d_unique.groupby("recipient_name"):
        cat_counts = Counter(g["cat"])
        entry = {
            "region": meta.get(country, {}).get("region", "Unknown"),
            "type":   meta.get(country, {}).get("type",   "Priority Target"),
            "total":  int(len(g)),
            "gov":    int(cat_counts.get("gov", 0)),
            "inc":    int(cat_counts.get("inc", 0)),
            "inf":    int(cat_counts.get("inf", 0)),
            "n_distinct": int(len(g)),
            "year_min": int(g["year"].min()),
            "year_max": int(g["year"].max()),
            "total_commit": round(float(g["usd_commitment"].fillna(0).sum()), 3),
            "total_disb":   round(float(g["usd_disbursement"].fillna(0).sum()), 3),
        }

        # Donors — top 8 by pledged USD. HTMLs render USD bars (dn.commit/commit_gov/…),
        # so we also emit USD sums per category alongside the project counts.
        donor_rows = []
        for donor, gg in g.groupby("donor_name"):
            cc = Counter(gg["cat"])
            uc = gg.groupby("cat")["usd_commitment"].sum()
            ud = gg.groupby("cat")["usd_disbursement"].sum()
            donor_rows.append({
                "name": donor,
                "gov": int(cc.get("gov", 0)),
                "inc": int(cc.get("inc", 0)),
                "inf": int(cc.get("inf", 0)),
                "total": int(len(gg)),
                "commit_gov": round(float(uc.get("gov", 0) or 0), 3),
                "commit_inc": round(float(uc.get("inc", 0) or 0), 3),
                "commit_inf": round(float(uc.get("inf", 0) or 0), 3),
                "commit":     round(float(gg["usd_commitment"].fillna(0).sum()), 3),
                "disb_gov":   round(float(ud.get("gov", 0) or 0), 3),
                "disb_inc":   round(float(ud.get("inc", 0) or 0), 3),
                "disb_inf":   round(float(ud.get("inf", 0) or 0), 3),
                "disb":       round(float(gg["usd_disbursement"].fillna(0).sum()), 3),
            })
        donor_rows.sort(key=lambda x: -x["commit"])
        entry["donors"] = donor_rows[:8]

        # Sectors — top 8 by row count
        sec_counts = Counter(g["sector_name"].dropna())
        entry["sectors"] = [{"name": s, "n": int(n)}
                            for s, n in sec_counts.most_common(8)]

        # Trend — year-by-year counts + USD sums. HTML reads cc_* (pledged) and dd_*
        # (disbursed) per year to drive the Pledged/Disbursed metric + chart.
        trend = []
        for year, gg in g.groupby("year"):
            cc = Counter(gg["cat"])
            uc = gg.groupby("cat")["usd_commitment"].sum()
            ud = gg.groupby("cat")["usd_disbursement"].sum()
            trend.append({
                "year": int(year),
                "gov": int(cc.get("gov", 0)),
                "inc": int(cc.get("inc", 0)),
                "inf": int(cc.get("inf", 0)),
                "cc_gov": round(float(uc.get("gov", 0) or 0), 3),
                "cc_inc": round(float(uc.get("inc", 0) or 0), 3),
                "cc_inf": round(float(uc.get("inf", 0) or 0), 3),
                "dd_gov": round(float(ud.get("gov", 0) or 0), 3),
                "dd_inc": round(float(ud.get("inc", 0) or 0), 3),
                "dd_inf": round(float(ud.get("inf", 0) or 0), 3),
            })
        trend.sort(key=lambda x: x["year"])
        entry["trend"] = trend

        # Themes — keyword count dict
        entry["themes"] = extract_themes(g)

        # Projects — dedup groups with members[], for the profile HTML cards
        entry["projects"] = build_projects(g)

        out[country] = entry

    return out, d_unique

def patch_html(src, dst, new_data):
    """Rewrite the DATA line + label constants, drop a v3.1 banner."""
    html = src.read_text()
    new_data_json = json.dumps(new_data, ensure_ascii=False, separators=(",", ":"))
    html = re.sub(
        r"var DATA = \{.*?\};",
        f"var DATA = {new_data_json};",
        html, count=1, flags=re.DOTALL,
    )
    # Update label constants so the UI reflects v3.1 taxonomy names.
    html = html.replace(
        'var CAT_LABELS = { gov: "Governance", inc: "Inclusion", inf: "Infra" };',
        'var CAT_LABELS = { gov: "Governance+Rights", inc: "Human Development", inf: "Infra" };',
    )
    html = html.replace(
        'var CAT_FULL = { gov: "Digital Governance", inc: "Digital Inclusion", inf: "Hard Infrastructure" };',
        'var CAT_FULL = { gov: "Digital Governance & Rights", inc: "Digital Human Development", inf: "Hard Infrastructure" };',
    )
    html = html.replace(
        'var CAT_LABEL = { gov: "Governance", inc: "Inclusion", inf: "Infra" };',
        'var CAT_LABEL = { gov: "Governance+Rights", inc: "Human Development", inf: "Infra" };',
    )
    # Card rendering reads p.cat and maps via CAT_KEY — update map to v3.1 labels
    # so the new 4-way-collapsed-to-3-slot labels resolve properly.
    html = html.replace(
        'var CAT_KEY = { digital_governance: "gov", digital_inclusion: "inc", hard_infrastructure: "inf" };',
        'var CAT_KEY = { digital_governance_and_rights: "gov", digital_human_development: "inc", hard_infrastructure: "inf" };',
    )
    # Banner injected right after <body> so readers know they're on the v3.1 cut.
    banner = (
        '<div style="background:#fef3c7;border-bottom:1px solid #f59e0b;'
        'padding:8px 16px;font:13px -apple-system,sans-serif;color:#78350f">'
        '<b>v3.1 ensemble classification</b> — 4-way soft labels '
        '(gemma4-31B + Qwen3.5-35B-A3B + Nemotron-3-Nano-30B), top-3-digital rule threshold=20. '
        'Showing 12 "priority target" recipients only. '
        '<a href="../tech_overview.html" style="color:#78350f">← v1 (3-way) dashboard</a>'
        '</div>'
    )
    html = re.sub(r"(<body[^>]*>)", r"\1" + banner, html, count=1)
    # v1 HTMLs defaulted state.country to "Ukraine"; Ukraine isn't in the 12-country
    # v3.1 cut, so the main panel rendered empty until the user clicked. Fall back
    # to the first country in DATA instead.
    first_country = next(iter(new_data))
    html = re.sub(
        r'(var state\s*=\s*\{\s*country:\s*)"[^"]*"',
        lambda m: m.group(1) + json.dumps(first_country, ensure_ascii=False),
        html, count=1,
    )
    # Refresh the stale "32 countries / 9,570 digital / 3-way" subtitles.
    html = html.replace(
        "32 priority countries · OECD CRS 1990–2024 · 9,570 deduplicated digital projects · 3-way tech classification",
        "12 priority-target recipients · OECD CRS 1990–2024 · 12,440 deduplicated digital projects · v3.1 4-way soft ensemble (rendered in 3-way UI slots)",
    )
    html = html.replace(
        "32 priority countries · project-level tech classification (1990–2024) · exact-row-duplicates removed",
        "12 priority-target recipients · project-level tech classification (1990–2024) · v3.1 ensemble, exact-row-duplicates removed",
    )
    dst.write_text(html)


NON_DIGITAL_CSS = """
.nd-toggle{display:flex;align-items:center;gap:8px;background:rgba(255,255,255,.08);border-radius:6px;padding:6px 12px;font-size:11px;color:rgba(255,255,255,.85);cursor:pointer;user-select:none}
.nd-toggle .nd-sw{position:relative;width:30px;height:16px;background:rgba(255,255,255,.2);border-radius:999px;transition:background .15s}
.nd-toggle .nd-sw::after{content:"";position:absolute;top:2px;left:2px;width:12px;height:12px;background:#fff;border-radius:50%;transition:left .15s}
.nd-toggle.on .nd-sw{background:#16a34a}
.nd-toggle.on .nd-sw::after{left:16px}
.nd-toggle .nd-lbl{font-size:10px;text-transform:uppercase;letter-spacing:.04em;font-weight:600}
.nd-status{font-size:10px;color:rgba(255,255,255,.55);margin-left:2px}
.proj-card.oth{border-left-color:#94a3b8}
.proj-card.oth .badge{background:#e2e8f0;color:#475569}
"""

NON_DIGITAL_PATCH = r"""
// ---------- Non-digital toggle ----------
state.includeND = false;
var ND_LOADED = false, ND_LOADING = false;
CAT_KEY.non_digital = "oth";
CAT_FULL.oth = "Non-digital";
CAT_LABELS.oth = "Non-digital";
CAT_COLORS.oth = "#94a3b8";

function loadNonDigital(cb) {
  if (ND_LOADED) { cb(); return; }
  if (ND_LOADING) { return; }
  ND_LOADING = true;
  var s = document.createElement("script");
  s.src = "non_digital_projects.js";
  s.onload = function() { ND_LOADED = true; ND_LOADING = false; cb(); };
  s.onerror = function() {
    ND_LOADING = false;
    alert("Could not load non_digital_projects.js (expected alongside this HTML).");
  };
  document.head.appendChild(s);
}

// Override getProjectsInRange to merge non-digital when toggle is on.
var _origGetProjectsInRange = getProjectsInRange;
getProjectsInRange = function(country) {
  var arr = _origGetProjectsInRange(country);
  if (state.includeND && ND_LOADED && window.NON_DIGITAL && window.NON_DIGITAL[country]) {
    var nd = window.NON_DIGITAL[country].filter(function(p) {
      return p.year_first <= state.yrEnd && p.year_last >= state.yrStart;
    });
    arr = arr.concat(nd);
  }
  return arr;
};

// Central sort so card list + hover handler stay in lockstep.
function sortProjectsForView(projects) {
  return projects.slice().sort(function(a,b) {
    return (b.year_last - a.year_last) || (b.total_commit - a.total_commit);
  });
}

// Swap renderCardsOnly's sort (was total_commit desc) to newest-first, and
// dynamically populate the non-digital option in the category <select>.
var _origRenderCardsOnly = renderCardsOnly;
renderCardsOnly = function(d) {
  var sel = document.querySelector(".project-controls select");
  if (sel) {
    var hasND = !!sel.querySelector('option[value="non_digital"]');
    if (state.includeND && !hasND) {
      var o = document.createElement("option");
      o.value = "non_digital"; o.textContent = "Non-digital";
      sel.appendChild(o);
    } else if (!state.includeND && hasND) {
      sel.querySelector('option[value="non_digital"]').remove();
      if (state.catFilter === "non_digital") { state.catFilter = "all"; sel.value = "all"; }
    }
  }
  var listWrap = document.getElementById("proj-list-wrap");
  var info = document.getElementById("results-info");
  var projects = getProjectsInRange(state.country);
  if (state.catFilter !== "all") projects = projects.filter(function(p) { return p.cat === state.catFilter; });
  projects = sortProjectsForView(projects);
  var totalCommit = projects.reduce(function(s,p) { return s + (p.total_commit || 0); }, 0);
  var totalDisb = projects.reduce(function(s,p) { return s + (p.total_disb || 0); }, 0);
  var totalEntries = projects.reduce(function(s,p) { return s + p.n_entries; }, 0);
  info.innerHTML = '<span>' + projects.length.toLocaleString() + " projects · " + totalEntries.toLocaleString() + " entries</span>" +
    '<span>Pledged <b>' + fmtUsd(totalCommit) + '</b></span>' +
    '<span class="disb">Disbursed <b>' + fmtUsd(totalDisb) + '</b></span>';
  if (projects.length === 0) {
    listWrap.innerHTML = '<div class="empty">No projects in this category for ' + escHtml(state.country) + '.</div>';
    return;
  }
  // Soft cap rendered cards — 11K Kenya non-digital rows would lock up the DOM.
  var LIMIT = 500;
  var shown = projects.slice(0, LIMIT);
  listWrap.innerHTML = shown.map(function(p, i) { return renderCard(p, i); }).join("");
  if (projects.length > LIMIT) {
    listWrap.innerHTML += '<div class="empty">Showing ' + LIMIT + ' newest of ' + projects.length.toLocaleString() + ' projects. Use Export CSV for the full list.</div>';
  }
};

// Hover handler re-sorts to find the card by index — must match renderCardsOnly.
// Fires in capture phase and stops propagation so the original (total_commit-sorted)
// bubble-phase handler can't overwrite the tooltip with the wrong project.
document.addEventListener("mouseover", function(e) {
  var card = e.target.closest(".proj-card");
  if (!card) return;
  var idx = parseInt(card.dataset.pi, 10);
  var projects = getProjectsInRange(state.country);
  if (state.catFilter !== "all") projects = projects.filter(function(p) { return p.cat === state.catFilter; });
  projects = sortProjectsForView(projects);
  var p = projects[idx];
  if (p) showCardTooltip(p, e);
  e.stopImmediatePropagation();
}, true);

// Tooltip: non-digital has members=[], so show a compact header-only tooltip.
var _origShowCardTooltip = showCardTooltip;
showCardTooltip = function(p, evt) {
  if (!p.members || p.members.length === 0) {
    var cls = CAT_KEY[p.cat] || "";
    var html = '<div class="tt-header">' + escHtml(p.title) +
      '<div class="tt-sub">' + p.n_entries + ' entries · ' + p.year_range +
      ' · ' + p.n_donors + ' donor' + (p.n_donors !== 1 ? 's' : '') + '</div></div>';
    html += '<div class="tt-footer"><span>' + (cls === "oth" ? "Non-digital" : cls.toUpperCase()) +
      '</span><span>Pledged: <b>' + fmtUsd(p.total_commit) + '</b></span>' +
      '<span>Disbursed: <b>' + fmtUsd(p.total_disb) + '</b></span></div>';
    entriesTooltip.innerHTML = html;
    entriesTooltip.style.display = "block";
    positionEntriesTooltip(evt);
    return;
  }
  _origShowCardTooltip(p, evt);
};

// Render the toggle in the header.
(function() {
  var yrCtrl = document.querySelector(".yr-ctrl");
  if (!yrCtrl) return;
  var t = document.createElement("div");
  t.className = "nd-toggle";
  t.innerHTML = '<span class="nd-lbl">Non-digital</span>' +
    '<span class="nd-sw"></span>' +
    '<span class="nd-status" id="nd-status">off</span>';
  t.addEventListener("click", function() {
    var turnOn = !state.includeND;
    if (turnOn) {
      document.getElementById("nd-status").textContent = "loading…";
      loadNonDigital(function() {
        state.includeND = true;
        t.classList.add("on");
        document.getElementById("nd-status").textContent = "on";
        if (state.view === "projects") renderCardsOnly(DATA[state.country]);
      });
    } else {
      state.includeND = false;
      t.classList.remove("on");
      document.getElementById("nd-status").textContent = "off";
      if (state.catFilter === "non_digital") state.catFilter = "all";
      if (state.view === "projects") renderCardsOnly(DATA[state.country]);
    }
  });
  yrCtrl.parentNode.insertBefore(t, yrCtrl.nextSibling);
})();
"""

def patch_profiles_v2(html_path):
    """Add the non-digital toggle + newest-first sort to all_country_profiles_v2.html."""
    html = html_path.read_text()
    # Inject CSS before </style>.
    html = html.replace("</style>", NON_DIGITAL_CSS + "</style>", 1)
    # Inject JS as its own block right before </body> so it runs after the original
    # script has defined state/DATA/getProjectsInRange/renderCardsOnly/showCardTooltip.
    patch_block = "<script>\n" + NON_DIGITAL_PATCH + "\n</script>\n</body>"
    html = html.replace("</body>", patch_block, 1)
    html_path.write_text(html)


def main():
    print("Loading new CSV...")
    df = pd.read_csv(NEW_CSV, low_memory=False)
    print(f"  {len(df):,} rows")
    meta = extract_old_meta()
    print(f"Extracted metadata for {len(meta)} countries from old DATA")

    new_data, d_unique = build_data(df, meta)
    print(f"\nBuilt DATA for {len(new_data)} countries (dedup rows: {len(d_unique):,})")
    totals = Counter()
    for c, v in new_data.items():
        totals["gov"] += v["gov"]; totals["inc"] += v["inc"]; totals["inf"] += v["inf"]
        print(f"  {c:20s}  total={v['total']:4d}  gov={v['gov']:4d}  inc={v['inc']:4d}  inf={v['inf']:4d}  years={v['year_min']}-{v['year_max']}")
    print(f"\nTotals: gov={totals['gov']}  inc={totals['inc']}  inf={totals['inf']}  sum={sum(totals.values())}")

    # Patch each published HTML.
    for name in ["tech_overview.html",
                 "all_country_profiles_v2.html",
                 "all_country_profiles_v3.html",
                 "all_country_profiles_v2a.html",
                 "country_comparison_v2.html"]:
        src = AID / name
        dst = OUT / name
        patch_html(src, dst, new_data)
        print(f"  wrote {dst.relative_to(AID.parent)}  ({dst.stat().st_size/1024:.0f} KB)")

    # Emit aggregated JSON alongside the HTMLs for the analysis step.
    (OUT / "v3_1_aggregates.json").write_text(
        json.dumps(new_data, ensure_ascii=False, indent=2))
    print(f"\nAggregates written to {OUT}/v3_1_aggregates.json")

    # Non-digital companion payload + toggle patch on all_country_profiles_v2.html.
    print("\nBuilding non-digital projects...")
    nd_data = build_non_digital(df)
    nd_js = "window.NON_DIGITAL = " + json.dumps(nd_data, ensure_ascii=False, separators=(",", ":")) + ";\n"
    nd_path = OUT / "non_digital_projects.js"
    nd_path.write_text(nd_js)
    print(f"  wrote {nd_path.relative_to(AID.parent)}  ({nd_path.stat().st_size/1024/1024:.1f} MB, "
          f"{sum(len(v) for v in nd_data.values()):,} project groups across {len(nd_data)} countries)")
    patch_profiles_v2(OUT / "all_country_profiles_v2.html")
    print(f"  patched all_country_profiles_v2.html with non-digital toggle")

if __name__ == "__main__":
    main()
