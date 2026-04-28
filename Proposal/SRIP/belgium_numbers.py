"""Generate Belgium-focused aggregates from the SRIP yearly CSVs.

Reads the per-year metric files already shipped into this folder:
    country/{crunchbase,openalex,regpat}/{year}.csv
    urban/{crunchbase,openalex,regpat}/{year}.csv

Writes:
    be_numbers.json -- BE totals per year per metric, EU totals, BE rank within
                       EU, BE/EU and BE/World shares, BE top cities per metric.

The dashboard `dashboard_be.html` consumes this JSON for header stats; the
charts themselves still load the per-year CSVs directly so series stay
sliceable by year on the client.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent
METRICS = ["crunchbase", "openalex", "regpat"]
METRIC_LABELS = {
    "crunchbase": "Investments (USD)",
    "openalex": "Publications",
    "regpat": "Patents",
}
YEARS = list(range(2000, 2026))
EU = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE",
}

ISO_RE = re.compile(r"\(([^)]+)\)\s*$")
URBAN_ID_RE = re.compile(r"\((\d+)\)\s*$")


def iso_from_geo(geo: str) -> str | None:
    if not isinstance(geo, str):
        return None
    m = ISO_RE.search(geo)
    return m.group(1).strip().upper() if m else None


def load_country(metric: str, year: int) -> pd.DataFrame:
    p = BASE / "country" / metric / f"{year}.csv"
    if not p.exists():
        return pd.DataFrame(columns=["geo", "count", "domain", "iso"])
    df = pd.read_csv(p)
    df = df[df["domain"].astype(str).str.strip() == "Artificial Intelligence"].copy()
    df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0.0)
    df["iso"] = df["geo"].map(iso_from_geo)
    return df


def load_urban(metric: str, year: int) -> pd.DataFrame:
    p = BASE / "urban" / metric / f"{year}.csv"
    if not p.exists():
        return pd.DataFrame(columns=["geo", "count", "domain"])
    df = pd.read_csv(p)
    df = df[df["domain"].astype(str).str.strip() == "Artificial Intelligence"].copy()
    df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0.0)
    return df


def load_be_city_lookup() -> dict[int, str]:
    cw_text = (BASE / "crosswalk.json").read_text().replace(": NaN", ": null")
    cw = json.loads(cw_text)
    out: dict[int, str] = {}
    for c in cw:
        if (c.get("country_id") or "").upper() != "BE":
            continue
        uid = c.get("urban_id")
        name = c.get("urban_name")
        if uid is None or name is None:
            continue
        out[int(uid)] = name
    return out


def main() -> None:
    out: dict = {
        "metrics": METRIC_LABELS,
        "years": YEARS,
        "eu_codes": sorted(EU),
        "be": {
            "per_year": {},
            "totals": {},
            "rank_in_eu": {},
            "share_of_eu": {},
            "share_of_world": {},
            "top_cities": {},
        },
        "eu_per_year": {},
        "world_per_year": {},
    }

    for m in METRICS:
        per_year_be: dict[int, float] = {}
        per_year_eu: dict[int, float] = {}
        per_year_world: dict[int, float] = {}
        ranks: dict[int, int | None] = {}
        share_eu: dict[int, float] = {}
        share_world: dict[int, float] = {}

        for y in YEARS:
            df = load_country(m, y)
            if df.empty:
                per_year_be[y] = per_year_eu[y] = per_year_world[y] = 0.0
                ranks[y] = None
                share_eu[y] = share_world[y] = 0.0
                continue

            be_v = float(df.loc[df["iso"] == "BE", "count"].sum())
            eu_df = df[df["iso"].isin(EU)]
            eu_v = float(eu_df["count"].sum())
            world_v = float(df["count"].sum())

            per_year_be[y] = be_v
            per_year_eu[y] = eu_v
            per_year_world[y] = world_v

            eu_sorted = (
                eu_df.groupby("iso", as_index=False)["count"].sum()
                     .sort_values("count", ascending=False)
                     .reset_index(drop=True)
            )
            be_row = eu_sorted.index[eu_sorted["iso"] == "BE"]
            ranks[y] = int(be_row[0]) + 1 if len(be_row) else None
            share_eu[y] = (be_v / eu_v) if eu_v else 0.0
            share_world[y] = (be_v / world_v) if world_v else 0.0

        out["be"]["per_year"][m] = per_year_be
        out["eu_per_year"][m] = per_year_eu
        out["world_per_year"][m] = per_year_world
        out["be"]["rank_in_eu"][m] = ranks
        out["be"]["share_of_eu"][m] = share_eu
        out["be"]["share_of_world"][m] = share_world
        out["be"]["totals"][m] = {
            "be": sum(per_year_be.values()),
            "eu": sum(per_year_eu.values()),
            "world": sum(per_year_world.values()),
        }

    be_city_names = load_be_city_lookup()
    be_city_ids = set(be_city_names)

    for m in METRICS:
        bag: dict[int, float] = {}
        for y in YEARS:
            u = load_urban(m, y)
            if u.empty:
                continue
            ids = u["geo"].astype(str).str.extract(URBAN_ID_RE)[0]
            mask = ids.notna()
            sub = u.loc[mask].copy()
            sub["urban_id"] = ids[mask].astype(int)
            sub = sub[sub["urban_id"].isin(be_city_ids)]
            for uid, total in sub.groupby("urban_id")["count"].sum().items():
                bag[int(uid)] = bag.get(int(uid), 0.0) + float(total)
        ranked = sorted(bag.items(), key=lambda kv: -kv[1])
        out["be"]["top_cities"][m] = [
            {"urban_id": uid, "name": be_city_names.get(uid, str(uid)), "value": v}
            for uid, v in ranked
        ]

    out_path = BASE / "be_numbers.json"
    out_path.write_text(json.dumps(out, indent=2))

    print(f"Wrote {out_path}")
    for m in METRICS:
        t = out["be"]["totals"][m]
        be, eu, wd = t["be"], t["eu"], t["world"]
        print(
            f"  {m:11s} BE={be:>16,.0f}  EU={eu:>16,.0f}  World={wd:>16,.0f}"
            f"   BE/EU={be / eu if eu else 0:6.1%}   BE/World={be / wd if wd else 0:6.2%}"
        )
        cities = out["be"]["top_cities"][m][:5]
        if cities:
            top = ", ".join(f"{c['name']} ({c['value']:,.0f})" for c in cities)
            print(f"               top BE cities: {top}")


if __name__ == "__main__":
    main()
