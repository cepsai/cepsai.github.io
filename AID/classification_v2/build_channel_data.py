"""Build channel ("who executes") data for channels_explorer.html.

The CRS "channel of delivery" is the type of organisation that implements a
project (recipient government, NGO, university, UN agency, private firm, …).
This emits one small JS file:

  window.TM_CHANNELS = [
    {name, fam, n, disb, commit,
     gov_d, inc_d, inf_d, nd_d,   # disbursed US$ by digital type
     gov_c, inc_c, inf_c, nd_c,   # committed US$ by digital type
     gov_n, inc_n, inf_n, nd_n},  # project-row counts by digital type
    ...                            # every channel, sorted by total disbursed
  ]

Family aggregates are derived client-side from `fam`. Headline numbers are
printed so they can be quoted in the page's narrative text.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path("/Users/robertpraas/Documents/GitHub/cepsai.github.io")
CSV = Path("/Users/robertpraas/CEPS-DST Dropbox/Robert Praas/5-taiwan/experiments_v2/results_v3_1/priority_target_v3_1_classified_ensemble_full.csv")
OUT = REPO / "tm_channel_data.js"

# --- NEW digital-classification rule (matches build_treemap_data.build_tiles) ---
# Each row's category is the argmax over the FOUR normalised ensemble weights
# (the three digital types + non_digital). The ens_* columns mix scales — EU
# ('full') rows are 0-100, others ('non_eu'/'eu_retro_mz') are 0-1 — so each row
# is divided by its own 4-way sum before the argmax (argmax is scale-invariant
# per row, but normalising keeps the logic explicit and identical to build_tiles).
# Rows with no ensemble weights fall back to non_digital. This replaces the old
# `tech_category` mapping, which ignored the non_digital weight and could promote
# weak-signal projects.
ENS = {"gov": "ens_digital_governance_and_rights",
       "inc": "ens_digital_human_development",
       "inf": "ens_hard_infrastructure"}
ND_COL = "ens_non_digital"
CATS4 = ["gov", "inc", "inf", "nd"]


def new_category(df):
    """Per-row argmax over the 4 normalised ensemble weights -> gov/inc/inf/nd."""
    raw = {c: df[ENS[c]].fillna(0.0).astype(float) for c in ("gov", "inc", "inf")}
    raw["nd"] = df[ND_COL].fillna(0.0).astype(float)
    s4 = raw["gov"] + raw["inc"] + raw["inf"] + raw["nd"]
    w = {}
    for c in CATS4:
        # rows never soft-scored (s4 == 0) -> non_digital
        w[c] = np.where(s4 > 0, raw[c] / s4, 1.0 if c == "nd" else 0.0)
    wmat = np.vstack([w[c] for c in CATS4]).T
    return np.array(CATS4)[wmat.argmax(axis=1)]
EU27 = {"Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czechia",
        "Denmark", "Estonia", "Finland", "France", "Germany", "Greece",
        "Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg",
        "Malta", "Netherlands", "Poland", "Portugal", "Romania",
        "Slovak Republic", "Slovenia", "Spain", "Sweden"}
EU_INST = "EU Institutions"


def funder_group(donor):
    """Team Europe = EU Institutions + EU member states; everyone else is non-TE."""
    if donor == EU_INST:
        return "inst"
    if donor in EU27:
        return "mem"
    return "oth"

FAM_ORDER = ["Government & public sector", "Multilateral", "NGOs & civil society",
             "Universities & research", "Private sector", "PPPs & networks",
             "Other / unspecified"]


def family(name):
    n = (name or "").lower()
    if "ngo" in n or "civil society" in n:
        return "NGOs & civil society"
    if "universit" in n or "college" in n or "research" in n or "teaching" in n:
        return "Universities & research"
    if "public-private" in n or "partnership" in n or "network" in n:
        return "PPPs & networks"
    if any(k in n for k in ["united nations", "unicef", "undp", "unesco", "unfpa",
                            "world bank", "reconstruction and development",
                            "international monetary", "imf", "multilateral",
                            "development bank", "global fund", "gavi", "wto",
                            "world health", "world food", "regional"]):
        return "Multilateral"
    if "government" in n or "public sector" in n or "public corporation" in n \
            or "public entit" in n or "public-sector" in n:
        return "Government & public sector"
    if "private" in n or "corporation" in n or "bank" in n or "micro finance" in n:
        return "Private sector"
    return "Other / unspecified"


def main():
    print("Loading CSV …")
    df = pd.read_csv(CSV, low_memory=False)
    df["cat"] = new_category(df)
    df["fg"] = df["donor_name"].map(funder_group)
    ch = df["channel_name"].fillna("").astype(str).str.strip().replace("", "(unspecified)")
    df = df.assign(ch=ch)
    df["disb"] = df["usd_disbursement"].fillna(0).astype(float)
    df["commit"] = df["usd_commitment"].fillna(0).astype(float)

    def type_split(sub):
        """{gov_d,inc_d,inf_d,nd_d, gov_c,...} for a slice of rows."""
        o = {}
        for cat in ["gov", "inc", "inf", "nd"]:
            cc = sub[sub["cat"] == cat]
            o[cat + "_d"] = round(float(cc["disb"].sum()), 1)
            o[cat + "_c"] = round(float(cc["commit"].sum()), 1)
            o[cat + "_n"] = int(len(cc))
        return o

    rows = []
    for name, g in df.groupby("ch"):
        rec = {"name": name, "fam": family(name), "n": int(len(g)),
               "disb": round(float(g["disb"].sum()), 1),
               "commit": round(float(g["commit"].sum()), 1)}
        rec.update(type_split(g))                      # all-funders totals
        # Team Europe split: per-funder-group type breakdown
        rec["fg"] = {grp: type_split(g[g["fg"] == grp]) for grp in ("inst", "mem", "oth")}
        rows.append(rec)
    rows.sort(key=lambda r: -r["disb"])

    OUT.write_text(
        "// AUTO-GENERATED by AID/classification_v2/build_channel_data.py — do not edit.\n"
        "window.TM_CHANNELS = " + json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + ";\n"
        "window.TM_FAM_ORDER = " + json.dumps(FAM_ORDER) + ";\n"
    )
    print(f"Wrote {OUT.name} ({OUT.stat().st_size/1e3:.0f} KB), {len(rows)} channels")

    # ---- headline numbers for the narrative ----
    def disb_dig(r): return r["gov_d"] + r["inc_d"] + r["inf_d"]
    tot_dig = sum(disb_dig(r) for r in rows)
    print(f"\nTotal DIGITAL disbursed: ${tot_dig/1000:.1f}B across {len(rows)} channels")
    fam = {}
    for r in rows:
        f = fam.setdefault(r["fam"], {"disb": 0, "n": 0, "gov": 0, "inc": 0, "inf": 0})
        f["disb"] += disb_dig(r); f["gov"] += r["gov_d"]; f["inc"] += r["inc_d"]; f["inf"] += r["inf_d"]
        f["n"] += r["gov_n"] + r["inc_n"] + r["inf_n"]
    print("\nBy FAMILY (digital disbursed):")
    for f in FAM_ORDER:
        if f in fam:
            d = fam[f]
            print(f"  {d['disb']/1000:6.2f}B  {100*d['disb']/tot_dig:5.1f}%  {f}  (gov {d['gov']/1000:.2f}B / inc {d['inc']/1000:.2f}B / inf {d['inf']/1000:.2f}B)")
    print("\nTop 8 channels (digital disbursed):")
    for r in sorted(rows, key=lambda r: -disb_dig(r))[:8]:
        print(f"  {disb_dig(r)/1000:6.2f}B  {r['name'][:48]:48s}  [{r['fam']}]")


if __name__ == "__main__":
    main()
