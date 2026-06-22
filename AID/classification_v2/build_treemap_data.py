"""Build project-tile data for the treemap pages (donor / recipient / donor×recipient).

Scope: years 2019-2024 (where the digital classification is dense).

A "tile" is one project = group of CRS rows sharing (axis_key, other_key, title).
Unified compact array form:

    [title, cat, other, yrs, W, desc]

  cat   : hard (argmax) category — "gov" | "inc" | "inf" (digital) or "nd"
  other : cross-axis label — recipient on the donor page, donor on the recipient page
  yrs   : [[year, disb, commit], ...]  per-year US$ (millions); lets the UI filter
          to any subset of 2019-2024 and re-sum the tile size
  W     : [Wg, Wi, Wf] — the project's digital-type mix from the ENSEMBLE weights,
          $-weighted and normalised to sum 1 over the three digital types. Used by
          the "Weighted %" classification button to split a project's $ across types.
          null for non-digital tiles (not split).
  desc  : full project description (longest non-empty CRS `description` in the
          group), for the tile tooltip. "" when absent or identical to the title.

Digital tiles are emitted in full (eager files). Non-digital tiles are capped to
the TOP_ND largest-by-total-disbursement per axis key (lazy files).
"""
import json
from pathlib import Path
import pandas as pd

REPO = Path("/Users/robertpraas/Documents/GitHub/cepsai.github.io")
CSV = Path("/Users/robertpraas/CEPS-DST Dropbox/Robert Praas/5-taiwan/experiments_v2/results_v3_1/priority_target_v3_1_classified_ensemble_full.csv")

CAT_MAP = {
    "digital_governance_and_rights": "gov",
    "digital_human_development":     "inc",
    "hard_infrastructure":           "inf",
}
ENS = {"gov": "ens_digital_governance_and_rights",
       "inc": "ens_digital_human_development",
       "inf": "ens_hard_infrastructure"}
ND_COL = "ens_non_digital"
DIGITAL3 = ["gov", "inc", "inf"]
CATS4 = ["gov", "inc", "inf", "nd"]
YEARS = list(range(2019, 2025))   # 2019..2024 inclusive
EU27 = {"Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czechia",
        "Denmark", "Estonia", "Finland", "France", "Germany", "Greece",
        "Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg",
        "Malta", "Netherlands", "Poland", "Portugal", "Romania",
        "Slovak Republic", "Slovenia", "Spain", "Sweden"}
EU_INST = "EU Institutions"
REGION = {
    "Kenya": "Africa", "Uganda": "Africa", "Mozambique": "Africa",
    "Nigeria": "Africa", "Côte d'Ivoire": "Africa", "Eswatini": "Africa",
    "Viet Nam": "Asia", "Indonesia": "Asia", "Philippines": "Asia",
    "Thailand": "Asia", "Timor-Leste": "Asia",
    "Fiji": "Pacific", "Palau": "Pacific",
}
TOP_ND = 1500


def build_tiles(df, axis_col, other_col):
    """Return {axis_value: {"dig": [...], "nd": [...]}} of unified tiles."""
    sub = df[df["project_title"].fillna("").astype(str).str.strip() != ""].copy()
    sub = sub.rename(columns={axis_col: "axis", other_col: "other"})
    sub["_disb"] = sub["usd_disbursement"].fillna(0).astype(float)
    sub["_commit"] = sub["usd_commitment"].fillna(0).astype(float)
    # --- per-row 4-way ensemble weights, normalised to sum 1 (change #3) ---
    # The ens_* columns mix scales — EU rows are 0-100, others 0-1 — so divide
    # each row by its own 4-category sum to put every row on the same 0-1 scale.
    # Rows never soft-scored (no ensemble weights) are treated as non_digital.
    raw = {c: sub[ENS[c]].fillna(0.0).astype(float) for c in DIGITAL3}
    raw["nd"] = sub[ND_COL].fillna(0.0).astype(float)
    s4 = sum(raw[c] for c in CATS4)
    for c in CATS4:
        sub["_w" + c] = (raw[c] / s4).where(s4 > 0, 1.0 if c == "nd" else 0.0)

    out = {}
    keys = ["axis", "other", "project_title"]
    n_groups = sub.groupby(keys, sort=False).ngroups
    done = 0
    for (axis, other, title), g in sub.groupby(keys, sort=False):
        done += 1
        if done % 40000 == 0:
            print(f"    {done:,}/{n_groups:,} groups")
        # per-year breakdown
        yr = (g.groupby("year")[["_disb", "_commit"]].sum())
        yrs = [[int(y), round(float(r["_disb"]), 1), round(float(r["_commit"]), 1)]
               for y, r in yr.iterrows()]
        # full description for the tooltip: longest non-empty in the group,
        # dropped if it merely repeats the (often truncated) CRS title.
        descs = [d.strip() for d in g["description"].fillna("").astype(str)
                 if d and d.strip()]
        desc = max(descs, key=len) if descs else ""
        if desc == str(title).strip():
            desc = ""
        if len(desc) > 500:
            desc = desc[:499].rstrip() + "…"
        # --- project's $-weighted 4-way mix, then argmax over ALL FOUR (change #1) ---
        # A project is digital only if a digital category outweighs non_digital.
        # This replaces the old "best digital >= 20" rule, which ignored the
        # non_digital weight and over-promoted weak-signal projects.
        wgt = g["_disb"].clip(lower=0)
        if wgt.sum() <= 0:
            wgt = pd.Series(1.0, index=g.index)
        W4 = {c: float((wgt * g["_w" + c]).sum() / wgt.sum()) for c in CATS4}
        # is_digital is now defined by this argmax (change #2): the dig/nd bucket
        # below is the digital verdict — no reliance on the legacy is_digital
        # column or the old per-row tech_category.
        cat = max(CATS4, key=lambda c: W4[c])
        tile = [str(title), cat, str(other), yrs, None, desc]
        if cat != "nd":
            digtot = W4["gov"] + W4["inc"] + W4["inf"]
            if digtot > 0:
                tile[4] = [round(W4["gov"] / digtot, 3),
                           round(W4["inc"] / digtot, 3),
                           round(W4["inf"] / digtot, 3)]
            else:
                tile[4] = {"gov": [1, 0, 0], "inc": [0, 1, 0], "inf": [0, 0, 1]}[cat]
        d = out.setdefault(axis, {"dig": [], "nd": []})
        (d["nd"] if cat == "nd" else d["dig"]).append(tile)

    def total_disb(tile):
        return sum(y[1] for y in tile[3])
    for axis, d in out.items():
        d["dig"].sort(key=lambda t: -total_disb(t))
        d["nd"].sort(key=lambda t: -total_disb(t))
        d["nd"] = d["nd"][:TOP_ND]
    return out


def write_js(path, varname, payload):
    path.write_text(
        "// AUTO-GENERATED by AID/classification_v2/build_treemap_data.py — do not edit.\n"
        f"window.{varname} = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n"
    )
    print(f"  wrote {path.name} ({path.stat().st_size/1e6:.2f} MB)")


def main():
    print("Loading classified CSV …")
    df = pd.read_csv(CSV, low_memory=False)
    df = df[df["year"].isin(YEARS)]
    print(f"  {len(df):,} rows in {YEARS[0]}-{YEARS[-1]}")

    print("Donor page tiles …")
    eu = df[df["donor_name"].isin(EU27) | (df["donor_name"] == EU_INST)]
    dt = build_tiles(eu, "donor_name", "recipient_name")
    dig = {k: v["dig"] for k, v in dt.items() if v["dig"]}
    nd = {k: v["nd"] for k, v in dt.items() if v["nd"]}
    print(f"  {len(dig)} donors, {sum(len(v) for v in dig.values()):,} dig + "
          f"{sum(len(v) for v in nd.values()):,} nd tiles")
    write_js(REPO / "tm_donor_dig.js", "TM_DONOR_DIG", dig)
    write_js(REPO / "tm_donor_nd.js", "TM_DONOR_ND", nd)

    print("Recipient page tiles …")
    rec = df[df["recipient_name"].isin(REGION)]
    rt = build_tiles(rec, "recipient_name", "donor_name")
    rdig = {k: v["dig"] for k, v in rt.items() if v["dig"]}
    rnd = {k: v["nd"] for k, v in rt.items() if v["nd"]}
    print(f"  {len(rdig)} recipients, {sum(len(v) for v in rdig.values()):,} dig + "
          f"{sum(len(v) for v in rnd.values()):,} nd tiles")
    write_js(REPO / "tm_rec_dig.js", "TM_REC_DIG", rdig)
    write_js(REPO / "tm_rec_nd.js", "TM_REC_ND", rnd)

    (REPO / "tm_regions.js").write_text(
        "// AUTO-GENERATED by AID/classification_v2/build_treemap_data.py — do not edit.\n"
        "window.TM_REGION = " + json.dumps(REGION, ensure_ascii=False) + ";\n"
        "window.TM_YEARS = " + json.dumps(YEARS) + ";\n"
    )
    print("  wrote tm_regions.js")


if __name__ == "__main__":
    main()
