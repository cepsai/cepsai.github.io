# V2 vs V1 — what changed in the AID dashboards

Two new files in this directory:

- `all_country_profiles_v2.html` — single-country deep dive, replaces `all_country_profiles.html` (66 MB → 5.8 MB)
- `country_comparison_v2.html` — cross-country comparison, replaces `country_comparison.html` (915 KB → 5.8 MB)

Both rebuilds use the new digital ODA dataset from `5-taiwan/priority_1990_2024_final_reclassified.csv` with the 3-way tech categorization.

## TL;DR

| Aspect                | V1 (March 2026)                              | V2 (April 2026)                              |
|-----------------------|----------------------------------------------|----------------------------------------------|
| **Scope of countries** | 157 DAC recipients + regional aggregates    | **32 priority countries** (Taiwan ICDF priority list) |
| **Year coverage**      | CRS 1973–2024                               | OECD CRS **1990–2024**                       |
| **Dataset**            | All ODA flows                               | **Digital ODA only** (filtered by `is_digital == yes`) |
| **Records**            | ~140k+ total ODA records                    | **9,570 deduplicated** digital projects (from 14,759 raw rows after exact-row dedup) |
| **Tech classification**| Binary `is_tech` flag + ~6 keyword "subtopics" + 8 Rio thematic markers | **3-way LLM categorization**: Digital Governance / Digital Inclusion / Hard Infrastructure |
| **Classifier sources** | Sector codes + keyword rules; "Wide" vs "Strict" toggle | Qwen3-4B (binary) + Nemotron-3-Nano-30B (4-way) |
| **Per-project enrichment** | Title, sector, donor, USD, raw description | + LLM-generated reasoning (`tech_reason`), confidence scores, member-level entry breakdown |
| **Project deduplication** | None — raw rows shown directly           | Exact-row dedup + grouped by `(title, category)` with `members[]` showing each entry |
| **File size**          | 66 MB / 915 KB                              | 5.8 MB / 5.8 MB                              |
| **Visual style**       | Dark navy gradient header + dense layout    | Same dark header carried over for continuity, lighter card-based body |

---

## File 1: `all_country_profiles.html` → `all_country_profiles_v2.html`

### What V1 had

V1 was a single-country deep-dive across all 157 DAC recipients and 52 years of CRS data. The country was selected from a top-bar dropdown (with Eswatini and Palau as quick-pick buttons). Four view modes lived in the header:

- **All Projects** — KPI cards, thematic markers row, sectors bar chart, project cards (filterable by donor/sector/location/search/show 10/25/50/all)
- **Tech Only** — same but filtered to `is_tech == 1`, plus a tech subtopics breakdown and a keyword chip filter
- **More** — top donors hbar, financial-instruments donut, commitment vs disbursement bar pair, top channels
- **Trends** — three SVG line charts (total ODA, tech ODA, project counts)

Plus a **Compare** mode that opened a second country dropdown and rendered two countries side by side, a **year-range slider** (1973–2024), a **Commit/Disb** aggregation toggle, an **Export CSV** button, a **treemap modal** for thematic markers, and a tooltip helper. Per-record schema was rich: `t,sd,de,dn,c,d,s,sn,f,ch,g,it,st,kw,th,ag,sdg,dt`.

### What V2 has

V2 is a single page that combines a country sidebar (left, 260 px) with a tabbed main panel (general / project focus). The dark gradient header is preserved for continuity, with a year-range slider on the right. Both tabs and the sidebar update live as the year range changes.

**Sidebar**: 32 priority countries grouped by region (Europe, Asia, Central Asia, Africa, Pacific), each row showing a mini stacked bar (gov / inc / inf split) and the entry count for the current year window. Diplomatic priority countries are tagged "(D)".

**Main panel header**: country title, region pill, period label, and a **6-cell KPI grid** (entries · pledged · disbursed · governance count · inclusion count · infrastructure count) all responsive to the year filter.

**General tab** (4 charts):
- **Top donors** — top 8 by pledged USD, with stacked bar showing how each donor splits across the 3 categories. Hover for cat-level breakdown.
- **Year trend** — d3 stacked bar chart, gov / inc / inf entries per year (within filter range)
- **Top sectors** — top 8 by entry count, bars colored by the country's dominant category, label wraps so long names like "Public sector policy and administrative management" stay readable
- **Themes from descriptions** — keyword-extracted themes as font-size-scaled pills (full period only)

**Project focus tab** (cards + dropdown):
- Tech category dropdown filter (All / Gov / Inc / Inf)
- Export CSV button (filtered set)
- Pledged + disbursed totals in the results bar
- Cards sorted by total pledged, with labeled fields (Title / Subtitle / Description / **Sector** bold / Why \<category\>) and confidence pills ("Confidence as tech: X%" / "Confidence in <category>: X%")
- Hover any card → tooltip showing every member entry of the deduplicated project group with year, donor, sector, pledged, disbursed, and confidence scores

URL hash deep-linking: `#Ukraine/projects/digital_governance/2018-2024`.

### Biggest differences (single-country)

| Aspect | V1 → V2 |
|---|---|
| **Country picker** | Top-bar dropdown of 157 → **left sidebar of 32 priority countries** with mini stacked bars |
| **View modes** | All Projects / Tech Only / More / Trends → **General / Project focus** (2 tabs, project focus is the new "Tech Only" + project list combined) |
| **Project granularity** | Raw rows → **deduplicated by `(title, category)`** with `members[]` for entry-level breakdown |
| **Tech breakdown** | "Subtopic" tags as keyword chips → **3 explicit categories** with stacked bars and labeled cards |
| **Why a project is "tech"** | Implicit (binary flag) → explicit **`tech_reason`** field shown on every card, + confidence percentages |
| **Compare mode** | Side-by-side 2-country panel | **Removed** — superseded by the country comparison file |
| **Treemap modal** | Thematic markers treemap | **Removed** — Rio markers aren't in the new dataset; sectors and themes serve a similar role |
| **Donor / sector / location / search filters** | All present | **Removed** — reduced to one filter (tech category) since the dataset is much smaller and the per-card hover handles entry-level inspection |
| **Financial instruments donut, channels** | Present in "More" mode | **Removed** — those columns weren't kept in the digital extract; can be added if useful |
| **Year range slider** | 1973–2024 | **1990–2024** (data only goes back to 1990 in the digital extract) |
| **CSV export** | Project list export | **Country-scoped CSV export** with all dedup-aware fields including reason and confidence |
| **File size** | 66 MB | **5.8 MB** (~92% smaller) |

### What V2 still does that V1 did
- Year range slider, sticky header
- Per-country trend chart
- Top sectors and top donors
- Project list with details
- Themes / keyword overview
- Dark gradient header
- CSV export

### What V2 does that V1 didn't
- 3-way tech categorization with stacked sub-totals everywhere
- Project deduplication: each "project" is the unique title+category, with all individual entries accessible via hover
- Confidence pills per project (binary + tech)
- Hash-based deep-linking for sharing exact views
- Sector labels that wrap (no more truncation)
- Member-level tooltip with year-by-year, donor-by-donor breakdown

---

## File 2: `country_comparison.html` → `country_comparison_v2.html`

### What V1 had

V1 was a multi-country comparison sticky-toolbar dashboard, with these controls along the top: All ODA / Tech Only · All donors / EU & Members · **Wide / Strict classifier** · Commitment / Disbursement · All / Pacific / Africa region · year range slider · Total / Tech % / Projects rank metric.

Below the toolbar, a single-column stack of cards:
1. **Rankings** — horizontal bar chart, click row → highlight country across all charts
2. **ODA Trends Over Time** — multi-line chart, click legend to toggle countries
3. **Top Donors by Country** — small per-country donor cards, sub-tab All ODA / Tech ODA
4. **Tech ODA Analysis** — Tech Share % bars + Tech Subtopics stacked bars (~6 named subtopics)
5. **Summary Table** — sortable: Rank, Country, Region, Total ODA, Tech ODA, Tech %, Projects, Tech Projects + Export CSV
6. **Largest Tech Projects** — country-select dropdown + project cards

The **"Wide" vs "Strict" classifier** swap was the killer feature — V1 carried 4 pre-computed datasets (`DATA_WIDE_ALL`, `DATA_STRICT_ALL`, `DATA_WIDE_EU`, `DATA_STRICT_EU`) and just hot-swapped the active object.

### What V2 has

V2 keeps the same six-card structure but rebuilt around the 3-way LLM categorization. New top toolbar:

- **Tech category filter**: All / Governance / Inclusion / Infrastructure (replaces Wide/Strict + All ODA/Tech Only)
- **Metric**: Pledged / Disbursed / Entries / Distinct projects
- **Region**: All / Europe / Africa / Asia / Central Asia / Pacific (5 regions, not just Pacific/Africa)
- **Year range**: dual slider 1990–2024

Cards:
1. **Country rankings** — horizontal bars colored by gov/inc/inf split, ranked by selected metric. Hover for full country stats.
2. **Trends over time** — top-12 country line chart, colored by region, click legend to toggle. Y-axis adapts to selected metric (USD / count).
3. **Top 5 donors per country** — top 9 countries by pledged, each with a mini-card of 5 donors and their gov/inc/inf split bars.
4. **Tech category share** — two side-by-side rankings: most governance-heavy and most inclusion-heavy countries, each as % bar charts.
5. **Summary table** — sortable: #, Country, Region, Distinct projects, Entries, Pledged, Disbursed, Gov %, Inc %, Inf %. Export CSV.
6. **Largest projects (top 60)** — across all selected countries, sorted by pledged amount, color-coded by category, with country, donor, year range, pledged + disbursed.

### Biggest differences (cross-country)

| Aspect | V1 → V2 |
|---|---|
| **Country set** | All DAC recipients in V1's data (~13–20 in scope, mostly Pacific + Africa) | **32 priority countries** across all 5 regions |
| **Tech classification** | Wide/Strict toggle (4 pre-computed datasets) | **Single LLM-based dataset**, no toggle — but split into 3 explicit categories |
| **Categories** | ~6 keyword "subtopics" (Telecom & Connectivity, Fintech & Digital Finance, Comms & Media, Cybersecurity & Digital Governance, ICT Infrastructure, Digital General) | **3 explicit categories**: Digital Governance, Digital Inclusion, Hard Infrastructure |
| **EU funder filter** | All donors / EU & Members toggle | **Removed** — could be added back as a 4th pre-computed dataset if needed |
| **Metric options** | Commitment / Disbursement | **Pledged / Disbursed / Entries / Distinct projects** (4 options instead of 2) |
| **Region filter** | All / Pacific / Africa | **All / Europe / Africa / Asia / Central Asia / Pacific** |
| **Tech subtopics chart** | Stacked horizontal bars by 6 subtopics | Replaced with **two ranked % bar charts**: most-governance-heavy and most-inclusion-heavy countries |
| **Donor breakdown per country** | All ODA / Tech ODA sub-tab | Single view, but each donor row is a stacked gov/inc/inf bar so you see the split inline |
| **Largest projects panel** | Country-by-country (one country at a time via dropdown) | **Cross-country top 60** — see the biggest digital projects globally, filterable by category/region/year |
| **Trend chart** | Total ODA + Tech ODA | Single line chart per country that adapts to the selected metric (pledged / disbursed / entries / distinct) |
| **Compare highlight** | Click rank row → highlight everywhere | Hover rank row → tooltip with full breakdown (no global highlight yet) |
| **CSV export** | Summary table | Same |
| **SVG download per chart** | Yes | **Removed** for now (could be added back) |
| **File size** | 915 KB | 5.8 MB (the new dataset embeds full project members for the largest-projects panel and the trend chart's per-year per-category aggregates) |

### What V2 still does that V1 did
- Sticky top toolbar with all controls
- 6-card vertical layout
- Country rankings with horizontal bars
- Multi-country trend chart with toggleable legend
- Top donors per country
- Sortable summary table with CSV export
- Largest projects card
- Year range slider
- Tooltip on hover

### What V2 does that V1 didn't
- Region split into 5 (not just Pacific/Africa)
- 4 metric options (was 2)
- Cross-country largest-projects view (was country-at-a-time)
- 3-way category breakdown everywhere (was 6 keyword buckets)
- Country tooltip in rankings showing all category counts
- Distinct vs Entries split (separates the "we have N project records" question from "we have M unique interventions")

---

## What V2 doesn't do that you might want

1. **EU vs all donors filter** — easy add (one boolean toggle that filters `members[]` by donor name list)
2. **Wide/Strict classifier comparison** — would need a parallel "wide" extract from CRS sector codes; the LLM classification is a single source of truth for now
3. **Click-to-highlight in rankings** — wires across cards in V1, removed in V2 for clarity
4. **Compare mode (2-country side-by-side)** in `all_country_profiles_v2` — could be added as a third tab
5. **SVG export per chart** — V1 had `downloadSVG()` for the rankings, trends, tech share, subtopic charts; not yet in V2
6. **Treemap modal for thematic markers** — Rio markers (Gender, Climate, Conflict, etc.) aren't in the digital extract; can be re-added if those columns get pulled from CRS
7. **Per-record sortable project table** — V1 had filterable table with donor/sector/location/search filters and 10/25/50/all pagination. V2 uses cards instead; a tabular view could be added.
8. **More panel** (financial instruments donut, channels chart) — those columns weren't kept in the digital extract; trivially restorable if useful

## Files in this directory

```
all_country_profiles.html        ← V1 (March 2026), all CRS, 157 countries, 66 MB
all_country_profiles_old.html    ← older draft
country_comparison.html          ← V1 (March 2026), Pacific + Africa focus, 915 KB
all_country_profiles_v2.html     ← V2 (April 2026), 32 priority countries, digital ODA, 5.8 MB
country_comparison_v2.html       ← V2 (April 2026), cross-country comparison, 5.8 MB
index.html                       ← integrated dashboard (oda_viz_country_v3, single country deep dive)
V2_DIFF.md                       ← this file
```

## Build pipeline

Both V2 files are generated from a single Python pass over `5-taiwan/priority_1990_2024_final_reclassified.csv`:
1. Filter to `is_digital == 'yes'` (14,759 rows)
2. Drop exact-row duplicates on `(year, donor, recipient, title, short_description, tech_category, usd_commitment, usd_disbursement)` → 9,570 rows
3. Per country, build the JSON payload: aggregates, donors, sectors, year trend (with money), themes, and projects with `members[]`
4. Inline the JSON into the HTML template

Themes are extracted via the same 16-keyword taxonomy described in `5-taiwan/THEMES_TODO.md` (improvements pending).
