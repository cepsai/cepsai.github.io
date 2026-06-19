"""Per-EU-member-state, per-year totals for the digital-intensity bar + scatter charts.

For each EU member state and each year 2019-2024, emit total ODA and the
digital-by-type split (disbursed and committed), so the page can compute
"digital ODA as % of that country's own funding" for any chosen set of years.

  window.TM_EU_FUNDER = {
    "Germany": { "2019": {td, tc, gd, id, fd, gc, ic, fc}, "2020": {...}, ... },
    ...
  }
  td/tc = total disbursed/committed (all sectors); gd/id/fd = gov/inc/inf disbursed;
  gc/ic/fc = gov/inc/inf committed.  All US$ millions.

METHODOLOGY (aligned with build_treemap_data.py / the v3.1 replication package):
  The digital verdict is computed at the PROJECT level (group of CRS rows sharing
  donor+recipient+title), NOT per row, and NOT from the legacy `tech_category`
  column. For each project:
    1. per-row 4-way ensemble weights, each row normalised to sum 1 — needed
       because EU rows are scored 0-100 while non-EU rows are 0-1;
    2. the project's $-weighted (by disbursement) 4-way mix;
    3. argmax over ALL FOUR categories — the project is digital only if a digital
       category outweighs non_digital (no absolute threshold).
  A digital project's whole $ is assigned to its argmax digital type (gov/inc/inf),
  matching how the treemap hard-classifies tiles. The total (td/tc) denominator is
  every EU row (full ODA programme), so "% of own ODA" stays a true share.
"""
import json
from pathlib import Path
import pandas as pd

REPO = Path("/Users/robertpraas/Documents/GitHub/cepsai.github.io")
CSV = Path("/Users/robertpraas/CEPS-DST Dropbox/Robert Praas/5-taiwan/experiments_v2/results_v3_1/priority_target_v3_1_classified_ensemble_full.csv")
OUT = REPO / "tm_eu_funder.js"

ENS = {"g": "ens_digital_governance_and_rights",
       "i": "ens_digital_human_development",
       "f": "ens_hard_infrastructure"}
ND_COL = "ens_non_digital"
DIGITAL3 = ["g", "i", "f"]
CATS4 = ["g", "i", "f", "nd"]
EU27 = {"Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czechia",
        "Denmark", "Estonia", "Finland", "France", "Germany", "Greece",
        "Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg",
        "Malta", "Netherlands", "Poland", "Portugal", "Romania",
        "Slovak Republic", "Slovenia", "Spain", "Sweden"}
YEARS = list(range(2019, 2025))


def classify_projects(df):
    """Return a Series 'cat' (g/i/f/nd) indexed like df, assigning every row the
    argmax-over-four verdict of the PROJECT (donor+recipient+title) it belongs to.
    Rows with empty titles can't be grouped into a project -> non-digital ('nd')."""
    cat = pd.Series("nd", index=df.index)

    titled = df[df["project_title"].fillna("").astype(str).str.strip() != ""]
    # per-row normalised 4-way weights (EU 0-100, others 0-1 -> divide by own sum)
    raw = {c: titled[ENS[c]].fillna(0.0).astype(float) for c in DIGITAL3}
    raw["nd"] = titled[ND_COL].fillna(0.0).astype(float)
    s4 = sum(raw[c] for c in CATS4)
    w = {}
    for c in CATS4:
        w[c] = (raw[c] / s4).where(s4 > 0, 1.0 if c == "nd" else 0.0)
    wt = titled["usd_disbursement"].fillna(0).astype(float).clip(lower=0)

    work = pd.DataFrame({"d": titled["donor_name"], "r": titled["recipient_name"],
                         "t": titled["project_title"], "wt": wt})
    for c in CATS4:
        work["num_" + c] = wt * w[c]      # $-weighted numerator per category

    grp = work.groupby(["d", "r", "t"], sort=False)
    agg = grp[["wt"] + ["num_" + c for c in CATS4]].sum()
    # fall back to an unweighted mean where a project has no positive disbursement
    no_wt = agg["wt"] <= 0
    if no_wt.any():
        cnt = grp.size()
        meanw = work.groupby(["d", "r", "t"], sort=False)[["num_" + c for c in CATS4]]
        # recompute unweighted: average of the per-row weights (wt all 0 -> use simple mean of w)
        simple = pd.DataFrame({c: w[c] for c in CATS4})
        simple[["d", "r", "t"]] = work[["d", "r", "t"]]
        smean = simple.groupby(["d", "r", "t"], sort=False)[CATS4].mean()
        for c in CATS4:
            agg.loc[no_wt, "num_" + c] = smean.loc[no_wt, c].values
        agg.loc[no_wt, "wt"] = 1.0

    mix = pd.DataFrame({c: agg["num_" + c] / agg["wt"] for c in CATS4})
    proj_cat = mix.idxmax(axis=1)        # argmax over all four

    # map project verdict back onto the titled rows
    key = list(zip(titled["donor_name"], titled["recipient_name"], titled["project_title"]))
    cat.loc[titled.index] = [proj_cat.loc[k] for k in key]
    return cat


def main():
    print("Loading classified CSV …")
    df = pd.read_csv(CSV, low_memory=False)
    df = df[df["year"].isin(YEARS) & df["donor_name"].isin(EU27)].copy()
    print(f"  {len(df):,} EU27 rows in {YEARS[0]}-{YEARS[-1]}")
    df["disb"] = df["usd_disbursement"].fillna(0).astype(float)
    df["commit"] = df["usd_commitment"].fillna(0).astype(float)

    print("Classifying projects (argmax-over-four, project-level) …")
    df["cat"] = classify_projects(df)

    out = {}
    for (donor, year), g in df.groupby(["donor_name", "year"]):
        rec = {"td": round(float(g["disb"].sum()), 1),
               "tc": round(float(g["commit"].sum()), 1)}
        for code, dk, ck in (("g", "gd", "gc"), ("i", "id", "ic"), ("f", "fd", "fc")):
            sub = g[g["cat"] == code]
            rec[dk] = round(float(sub["disb"].sum()), 1)
            rec[ck] = round(float(sub["commit"].sum()), 1)
        out.setdefault(donor, {})[str(int(year))] = rec

    OUT.write_text(
        "// AUTO-GENERATED by AID/classification_v2/build_eu_funder.py — do not edit.\n"
        "window.TM_EU_FUNDER = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n"
        "window.TM_EU_FUNDER_YEARS = " + json.dumps(YEARS) + ";\n"
    )
    print(f"Wrote {OUT.name} ({OUT.stat().st_size/1e3:.0f} KB), {len(out)} member states")

    print("\nDigital % of own ODA (all years, disbursed) — NEW methodology:")
    rows = []
    for donor, yrs in out.items():
        td = sum(y["td"] for y in yrs.values())
        dig = sum(y["gd"] + y["id"] + y["fd"] for y in yrs.values())
        if td > 0:
            rows.append((dig / td * 100, donor, dig, td))
    for pct, donor, dig, td in sorted(rows, reverse=True):
        print(f"  {pct:5.1f}%  {donor:16s}  dig ${dig/1000:.2f}B / total ${td/1000:.2f}B")


if __name__ == "__main__":
    main()
