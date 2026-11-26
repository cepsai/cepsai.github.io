import csv
import statistics
import sys
from datetime import datetime
from pathlib import Path

import openpyxl

EU = {
    "Austria": ("AT", "AUT"), "Belgium": ("BE", "BEL"), "Croatia": ("HR", "HRV"), "Cyprus": ("CY", "CYP"),
    "Czechia": ("CZ", "CZE"), "Denmark": ("DK", "DNK"), "Estonia": ("EE", "EST"), "Finland": ("FI", "FIN"),
    "France": ("FR", "FRA"), "Germany": ("DE", "DEU"), "Greece": ("GR", "GRC"), "Hungary": ("HU", "HUN"),
    "Ireland": ("IE", "IRL"), "Italy": ("IT", "ITA"), "Latvia": ("LV", "LVA"), "Lithuania": ("LT", "LTU"),
    "Luxembourg": ("LU", "LUX"), "Malta": ("MT", "MLT"), "Netherlands": ("NL", "NLD"), "Poland": ("PL", "POL"),
    "Portugal": ("PT", "PRT"), "Romania": ("RO", "ROU"), "Slovenia": ("SI", "SVN"), "Spain": ("ES", "ESP"),
    "Sweden": ("SE", "SWE"),
}
EU_MISSING = ["Bulgaria", "Slovakia"]
REF = {"United States": ("US", "USA"), "United Kingdom": ("UK", "GBR")}
OTHER = {
    "Algeria", "Argentina", "Australia", "Bahrain", "Bangladesh", "Barbados", "Bolivia", "Brazil", "Brunei", "Canada",
    "Chile", "Colombia", "Costa Rica", "Dominican Republic", "Ecuador", "Egypt", "Ghana", "Guatemala",
    "Hong Kong SAR", "Iceland", "India", "Indonesia", "Iraq", "Israel", "Jamaica", "Japan", "Jordan", "Kenya",
    "Malaysia", "Maldives", "Mauritius", "Mexico", "Morocco", "Nepal", "New Zealand", "Nigeria", "Norway", "Pakistan",
    "Panama", "Peru", "Philippines", "Puerto Rico", "Qatar", "Saudi Arabia", "Singapore", "South Africa",
    "South Korea", "Sri Lanka", "Switzerland", "Thailand", "Trinidad and Tobago", "Tunisia", "Turkiye", "Ukraine",
    "United Arab Emirates", "Uruguay", "Venezuela", "Vietnam",
}
KEEP = {**EU, **REF}
TIGHT_KEEP = ["France", "Germany", "Ireland", "Italy", "Netherlands", "United States", "United Kingdom"]
TIGHT_SHEETS = [
    ("Natl LMT - App't Index", "attractive_jobs_per_applicant_indexed", "applicants"),
    ("Natl LMT - App'n Index", "attractive_jobs_per_application_indexed", "applications"),
]
LHR_FIRST, LHR_LAST = "2017-01", "2026-10"
YOY_NOW, YOY_BEFORE = "2026-10", "2025-10"
MIN_INDUSTRY_COUNTRIES = 10


def check_country(sheet, name):
    if name not in KEEP and name not in OTHER:
        sys.exit(f"{sheet}: unknown country {name!r}")
    if name in EU_MISSING:
        sys.exit(f"{sheet}: {name} is now in the data, update EU and the page notes")


def month_of(sheet, v):
    if isinstance(v, datetime):
        return v.strftime("%Y-%m")
    s = str(v).strip()
    try:
        datetime.strptime(s, "%Y-%m")
    except ValueError:
        sys.exit(f"{sheet}: bad month {v!r}")
    return s


def months(first, last):
    y, m = map(int, first.split("-"))
    out = []
    while f"{y:04d}-{m:02d}" <= last:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def data_rows(ws, header):
    rows = ws.iter_rows(values_only=True)
    for r in rows:
        if r is not None and tuple(r[1:1 + len(header)]) == header:
            break
    else:
        sys.exit(f"{ws.title}: header {header} not found")
    for r in rows:
        vals = r[1:1 + len(header)]
        if all(v is None for v in vals):
            continue
        if any(v is None for v in vals):
            sys.exit(f"{ws.title}: empty value in {vals}")
        yield vals


def read_tiers(wb):
    tiers = {}
    ws = wb["1C - Country List"]
    rows = ws.iter_rows(values_only=True)
    for r in rows:
        if r[1] == "Country":
            break
    for r in rows:
        if r[1] is None:
            continue
        check_country(ws.title, r[1].strip())
        if r[2] is None:
            sys.exit(f"{ws.title}: no tier for {r[1]!r}")
        tiers[r[1].strip()] = str(r[2]).split("-", 1)[1].strip()
    return tiers


def read_lhr(wb):
    name = "2A - LHR SA by Ctry"
    series = {c: {} for c in KEEP}
    for month, country, v in data_rows(wb[name], ("Month", "Country", "LHR (SA)")):
        country = country.strip()
        check_country(name, country)
        if country in KEEP:
            series[country][month_of(name, month)] = float(v)
    want = months(LHR_FIRST, LHR_LAST)
    for c, s in series.items():
        gaps = [m for m in want if m not in s]
        if gaps:
            sys.exit(f"{name}: {c} misses {len(gaps)} months, first {gaps[0]}")
        extra = sorted(set(s) - set(want))
        if extra:
            sys.exit(f"{name}: {c} has months outside {LHR_FIRST} to {LHR_LAST}: {extra[:3]}")
    return series


def read_industry(wb):
    name = "2B - LHR SA by Ctry, Ind"
    cells = {}
    negatives = []
    for month, country, industry, v in data_rows(wb[name], ("Month", "Country", "Industry", "LHR (SA)")):
        country, industry = country.strip(), industry.strip()
        check_country(name, country)
        m, v = month_of(name, month), float(v)
        if v <= 0:
            negatives.append((country, industry, m, v))
            continue
        if country not in EU or m not in (YOY_NOW, YOY_BEFORE):
            continue
        cells[(country, industry, m)] = v
    return cells, negatives


def read_tightness(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = []
    for sheet, col, measure in TIGHT_SHEETS:
        rows = wb[sheet].iter_rows(values_only=True)
        header = tuple(next(rows))
        if header != ("month", "country_region", col):
            sys.exit(f"{sheet}: unexpected header {header}")
        seen = {}
        for r in rows:
            if r is None or all(v is None for v in r):
                continue
            if any(v is None for v in r):
                sys.exit(f"{sheet}: empty value in {r}")
            month, country, v = month_of(sheet, r[0]), r[1].strip(), float(r[2])
            check_country(sheet, country)
            if country in TIGHT_KEEP:
                seen.setdefault(country, {})[month] = v
        for c in TIGHT_KEEP:
            if c not in seen:
                sys.exit(f"{sheet}: no data for {c}")
            ms = sorted(seen[c])
            gaps = [m for m in months(ms[0], ms[-1]) if m not in seen[c]]
            if gaps:
                sys.exit(f"{sheet}: {c} misses months {gaps[:3]}")
            for m in ms:
                out.append([c, KEEP[c][0], m, measure, f"{seen[c][m]:.4f}"])
    return out


def write(dest, fname, header, rows):
    with open(dest / fname, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"{fname} {len(rows)} rows")


def main(lhr_path, lmt_path, dest):
    wb = openpyxl.load_workbook(lhr_path, read_only=True, data_only=True)
    tiers = read_tiers(wb)
    for c in KEEP:
        if c not in tiers:
            sys.exit(f"1C - Country List: no tier for {c}")
    write(dest, "countries.csv", ["country", "iso2", "group", "tier"],
          [[c, KEEP[c][0], "EU" if c in EU else "Reference", tiers[c]] for c in sorted(KEEP)])

    lhr = read_lhr(wb)
    write(dest, "hiring_rate.csv", ["country", "iso2", "month", "lhr"],
          [[c, KEEP[c][0], m, f"{v:.4f}"] for c in sorted(lhr) for m, v in sorted(lhr[c].items())])

    for fname, group in (("eu_hiring_yoy.csv", EU), ("ref_hiring_yoy.csv", REF)):
        yoy = []
        for c in group:
            before, now = lhr[c][YOY_BEFORE], lhr[c][YOY_NOW]
            yoy.append([c, KEEP[c][0], f"{before:.4f}", f"{now:.4f}", f"{(now / before - 1) * 100:.2f}"])
        yoy.sort(key=lambda r: float(r[4]))
        write(dest, fname, ["country", "iso2", "lhr_2025_10", "lhr_2026_10", "change_pct"], yoy)

    cells, negatives = read_industry(wb)
    for c, ind, m, v in negatives:
        print(f"excluded negative value: {c} / {ind} / {m} / {v}")
    by_ind = {}
    for (c, ind, m), v in cells.items():
        if m != YOY_NOW or (c, ind, YOY_BEFORE) not in cells:
            continue
        by_ind.setdefault(ind, []).append((c, (v / cells[(c, ind, YOY_BEFORE)] - 1) * 100))
    ind_rows, dropped = [], []
    for ind, xs in by_ind.items():
        if len(xs) < MIN_INDUSTRY_COUNTRIES:
            dropped.append(f"{ind} ({len(xs)})")
            continue
        ind_rows.append([ind, f"{statistics.median(x for _, x in xs):.2f}", len(xs)])
    ind_rows.sort(key=lambda r: float(r[1]))
    print("industries dropped for fewer than", MIN_INDUSTRY_COUNTRIES, "EU countries:", ", ".join(sorted(dropped)) or "none")
    write(dest, "eu_industry_yoy.csv", ["industry", "median_change_pct", "n_countries"], ind_rows)

    write(dest, "tightness.csv", ["country", "iso2", "month", "measure", "value"], read_tightness(lmt_path))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("usage: python3 build.py <LHR xlsx> <LMT xlsx> [out_dir]")
    main(sys.argv[1], sys.argv[2], Path(sys.argv[3]) if len(sys.argv) > 3 else Path(__file__).resolve().parent)
