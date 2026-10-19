import csv
import sys
from pathlib import Path

import openpyxl

HIRING_SHEETS = [
    ("09 - YOY LHR by Exposure", "Overall", "yoy"),
    ("10 - YOY Rel LHR by Exposure", "Overall", "rel_yoy"),
    ("12 - Entry YOY LHR by Exposure", "Entry", "yoy"),
    ("13 - Entry YOY Rel LHR by Expo", "Entry", "rel_yoy"),
]
SHARE_SHEET = "11 - Posting Share by Exposure"
EXPOSURES = ["Augmented", "Disrupted", "Insulated"]
META = {
    "Australia": ("AUS", "Asia-Pacific"),
    "Brazil": ("BRA", "Americas"),
    "Canada": ("CAN", "Americas"),
    "France": ("FRA", "EU27"),
    "Germany": ("DEU", "EU27"),
    "India": ("IND", "Asia-Pacific"),
    "Ireland": ("IRL", "EU27"),
    "Italy": ("ITA", "EU27"),
    "Mexico": ("MEX", "Americas"),
    "Netherlands": ("NLD", "EU27"),
    "Singapore": ("SGP", "Asia-Pacific"),
    "Spain": ("ESP", "EU27"),
    "Sweden": ("SWE", "EU27"),
    "United Arab Emirates": ("ARE", "Middle East"),
    "United Kingdom": ("GBR", "Europe (non-EU)"),
    "United States": ("USA", "Americas"),
}


def read_sheet(wb, name):
    rows = wb[name].iter_rows(values_only=True)
    header = next(rows)
    out = []
    for r in rows:
        if r is None or all(v is None for v in r):
            continue
        d = dict(zip(header, r))
        country = str(d["country_region"]).strip()
        exposure = str(d["segment"]).strip()
        if country not in META:
            sys.exit(f"{name}: unknown country {country!r}")
        if exposure not in EXPOSURES:
            sys.exit(f"{name}: unknown segment {exposure!r}")
        if d["metric_value"] is None:
            sys.exit(f"{name}: empty value for {country} {exposure} {d['month_date']}")
        out.append((country, str(d["month_date"]).strip(), exposure, float(d["metric_value"])))
    return out


def order(rows):
    return sorted(rows, key=lambda r: (r[0], r[1], EXPOSURES.index(r[2])))


def main(src, dest):
    wb = openpyxl.load_workbook(src, read_only=True, data_only=True)
    hiring = []
    for sheet, level, metric in HIRING_SHEETS:
        for country, month, exposure, v in order(read_sheet(wb, sheet)):
            iso3, region = META[country]
            hiring.append([country, iso3, region, month, exposure, level, metric, f"{v * 100:.2f}"])
    with open(dest / "hiring_by_exposure.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["country", "iso3", "region", "month", "exposure", "level", "metric", "value_pct"])
        w.writerows(hiring)
    share = []
    for country, month, exposure, v in order(read_sheet(wb, SHARE_SHEET)):
        iso3, region = META[country]
        share.append([country, iso3, region, month, exposure, f"{v * 100:.2f}"])
    with open(dest / "posting_share_by_exposure.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["country", "iso3", "region", "month", "exposure", "share_pct"])
        w.writerows(share)
    print(f"hiring_by_exposure.csv {len(hiring)} rows, posting_share_by_exposure.csv {len(share)} rows")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python3 build.py <xlsx> [out_dir]")
    main(sys.argv[1], Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent)
