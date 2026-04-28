"""
build_data.py — Slice the v3.1 ensemble CSV into a reviewer slate (data.json).

Three tabs, each limited to borderline / ambiguous cases so a human can
audit without drowning:

    binary   — is_digital='yes' with 50 <= confidence <= 75
               (model leaned digital but wasn't sure)
    multiway — tech_category is one of the 3 digital categories
               AND tech_confidence in [40, 65]
               (maximum-uncertainty zone — v3.1 confidence skews low, so this
               targets the calibration middle-band)
    nontech  — tech_category='non_digital' with max(ens_digital_*) >= 0.10
               (model said non-digital but the ensemble had digital signal)

Each item carries the ensemble weights so the reviewer can see where the
models disagreed. Orig_idx is preserved for CSV-level traceability.
"""
import json, re, pandas as pd, html
from pathlib import Path

CSV = Path("/Users/robertpraas/CEPS-DST Dropbox/Robert Praas/5-taiwan/"
           "experiments_v2/results_v3_1/priority_target_v3_1_classified_ensemble_full.csv")
OUT = Path(__file__).parent / "data.json"
INDEX_HTML = Path(__file__).parent / "index.html"

DIG_CATS = [
    "digital_governance_and_rights",
    "digital_human_development",
    "hard_infrastructure",
]
ALL_CATS = DIG_CATS + ["non_digital"]
# Focus review slates on EU/EFTA/UK + EU Institutions + Taiwan donors.
EU_TAIWAN_DONORS = {
    "Austria","Belgium","Bulgaria","Croatia","Cyprus","Czechia","Czech Republic",
    "Denmark","Estonia","Finland","France","Germany","Greece","Hungary",
    "Iceland","Ireland","Italy","Latvia","Liechtenstein","Lithuania","Luxembourg",
    "Malta","Monaco","Netherlands","Norway","Poland","Portugal","Romania",
    "Slovak Republic","Slovenia","Spain","Sweden","Switzerland","United Kingdom",
    "EU Institutions","Taiwan",
}
ENS_COLS = [
    "ens_digital_governance_and_rights",
    "ens_digital_human_development",
    "ens_hard_infrastructure",
    "ens_non_digital",
]
# Raw per-model soft weights, loaded at module level so to_item() can look up
# each orig_idx without re-opening the files.
SOFT_DIR = CSV.parent
SOFT_FILES = {
    "g": ["EXPORT_soft_gemma31.csv",  "EXPORT_soft_gemma31_non_eu.csv"],
    "q": ["EXPORT_soft_qwen35.csv",   "EXPORT_soft_qwen35_non_eu.csv"],
    "n": ["EXPORT_soft_nemotron.csv", "EXPORT_soft_nemotron_non_eu.csv"],
}
SOFT_WEIGHTS = {"g": {}, "q": {}, "n": {}}  # {prefix: {orig_idx: {cat: %}}}


def _s(v):
    """Coerce pandas NaN / None to empty string, otherwise str()."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v)


def mk_text(row):
    """Combine title + short_description like the reviewer text field in v1."""
    t = _s(row.get("project_title")).strip()
    s = _s(row.get("short_description")).strip()
    d = _s(row.get("description")).strip()
    parts = [p for p in (t, s) if p]
    text = " — ".join(parts) if parts else ""
    if d and d not in text:
        text = (text + " — " + d) if text else d
    return text[:1200]


def to_item(row):
    """Per-row payload. Numeric fields are safely coerced; orig_idx is the
    pointer back to the full CSV."""
    def f(v):
        try:
            return round(float(v), 3)
        except (TypeError, ValueError):
            return None
    ens = {c.replace("ens_", ""): f(row.get(c)) for c in ENS_COLS}
    oi = int(row["orig_idx"]) if pd.notna(row.get("orig_idx")) else None
    # Per-model soft weights (0-100 for each of 4 categories). Populated if
    # this orig_idx was in the digital_only pool (i.e. ran through all 3
    # soft models). Non-digital rows outside that pool won't have these.
    per_model = {}
    for prefix in ("g", "q", "n"):
        w = SOFT_WEIGHTS[prefix].get(oi)
        if w:
            per_model[prefix] = {c: round(float(w.get(c, 0) or 0), 2) for c in ALL_CATS}
    return {
        "orig_idx": oi,
        "year": int(row["year"]) if pd.notna(row.get("year")) else None,
        "recipient": _s(row.get("recipient_name")),
        "donor": _s(row.get("donor_name")),
        "text": mk_text(row),
        "purpose": _s(row.get("purpose_name")),
        "sector": _s(row.get("sector_name")),
        "is_digital": _s(row.get("is_digital")),
        "confidence": f(row.get("confidence")),
        "tech_category": _s(row.get("tech_category")),
        "tech_confidence": f(row.get("tech_confidence")),
        "tech_reason": _s(row.get("tech_reason"))[:1200],
        "ens": ens,
        "models": per_model,
    }


def load_soft_weights():
    """Populate SOFT_WEIGHTS from the per-model pred_weights JSON strings."""
    for prefix, files in SOFT_FILES.items():
        for fname in files:
            fp = SOFT_DIR / fname
            if not fp.exists():
                continue
            dfm = pd.read_csv(fp, usecols=["orig_idx", "pred_weights"])
            for _, r in dfm.iterrows():
                raw = r["pred_weights"]
                if isinstance(raw, str) and raw.strip():
                    try:
                        SOFT_WEIGHTS[prefix][int(r["orig_idx"])] = json.loads(raw)
                    except json.JSONDecodeError:
                        pass
        print(f"  {prefix}: {len(SOFT_WEIGHTS[prefix]):,} soft rows loaded")


def main():
    print(f"Loading {CSV} ...")
    df = pd.read_csv(CSV, low_memory=False)
    print(f"  {len(df):,} rows")
    # Display rename: CRS uses "Chinese Taipei"; user-facing label is "Taiwan".
    df["donor_name"] = df["donor_name"].replace({"Chinese Taipei": "Taiwan"})
    # Normalize ens scale. EU-run rows (stratum=full) are 0-100; non-EU and
    # eu_retro_mz rows (from finalize_non_eu_ensemble.py) are 0-1. Scale the
    # latter two strata only so they match.
    ens_cols = [c for c in ENS_COLS if c in df.columns]
    if ens_cols and "stratum" in df.columns:
        mask = df["stratum"].isin(["non_eu", "eu_retro_mz"])
        df.loc[mask, ens_cols] = df.loc[mask, ens_cols] * 100
        print(f"  Scaled {int(mask.sum()):,} rows from 0-1 → 0-100 ens scale")
    print("Loading per-model soft weights ...")
    load_soft_weights()
    # Focus the review slates on EU + Taiwan donors.
    before = len(df)
    df = df[df["donor_name"].isin(EU_TAIWAN_DONORS)].copy()
    print(f"  Filtered to EU + Taiwan donors: {len(df):,} / {before:,} rows")

    # Binary — all items flagged is_digital='yes' by the binary pipeline, so
    # reviewers can sweep every Taiwan/EU-funded project the binary called digital.
    # Sorted by confidence ascending so borderline cases surface first.
    binary_mask = df["is_digital"] == "yes"
    binary = df[binary_mask].sort_values("confidence")
    print(f"\nbinary  (is_digital='yes'): {len(binary):,}")

    # Multiway — every item tagged with a digital tech_category by the v3.1
    # ensemble, plus "digital-but-non-tech" edge cases (binary=digital,
    # 4-way=non_digital with ens data). No confidence band — the reviewer
    # drills in via the category / donor / recipient filters in the UI.
    has_ens = df[ens_cols].notna().any(axis=1) if ens_cols else True
    dig_all = df["tech_category"].isin(DIG_CATS)
    nontech_after_digital = (df["tech_category"] == "non_digital") & (df["is_digital"] == "yes") & has_ens
    multi_mask = dig_all | nontech_after_digital
    multiway = df[multi_mask].sort_values("tech_confidence")
    print(f"multiway (all digital tech_category + digital-but-non-tech): {len(multiway):,}")
    print("  by category:")
    for c, n in multiway["tech_category"].value_counts().items():
        print(f"    {c:38s} {n}")

    # Nontech ambiguity — non_digital items with notable digital ensemble weight.
    # Ens scale is now 0-100 (see top of main) — threshold in percent.
    nd = df[df["tech_category"] == "non_digital"].copy()
    nd["max_dig_ens"] = nd[[f"ens_{c}" for c in DIG_CATS]].max(axis=1)
    nt_mask = nd["max_dig_ens"] >= 10
    nontech = nd[nt_mask].sort_values("max_dig_ens", ascending=False)
    print(f"nontech (non_digital & max digital ens >= 10%): {len(nontech):,}")

    data = {
        "binary":   [to_item(r) for _, r in binary.iterrows()],
        "multiway": [to_item(r) for _, r in multiway.iterrows()],
        "nontech":  [to_item(r) for _, r in nontech.iterrows()],
    }
    payload = json.dumps(data, ensure_ascii=False)
    OUT.write_text(payload)
    kb = OUT.stat().st_size / 1024
    print(f"\nWrote {OUT}  ({kb:.0f} KB)")
    print(f"  binary:   {len(data['binary']):,}")
    print(f"  multiway: {len(data['multiway']):,}")
    print(f"  nontech:  {len(data['nontech']):,}")

    # Embed the same payload directly into index.html so `open file://...` works
    # (browsers block fetch() on file://). The sentinel block is injected right
    # after <body> (BEFORE the main script) so window.EMBEDDED_DATA is defined
    # by the time the Promise chain reads it.
    html_src = INDEX_HTML.read_text()
    start = "/*EMBEDDED_DATA_START*/"
    end = "/*EMBEDDED_DATA_END*/"
    block = f"<script>{start}\nwindow.EMBEDDED_DATA = {payload};\n{end}</script>"
    # Remove any prior block (incl. mis-placed ones before </body>) to keep idempotent.
    html_src = re.sub(
        rf"<script>{re.escape(start)}.*?{re.escape(end)}</script>\s*",
        "", html_src, flags=re.DOTALL)
    # Inject right after the opening <body ...> tag.
    html_src = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + block, html_src, count=1)
    INDEX_HTML.write_text(html_src)
    print(f"Patched {INDEX_HTML.name} with EMBEDDED_DATA  ({INDEX_HTML.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
