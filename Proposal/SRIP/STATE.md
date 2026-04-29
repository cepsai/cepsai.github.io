# SRIP — Belgium dashboard session

## 1. Accomplished
- Traced the SRIP data flow: raw Crunchbase dumps in `cb_sep_25/` → `cb_srip.py` aggregates → `1-load/geo/{country,urban}/aiw/crunchbase/{year}.csv` → copied into `Proposal/SRIP/{country,urban}/{metric}/{year}.csv`. (OpenAlex/RegPat upstream not traced.)
- Built a Belgium-focused summary script and a single-page BE dashboard with all 3 charts (map, line, treemap), EU-27 only, BE highlighted in royal blue.

## 2. Files created
- `Proposal/SRIP/belgium_numbers.py` — reads the per-year metric CSVs, filters to AI, writes `be_numbers.json` (BE/EU/World per-year totals, BE rank in EU, BE share, top BE cities). Headline numbers: BE crunchbase $1.40B (3.5% of EU); BE OpenAlex 35,936 (3.5%); BE RegPat 985 (2.5%); top BE cities: Bruxelles, Gent, Antwerpen, Liege, Charleroi.
- `Proposal/SRIP/be_numbers.json` — generated output, consumed by the dashboard.
- `Proposal/SRIP/dashboard_be.html` — single page: 4 summary cards + EU bubble map + EU year-on-year line chart (BE thick blue, others gray, EU-27 avg dashed) + EU treemap. Shared metric switcher + year-range slider. Inline JS passes `node --check`.

## 3. Outstanding TODOs
- **Browser verification not done** — sandbox blocked `python -m http.server`, `/browse` doesn't follow `file://`. User must run a local server to view.
- **Pipeline placement decision pending** — script lives in `Proposal/SRIP/` (consumes already-shipped CSVs), not in `cb_sep_25/` like `cb_srip.py`. Move + write to Dropbox `1-load/geo/be/...` if pipeline parity matters.
- **Shape decision pending** — combined dashboard vs three iframe-friendly files (`line_be.html`/`map_be.html`/`treemap_be.html`) matching the existing `line.html`/`map.html`/`treemap.html` pattern. Unknown which is iframed where on cepsai.github.io.
- Optional polish: city-level BE view (Bruxelles/Gent/Antwerpen/Liège/Charleroi bubbles); UK as comparison line; make "top BE city" card slider-scoped (currently all-time from `be_numbers.json`).

## 4. Decisions / gotchas
- ISO code parsed from trailing `(XX)` in `geo` column; matches the line/map convention.
- AI filter applied: only rows where `domain == "Artificial Intelligence"` (matches existing pages).
- EU set is the 27 current member states; UK excluded (was its own macro-region in `line.html`).
- EU country positions on the map are hardcoded capital lat/lon (28 entries) — `crosswalk.json` only has city-level coords; world-atlas centroids would be the more principled alternative.
- `be_numbers.json` keys for per-year dicts are JSON strings (e.g. `"2024"`), not ints — JS handles via string keys.
- Sandbox blocks binding HTTP servers; tests had to be static (`node --check` + JSON shape check).

## 5. Resume command
```
cd /Users/robertpraas/Documents/GitHub/cepsai.github.io/Proposal/SRIP \
  && python3 belgium_numbers.py \
  && python3 -m http.server 8000
# then open http://localhost:8000/dashboard_be.html
```
