"""Compare v1 (3-way Nemotron) to v3.1 (4-way ensemble) on the 12 overlap recipients.

Joins the two classification CSVs row-wise on (year, donor, recipient, purpose_code,
project_title, short_description, usd_commitment, usd_disbursement). The new v3.1
taxonomy remaps cleanly:
  digital_governance      -> digital_governance_and_rights
  digital_inclusion       -> digital_human_development   (along with other_digital)
  hard_infrastructure     -> hard_infrastructure
So label flips are meaningful when compared in that space.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import json

OUT = Path("/Users/robertpraas/Documents/GitHub/cepsai.github.io/AID/classification_v2")
OLD = Path("/Users/robertpraas/CEPS-DST Dropbox/Robert Praas/5-taiwan/experiments_v2/priority_target_recipients.csv")
NEW = Path("/Users/robertpraas/CEPS-DST Dropbox/Robert Praas/5-taiwan/experiments_v2/results_v3_1/priority_target_v3_1_classified_ensemble.csv")

TARGETS = {"Côte d'Ivoire","Eswatini","Fiji","Indonesia","Kenya","Nigeria",
           "Palau","Philippines","Thailand","Timor-Leste","Uganda","Viet Nam"}

V1_TO_V31 = {
    "digital_governance":    "digital_governance_and_rights",
    "digital_inclusion":     "digital_human_development",
    "hard_infrastructure":   "hard_infrastructure",
}

def load():
    """v1 source (= priority_target_recipients.csv) and v3.1 output share orig_idx.
    Both files are the same 191,466 rows; v3.1 added new-taxonomy columns.
    """
    print("Loading v1 source (priority_target_recipients.csv)...")
    v1 = pd.read_csv(OLD, low_memory=False)
    print(f"  v1 rows: {len(v1):,}")
    v1["v1_cat"] = v1["tech_category"].map(V1_TO_V31).fillna("non_digital")
    v1["v1_digital"] = (v1["is_digital"] == "yes").astype(int)
    v1 = v1[["orig_idx","recipient_name","donor_name","year","sector_name",
             "usd_commitment","usd_disbursement","v1_cat","v1_digital"]]

    print("Loading v3.1 output...")
    v3 = pd.read_csv(NEW, low_memory=False)
    print(f"  v3.1 rows: {len(v3):,}")
    v3["v3_cat"] = v3["tech_category"].fillna("non_digital")
    v3["v3_digital"] = (v3["v3_cat"] != "non_digital").astype(int)
    v3 = v3[["orig_idx","v3_cat","v3_digital","primary_weight"]]
    return v1, v3

def distribution(df, col, label):
    out = df[col].value_counts(dropna=False).to_dict()
    print(f"\n{label}:")
    for k, v in sorted(out.items(), key=lambda x: -x[1]):
        print(f"  {str(k):40s} {v:>8,}")
    return out

def join_and_compare(v1, v3):
    m = v1.merge(v3, on="orig_idx", how="inner", validate="one_to_one")
    print(f"\nJoined rows: {len(m):,} / v1 {len(v1):,} / v3 {len(v3):,}")
    return m

def flip_matrix(m):
    print("\n=== LABEL FLIP MATRIX (v1 → v3.1) ===")
    ct = pd.crosstab(m["v1_cat"], m["v3_cat"], margins=True)
    print(ct.to_string())

    # Summary numbers
    print("\n=== SUMMARY ===")
    same = int((m["v1_cat"] == m["v3_cat"]).sum())
    diff = int((m["v1_cat"] != m["v3_cat"]).sum())
    print(f"Rows unchanged: {same:,} ({same/len(m)*100:.2f}%)")
    print(f"Rows flipped:   {diff:,} ({diff/len(m)*100:.2f}%)")

    # Digital classification agreement
    print("\n=== BINARY DIGITAL (is_digital flag) ===")
    both_digital = int(((m["v1_digital"]==1) & (m["v3_digital"]==1)).sum())
    only_v1      = int(((m["v1_digital"]==1) & (m["v3_digital"]==0)).sum())
    only_v3      = int(((m["v1_digital"]==0) & (m["v3_digital"]==1)).sum())
    neither      = int(((m["v1_digital"]==0) & (m["v3_digital"]==0)).sum())
    print(f"  digital in both:   {both_digital:>7,}")
    print(f"  digital v1 only:   {only_v1:>7,} (v3.1 pushed these to non_digital)")
    print(f"  digital v3.1 only: {only_v3:>7,} (ensemble rescued these)")
    print(f"  neither:           {neither:>7,}")
    return ct

def per_country(m):
    print("\n=== PER-COUNTRY DIGITAL COUNTS (v1 vs v3.1, on joined rows) ===")
    g = m.groupby("recipient_name").apply(lambda x: pd.Series({
        "v1_digital": int(x["v1_digital"].sum()),
        "v3_digital": int(x["v3_digital"].sum()),
        "delta":      int(x["v3_digital"].sum() - x["v1_digital"].sum()),
        "v1_gov":     int((x["v1_cat"]=="digital_governance_and_rights").sum()),
        "v3_gov":     int((x["v3_cat"]=="digital_governance_and_rights").sum()),
        "v1_hd":      int((x["v1_cat"]=="digital_human_development").sum()),
        "v3_hd":      int((x["v3_cat"]=="digital_human_development").sum()),
        "v1_inf":     int((x["v1_cat"]=="hard_infrastructure").sum()),
        "v3_inf":     int((x["v3_cat"]=="hard_infrastructure").sum()),
    })).reset_index()
    print(g.to_string(index=False))
    return g

def main():
    v1, v3 = load()

    # Distributions on their own.
    distribution(v1, "v1_cat", "v1 categories (12 targets, remapped to v3.1 space)")
    distribution(v3, "v3_cat", "v3.1 categories (12 targets)")

    # Join row-wise.
    m = join_and_compare(v1, v3)
    ct = flip_matrix(m)
    pc = per_country(m)

    # Dump for the analysis doc.
    pc.to_csv(OUT / "per_country_delta.csv", index=False)
    ct.to_csv(OUT / "flip_matrix.csv")
    print(f"\nWrote {OUT}/per_country_delta.csv and flip_matrix.csv")

if __name__ == "__main__":
    main()
