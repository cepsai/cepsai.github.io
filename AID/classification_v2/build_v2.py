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
NEW_CSV = Path("/Users/robertpraas/CEPS-DST Dropbox/Robert Praas/5-taiwan/experiments_v2/results_v3_1/priority_target_v3_1_classified_ensemble_full.csv")
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
        def _num(v):
            # `float(nan or 0)` returns nan (nan is truthy) — must guard with isna.
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return 0.0
            try:
                f = float(v)
                return 0.0 if pd.isna(f) else f
            except (TypeError, ValueError):
                return 0.0
        members = [{
            "year": int(r["year"]),
            "donor": r["donor_name"],
            "sector": r.get("sector_name") or "",
            "uc": round(_num(r["usd_commitment"]), 3),
            "ud": round(_num(r["usd_disbursement"]), 3),
            "cb": int(_num(r["confidence"])),
            "ct": int(_num(r["tech_confidence"])),
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

def build_donor_data(df):
    """Aggregate digital rows keyed by donor (mirror of build_data but flipped).

    Output schema per donor:
      {
        total, gov, inc, inf, commit, disb, year_min, year_max,
        recipients: [{name, region, gov, inc, inf, total,
                      commit, commit_gov/inc/inf, disb, disb_gov/inc/inf}, ...]
                    — sorted by commit desc, up to 12
        sectors:    [{name, n, commit}, ...]  top 8 by n
        trend:      [{year, gov, inc, inf, cc_gov, cc_inc, cc_inf, dd_gov, dd_inc, dd_inf}]
        nd:         {total, commit, disb,
                     recipients: [{name, n, commit, disb}, ...]  top 8,
                     trend: [{year, c, cc, dd}]}
      }
    """
    d = df[df["tech_category"].isin(CAT_MAP)].copy()
    d["cat"] = d["tech_category"].map(CAT_MAP)
    d_unique = d.drop_duplicates(DEDUP_KEYS)
    out = {}
    for donor, g in d_unique.groupby("donor_name"):
        cat_counts = Counter(g["cat"])
        entry = {
            "total": int(len(g)),
            "gov":    int(cat_counts.get("gov", 0)),
            "inc":    int(cat_counts.get("inc", 0)),
            "inf":    int(cat_counts.get("inf", 0)),
            "year_min": int(g["year"].min()),
            "year_max": int(g["year"].max()),
            "commit": round(float(g["usd_commitment"].fillna(0).sum()), 3),
            "disb":   round(float(g["usd_disbursement"].fillna(0).sum()), 3),
        }
        # Recipients — analogous to donors in build_data, but keyed by recipient.
        rec_rows = []
        for rec, gg in g.groupby("recipient_name"):
            cc = Counter(gg["cat"])
            uc = gg.groupby("cat")["usd_commitment"].sum()
            ud = gg.groupby("cat")["usd_disbursement"].sum()
            rec_rows.append({
                "name": rec,
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
        rec_rows.sort(key=lambda x: -x["commit"])
        entry["recipients"] = rec_rows[:12]
        # Sectors — top 8
        sec_counts = Counter(g["sector_name"].dropna())
        entry["sectors"] = [{"name": s, "n": int(n)} for s, n in sec_counts.most_common(8)]
        # Trend — per-year counts + USD sums (mirror build_data trend schema).
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
        # Non-digital aggregates for the "Include non-digital" toggle on donor view.
        nd_donor = df[(df["donor_name"] == donor) & (df["tech_category"] == "non_digital")]
        if len(nd_donor):
            nd_recs = (nd_donor.groupby("recipient_name")
                       .agg(n=("orig_idx", "count"),
                            commit=("usd_commitment", "sum"),
                            disb=("usd_disbursement", "sum"))
                       .reset_index()
                       .sort_values("commit", ascending=False)
                       .head(8))
            nd_rec_list = [
                {"name": r["recipient_name"], "n": int(r["n"]),
                 "commit": round(float(r["commit"] or 0), 3),
                 "disb": round(float(r["disb"] or 0), 3)}
                for _, r in nd_recs.iterrows()
            ]
            nd_trend = []
            for year, yg in nd_donor.groupby("year"):
                nd_trend.append({
                    "year": int(year),
                    "c": int(len(yg)),
                    "cc": round(float(yg["usd_commitment"].fillna(0).sum()), 3),
                    "dd": round(float(yg["usd_disbursement"].fillna(0).sum()), 3),
                })
            nd_trend.sort(key=lambda x: x["year"])
            entry["nd"] = {
                "total": int(len(nd_donor)),
                "commit": round(float(nd_donor["usd_commitment"].fillna(0).sum()), 3),
                "disb":   round(float(nd_donor["usd_disbursement"].fillna(0).sum()), 3),
                "recipients": nd_rec_list,
                "trend": nd_trend,
            }
        else:
            entry["nd"] = {"total": 0, "commit": 0, "disb": 0, "recipients": [], "trend": []}
        out[donor] = entry
    return out


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

        # Non-digital aggregates for the General-view toggle. Kept as lightweight
        # per-country totals / donors / trend (no project-level detail); the
        # 42 MB non_digital_projects.js is still used for Project-focus cards.
        nd_country = df[(df["recipient_name"] == country) &
                        (df["tech_category"] == "non_digital")]
        if len(nd_country) > 0:
            nd_donors = (
                nd_country.groupby("donor_name")
                .agg(n=("orig_idx", "count"),
                     commit=("usd_commitment", "sum"),
                     disb=("usd_disbursement", "sum"))
                .reset_index()
                .sort_values("commit", ascending=False)
                .head(8)
            )
            nd_donors_list = [
                {"name": r["donor_name"], "n": int(r["n"]),
                 "commit": round(float(r["commit"] or 0), 3),
                 "disb": round(float(r["disb"] or 0), 3)}
                for _, r in nd_donors.iterrows()
            ]
            nd_trend = []
            for year, yg in nd_country.groupby("year"):
                nd_trend.append({
                    "year": int(year),
                    "c": int(len(yg)),
                    "cc": round(float(yg["usd_commitment"].fillna(0).sum()), 3),
                    "dd": round(float(yg["usd_disbursement"].fillna(0).sum()), 3),
                })
            nd_trend.sort(key=lambda x: x["year"])
            entry["nd"] = {
                "total": int(len(nd_country)),
                "commit": round(float(nd_country["usd_commitment"].fillna(0).sum()), 3),
                "disb": round(float(nd_country["usd_disbursement"].fillna(0).sum()), 3),
                "donors": nd_donors_list,
                "trend": nd_trend,
            }
        else:
            entry["nd"] = {"total": 0, "commit": 0, "disb": 0, "donors": [], "trend": []}

        out[country] = entry

    return out, d_unique

def patch_html(src, dst, new_data, donor_data=None):
    """Rewrite the DATA line + label constants, drop a v3.1 banner."""
    html = src.read_text()
    new_data_json = json.dumps(new_data, ensure_ascii=False, separators=(",", ":"))
    # Strip any prior DONOR_DATA block so re-runs stay idempotent (before the
    # var DATA replacement, so the regex below sees a clean var DATA line).
    html = re.sub(r"\nvar DONOR_DATA = \{.*?\};", "", html, flags=re.DOTALL)
    data_replacement = f"var DATA = {new_data_json};"
    if donor_data is not None:
        donor_json = json.dumps(donor_data, ensure_ascii=False, separators=(",", ":"))
        data_replacement += f"\nvar DONOR_DATA = {donor_json};"
    # Use a function for the replacement so json braces in data_replacement aren't
    # interpreted as regex group backrefs.
    html = re.sub(
        r"var DATA = \{.*?\};",
        lambda m: data_replacement,
        html, count=1, flags=re.DOTALL,
    )
    # Keep v1 labels — user prefers "Digital Governance" / "Digital Inclusion"
    # to the longer v3.1 names. The underlying category still carries
    # governance + rights (resp. human development) scope; this is purely a
    # display rename.
    # Widen the donor-name column so "African Development Bank" / "IMF Resilience
    # and Sustainability Trust" / similar long names don't get truncated.
    html = html.replace(
        ".donor-name{width:130px;",
        ".donor-name{width:210px;",
    )
    # Card rendering reads p.cat and maps via CAT_KEY — update map to v3.1 labels
    # so the new 4-way-collapsed-to-3-slot labels resolve properly.
    html = html.replace(
        'var CAT_KEY = { digital_governance: "gov", digital_inclusion: "inc", hard_infrastructure: "inf" };',
        'var CAT_KEY = { digital_governance_and_rights: "gov", digital_human_development: "inc", hard_infrastructure: "inf" };',
    )
    # The project-view category select uses old v1 category-value strings
    # (digital_governance, digital_inclusion) that no longer match the v3.1
    # tech_category values in project data, so filtering was a no-op for two
    # of three categories. Rewrite the option values + hash-restore list to
    # v3.1 names.
    html = html.replace(
        '[["all","All categories"],["digital_governance","Digital Governance"],["digital_inclusion","Digital Inclusion"],["hard_infrastructure","Hard Infrastructure"]]',
        '[["all","All categories"],["digital_governance_and_rights","Digital Governance"],["digital_human_development","Digital Inclusion"],["hard_infrastructure","Hard Infrastructure"]]',
    )
    html = html.replace(
        '["digital_governance","digital_inclusion","hard_infrastructure"]',
        '["digital_governance_and_rights","digital_human_development","hard_infrastructure"]',
    )
    # Classification note — appended as plain-text footnote before </body> rather
    # than a yellow top banner. Also strip any previously-injected yellow banner
    # so re-runs don't stack them.
    html = re.sub(
        r'<div style="background:#fef3c7;[^"]*"[^>]*>.*?</div>',
        '', html, count=1, flags=re.DOTALL,
    )
    footer_note = (
        '<div style="max-width:1100px;margin:24px auto 40px;padding:0 24px;'
        'font:12px/1.55 -apple-system,sans-serif;color:#64748b">'
        '<b>About the classification.</b> Digital projects are identified and '
        'categorized via a v3.1 4-way soft ensemble of three LLMs '
        '(gemma4-31B + Qwen3.5-35B-A3B + Nemotron-3-Nano-30B) with a '
        'top-3-digital rule at threshold=20. EU donors cover 1990–2024; '
        'non-EU donors (incl. US, Japan, Korea, Canada, Australia) '
        'cover 2019–2024 only. Dataset spans 13 recipients.'
        '</div>'
    )
    if '</body>' in html:
        html = html.replace('</body>', footer_note + '</body>', 1)
    # v1 HTMLs defaulted state.country to "Ukraine"; Ukraine isn't in the 12-country
    # v3.1 cut, so the main panel rendered empty until the user clicked. Fall back
    # to the first country in DATA instead.
    first_country = next(iter(new_data))
    html = re.sub(
        r'(var state\s*=\s*\{\s*country:\s*)"[^"]*"',
        lambda m: m.group(1) + json.dumps(first_country, ensure_ascii=False),
        html, count=1,
    )
    # Default year range → 2019–2024 (aligns with non-EU coverage). Users can
    # still drag the slider back to 1990 since min stays 1990.
    html = html.replace(
        'id="yr-start" min="1990" max="2024" value="1990"',
        'id="yr-start" min="1990" max="2024" value="2019"',
    )
    html = html.replace(
        '<span class="yr-val" id="yr-start-val">1990</span>',
        '<span class="yr-val" id="yr-start-val">2019</span>',
    )
    html = html.replace(
        'yrStart: 1990, yrEnd: 2024',
        'yrStart: 2019, yrEnd: 2024',
    )
    # Refresh the stale "32 countries / 9,570 digital / 3-way" subtitles.
    html = html.replace(
        "32 priority countries · OECD CRS 1990–2024 · 9,570 deduplicated digital projects · 3-way tech classification",
        "13 priority-target recipients · EU donors 1990–2024 · non-EU donors 2019–2024 · v3.1 LLM ensemble",
    )
    html = html.replace(
        "32 priority countries · project-level tech classification (1990–2024) · exact-row-duplicates removed",
        "13 priority-target recipients · project-level digital tech classification · v3.1 LLM ensemble",
    )
    dst.write_text(html)


NON_DIGITAL_CSS = """
.nd-toggle{display:flex;align-items:center;gap:8px;background:rgba(255,255,255,.08);border-radius:6px;padding:6px 12px;font-size:11px;color:rgba(255,255,255,.85);cursor:pointer;user-select:none}
.nd-toggle .nd-sw{position:relative;width:30px;height:16px;background:rgba(255,255,255,.2);border-radius:999px;transition:background .15s}
.nd-toggle .nd-sw::after{content:"";position:absolute;top:2px;left:2px;width:12px;height:12px;background:#fff;border-radius:50%;transition:left .15s}
.nd-toggle.on .nd-sw{background:#16a34a}
.nd-toggle.on .nd-sw::after{left:16px}
.nd-toggle .nd-lbl{font-size:10px;text-transform:uppercase;letter-spacing:.04em;font-weight:600}
.nd-toggle.hidden{display:none}
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

// Toggle is visible in both General and Project focus views. In General view
// it reads lightweight aggregates from DATA[country].nd (embedded, no async
// load); in Project focus it loads the 42 MB non_digital_projects.js lazily
// on first use.

// Override computeAggregates so General view KPIs / donor bars / trend reflect
// non-digital when the toggle is on. Safe for Project focus too (it doesn't
// read these fields). We additively mutate agg.commit / n_total / donors so
// existing render paths pick up combined values without further edits.
var _origComputeAggregates = computeAggregates;
computeAggregates = function(country) {
  var agg = _origComputeAggregates(country);
  if (!agg || !state.includeND) return agg;
  var d = DATA[country];
  if (!d || !d.nd) return agg;
  var nd = d.nd;
  // Sum ND per-year within current range.
  var nd_c = 0, nd_cc = 0, nd_dd = 0;
  (nd.trend || []).forEach(function(t) {
    if (t.year >= state.yrStart && t.year <= state.yrEnd) {
      nd_c  += t.c  || 0;
      nd_cc += t.cc || 0;
      nd_dd += t.dd || 0;
    }
  });
  // Expose ND fields (for KPI renderer below) and fold into headline totals.
  agg.nd_n = nd_c;
  agg.nd_commit = nd_cc;
  agg.nd_disb   = nd_dd;
  agg.n_total += nd_c;
  agg.n_distinct += nd_c; // ND groups are already project-level in the lightweight aggregate
  agg.commit += nd_cc;
  agg.disb   += nd_dd;
  // Merge ND donors. Existing donors carry digital commit; we append ND commit
  // to commit and total, and flag a new "oth" slot for the bar segment.
  var byDonor = {};
  agg.donors.forEach(function(dn) { byDonor[dn.name] = dn; });
  (nd.donors || []).forEach(function(ndn) {
    var dd = byDonor[ndn.name];
    if (!dd) {
      dd = { name: ndn.name, gov:0, inc:0, inf:0, oth:0, total:0,
             commit:0, disb:0, c_gov:0, c_inc:0, c_inf:0, c_oth:0 };
      byDonor[ndn.name] = dd;
    }
    dd.oth = (dd.oth || 0) + ndn.n;
    dd.total += ndn.n;
    dd.commit += ndn.commit || 0;
    dd.disb   += ndn.disb   || 0;
    dd.c_oth  = (dd.c_oth || 0) + (ndn.commit || 0);
  });
  agg.donors = Object.values(byDonor).sort(function(a,b){return b.commit - a.commit;}).slice(0, 8);
  return agg;
};

// When the ND toggle is on, add a 4th segment colour (oth) to the donor bars.
// The existing render loop only knows gov/inc/inf — post-process the built
// donor card by appending an "oth" segment wherever c_oth > 0.
var _origBuildMainPanel = buildMainPanel;
buildMainPanel = function() {
  _origBuildMainPanel.apply(this, arguments);
  if (!state.includeND || state.view !== "general") return;
  var d = DATA[state.country]; if (!d) return;
  var agg = computeAggregates(state.country); if (!agg) return;
  // Add a compact ND pill to the KPI row. The existing CSS sets 6 columns; we
  // bump to 7 via inline style only when the toggle is on.
  var kpiGrid = document.querySelector(".kpi-grid");
  if (kpiGrid && !kpiGrid.querySelector(".kpi.oth")) {
    kpiGrid.style.gridTemplateColumns = "repeat(7, 1fr)";
    var ndPill = document.createElement("div");
    ndPill.className = "kpi oth";
    ndPill.innerHTML = '<div class="lb">Non-digital</div>' +
      '<div class="vl" style="color:#64748b">' + (agg.nd_n || 0).toLocaleString() + '</div>' +
      '<div class="sb">' + fmtUsd(agg.nd_commit || 0) + ' pledged</div>';
    kpiGrid.appendChild(ndPill);
  }
  // Append a grey "oth" segment to each donor bar.
  var donorRows = document.querySelectorAll(".donor-row");
  donorRows.forEach(function(row, i) {
    var donor = agg.donors[i]; if (!donor) return;
    var bw = row.querySelector(".donor-bar-wrap");
    if (!bw || bw.querySelector(".seg.oth")) return;
    var coth = donor.c_oth || 0;
    if (coth <= 0) return;
    var ct = (donor.c_gov || 0) + (donor.c_inc || 0) + (donor.c_inf || 0) + coth || 1;
    // Recompute widths so the 4 segments sum to 100%.
    var segs = bw.querySelectorAll(".seg");
    var existingCats = ["gov","inc","inf"];
    segs.forEach(function(seg, si) {
      var v = donor["c_" + existingCats[si]] || 0;
      seg.style.width = (v / ct * 100) + "%";
    });
    var seg = document.createElement("div");
    seg.className = "seg oth";
    seg.style.width = (coth / ct * 100) + "%";
    seg.style.background = "#94a3b8";
    bw.appendChild(seg);
  });
};

// Render the toggle in the header.
(function() {
  var yrCtrl = document.querySelector(".yr-ctrl");
  if (!yrCtrl) return;
  var t = document.createElement("div");
  t.className = "nd-toggle";
  t.innerHTML = '<span class="nd-lbl">Include non-digital</span>' +
    '<span class="nd-sw"></span>' +
    '<span class="nd-status" id="nd-status">off</span>';
  t.addEventListener("click", function() {
    var turnOn = !state.includeND;
    if (turnOn) {
      // Project-focus needs the big JS companion; General view reads DATA.nd.
      if (state.view === "projects") {
        document.getElementById("nd-status").textContent = "loading…";
        loadNonDigital(function() {
          state.includeND = true;
          t.classList.add("on");
          document.getElementById("nd-status").textContent = "on";
          buildMainPanel();
        });
      } else {
        state.includeND = true;
        t.classList.add("on");
        document.getElementById("nd-status").textContent = "on";
        buildMainPanel();
      }
    } else {
      state.includeND = false;
      t.classList.remove("on");
      document.getElementById("nd-status").textContent = "off";
      if (state.catFilter === "non_digital") state.catFilter = "all";
      buildMainPanel();
    }
  });
  yrCtrl.parentNode.insertBefore(t, yrCtrl.nextSibling);
})();

// ---------- EU + Taiwan donor filter ----------
var EU_TAIWAN_DONORS = new Set([
  "Austria","Belgium","Bulgaria","Croatia","Cyprus","Czechia","Czech Republic",
  "Denmark","Estonia","Finland","France","Germany","Greece","Hungary",
  "Iceland","Ireland","Italy","Latvia","Liechtenstein","Lithuania","Luxembourg",
  "Malta","Monaco","Netherlands","Norway","Poland","Portugal","Romania",
  "Slovak Republic","Slovenia","Spain","Sweden","Switzerland","United Kingdom",
  "EU Institutions","Taiwan"
]);
state.euOnly = false;

// When the toggle is on, rebuild EVERY agg field (KPIs, donor bars, sectors)
// from member walk so the whole General view reflects only EU+Taiwan donors.
var _origComputeAggregates2 = computeAggregates;
computeAggregates = function(country) {
  var agg = _origComputeAggregates2(country);
  if (!agg || !state.euOnly) return agg;
  var d = DATA[country];
  if (!d) return agg;
  var n_gov = 0, n_inc = 0, n_inf = 0;
  var commit = 0, disb = 0;
  var donorMap = {}, sectorMap = {}, projInRange = {};
  d.projects.forEach(function(p) {
    p.members.forEach(function(m) {
      if (m.year < state.yrStart || m.year > state.yrEnd) return;
      if (!EU_TAIWAN_DONORS.has(m.donor)) return;
      var cls = CAT_KEY[p.cat];
      if (cls === "gov") n_gov++;
      else if (cls === "inc") n_inc++;
      else if (cls === "inf") n_inf++;
      commit += m.uc || 0; disb += m.ud || 0;
      if (!donorMap[m.donor]) donorMap[m.donor] = { name: m.donor, gov:0, inc:0, inf:0, total:0, commit:0, disb:0, c_gov:0, c_inc:0, c_inf:0 };
      var dn = donorMap[m.donor];
      if (cls === "gov" || cls === "inc" || cls === "inf") dn[cls]++;
      dn.total++; dn.commit += m.uc || 0; dn.disb += m.ud || 0;
      if (cls) dn["c_" + cls] += m.uc || 0;
      var sec = m.sector || "(unknown)";
      if (!sectorMap[sec]) sectorMap[sec] = { name: sec, n:0, commit:0 };
      sectorMap[sec].n++; sectorMap[sec].commit += m.uc || 0;
      projInRange[p.title + "|" + p.cat] = true;
    });
  });
  var n_total = n_gov + n_inc + n_inf;
  agg.n_total = n_total;
  agg.n_distinct = Object.keys(projInRange).length;
  agg.gov = n_gov; agg.inc = n_inc; agg.inf = n_inf;
  agg.commit = commit; agg.disb = disb;
  agg.donors  = Object.values(donorMap).sort(function(a,b){return b.commit - a.commit;}).slice(0, 10);
  agg.sectors = Object.values(sectorMap).sort(function(a,b){return b.n - a.n;}).slice(0, 8);
  return agg;
};

// Filter project-focus cards to projects with ≥1 EU+Taiwan donor member when on.
var _origGetProjectsInRange2 = getProjectsInRange;
getProjectsInRange = function(country) {
  var arr = _origGetProjectsInRange2(country);
  if (!state.euOnly) return arr;
  return arr.filter(function(p) {
    if (!p.members) return false;
    return p.members.some(function(m) {
      return EU_TAIWAN_DONORS.has(m.donor) && m.year >= state.yrStart && m.year <= state.yrEnd;
    });
  });
};

// Year-trend chart reads d.trend directly; rebuild from member walk when
// EU+Taiwan filter is on so the chart matches the filtered KPIs.
var _origBuildTrendChart = buildTrendChart;
buildTrendChart = function(trend, container) {
  if (!state.euOnly) return _origBuildTrendChart(trend, container);
  var country = state.country;
  var d = DATA[country];
  if (!d) return _origBuildTrendChart(trend, container);
  var byYear = {};
  d.projects.forEach(function(p) {
    var cls = CAT_KEY[p.cat];
    if (cls !== "gov" && cls !== "inc" && cls !== "inf") return;
    p.members.forEach(function(m) {
      if (!EU_TAIWAN_DONORS.has(m.donor)) return;
      if (!byYear[m.year]) byYear[m.year] = { year: m.year, gov:0, inc:0, inf:0 };
      byYear[m.year][cls]++;
    });
  });
  var filteredTrend = Object.values(byYear)
    .filter(function(t) { return t.year >= state.yrStart && t.year <= state.yrEnd; })
    .sort(function(a,b){return a.year - b.year;});
  return _origBuildTrendChart(filteredTrend, container);
};

(function() {
  var yrCtrl = document.querySelector(".yr-ctrl");
  if (!yrCtrl) return;
  var t = document.createElement("div");
  t.className = "nd-toggle";
  t.innerHTML = '<span class="nd-lbl">EU + Taiwan only</span>' +
    '<span class="nd-sw"></span>' +
    '<span class="nd-status" id="eu-status">off</span>';
  t.addEventListener("click", function() {
    state.euOnly = !state.euOnly;
    t.classList.toggle("on", state.euOnly);
    document.getElementById("eu-status").textContent = state.euOnly ? "on" : "off";
    buildMainPanel();
  });
  // Insert after the ND toggle so the two sit side-by-side.
  var nd = yrCtrl.parentNode.querySelector(".nd-toggle");
  if (nd) nd.parentNode.insertBefore(t, nd.nextSibling);
  else yrCtrl.parentNode.insertBefore(t, yrCtrl.nextSibling);
})();

// ---------- By-donor view ----------
// A second axis for the dashboard: pick a donor, see which countries they fund
// and on what. Uses DONOR_DATA aggregate (no per-project member detail — KPIs,
// top recipients, sectors, and year trend only).
state.byDonor = false;
state.donor = null;

// Populate the donor <select> in the header. Sidebar stays hidden in donor mode.
function populateDonorSelect() {
  var sel = document.getElementById("donor-select");
  if (!sel || typeof DONOR_DATA === "undefined") return;
  if (sel.dataset.populated === "1") {
    sel.value = state.donor || sel.value;
    return;
  }
  var donors = Object.entries(DONOR_DATA).map(function(e) {
    return Object.assign({ name: e[0] }, e[1]);
  }).sort(function(a,b){return b.commit - a.commit;});
  if (!state.donor && donors.length) state.donor = donors[0].name;
  donors.forEach(function(dn) {
    var o = document.createElement("option");
    o.value = dn.name;
    o.textContent = dn.name + "  (" + dn.total.toLocaleString() + " entries · " + fmtUsd(dn.commit) + ")";
    if (dn.name === state.donor) o.selected = true;
    sel.appendChild(o);
  });
  sel.addEventListener("change", function() {
    state.donor = sel.value;
    syncHash();
    buildMainPanel();
  });
  sel.dataset.populated = "1";
}

function renderDonorView(panel) {
  panel.innerHTML = "";
  var dn = DONOR_DATA[state.donor];
  if (!dn) {
    panel.innerHTML = '<div style="padding:40px;color:#94a3b8">Pick a donor to view their funding stats.</div>';
    return;
  }
  // Filter trend + recipients + sectors to current year range. Recipients + sectors
  // are already aggregated over the full period in DONOR_DATA, so for a strict
  // year-filter we'd need per-year breakdown; approximate by rebuilding from trend.
  var trend = (dn.trend || []).filter(function(t){return t.year >= state.yrStart && t.year <= state.yrEnd;});
  var gov = 0, inc = 0, inf = 0, cc = 0, dd = 0;
  trend.forEach(function(t) {
    gov += t.gov || 0; inc += t.inc || 0; inf += t.inf || 0;
    cc  += (t.cc_gov || 0) + (t.cc_inc || 0) + (t.cc_inf || 0);
    dd  += (t.dd_gov || 0) + (t.dd_inc || 0) + (t.dd_inf || 0);
  });
  // Non-digital totals (when toggle is on) — fold into headline counts/USD and
  // append a "Non-digital" KPI pill so the summary reflects the full picture.
  var ndStats = { n: 0, cc: 0, dd: 0 };
  if (state.includeND && dn.nd) {
    (dn.nd.trend || []).forEach(function(t) {
      if (t.year < state.yrStart || t.year > state.yrEnd) return;
      ndStats.n  += t.c  || 0;
      ndStats.cc += t.cc || 0;
      ndStats.dd += t.dd || 0;
    });
    cc += ndStats.cc; dd += ndStats.dd;
  }
  var total = gov + inc + inf + ndStats.n;
  var header = document.createElement("div");
  header.className = "profile-header";
  var left = document.createElement("div");
  left.className = "header-left";
  var titleLine = document.createElement("div");
  titleLine.innerHTML = '<span class="country-title">' + escHtml(state.donor) + '</span>' +
    '<span class="proj-count">Donor · ' + state.yrStart + '–' + state.yrEnd + '</span>';
  left.appendChild(titleLine);
  var kpi = document.createElement("div");
  kpi.className = "kpi-grid";
  var pct = function(n) { return total > 0 ? Math.round(n/total*100) : 0; };
  function k(cls, lb, vl, sb) {
    return '<div class="kpi ' + (cls||"") + '"><div class="lb">' + lb + '</div><div class="vl">' + vl + '</div>' +
      (sb ? '<div class="sb">' + sb + '</div>' : '') + '</div>';
  }
  var kpiHtml =
    k("", "Entries", total.toLocaleString(), "&nbsp;") +
    k("", "Pledged", fmtUsd(cc), "&nbsp;") +
    k("", "Disbursed", fmtUsd(dd), "&nbsp;") +
    k("gov", "Governance", gov + " (" + pct(gov) + "%)") +
    k("inc", "Inclusion", inc + " (" + pct(inc) + "%)") +
    k("inf", "Infrastructure", inf + " (" + pct(inf) + "%)");
  if (state.includeND && dn.nd) {
    kpi.style.gridTemplateColumns = "repeat(7, 1fr)";
    kpiHtml += '<div class="kpi oth"><div class="lb">Non-digital</div>' +
      '<div class="vl" style="color:#64748b">' + (ndStats.n || 0).toLocaleString() + '</div>' +
      '<div class="sb">' + fmtUsd(ndStats.cc || 0) + ' pledged</div></div>';
  }
  kpi.innerHTML = kpiHtml;
  left.appendChild(kpi);
  header.appendChild(left);
  panel.appendChild(header);

  // Top recipients bar list (mirror of donor bars in recipient view). When ND
  // toggle is on, merge non-digital commit per recipient into the same bar and
  // re-rank by combined commit.
  var row2 = document.createElement("div");
  row2.className = "chart-row";
  var recCard = document.createElement("div");
  recCard.className = "chart-card left";
  recCard.innerHTML = '<div class="chart-title">Top recipients <span class="sub">by pledged</span></div>';
  var recs = (dn.recipients || []).map(function(r){return Object.assign({}, r);});
  if (state.includeND && dn.nd && dn.nd.recipients) {
    var byName = {};
    recs.forEach(function(r){ byName[r.name] = r; });
    dn.nd.recipients.forEach(function(ndr) {
      var r = byName[ndr.name];
      if (!r) {
        r = { name: ndr.name, gov:0, inc:0, inf:0, total:0, commit:0, disb:0,
              commit_gov:0, commit_inc:0, commit_inf:0, c_oth:0 };
        byName[ndr.name] = r; recs.push(r);
      }
      r.total  += ndr.n || 0;
      r.commit += ndr.commit || 0;
      r.disb   += ndr.disb   || 0;
      r.c_oth  = (r.c_oth || 0) + (ndr.commit || 0);
    });
    recs.sort(function(a,b){return b.commit - a.commit;});
    recs = recs.slice(0, 12);
  }
  var maxC = recs.length ? Math.max.apply(null, recs.map(function(x){return x.commit;})) : 1;
  recs.forEach(function(rec) {
    var dr = document.createElement("div");
    dr.className = "donor-row";
    dr.innerHTML = '<div class="donor-name" title="' + escHtml(rec.name) + '">' + escHtml(rec.name) + '</div>';
    var bw = document.createElement("div");
    bw.className = "donor-bar-wrap";
    bw.style.width = Math.max(8, rec.commit / maxC * 100) + "%";
    var ct = (rec.commit_gov || 0) + (rec.commit_inc || 0) + (rec.commit_inf || 0) + (rec.c_oth || 0) || 1;
    [["gov",rec.commit_gov,"#2563eb"],["inc",rec.commit_inc,"#16a34a"],["inf",rec.commit_inf,"#d97706"],["oth",rec.c_oth,"#94a3b8"]].forEach(function(tup) {
      var v = tup[1] || 0; if (v <= 0) return;
      var seg = document.createElement("div");
      seg.className = "seg " + tup[0];
      seg.style.width = (v / ct * 100) + "%";
      seg.style.background = tup[2];
      bw.appendChild(seg);
    });
    dr.appendChild(bw);
    dr.innerHTML += '<div class="donor-n">' + fmtUsd(rec.commit) + '</div>';
    recCard.appendChild(dr);
  });
  if (!recs.length) recCard.innerHTML += '<div class="empty">No recipients in period.</div>';
  row2.appendChild(recCard);

  // Trend chart (reuse existing helper).
  var trendCard = document.createElement("div");
  trendCard.className = "chart-card right";
  trendCard.innerHTML = '<div class="chart-title">Year trend (entries)</div>';
  var trendBox = document.createElement("div");
  trendCard.appendChild(trendBox);
  row2.appendChild(trendCard);
  panel.appendChild(row2);
  requestAnimationFrame(function(){ _origBuildTrendChart(trend, trendBox); });

  // Sectors
  var row3 = document.createElement("div");
  row3.className = "chart-row";
  var secCard = document.createElement("div");
  secCard.className = "chart-card left";
  secCard.innerHTML = '<div class="chart-title">Top sectors <span class="sub">by entries</span></div>';
  var sectors = dn.sectors || [];
  var maxSN = sectors.length ? Math.max.apply(null, sectors.map(function(s){return s.n;})) : 1;
  sectors.forEach(function(sec) {
    var sr = document.createElement("div");
    sr.className = "sector-row";
    sr.innerHTML = '<div class="sector-name">' + escHtml(sec.name) + '</div>';
    var bar = document.createElement("div");
    bar.className = "sector-bar";
    bar.style.width = Math.max(2, sec.n / maxSN * 100) + "px";
    bar.style.background = CAT_COLORS.gov;
    sr.appendChild(bar);
    sr.innerHTML += '<span class="sector-count">' + sec.n + '</span>';
    secCard.appendChild(sr);
  });
  if (!sectors.length) secCard.innerHTML += '<div class="empty">No sector data.</div>';
  row3.appendChild(secCard);
  panel.appendChild(row3);
}

var _origBuildSidebar = buildSidebar;
buildSidebar = function() {
  // In donor mode the sidebar is empty and hidden — donor pick lives in the header.
  if (state.byDonor) {
    var sidebar = document.getElementById("sidebar");
    if (sidebar) sidebar.innerHTML = "";
    return;
  }
  return _origBuildSidebar();
};

var _origBuildMainPanel3 = buildMainPanel;
buildMainPanel = function() {
  // Toggle sidebar + donor select visibility based on mode.
  var sidebar = document.getElementById("sidebar");
  var main = document.querySelector(".main");
  var donorSelWrap = document.getElementById("donor-select-wrap");
  if (state.byDonor) {
    if (sidebar) sidebar.style.display = "none";
    if (main) main.style.gridTemplateColumns = "1fr";
    if (donorSelWrap) donorSelWrap.style.display = "";
    populateDonorSelect();
    var panel = document.getElementById("main-panel");
    return renderDonorView(panel);
  }
  if (sidebar) sidebar.style.display = "";
  if (main) main.style.gridTemplateColumns = "";
  if (donorSelWrap) donorSelWrap.style.display = "none";
  return _origBuildMainPanel3.apply(this, arguments);
};

(function() {
  var yrCtrl = document.querySelector(".yr-ctrl");
  if (!yrCtrl || typeof DONOR_DATA === "undefined") return;
  // Donor <select> — hidden unless By-donor mode is on.
  var selWrap = document.createElement("div");
  selWrap.id = "donor-select-wrap";
  selWrap.style.cssText = "display:none;align-items:center;gap:8px;background:rgba(255,255,255,.08);border-radius:6px;padding:4px 10px;font-size:11px;color:rgba(255,255,255,.85)";
  selWrap.innerHTML = '<span style="font-size:10px;text-transform:uppercase;letter-spacing:.04em;font-weight:600">Donor</span>';
  var sel = document.createElement("select");
  sel.id = "donor-select";
  sel.style.cssText = "min-width:260px;padding:5px 8px;font-size:12px;color:#0f172a;background:#fff;border:1px solid #cbd5e1;border-radius:4px;cursor:pointer";
  selWrap.appendChild(sel);
  yrCtrl.parentNode.insertBefore(selWrap, yrCtrl.nextSibling);
  // By-donor toggle.
  var t = document.createElement("div");
  t.className = "nd-toggle";
  t.innerHTML = '<span class="nd-lbl">By donor</span>' +
    '<span class="nd-sw"></span>' +
    '<span class="nd-status" id="donor-status">off</span>';
  t.addEventListener("click", function() {
    state.byDonor = !state.byDonor;
    t.classList.toggle("on", state.byDonor);
    document.getElementById("donor-status").textContent = state.byDonor ? "on" : "off";
    buildSidebar();
    buildMainPanel();
  });
  var existing = yrCtrl.parentNode.querySelectorAll(".nd-toggle");
  if (existing.length) existing[existing.length - 1].parentNode.insertBefore(t, existing[existing.length - 1].nextSibling);
  else yrCtrl.parentNode.insertBefore(t, yrCtrl.nextSibling);
})();
"""

FOCUS_COUNTRIES = ["Fiji", "Palau", "Timor-Leste", "Eswatini", "Kenya", "Nigeria", "Mozambique"]
FOCUS_PLACEHOLDER = []
FOCUS_YEAR_MIN = 2019
FOCUS_YEAR_MAX = 2024


def _focus_project_groups(rows):
    """Collapse rows into project cards (merges digital + non-digital in one shape).

    Returns list of cards sorted in-use-first (year_last >= 2023), then newest,
    then biggest pledge. Cards dropped if project_title is blank."""
    out = []
    gg = rows[rows["project_title"].fillna("").str.strip() != ""]
    for (title, cat), g in gg.groupby(["project_title", "tech_category"], sort=False):
        donors = g["donor_name"].value_counts()
        years = g["year"].astype(int)
        def mode_nonempty(series):
            s = series.fillna("").astype(str)
            s = s[s.str.strip() != ""]
            if s.empty: return ""
            return s.mode().iat[0]
        out.append({
            "title": str(title)[:220],
            "cat": cat,
            "donor": donors.index[0],
            "n_donors": int(donors.shape[0]),
            "desc": mode_nonempty(g["short_description"])[:280],
            "sector": mode_nonempty(g["sector_name"]),
            "total_commit": round(float(g["usd_commitment"].fillna(0).sum()), 3),
            "total_disb":   round(float(g["usd_disbursement"].fillna(0).sum()), 3),
            "n_entries": int(len(g)),
            "year_first": int(years.min()),
            "year_last":  int(years.max()),
            "year_range": f"{years.min()}-{years.max()}" if years.min() != years.max() else f"{years.min()}",
        })
    out.sort(key=lambda p: (0 if p["year_last"] >= 2023 else 1,
                            -p["year_last"], -p["total_commit"]))
    return out


def _focus_bundle(rows):
    """Compute {kpis, yearly, projects, cat_breakdown, top_donors} for a row
    subset already filtered to 2019-FOCUS_YEAR_MAX."""
    is_dig = rows["tech_category"].isin(CAT_MAP)
    dig = rows[is_dig]
    nondig = rows[~is_dig]
    total = len(rows)
    kpis = {
        "digital_count":    int(len(dig)),
        "nondigital_count": int(len(nondig)),
        "digital_share":    round(len(dig) / total, 4) if total else 0,
        "pledged":          round(float(dig["usd_commitment"].fillna(0).sum()), 3),
        "disbursed":        round(float(dig["usd_disbursement"].fillna(0).sum()), 3),
    }
    yearly = []
    for year in range(FOCUS_YEAR_MIN, FOCUS_YEAR_MAX + 1):
        y = rows[rows["year"] == year]
        yd = y[y["tech_category"].isin(CAT_MAP)]
        yn = y[~y["tech_category"].isin(CAT_MAP)]
        yearly.append({
            "year": year,
            "digital":    int(len(yd)),
            "nondigital": int(len(yn)),
            "digital_usd":    round(float(yd["usd_commitment"].fillna(0).sum()), 3),
            "nondigital_usd": round(float(yn["usd_commitment"].fillna(0).sum()), 3),
        })
    # Per-category digital breakdown: count + pledged USD per slot (gov/inc/inf).
    cat_breakdown = []
    for full_name, slot in CAT_MAP.items():
        c = dig[dig["tech_category"] == full_name]
        cat_breakdown.append({
            "slot":    slot,
            "name":    full_name,
            "count":   int(len(c)),
            "pledged": round(float(c["usd_commitment"].fillna(0).sum()), 3),
        })
    # Top 5 donors by digital pledged USD.
    td = (
        dig.groupby("donor_name")
        .agg(n=("orig_idx", "count"),
             pledged=("usd_commitment", "sum"),
             disb=("usd_disbursement", "sum"))
        .reset_index()
        .sort_values("pledged", ascending=False)
        .head(5)
    )
    top_donors = [
        {"name": r["donor_name"], "n": int(r["n"]),
         "pledged": round(float(r["pledged"] or 0), 3),
         "disb": round(float(r["disb"] or 0), 3)}
        for _, r in td.iterrows()
    ]
    return {
        "kpis": kpis, "yearly": yearly,
        "cat_breakdown": cat_breakdown,
        "top_donors": top_donors,
        "projects": _focus_project_groups(rows),
    }


def build_country_focus(df):
    """Build FOCUS_DATA for country_focus.html.

    6 target countries (all present in v3.1 CSV) + all_countries aggregate across
    the full 12-recipient set + Mozambique placeholder (classification pending)."""
    d = df[(df["year"] >= FOCUS_YEAR_MIN) & (df["year"] <= FOCUS_YEAR_MAX)].copy()
    d = d.drop_duplicates(DEDUP_KEYS)
    out = {}
    for country in FOCUS_COUNTRIES:
        out[country] = _focus_bundle(d[d["recipient_name"] == country])
    for country in FOCUS_PLACEHOLDER:
        out[country] = {"placeholder": True}
    out["all_countries"] = _focus_bundle(d)
    return out


def patch_country_focus(html_path, focus_data):
    """Inject var FOCUS_DATA into the country_focus.html template in place."""
    html = html_path.read_text()
    payload = json.dumps(focus_data, ensure_ascii=False, separators=(",", ":"))
    html = re.sub(
        r"var FOCUS_DATA = \{.*?\}\s*;\s*/\*END_FOCUS\*/",
        "var FOCUS_DATA = " + payload + "; /*END_FOCUS*/",
        html, count=1, flags=re.DOTALL,
    )
    html_path.write_text(html)


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
    # Display rename: OECD CRS uses "Chinese Taipei"; user-facing label is "Taiwan".
    n_tw = int((df["donor_name"] == "Chinese Taipei").sum())
    df["donor_name"] = df["donor_name"].replace({"Chinese Taipei": "Taiwan"})
    if n_tw:
        print(f"  Renamed {n_tw:,} donor rows: Chinese Taipei → Taiwan")
    # Normalize ens scale. EU-run rows (stratum=full) are 0-100; non-EU and
    # eu_retro_mz rows (from finalize_non_eu_ensemble.py) are 0-1.
    ens_cols = [c for c in [
        "ens_digital_governance_and_rights",
        "ens_digital_human_development",
        "ens_hard_infrastructure",
        "ens_non_digital",
    ] if c in df.columns]
    if ens_cols and "stratum" in df.columns:
        mask = df["stratum"].isin(["non_eu", "eu_retro_mz"])
        df.loc[mask, ens_cols] = df.loc[mask, ens_cols] * 100
        print(f"  Scaled {int(mask.sum()):,} rows from 0-1 → 0-100 ens scale")
    meta = extract_old_meta()
    print(f"Extracted metadata for {len(meta)} countries from old DATA")

    new_data, d_unique = build_data(df, meta)
    donor_data = build_donor_data(df)
    print(f"\nBuilt DATA for {len(new_data)} countries (dedup rows: {len(d_unique):,})")
    print(f"Built DONOR_DATA for {len(donor_data)} donors")
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
        # Only all_country_profiles_v2 gets the donor-view data.
        dd = donor_data if name == "all_country_profiles_v2.html" else None
        patch_html(src, dst, new_data, donor_data=dd)
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

    # Country focus viewer (7 targets + all_countries baseline, 2019-2024 only)
    print("\nBuilding country_focus.html payload...")
    focus_data = build_country_focus(df)
    cf_path = OUT / "country_focus.html"
    patch_country_focus(cf_path, focus_data)
    for c in FOCUS_COUNTRIES + FOCUS_PLACEHOLDER + ["all_countries"]:
        v = focus_data.get(c, {})
        if "kpis" not in v:
            print(f"  {c:18s}  placeholder")
            continue
        k = v["kpis"]
        print(f"  {c:18s}  dig={k['digital_count']:5d}  nd={k['nondigital_count']:5d}  "
              f"share={k['digital_share']*100:5.1f}%  pledged=${k['pledged']:,.0f}M")
    print(f"  wrote {cf_path.relative_to(AID.parent)}  ({cf_path.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
