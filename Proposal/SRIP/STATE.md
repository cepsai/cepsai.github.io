# SRIP — Belgium dashboard session

## 1. Accomplished
- Traced the SRIP data flow: raw Crunchbase dumps in `cb_sep_25/` → `cb_srip.py` → `1-load/geo/{country,urban}/aiw/crunchbase/{year}.csv` → copied into `Proposal/SRIP/{country,urban}/{metric}/{year}.csv`. (OpenAlex/RegPat upstream not traced.)
- Built a BE summary script + a 3-graph BE-focused dashboard.
- Scanned the Bel-AI policy-brief skeleton (~/Downloads/industrial_ecosystem_explainer_skeleton.docx) and produced a viz plan.
- Built the combined Bel-AI dashboard covering §2–§6 with BE vs EU founding six (BE/NL/LU/DE/FR/IT), T1/T2 charts populated and T3 panels stubbed with "awaiting data" placeholders.

## 2. Files created
- `Proposal/SRIP/belgium_numbers.py` — reads the per-year metric CSVs, filters to AI, writes `be_numbers.json`. Headline: BE crunchbase $1.40B (3.5% of EU); OpenAlex 35,936 (3.5%); RegPat 985 (2.5%); top BE cities: Bruxelles, Gent, Antwerpen, Liege, Charleroi.
- `Proposal/SRIP/be_numbers.json` — generated, consumed by `dashboard_be.html`.
- `Proposal/SRIP/dashboard_be.html` — single-page summary: 4 cards + EU map + line + treemap, BE highlighted.
- `Proposal/SRIP/outputs/be_brief_viz_plan.md` — viz plan (T1/T2/T3 tiers, ~22 visuals across §2–§6).
- `Proposal/SRIP/dashboard_brief.html` — combined Bel-AI brief dashboard. §2 (3 charts + 2 placeholders), §3 (5 charts + 1 placeholder + 1 BE-city treemap as org-treemap stand-in), §4 (3 charts + 2 placeholders), §5 (5 placeholders), §6 (radar + table). Shared year-range slider; per-section metric is fixed. Inline JS passes `node --check`. EU-6 populations + capitals hardcoded; per-capita uses /M for pubs+patents and /capita for investments USD.

## 3. Outstanding TODOs
- **Browser verification not done** — sandbox blocks `python -m http.server`, `/browse` doesn't follow `file://`. User must run a local server to view.
- **T3 data sources still needed**: GenAI sub-flag (rebuild `cb_srip.py` keeping the genAI tag); GICS sector aggregation (re-run cb_srip without collapsing to single AI domain); OpenAlex institution-level extract; OpenAlex/REGPAT co-author/co-patent edges; Eurostat `isoc_eb_ai` + Statbel microdata for §5 adoption pillar; NUTS-2 BE regional split.
- Pipeline placement decision still open — `belgium_numbers.py` lives in SRIP/, not in `cb_sep_25/`.
- Optional polish: extend EU-6 to include UK or US/CN benchmarks; add per-capita to bench table radar normalisation note; year-clamp visual feedback per metric (REGPAT only goes to 2024).

## 4. Decisions / gotchas
- Comparator set fixed by user: EU founding six = BE, NL, LU, DE, FR, IT. EU-27 average dashed on absolute time-series.
- Per-capita unit: per million for pubs/patents; per inhabitant USD for investments. Populations hardcoded inline (UN/Eurostat 2024 estimates).
- AI filter applied: only rows where `domain == "Artificial Intelligence"` — same as existing SRIP pages. Means GenAI/sector splits cannot come from current CSVs.
- ISO code parsed from trailing `(XX)` in `geo`; urban id from trailing `(NNN)`.
- EU country positions on bubble maps = hardcoded capital lat/lon (27 entries).
- `dashboard_brief.html` placeholders are intentional (T3 awaiting-data panels), not bugs.
- File:// in browsers blocks `fetch()` — `open dashboard_brief.html` will render frame but charts stay empty until served via HTTP.
- Sandbox blocks `python -m http.server`; user must launch the server themselves (use `! cd ... && python3 -m http.server 8000`).

## 5. Resume command
```
cd /Users/robertpraas/Documents/GitHub/cepsai.github.io/Proposal/SRIP \
  && python3 belgium_numbers.py \
  && python3 -m http.server 8000
# then open http://localhost:8000/dashboard_brief.html  (combined Bel-AI brief)
#                http://localhost:8000/dashboard_be.html (BE summary)
```
