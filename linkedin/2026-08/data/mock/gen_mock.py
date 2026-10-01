#!/usr/bin/env python3
"""MOCK DATA GENERATOR. Synthetic values for a dashboard mock-up. NOT LinkedIn data.

Reads the real CSVs in ../ and writes one mock CSV per real CSV into this folder.
Same filename and columns as the real file, plus `iso3`, `region` and `mock`.
Rows with mock=0 are the 5 real countries, copied unchanged as strings.
Rows with mock=1 are generated here. Mock rows carry method="mock".

Run: python3 gen_mock.py   (stdlib only, fixed seed, reproducible)
"""
import csv
import math
import os
import random

SEED = 20260930
HERE = os.path.dirname(os.path.abspath(__file__))
REAL = os.path.dirname(HERE)

# (country, iso3, region, is_real)
COUNTRIES = [
    ("France", "FRA", "EU27", True),
    ("Germany", "DEU", "EU27", True),
    ("India", "IND", "Asia-Pacific", True),
    ("United Kingdom", "GBR", "Europe (non-EU)", True),
    ("United States", "USA", "Americas", True),
    # EU27 (20 mock)
    ("Spain", "ESP", "EU27", False),
    ("Italy", "ITA", "EU27", False),
    ("Netherlands", "NLD", "EU27", False),
    ("Belgium", "BEL", "EU27", False),
    ("Sweden", "SWE", "EU27", False),
    ("Poland", "POL", "EU27", False),
    ("Ireland", "IRL", "EU27", False),
    ("Portugal", "PRT", "EU27", False),
    ("Denmark", "DNK", "EU27", False),
    ("Austria", "AUT", "EU27", False),
    ("Finland", "FIN", "EU27", False),
    ("Czechia", "CZE", "EU27", False),
    ("Romania", "ROU", "EU27", False),
    ("Greece", "GRC", "EU27", False),
    ("Hungary", "HUN", "EU27", False),
    ("Bulgaria", "BGR", "EU27", False),
    ("Croatia", "HRV", "EU27", False),
    ("Slovakia", "SVK", "EU27", False),
    ("Lithuania", "LTU", "EU27", False),
    ("Estonia", "EST", "EU27", False),
    # Rest of Europe (3 mock)
    ("Switzerland", "CHE", "Europe (non-EU)", False),
    ("Norway", "NOR", "Europe (non-EU)", False),
    ("Turkey", "TUR", "Europe (non-EU)", False),
    # Americas (7 mock)
    ("Canada", "CAN", "Americas", False),
    ("Mexico", "MEX", "Americas", False),
    ("Brazil", "BRA", "Americas", False),
    ("Argentina", "ARG", "Americas", False),
    ("Chile", "CHL", "Americas", False),
    ("Colombia", "COL", "Americas", False),
    ("Peru", "PER", "Americas", False),
    # Asia-Pacific (7 mock)
    ("Australia", "AUS", "Asia-Pacific", False),
    ("New Zealand", "NZL", "Asia-Pacific", False),
    ("Japan", "JPN", "Asia-Pacific", False),
    ("Singapore", "SGP", "Asia-Pacific", False),
    ("Indonesia", "IDN", "Asia-Pacific", False),
    ("Philippines", "PHL", "Asia-Pacific", False),
    ("Malaysia", "MYS", "Asia-Pacific", False),
    # Middle East (4 mock)
    ("United Arab Emirates", "ARE", "Middle East", False),
    ("Saudi Arabia", "SAU", "Middle East", False),
    ("Israel", "ISR", "Middle East", False),
    ("Qatar", "QAT", "Middle East", False),
    # Africa (4 mock)
    ("South Africa", "ZAF", "Africa", False),
    ("Nigeria", "NGA", "Africa", False),
    ("Egypt", "EGY", "Africa", False),
    ("Kenya", "KEN", "Africa", False),
]
REAL_NAMES = [c for c, _, _, r in COUNTRIES if r]
MOCK = [(c, i, g) for c, i, g, r in COUNTRIES if not r]
META = {c: (i, g) for c, i, g, _ in COUNTRIES}

# Mild regional tilt on the hiring slowdown (points added to overall YoY).
REGION_HIRING = {"EU27": -2.0, "Europe (non-EU)": -0.5, "Americas": 0.5,
                 "Asia-Pacific": 1.0, "Middle East": 3.0, "Africa": 0.0}
# Mild regional tilt on AI intensity (z-score shift).
REGION_AI = {"EU27": -0.1, "Europe (non-EU)": 0.2, "Americas": 0.0,
             "Asia-Pacific": 0.2, "Middle East": 0.1, "Africa": -0.5}
# Country-specific AI intensity nudges so hubs look like hubs.
AI_NUDGE = {"Israel": 1.2, "Singapore": 1.1, "Switzerland": 0.8, "Netherlands": 0.6,
            "Ireland": 0.7, "Sweden": 0.5, "Estonia": 0.6, "Finland": 0.4, "Denmark": 0.4,
            "Canada": 0.4, "United Arab Emirates": 0.6, "Nigeria": -0.3, "Peru": -0.5,
            "Kenya": -0.2, "Egypt": -0.3, "Bulgaria": -0.2, "Greece": -0.3}

SKILLS_REAL = ["Large Language Models (LLM)", "AI Strategy", "Automated Machine Learning (AutoML)", "Spring AI"]
SKILLS_EXTRA = ["Generative AI", "Retrieval-Augmented Generation (RAG)", "AI Agents", "Prompt Engineering", "LangChain"]

rng = random.Random(SEED)


def r1(x):
    return f"{round(x, 1):.1f}".replace("-0.0", "0.0")


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def read(name):
    with open(os.path.join(REAL, name), newline="") as f:
        rd = csv.DictReader(f)
        return rd.fieldnames, list(rd)


def write(name, fields, real_rows, mock_rows):
    out_fields = fields + ["iso3", "region", "mock"]
    rows = []
    for r in real_rows:
        i, g = META[r["country"]]
        rows.append({**r, "iso3": i, "region": g, "mock": "0"})
    for r in mock_rows:
        i, g = META[r["country"]]
        rows.append({**r, "iso3": i, "region": g, "mock": "1"})
    with open(os.path.join(HERE, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return rows


# ---------- latent country factors (drawn once, in a fixed order) ----------
LAT = {}
n_entry_beats = 0
for c, _, g in MOCK:
    overall = clamp(rng.gauss(-12.5, 4.0) + REGION_HIRING[g], -24.0, -2.5)
    gap = rng.gauss(-1.4, 0.9)
    LAT[c] = {"overall": overall, "gap": gap,
              "ai": rng.gauss(0, 0.7) + REGION_AI[g] + AI_NUDGE.get(c, 0.0)}
# A few countries where entry beats overall (the real 5 never do).
for c in rng.sample([c for c, _, _ in MOCK], 5):
    LAT[c]["gap"] = rng.uniform(0.2, 1.4)


# ---------- p2_entry_overall ----------
def gen_p2_entry_overall():
    fields, real = read("p2_entry_overall.csv")
    period = real[0]["period"]
    out = []
    for c, _, _ in MOCK:
        o = LAT[c]["overall"]
        e = o + LAT[c]["gap"]
        out.append({"country": c, "level": "Entry", "yoy_hiring_rate_pct": r1(e), "period": period, "method": "mock"})
        out.append({"country": c, "level": "Overall", "yoy_hiring_rate_pct": r1(o), "period": period, "method": "mock"})
    return write("p2_entry_overall.csv", fields, real, out)


# ---------- p2_ai_exposure ----------
def gen_p2_ai_exposure():
    fields, real = read("p2_ai_exposure.csv")
    period = real[0]["period"]
    out = []
    for c, _, _ in MOCK:
        o = LAT[c]["overall"]
        # Real pattern: augmented overall softer than all-jobs, augmented entry much worse;
        # disrupted and insulated entry sit close to their overall.
        spec = {
            "Augmented": (o + rng.gauss(1.8, 1.8), rng.gauss(-6.0, 2.5)),
            "Disrupted": (o + rng.gauss(-2.0, 1.8), rng.gauss(0.4, 1.4)),
            "Insulated": (o + rng.gauss(-3.0, 1.8), rng.gauss(-0.3, 1.2)),
        }
        for exp in ["Augmented", "Disrupted", "Insulated"]:
            ov, eg = spec[exp]
            ov = clamp(ov, -30, -1)
            en = clamp(ov + eg, -35, 0)
            out.append({"country": c, "ai_exposure": exp, "level": "Entry", "yoy_hiring_rate_pct": r1(en), "period": period, "method": "mock"})
            out.append({"country": c, "ai_exposure": exp, "level": "Overall", "yoy_hiring_rate_pct": r1(ov), "period": period, "method": "mock"})
    return write("p2_ai_exposure.csv", fields, real, out)


# ---------- p4_founder_growth ----------
def gen_p4_founder_growth():
    fields, real = read("p4_founder_growth.csv")
    period = real[0]["period"]
    out = []
    for c, _, _ in MOCK:
        v = clamp(rng.gauss(23.5, 4.5) + 3.0 * LAT[c]["ai"], 10.0, 40.0)
        out.append({"country": c, "yoy_change_share_adding_founder_pct": r1(v), "period": period, "method": "mock"})
    return write("p4_founder_growth.csv", fields, real, out)


def smooth_rising(years, start, end, curve, jitter):
    """Monotone non-decreasing path from start to end with an accelerating shape."""
    n = len(years) - 1
    vals = []
    for k in range(len(years)):
        t = k / n
        s = (math.exp(curve * t) - 1) / (math.exp(curve) - 1)
        vals.append(start + (end - start) * s)
    for k in range(1, len(vals) - 1):
        vals[k] += rng.gauss(0, jitter)
    for k in range(1, len(vals)):
        vals[k] = max(vals[k], vals[k - 1])
    return vals


# ---------- p4_founders_ai_skill_by_country ----------
def gen_p4_founders_by_country():
    fields, real = read("p4_founders_ai_skill_by_country.csv")
    years = sorted({int(r["year"]) for r in real})
    out = []
    for c, _, _ in MOCK:
        a = LAT[c]["ai"]
        start = clamp(rng.gauss(2.9, 0.5) + 0.5 * a, 1.2, 5.0)
        end = clamp(start * rng.uniform(3.4, 4.8) + 1.2 * a, 6.0, 21.0)
        vals = smooth_rising(years, start, end, curve=rng.uniform(2.2, 3.4), jitter=0.25)
        for y, v in zip(years, vals):
            out.append({"country": c, "year": str(y), "share_founders_with_ai_skill_pct": r1(v), "method": "mock"})
    return write("p4_founders_ai_skill_by_country.csv", fields, real, out)


# ---------- p5_finance_ai_talent (feeds the bump chart) ----------
def gen_p5_talent():
    fields, real = read("p5_finance_ai_talent.csv")
    years = sorted({int(r["year"]) for r in real})
    out = []
    for c, _, _ in MOCK:
        a = LAT[c]["ai"]
        # Start level and growth are drawn separately so ranks cross over time.
        start = clamp(rng.gauss(1.5, 0.3) + 0.45 * a, 0.6, 2.8)
        mult = clamp(rng.gauss(2.6, 0.45) + 0.3 * a, 2.0, 4.4)
        raw = max(start * mult, 2.2)
        end = raw if raw < 5.0 else 5.0 + (raw - 5.0) * 0.35  # soft cap near the real top (5.8)
        vals = smooth_rising(years, start, end, curve=rng.uniform(0.6, 1.8), jitter=0.04)
        for y, v in zip(years, vals):
            out.append({"country": c, "year": str(y), "share_finance_members_ai_talent_pct": r1(v), "method": "mock"})
    return write("p5_finance_ai_talent.csv", fields, real, out)


# ---------- p5_ai_talent_by_field (feeds the bump chart field selector) ----------
# Finance stays in p5_finance_ai_talent.csv. The other fields are mock for every country,
# the real 5 included, so every row here carries mock=1.
FIELD_LEVEL = {"ICT": 2.6, "Professional services": 1.15, "Manufacturing": 0.75, "Health": 0.5,
               "Education": 0.55, "Retail": 0.4, "Public administration": 0.45}


def gen_p5_talent_by_field(finance_rows):
    fields, _ = read("p5_finance_ai_talent.csv")
    val = "share_finance_members_ai_talent_pct"
    years = sorted({int(r["year"]) for r in finance_rows})
    anchor = {}
    for r in finance_rows:
        anchor.setdefault(r["country"], {})[int(r["year"])] = float(r[val])
    out = []
    for field, level in FIELD_LEVEL.items():
        for c, _, _, _ in COUNTRIES:
            fin = anchor[c]
            start = max(0.1, fin[years[0]] * level * math.exp(rng.gauss(0, 0.2)))
            end = max(start * 1.6, fin[years[-1]] * level * math.exp(rng.gauss(0, 0.2)))
            cap = 4.5 * level
            end = end if end < cap else cap + (end - cap) * 0.35
            vals = smooth_rising(years, start, end, curve=rng.uniform(0.6, 1.8), jitter=0.03 * level)
            for y, v in zip(years, vals):
                out.append({"country": c, "year": str(y), val: r1(v), "method": "mock", "field": field})
    rows = []
    for r in out:
        i, g = META[r["country"]]
        rows.append({**r, "iso3": i, "region": g, "mock": "1"})
    with open(os.path.join(HERE, "p5_ai_talent_by_field.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields + ["field", "iso3", "region", "mock"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return rows


# ---------- p5_finance_ai_job_ads ----------
def gen_p5_job_ads():
    fields, real = read("p5_finance_ai_job_ads.csv")
    years = sorted({int(r["year"]) for r in real})
    out = []
    for c, _, _ in MOCK:
        a = LAT[c]["ai"]
        level = clamp(rng.gauss(2.9, 0.7) + 0.6 * a, 1.2, 5.5)
        drift = rng.gauss(0.03, 0.05)
        v = level
        for k, y in enumerate(years):
            if k:
                v = v + drift + rng.gauss(0, 0.18)
            if y == years[-1]:
                v += rng.uniform(0.2, 0.7)  # 2026 uptick, as in the real series
            v = clamp(v, 0.8, 7.0)
            out.append({"country": c, "year": str(y), "share_finance_job_ads_ai_skill_pct": r1(v), "method": "mock"})
    return write("p5_finance_ai_job_ads.csv", fields, real, out)


# ---------- p5_finance_entry_overall ----------
def gen_p5_finance_entry_overall():
    fields, real = read("p5_finance_entry_overall.csv")
    period = real[0]["period"]
    out = []
    for c, _, _ in MOCK:
        fo = clamp(0.5 * LAT[c]["overall"] + rng.gauss(-6.0, 1.6), -22, -3)
        gap = rng.gauss(-2.0, 1.4)
        if rng.random() < 0.12:
            gap = rng.uniform(0.2, 1.2)
        fe = clamp(fo + gap, -26, -1)
        skill = rng.choice(SKILLS_REAL) if rng.random() < 0.7 else rng.choice(SKILLS_EXTRA)
        for lvl, v in (("Entry", fe), ("Overall", fo)):
            out.append({"country": c, "level": lvl, "yoy_finance_hiring_rate_pct": r1(v), "period": period,
                        "fastest_growing_ai_engineering_skill": skill, "method": "mock"})
    return write("p5_finance_entry_overall.csv", fields, real, out)


# ---------- top5 ----------
# Occupation weights by list, using only occupations present in the real file,
# so the THEMES map in app.js covers every mock row.
GROW_BIAS = {"Founder": 6, "Co-Founder": 4, "AI Engineer": 4, "AI Specialist": 3, "Datacenter Technician": 2,
             "Sales Development Representative": 2, "Program Specialist": 2, "Growth Specialist": 2,
             "Retail Associate": 2, "Salesperson": 2, "Sales Specialist": 2, "IT Analyst": 2, "Office Assistant": 1.5,
             "Campus Ambassador": 1.5, "Teaching Assistant": 1.5, "Bartender": 1.2, "Operations Associate": 1.5}
DECL_BIAS = {"Project Manager": 5, "Project Associate": 3, "Product Manager": 3, "UX Designer": 3, "UI Designer": 2.5,
             "Interface Specialist": 2, "Copywriter": 3, "Technical Writer": 3, "Comms Manager": 2, "Comms Assistant": 2,
             "Community Manager": 2, "Data Analyst": 3, "Software Engineer": 3, "Frontend Developer": 2.5,
             "QA Specialist": 2, "Marketing Assistant": 2, "Digital Marketing Specialist": 2,
             "Product Marketing Manager": 2, "Research Assistant": 1.5, "Real Estate Agent": 1.5,
             "Direction Assistant": 1.5, "HR Manager": 1.5}
ENTRY_ONLY_GROW = {"Campus Ambassador", "Teaching Assistant", "Research Assistant", "Postdoc Researcher", "Law Clerk"}
OVERALL_ONLY = {"Principal", "Board Member", "Owner", "Head of Sales", "Founder", "Co-Founder"}


def pick(pool, weights, k, exclude):
    cands = [o for o in pool if o not in exclude]
    chosen = []
    for _ in range(k):
        w = [weights.get(o, 1.0) for o in cands]
        tot = sum(w)
        x = rng.random() * tot
        acc = 0.0
        for o, wi in zip(cands, w):
            acc += wi
            if x <= acc:
                chosen.append(o)
                cands.remove(o)
                break
    return chosen


def desc_values(top, steps):
    vals = [top]
    for s in steps:
        vals.append(vals[-1] - s)
    return [int(round(v)) for v in vals]


def gen_top5():
    fields, real = read("top5.csv")
    pool = []
    for r in real:
        if r["occupation"] not in pool:
            pool.append(r["occupation"])
    out = []
    for c, _, _ in MOCK:
        o = LAT[c]["overall"]
        a = LAT[c]["ai"]
        lists = {}
        # Overall growing: founders usually lead, values mostly positive.
        g_over = []
        if rng.random() < 0.7:
            g_over.append("Founder")
        g_over += pick([p for p in pool if p not in ENTRY_ONLY_GROW], GROW_BIAS, 5 - len(g_over), set(g_over))
        g_entry = pick([p for p in pool if p not in OVERALL_ONLY], GROW_BIAS, 5, set())
        d_over = pick(pool, DECL_BIAS, 5, set(g_over))
        d_entry = pick([p for p in pool if p not in OVERALL_ONLY], DECL_BIAS, 5, set(g_entry))
        # Magnitudes shift with the country's overall hiring softness and AI intensity.
        soft = (o + 12.5) * 1.2
        top_o = clamp(rng.gauss(52, 16) + soft + 6 * a, 12, 140)
        vo = desc_values(top_o, [rng.uniform(4, 22), rng.uniform(2, 14), rng.uniform(1, 10), rng.uniform(1, 9)])
        top_e = clamp(top_o * rng.uniform(0.25, 0.8) + rng.gauss(0, 5), -5, 90)
        ve = desc_values(top_e, [rng.uniform(1, 15), rng.uniform(1, 10), rng.uniform(0, 8), rng.uniform(0, 6)])
        dtop_o = clamp(rng.gauss(-28, 5) + 0.4 * soft, -45, -12)
        vdo = desc_values(dtop_o, [rng.uniform(0, 3), rng.uniform(0, 3), rng.uniform(0, 5), rng.uniform(1, 14)])
        dtop_e = clamp(dtop_o + rng.gauss(2, 4), -45, -12)
        vde = desc_values(dtop_e, [rng.uniform(0, 3), rng.uniform(0, 4), rng.uniform(0, 5), rng.uniform(1, 10)])
        lists[("overall", "growing")] = (g_over, vo)
        lists[("entry", "growing")] = (g_entry, ve)
        lists[("overall", "declining")] = (d_over, vdo)
        lists[("entry", "declining")] = (d_entry, vde)
        for key in [("overall", "growing"), ("entry", "growing"), ("overall", "declining"), ("entry", "declining")]:
            occs, vals = lists[key]
            for rank, (occ, v) in enumerate(zip(occs, vals), 1):
                out.append({"country": c, "level": key[0], "direction": key[1], "rank": str(rank),
                            "occupation": occ, "yoy_pct": str(min(v, -1) if key[1] == "declining" else v)})
    return write("top5.csv", fields, real, out)


if __name__ == "__main__":
    gen_p2_entry_overall()
    gen_p2_ai_exposure()
    gen_p4_founder_growth()
    gen_p4_founders_by_country()
    talent = gen_p5_talent()
    gen_p5_job_ads()
    gen_p5_finance_entry_overall()
    gen_top5()
    gen_p5_talent_by_field(talent)
    print("Wrote 9 mock CSVs to", HERE)
