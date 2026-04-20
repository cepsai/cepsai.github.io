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
import json, pandas as pd, html
from pathlib import Path

CSV = Path("/Users/robertpraas/CEPS-DST Dropbox/Robert Praas/5-taiwan/"
           "experiments_v2/results_v3_1/priority_target_v3_1_classified_ensemble.csv")
OUT = Path(__file__).parent / "data.json"

DIG_CATS = [
    "digital_governance_and_rights",
    "digital_human_development",
    "hard_infrastructure",
]
ENS_COLS = [
    "ens_digital_governance_and_rights",
    "ens_digital_human_development",
    "ens_hard_infrastructure",
    "ens_non_digital",
]


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
    return {
        "orig_idx": int(row["orig_idx"]) if pd.notna(row.get("orig_idx")) else None,
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
    }


def main():
    print(f"Loading {CSV} ...")
    df = pd.read_csv(CSV, low_memory=False)
    print(f"  {len(df):,} rows")

    # Binary — borderline digital assertions.
    binary_mask = (df["is_digital"] == "yes") & df["confidence"].between(50, 75)
    binary = df[binary_mask].sort_values("confidence")
    print(f"\nbinary  (is_digital='yes' & conf 50-75): {len(binary):,}")

    # Multiway — digital items in the uncertainty middle-band (v3.1 skews
    # lower than v1, so [40, 65] is the "unsure" zone rather than [50, 70]).
    multi_mask = df["tech_category"].isin(DIG_CATS) & df["tech_confidence"].between(40, 65)
    multiway = df[multi_mask].sort_values("tech_confidence")
    print(f"multiway (digital & tech_conf 40-65): {len(multiway):,}")
    print("  by category:")
    for c, n in multiway["tech_category"].value_counts().items():
        print(f"    {c:38s} {n}")

    # Nontech ambiguity — non_digital items with notable digital ensemble weight.
    nd = df[df["tech_category"] == "non_digital"].copy()
    nd["max_dig_ens"] = nd[[f"ens_{c}" for c in DIG_CATS]].max(axis=1)
    nt_mask = nd["max_dig_ens"] >= 0.10
    nontech = nd[nt_mask].sort_values("max_dig_ens", ascending=False)
    print(f"nontech (non_digital & max digital ens >= 0.10): {len(nontech):,}")

    data = {
        "binary":   [to_item(r) for _, r in binary.iterrows()],
        "multiway": [to_item(r) for _, r in multiway.iterrows()],
        "nontech":  [to_item(r) for _, r in nontech.iterrows()],
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False))
    kb = OUT.stat().st_size / 1024
    print(f"\nWrote {OUT}  ({kb:.0f} KB)")
    print(f"  binary:   {len(data['binary']):,}")
    print(f"  multiway: {len(data['multiway']):,}")
    print(f"  nontech:  {len(data['nontech']):,}")


if __name__ == "__main__":
    main()
