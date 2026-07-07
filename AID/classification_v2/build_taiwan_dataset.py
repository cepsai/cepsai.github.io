"""Build the Taiwan (Chinese Taipei) digital-ODA project dataset + embed file.

SCOPE: the FULL OECD CRS bulk record for provider "Chinese Taipei", 2023-2024
(540 activity rows / 218 unique projects / ~US$885M disbursed), NOT the
priority-recipient subset used elsewhere on the site. Each of the 540 rows was
classified for digital content (4-way: digital governance, digital inclusion /
human development, hard infrastructure, non-digital). 15 projects carry a
genuine digital element; they are curated here with web-verified metadata.

Two tiers (matching the user ask "all digital projects … and other projects
with a digital connection"):
  Tier 1 — digital-led / component: digital tech is the core or a distinct
           named workstream.
  Tier 2 — digital thread: a conventional project with a minor digital element.

Every URL was fetched and confirmed to describe the project before inclusion;
none are guessed. Outputs at repo root:
  taiwan_digital_projects.csv   — one row per project
  taiwan_digital_projects.json  — same data, inlined into the HTML explainer
"""
import json
from pathlib import Path
import pandas as pd

REPO = Path("/Users/robertpraas/Documents/GitHub/cepsai.github.io")
HOSTED = Path("/Users/robertpraas/CEPS-DST Dropbox/Robert Praas/Code/ICDF_ODA/mockup/data/hosted")
OUT_CSV = REPO / "taiwan_digital_projects.csv"
OUT_JSON = REPO / "taiwan_digital_projects.json"

# --- the 15 digital projects ------------------------------------------------
# match: (title_substring, recipient) used to aggregate the raw CRS rows.
# tier: 1 = digital-led/component, 2 = digital thread.
# links: kind in {icdf, icdf_news, partner}.
PROJECTS = [
{"key": "svg_video", "title": "Enhancing Public Safety with Intelligent Video Analytics (St. Vincent & the Grenadines)",
 "match": ("Intelligent Video Analytics", "Saint Vincent and the Grenadines"),
 "recipient": "St. Vincent & the Grenadines", "cat": "gov", "intensity": "led", "tier": 1,
 "duration": "2023 to 2025", "status": "Completed",
 "partners": "Taiwan Technical Mission in SVG; SVG IT Services Division; Royal St. Vincent & the Grenadines Police Force",
 "digital_note": "Digital-led. A nationwide smart video-surveillance and analytics system for public safety.",
 "facts": "300+ cameras at 20+ locations incl. Union Island and Bequia; AI licence-plate recognition; a centralised video-sharing platform; cybersecurity training for 200+ Vincentians. Investigation time in covered areas cut by ~50%.",
 "links": [
   {"url": "https://www.icdf.org.tw/wSite/ct?ctNode=31539&mp=2&xItem=69786", "label": "TaiwanICDF project page", "kind": "icdf"},
   {"url": "https://www.searchlight.vc/news/2025/08/14/police-receive-bucket-truck-taiwan-funded-video-analytics-project/", "label": "Searchlight (SVG): 300+ cameras installed", "kind": "partner"}]},

{"key": "pry_his", "title": "Health Information Management Efficiency Enhancement Project (Paraguay)",
 "match": ("Health Information Management Efficiency Enhancement Project in Paraguay", "Paraguay"),
 "recipient": "Paraguay", "cat": "gov", "intensity": "led", "tier": 1,
 "duration": "2016 to 2024 (Phases 1–3)", "status": "In operation",
 "partners": "TaiwanICDF; Cathay General Hospital; Paraguay Ministry of Public Health & Social Welfare; Paraguay Ministry of ICT",
 "digital_note": "Digital-led. A national health information system (HIS) replacing handwritten hospital records.",
 "facts": "The HIS is now in 1,000 public healthcare facilities, covering health data for over 70% of Paraguay's population; the goal is all 1,592 public medical institutions.",
 "links": [
   {"url": "https://www.icdf.org.tw/wSite/ct?ctNode=31549&mp=2&xItem=58289", "label": "TaiwanICDF project page (Phase 2)", "kind": "icdf"},
   {"url": "https://www.icdf.org.tw/wSite/ct?ctNode=31765&mp=2&xItem=33764", "label": "TaiwanICDF project page (Phase 1)", "kind": "icdf"},
   {"url": "https://www.icdf.org.tw/wSite/ct?ctNode=31572&mp=2&xItem=73589", "label": "ICDF news: HIS now in 1,000 public hospitals", "kind": "icdf_news"}]},

{"key": "blz_flood", "title": "Flood Warning Capacity Improvement for the Belize River Basin",
 "match": ("Flood Warning Capacity", "Belize"),
 "recipient": "Belize", "cat": "gov", "intensity": "led", "tier": 1,
 "duration": "2023 to 2025", "status": "Completed",
 "partners": "TaiwanICDF; National Taiwan University; Belize Ministry of Sustainable Development, Climate Change & DRM; NEMO; National Met & Hydrological Services",
 "digital_note": "Digital-led. A hydrological-sensor flood early-warning system for the Belize River Basin.",
 "facts": "Five hydrological monitoring stations; flood-potential maps for Belmopan, San Ignacio and Belize City. San Ignacio — previously with no alert mechanism — can now receive flood warnings up to three hours in advance.",
 "links": [
   {"url": "https://www.icdf.org.tw/wSite/ct?ctNode=31572&mp=2&xItem=74183", "label": "ICDF news: NTU flood-warning project concludes", "kind": "icdf_news"},
   {"url": "https://www.pressoffice.gov.bz/ministry-of-sustainable-development-and-taiwanicdf-host-closing-ceremony-for-disaster-management-training/", "label": "Govt of Belize: disaster-management training", "kind": "partner"}]},

{"key": "som_his", "title": "Health Information Management Efficiency Enhancement Project (Somaliland)",
 "match": ("Health Information Management Efficiency Enhancement Project in Somaliland", "Eastern Africa, regional"),
 "recipient": "Somaliland (CRS: Eastern Africa, regional)", "cat": "gov", "intensity": "led", "tier": 1,
 "duration": "2022 to 2027", "status": "In operation",
 "partners": "TaiwanICDF; Somaliland Ministry of Health Development; Kaohsiung Medical University Chung-Ho Memorial Hospital",
 "digital_note": "Digital-led. An integrated hospital health information system (SHIS) with electronic medical records.",
 "facts": "SHIS deployed at 6 hospitals; 394,374 electronic medical records accumulated; 60 training sessions / 1,497 participants; automated daily uploads to the Ministry's central server.",
 "links": [
   {"url": "https://www.icdf.org.tw/wSite/ct?ctNode=31549&mp=2&xItem=68951", "label": "TaiwanICDF project page", "kind": "icdf"},
   {"url": "https://somalilandchronicle.com/2023/03/29/the-first-somaliland-health-information-system-at-hargeisa-group-hospital-launched/", "label": "Somaliland Chronicle: HIS launched at Hargeisa", "kind": "partner"}]},

{"key": "slu_ict", "title": "Application of ICT in Digital Capacity Building Project (Saint Lucia)",
 "match": ("Application of Information and Communication Technology", "Saint Lucia"),
 "recipient": "Saint Lucia", "cat": "inc", "intensity": "led", "tier": 1,
 "duration": "2023 to 2027", "status": "In operation",
 "partners": "TaiwanICDF; St. Lucia Ministry of Public Service; Ministry of Education; Taiwan Technical Mission",
 "digital_note": "Digital-led. Builds national ICT-training capacity and Digital Development Centres.",
 "facts": "Converting government buildings (Laborie, then Gros Islet, Dennery, Soufrière) into Digital Development Centres; target +54% training capacity (up to 1,440 trainees/year). Total value US$2.01M (Taiwan US$1.52M + St. Lucia US$0.49M).",
 "links": [
   {"url": "https://www.icdf.org.tw/wSite/ct?ctNode=31539&mp=2&xItem=70201", "label": "TaiwanICDF project page", "kind": "icdf"},
   {"url": "https://thevoiceslu.com/2023/10/taiwan-saint-lucia-sponsored-ict-capacity-building-project-launched/", "label": "The Voice (St. Lucia): project launched", "kind": "partner"}]},

{"key": "gtm_ews", "title": "Early Warning and Disaster Management System Project (Guatemala)",
 "match": ("Early Warning and Disaster Management System", "Guatemala"),
 "recipient": "Guatemala", "cat": "gov", "intensity": "led", "tier": 1,
 "duration": "2023 to 2025", "status": "Completed",
 "partners": "TaiwanICDF; Guatemala CONRED; National Taiwan University civil-engineering team; Taiwan Investment & Trade Mission in Central America",
 "digital_note": "Digital-led. An IoT-sensor flood early-warning and disaster-management system. The CRS line shown is the preparatory tranche.",
 "facts": "Three IoT monitoring stations in the Cahabón river basin; a flood-simulation model (50/150/300mm scenarios); a disaster risk map; 4 community response plans; targeting a 30% reduction in response time.",
 "links": [
   {"url": "https://www.icdf.org.tw/wSite/ct?xItem=71011&ctNode=31531&mp=2", "label": "TaiwanICDF project page", "kind": "icdf"}]},

{"key": "som_egov", "title": "Somaliland E-government Capability Enhancement Project",
 "match": ("E-government Capability Enhancement", "Eastern Africa, regional"),
 "recipient": "Somaliland (CRS: Eastern Africa, regional)", "cat": "gov", "intensity": "led", "tier": 1,
 "duration": "2021 to 2023", "status": "Completed",
 "partners": "TaiwanICDF; Somaliland Ministry of ICT; Taiwan Technical Mission",
 "digital_note": "Digital-led. Built the 'S-Road' intra-government data-exchange platform and a government portal.",
 "facts": "Deployed the 'S-Road' data-exchange system and a government portal; 52 ICT training programmes for 1,096+ participants; supports the Somaliland e-Government Strategy 2020-2024 Action Plan.",
 "links": [
   {"url": "https://www.icdf.org.tw/wSite/ct?xItem=62522&ctNode=31626&mp=2", "label": "TaiwanICDF project page", "kind": "icdf"},
   {"url": "https://somalilandreporter.com/2024/05/24/taiwans-to-boost-somalilands-digital-transformation-in-phase-ii-partnership/", "label": "Somaliland Reporter: digital-transformation phase II", "kind": "partner"}]},

{"key": "plw_fish", "title": "Strengthening Coastal Fisheries Resource Management Project (Palau)",
 "match": ("Strengthening Coastal Fisheries", "Palau"),
 "recipient": "Palau", "cat": "inc", "intensity": "component", "tier": 1,
 "duration": "2024 to 2027", "status": "In operation",
 "partners": "Taiwan Technical Mission in Palau; Palau Ministry of Agriculture, Fisheries & Environment / Bureau of Fisheries",
 "digital_note": "Digital component. Procures an information-integration platform to digitise fisheries-resource data management.",
 "facts": "Coastal catch-reporting points and an information-integration platform; target of 80% of catch across Palau's three states under the new monitoring mechanism. Aligned to SDG 14.",
 "links": [
   {"url": "https://www.icdf.org.tw/wSite/ct?ctNode=31665&mp=2&xItem=71819", "label": "TaiwanICDF project page", "kind": "icdf"},
   {"url": "https://www.icdf.org.tw/wSite/ct?xItem=72093&ctNode=31572&mp=2", "label": "ICDF news: Taiwan–Palau blue economy", "kind": "icdf_news"}]},

{"key": "fji_health", "title": "Strengthening Digital Healthcare for NCDs and COVID-19 in Fiji",
 "match": ("Strengthening Digital Healthcare", "Fiji"),
 "recipient": "Fiji", "cat": "inc", "intensity": "led", "tier": 1,
 "duration": "2024 to 2025", "status": "Completed",
 "partners": "TaiwanICDF; USAID; Fiji Ministry of Health & Medical Services; National Taiwan University Hospital Hsin-Chu Branch",
 "digital_note": "Digital-led. Built the 'Sova Ni Bula' app, replacing paper records with digital case management for NCD, COVID-19 and long-COVID patient tracking.",
 "facts": "9,000+ patient records digitised; 4,100+ clinical consultations supported; 88 healthcare professionals trained. TaiwanICDF's first public-health project in Fiji.",
 "links": [
   {"url": "https://www.icdf.org.tw/wSite/ct?ctNode=31680&mp=2&xItem=72267", "label": "TaiwanICDF project page", "kind": "icdf"},
   {"url": "https://www.icdf.org.tw/wSite/ct?ctNode=31572&mp=2&xItem=72053", "label": "ICDF news: ICDF–USAID–Fiji MHMS app", "kind": "icdf_news"},
   {"url": "https://islandsbusiness.com/partner-advertorials/building-a-more-resilient-pacific-taiwan-and-fijis-partnership-in-digital-health-and-medical-capacity/", "label": "Islands Business: Taiwan–Fiji digital health", "kind": "partner"}]},

{"key": "tha_smart", "title": "Smart Farming Systems for Horticulture (Thailand)",
 "match": ("Smart Farming Systems", "Thailand"),
 "recipient": "Thailand", "cat": "inc", "intensity": "led", "tier": 1,
 "duration": "2023 to 2026", "status": "In operation",
 "partners": "Taiwan Technical Mission in Thailand; Royal Project Foundation (RPF), Chiang Mai",
 "digital_note": "Digital-led. Introduces sensing, decision and environmental-control (IoT) systems for precision agriculture at RPF stations.",
 "facts": "10 smart-agriculture demonstration sites; block-program modules for 4 target crops; 146+ RPF personnel trained (to Mar 2026). Targets: +10% yield, −15% pesticide use.",
 "links": [
   {"url": "https://www.icdf.org.tw/wSite/ct?xItem=70877&ctNode=31677&mp=2", "label": "TaiwanICDF project page", "kind": "icdf"},
   {"url": "https://www.icdf.org.tw/wSite/ct?ctNode=31929&mp=1&xItem=74033", "label": "ICDF quarterly: 'When AI Enters the Fields'", "kind": "icdf_news"},
   {"url": "https://www.icdf.org.tw/wSite/ct?ctNode=31572&mp=2&xItem=70632", "label": "ICDF news: 5th RPF cooperation MOU", "kind": "icdf_news"}]},

{"key": "blz_imaging", "title": "Strengthening Medical Imaging System in Belize",
 "match": ("Strengthening Medical Imaging System", "Belize"),
 "recipient": "Belize", "cat": "inc", "intensity": "led", "tier": 1,
 "duration": "2019 to 2023", "status": "Completed",
 "partners": "TaiwanICDF; Far Eastern Memorial Hospital (Taiwan); Belize Ministry of Health & Wellness",
 "digital_note": "Digital-led. Strengthens digital medical-imaging services with software, equipment and IT-personnel training.",
 "facts": "Digital imaging at Karl Heusner Memorial Hospital plus Western, Northern (later Southern) regional hospitals; trained two Belizean radiologists via a three-year Taiwan residency.",
 "links": [
   {"url": "https://www.icdf.org.tw/wSite/ct?ctNode=31572&mp=2&xItem=57351", "label": "ICDF news: Far Eastern Memorial Hospital partnership", "kind": "icdf_news"},
   {"url": "https://www.icdf.org.tw/wSite/ct?xItem=69307&ctNode=31572&mp=2", "label": "ICDF news: training Belize's first radiologists", "kind": "icdf_news"},
   {"url": "https://www.pressoffice.gov.bz/mohw-and-taiwan-sign-public-health-projects-agreement/", "label": "Govt of Belize: imaging project concluded", "kind": "partner"}]},

{"key": "hnd_his", "title": "Hospital Health Information Management Efficiency Enhancement Project (Honduras)",
 "match": ("Hospital Health Information Management", "Honduras"),
 "recipient": "Honduras", "cat": "gov", "intensity": "led", "tier": 1,
 "duration": "to 2023", "status": "Discontinued",
 "partners": "Taiwan Technical Mission in Honduras; Taipei Municipal Wanfang Hospital; Honduras Secretaría de Salud",
 "digital_note": "Digital-led. Developed a hospital health information system for two public hospitals.",
 "facts": "HIS for Puerto Cortés and Gabriela Alvarado (Danlí) hospitals; trained doctors and IT staff. No TaiwanICDF page survives — Honduras switched diplomatic recognition to the PRC in March 2023, after which ICDF wound down; documented here via the Honduran press.",
 "links": [
   {"url": "https://www.elheraldo.hn/honduras/gestion-hospitales-capacitacion-taiwan-honduras-HQEH1496735", "label": "El Heraldo (Honduras): Taiwan trains hospital staff", "kind": "partner"}]},

# --- Tier 2: digital thread ---
{"key": "swz_maternal", "title": "Maternal and Infant Health Care Improvement Project (Eswatini, Phase 2)",
 "match": ("Maternal and Infant Health Care Improvement Project in the Kingdom of Eswatini", "Eswatini"),
 "recipient": "Eswatini", "cat": "inc", "intensity": "thread", "tier": 2,
 "duration": "2019 to 2023", "status": "Completed",
 "partners": "Chiayi Christian Hospital; Hualien Tzu Chi Hospital; Eswatini Ministry of Health; Swaziland Nazarene Health Institution",
 "digital_note": "Digital thread. A conventional maternal-health project; the digital element is strengthening health-data analysis capacity.",
 "facts": "Scaled to ~85 health facilities nationwide; E9.5M of medical equipment donated. Postnatal-care coverage within 7–14 days in target areas reported rising from 22% (2016) to 90% (2019).",
 "links": [
   {"url": "https://www.icdf.org.tw/wSite/ct?ctNode=31623&mp=2&xItem=53647", "label": "TaiwanICDF project page", "kind": "icdf"},
   {"url": "https://independentnews.co.sz/7433/news/taiwan-donates-e9-5-million-worth-of-medical-equipment-towards-maternal-health-care/", "label": "Eswatini Independent News: E9.5M equipment", "kind": "partner"}]},

{"key": "swz_tvet", "title": "Technical and Vocational Skills Certification Enhancement Project (Eswatini)",
 "match": ("Technical and Vocational Skills Certification", "Eswatini"),
 "recipient": "Eswatini", "cat": "inc", "intensity": "thread", "tier": 2,
 "duration": "2021 to 2025", "status": "Completed",
 "partners": "Taiwan Technical Mission in Eswatini; Eswatini Ministry of Labour & Social Security; Ministry of Education & Training",
 "digital_note": "Digital thread. A skills-certification (TVET) project; the digital element is ICT labs and an upgraded certification information system.",
 "facts": "High-Demand trade test for 1,138 people; 44 upskilling classes with 606 graduates (to June 2025). Beneficiary institutions ECOT and Gwamile VOCTIM received upgraded electrical-engineering and ICT labs.",
 "links": [
   {"url": "https://www.icdf.org.tw/wSite/ct?ctNode=31623&mp=2&xItem=63477", "label": "TaiwanICDF project page", "kind": "icdf"},
   {"url": "https://www.divt.org.sz/tvet-projects/", "label": "Eswatini DIVT: TVET projects", "kind": "partner"}]},

{"key": "idn_rice", "title": "Expanding High-Quality Rice Seed Production in South Sulawesi (Indonesia)",
 "match": ("Expanding High-Quality Rice Seed Production", "Indonesia"),
 "recipient": "Indonesia", "cat": "inc", "intensity": "thread", "tier": 2,
 "duration": "2021 to 2023", "status": "Completed",
 "partners": "Taiwan Technical Mission in Indonesia; Hasanuddin University (UNHAS); Indonesian Cereals Research Institute (ICERI); IRRI",
 "digital_note": "Digital thread. Primarily a rice-seed agronomy project; the digital element is meteorological stations and climate-monitoring technology.",
 "facts": "~400 ha of rice-farming promotion, training workshops, meteorological stations. Extension of a phase-1 project that aimed to make UNHAS a certified-seed technology centre.",
 "links": [
   {"url": "https://www.icdf.org.tw/wSite/ct?xItem=63091&ctNode=31668&mp=2", "label": "TaiwanICDF project page", "kind": "icdf"},
   {"url": "https://www.icdf.org.tw/wSite/ct?ctNode=31572&mp=2&xItem=44606", "label": "ICDF news: phase-1 launch", "kind": "icdf_news"}]},
]

ANCHORS = {
    "icdf_home": "https://www.icdf.org.tw/wSite/mp?mp=2",
    "icdf_about": "https://www.icdf.org.tw/wSite/ct?xItem=4470&ctNode=31511&mp=2",
    "icdf_reports": "https://www.icdf.org.tw/wSite/lp?BaseDSD=7&CtUnit=148&ctNode=31575&mp=2",
    "icdf_2024_report_pdf": "https://www.icdf.org.tw/wSite/DownloadFile?type=attach&file=f1750730377181.pdf&realname=2024+Annual+Report+(Single+page).pdf",
    "oecd_profile_pdf": "https://www.oecd.org/content/dam/oecd/en/publications/reports/2025/06/development-co-operation-profiles_02ffa45c/chinese-taipei_efd7b737/a6401e1c-en.pdf",
}

CAT_LABEL = {"gov": "Digital governance & public services",
             "inc": "Digital inclusion / human development",
             "inf": "Hard digital infrastructure"}


def main():
    raw = pd.concat([pd.read_parquet(HOSTED / f"crs_{y}.parquet") for y in (2023, 2024)], ignore_index=True)
    tw = raw[raw["donor_name"].astype(str).str.contains("Taipei", case=False, na=False)].copy()
    tw["d"] = pd.to_numeric(tw["usd_disbursement"], errors="coerce").fillna(0)
    tw["c"] = pd.to_numeric(tw["usd_commitment"], errors="coerce").fillna(0)
    T = tw["project_title"].fillna("")

    total_disb = round(float(tw["d"].sum()), 4)
    total_commit = round(float(tw["c"].sum()), 4)
    n_rows_total = len(tw)
    n_projects_total = tw.groupby([T, tw["recipient_name"].fillna("?")]).ngroups

    # The total is dominated by a few pooled "Global Development Program" budget
    # lines that are not discrete projects. Compute a discrete-project denominator
    # so the digital share can be read both ways (honest framing).
    S = tw["sector_name"].fillna("")
    pooled = T.str.contains("Global Development Program") | T.str.contains("Global Aid Management Initiative")
    excl = (pooled | S.str.contains("Administrative Costs of Donors")
            | T.str.contains("repayment of all bilateral loans")
            | T.str.contains("Special Fund") | T.str.contains("Financial Intermediary")
            | T.str.contains("Investment Project") | T.str.contains("Credit Program"))
    pooled_disb = round(float(tw[pooled]["d"].sum()), 4)
    discrete_disb = round(float(tw[~excl]["d"].sum()), 4)
    print(f"Full Taiwan CRS 2023-24: {n_rows_total} rows, {n_projects_total} unique projects, "
          f"${total_disb:.1f}M disbursed (pooled programme lines ${pooled_disb:.1f}M = "
          f"{100*pooled_disb/total_disb:.0f}%; discrete project spend ${discrete_disb:.1f}M)")

    records, matched_idx = [], set()
    for p in PROJECTS:
        sub_t, sub_r = p["match"]
        mask = T.str.contains(sub_t, regex=False) & (tw["recipient_name"] == sub_r)
        rows = tw[mask]
        assert len(rows) > 0, f"no CRS rows matched {p['key']} ({sub_t} / {sub_r})"
        overlap = matched_idx & set(rows.index)
        assert not overlap, f"row overlap for {p['key']}: {overlap}"
        matched_idx |= set(rows.index)
        rec = {
            "project": p["title"], "recipient": p["recipient"],
            "tier": p["tier"], "tier_label": "Digital project" if p["tier"] == 1 else "Project with a digital thread",
            "digital_category": CAT_LABEL[p["cat"]], "cat": p["cat"], "intensity": p["intensity"],
            "years_in_crs": "/".join(map(str, sorted(rows["year"].unique()))),
            "crs_rows": int(len(rows)),
            "usd_disbursement_m": round(float(rows["d"].sum()), 4),
            "usd_commitment_m": round(float(rows["c"].sum()), 4),
            "crs_sector": rows["sector_name"].dropna().iloc[0] if rows["sector_name"].notna().any() else "",
            "duration": p["duration"], "status": p["status"],
            "implementing_partners": p["partners"],
            "digital_component": p["digital_note"], "key_facts": p["facts"],
            "icdf_project_page": next((l["url"] for l in p["links"] if l["kind"] == "icdf"), p["links"][0]["url"]),
            "more_links": " | ".join(f'{l["label"]}: {l["url"]}' for l in p["links"]),
            "links": p["links"],
        }
        records.append(rec)

    dig_disb = round(sum(r["usd_disbursement_m"] for r in records), 4)
    t1 = [r for r in records if r["tier"] == 1]
    t2 = [r for r in records if r["tier"] == 2]
    print(f"Digital projects: {len(records)} (Tier1 {len(t1)}, Tier2 {len(t2)}); "
          f"${dig_disb:.3f}M disbursed = {100*dig_disb/total_disb:.2f}% of total")

    # CSV (drop the nested links list; more_links holds them flat)
    df = pd.DataFrame([{k: v for k, v in r.items() if k != "links"} for r in records])
    df.to_csv(OUT_CSV, index=False)
    print(f"Wrote {OUT_CSV.name} ({len(df)} rows)")

    # sort for display: tier asc, then disbursement desc
    records.sort(key=lambda r: (r["tier"], -r["usd_disbursement_m"]))
    payload = {
        "scope": "Chinese Taipei (Taiwan) projects with a digital element in the OECD CRS, 2023-2024",
        "total_portfolio_disbursed_usd_m": total_disb,
        "total_portfolio_projects": int(n_projects_total),
        "total_portfolio_rows": int(n_rows_total),
        "pooled_programme_disbursed_usd_m": pooled_disb,
        "pooled_programme_share_pct": round(100 * pooled_disb / total_disb, 0),
        "discrete_project_disbursed_usd_m": discrete_disb,
        "digital_disbursed_usd_m": dig_disb,
        "digital_share_pct": round(100 * dig_disb / total_disb, 2),
        "digital_share_of_discrete_pct": round(100 * dig_disb / discrete_disb, 1),
        "n_digital_projects": len(records),
        "n_tier1": len(t1), "n_tier2": len(t2),
        "n_recipients": len({r["recipient"] for r in records}),
        "anchors": ANCHORS,
        "projects": records,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"Wrote {OUT_JSON.name}")


if __name__ == "__main__":
    main()
