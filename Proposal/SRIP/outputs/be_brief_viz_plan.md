# Bel-AI policy brief — visualization plan

Source: `~/Downloads/industrial_ecosystem_explainer_skeleton.docx`. Builds on
the SRIP per-year CSVs at `Proposal/SRIP/{country,urban}/{crunchbase,openalex,regpat}/{year}.csv`,
filtered to the AI domain, plus `crosswalk.json` (city metadata: lat/lon,
population, region/state).

## Tier definitions
- **T1 — build now**, fully covered by existing SRIP data.
- **T2 — build with light prep** (per-capita join from `crosswalk.json` populations, comparator picker, simple aggregations).
- **T3 — needs new data not in this folder** (GenAI flag, GICS sectors, institutions, NUTS-2, Eurostat/Statbel). Defer until data lands.

Existing patterns to reuse:
- Line chart: `Proposal/SRIP/line.html`, `eu-gigafactories-paper/fig1.html`, `fig7.html`.
- Bubble map (world / Europe): `Proposal/SRIP/map.html`, `dashboard_be.html`.
- Bar chart (vertical/horizontal): `eu-gigafactories-paper/fig5a.html`, `fig5b.html`, `fig6.html`.
- Treemap (D3 native): `Proposal/SRIP/dashboard_be.html`. Treemap (d3plus): `Proposal/SRIP/treemap.html`.
- Choropleth/topojson: `country_profiles.html`.
- Multi-panel dashboard layout: `Proposal/SRIP/dashboard_be.html`, `Tools/ai_funding_dashboard.html`.

## §2 Scientific Publications (OpenAlex)

| # | Visual | Tier | File | Notes |
|---|---|---|---|---|
| 2a | Time-series: BE vs NL/DE/FR/EU/EU-avg | T1 | `pub_line_be_vs_peers.html` | Reuse SRIP `line.html`; replace macro-region grouping with named comparators |
| 2b | Belgium city heatmap (publications by city) | T1 | `pub_map_be_cities.html` | 5 BE cities from crosswalk; bubble-on-Europe map zoomed to BE |
| 2c | European regional bubble/choropleth (publications) | T1 | `pub_map_eu_countries.html` | Country-level Europe map; reuse `dashboard_be.html` map block |
| 2d | Treemap of institutions (BE) | **T3** | — | Need institution-level OpenAlex extract, not in SRIP |
| 2e | Co-authorship network (nice-to-have) | **T3** | — | Need co-author edges, not in SRIP |

## §3 Patents (REGPAT, 2000–2024)

| # | Visual | Tier | File | Notes |
|---|---|---|---|---|
| 3a | Time-series: BE vs comparators | T1 | `pat_line_be_vs_peers.html` | Mirror 2a with regpat |
| 3b | Bar chart: AI patents per capita across countries | T2 | `pat_bar_per_capita.html` | Need population join — country-level pop missing in `crosswalk.json` (city-only); add small `country_pop.json` lookup |
| 3c | Time-series: AI patents per capita over time | T2 | `pat_line_per_capita.html` | Same pop join; line variant of 3b |
| 3d | Belgium regional heatmap (patents by city) | T1 | `pat_map_be_cities.html` | 5 BE cities |
| 3e | European map (patents by country) | T1 | `pat_map_eu_countries.html` | Same shell as 2c |
| 3f | Treemap of organisations / urban areas | **T3** | — | Org-level data not in SRIP; urban-area variant possible (T1) → split into 3f-i `pat_tree_be_cities.html` (T1) and 3f-ii orgs (T3) |

## §4 Startup Investments (Crunchbase, 2014–2026)

| # | Visual | Tier | File | Notes |
|---|---|---|---|---|
| 4a | Time-series investment volumes (stacked GenAI vs other AI) | **T3** | — | Current data is single AI domain; need GenAI sub-flag rebuild from raw Crunchbase. T1 fallback: stacked by region. |
| 4b | Map of Belgium with city startups, zoomable | T1 | `inv_map_be_zoom.html` | Bubble per BE city; zoom controls; reuse `map.html` zoom pattern |
| 4c | GICS sector treemaps | **T3** | — | Need re-aggregation by GICS — current SRIP CSVs filtered to single domain |
| 4d | Bar chart: BE vs comparators (per-capita investment) | T2 | `inv_bar_per_capita.html` | Pop join |
| 4e | Heatmap/treemap of AI startup concentration by sector | **T3** | — | Sector dim missing |

## §5 Firm-Level Adoption (Eurostat / Statbel)

All of §5 is **T3** — no Eurostat/Statbel data in SRIP. Plan stub files now,
fill once `isoc_eb_ai` and Statbel microdata are extracted:

| # | Visual | Tier | File | Notes |
|---|---|---|---|---|
| 5a | Bar: BE vs EU vs NL/DE/FR (firms using AI) | T3 | `adopt_bar_share.html` (stub) | |
| 5b | Time-series: 2021–2025 trend | T3 | `adopt_line_trend.html` (stub) | |
| 5c | Horizontal bar: 8 AI tech types | T3 | `adopt_hbar_tech.html` (stub) | |
| 5d | Firm-size comparison | T3 | `adopt_bar_size.html` (stub) | |
| 5e | Sectoral heatmap + BE regional map | T3 | `adopt_heatmap_sectors.html` (stub) | |

## §6 Benchmark synthesis

| # | Visual | Tier | File | Notes |
|---|---|---|---|---|
| 6a | Radar/spider — BE vs comparators across 4 pillars | T2 | `bench_radar.html` | Need normalised per-capita scores per pillar; 4th pillar (adoption) blank until §5 data lands |
| 6b | Compact comparison table | T1 | `bench_table.html` | Reuse summary numbers from `belgium_numbers.py` |

## Build order (proposal)

**Phase 1 — pure T1 (existing data only)**: 2a, 2b, 2c, 3a, 3d, 3e, 3f-i, 4b, 6b. ~9 files, all reuse existing line/map/treemap shells. ETA fast.

**Phase 2 — T2 (small data prep)**: write `country_pop.json` from a static UN/World Bank table (one-time), then 3b, 3c, 4d, 6a. ~4 files.

**Phase 3 — T3 stubs**: scaffold §5 files with placeholder text and the same chrome (header, controls, source line) so they can be filled in when Eurostat/Statbel data lands. ~5 stubs + 3 deferred treemaps.

**Phase 4 — T3 with new data**: 2d (institutions), 4a (GenAI split), 4c/3f-ii/4e (GICS sector) — needs new pipeline work in `cb_sep_25/` to re-aggregate raw Crunchbase by GenAI tag and GICS, plus institution extract from OpenAlex.

## Folder + naming

Place all under `Proposal/SRIP/be_brief/` to avoid mixing with the existing
`line.html`/`map.html`/`treemap.html` (which are the SRIP-page graphs). Each
file is standalone (iframe-friendly) like the gigafactories `fig*.html`. The
combined `dashboard_be.html` already in SRIP/ stays as the at-a-glance overview.

## Open questions for you
1. Comparator set for time-series (2a/3a): NL + DE + FR + EU avg + BE? Add LU? UK?
2. For per-capita charts, which country list? (EU-27 + UK? + US/CN benchmarks?)
3. Iframe target — are these going into a Proposal page, or standalone like the existing SRIP graphs?
4. Approve T3 stubs now (placeholder pages) or wait until data is in hand?
