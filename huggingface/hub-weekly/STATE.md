# hub-weekly — STATE

Weekly "New Models & Datasets" treemap from Hugging Face Hub snapshots.

## What this is
A Monday-callable pipeline + dashboard. Pulls the freshest HF Hub metadata snapshot,
finds newly released models & datasets, and renders a NeurIPS-style treemap where tile
area = release velocity (downloads/day or likes/day).

## Files
- `build_hub_weekly_treemap.py` — the build script. Resolves latest snapshot, reads remote
  parquet via duckdb httpfs (no full download), writes `hub_weekly_data.json`.
- `hub_weekly_treemap.html` — self-contained d3plus treemap, 4 client-side toggles.
- `hub_weekly_data.json` — generated output (~190 KB). Regenerated each run.

## Run it (every Monday)
```
python3 ~/Documents/GitHub/cepsai.github.io/huggingface/hub-weekly/build_hub_weekly_treemap.py
```
Takes ~30s (streams two remote parquets). Then open `hub_weekly_treemap.html`.
Local viewing needs HTTP (it fetches the JSON), e.g.:
`python3 -m http.server 8778 --directory <this folder>` then open
`http://localhost:8778/hub_weekly_treemap.html`. On the live CEPS site (github.io) it just works.

## Data source
`hfmlsoc/hub_weekly_snapshots` (HF ML & Society Team), derived from `cfahlgren1/hub-stats`.
Layout: `models/<YYYY-MM-DD>/models.parquet`, `datasets/<date>/datasets.parquet`.
Updated ~weekly; the script auto-picks the latest date dir.

## Key decisions / gotchas
- Sizing = per-day velocity: `downloadsAllTime / age_days`, `age_days` fractional with a
  1-day floor (integer-day truncation inflates hours-old items — verified).
- Build exports the **30-day** window; the HTML derives the 7-day view client-side. Top-N
  cap = union of top-250 by {7d,30d} × {dl/day, likes/day} per type → ~600-700 rows/type.
- Datasets have no `pipeline_tag` → task derived from `task_categories:*` tag, fallback
  `modality:*`, else "other". "other" bucket ≈ 21-30% (healthy, not dominant).
- Toggles: Item type (Models/Datasets), Metric (dl/day, likes/day), Window (7d/30d),
  Grouping (task/author). Defaults: Models, dl/day, 7 days, By task.
- HTML loads JSON via d3.json → must be served over HTTP locally (file:// is CORS-blocked).

## Outstanding / optional
- Not yet automated. To run automatically every Monday, add a launchd weekly agent
  mirroring the Crunchbase plist pattern (~/Library/LaunchAgents). Not set up — opt-in.
- Optional: archive each week's JSON (`archive/hub_weekly_<date>.json`) for trend tracking.
- Not committed/pushed to the cepsai.github.io repo yet.

## Resume
This session: built script + HTML via two parallel subagents, QA'd all toggles in browse
(490→327 tiles on 7d filter, datasets 266, styled tooltip clean, 0 console errors).
