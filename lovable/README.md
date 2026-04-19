# Atlas of European AI Makers — CEPS-DST research preview

A Europe-first research dataset + static dashboard mapping companies built on [Lovable](https://lovable.dev) to the **occupations, tasks, and economic work** they augment or automate. Independent research preview by CEPS-DST (data team, Centre for European Policy Studies, Brussels).

Four navigational tabs on one site:

1. **Advent** — ten headline visualisations blending real founder data with synthetic platform-level calibration.
2. **Apps Atlas** — ~400 Lovable-deployed apps discovered from CT logs + madewithlovable sitemap, with ESCO-occupation classification + published GenAI-exposure scores.
3. **Founders** — 82 source-verified European Lovable founders with traction, geography, problem taxonomy.
4. **Sovereign AI Index** (stealth preview) — cross-platform benchmark of EU AI-native entrepreneurship + supply-chain visualisations.

## What's here

```
data/
  taxonomy.json                 — founder-story problem categories + traction tiers
  founders.balanced.json        — 15 European founders, mid-depth profiles
  founders.breadth.json         — 67 founders, shallow (one-line stories)
  discovered_apps.json          — ~400 Lovable-deployed apps (URL, liveness, title, meta, sources)
  apps_classified.json          — subset classified to ESCO occupations via Ollama + ESCO API
scripts/
  validate.py                   — schema validator for founder files
  discover.py                   — CT-log + madewithlovable sitemap enumeration pipeline
  classify.py                   — Ollama + ESCO retrieval-augmented classifier
index.html + dashboard.{js,css} — single-page site, four nav tabs
research/
  sources.md                    — reproducibility log of every source consulted
  raw/                          — scratch notes, transcripts, raw HTML
```

## Running the dashboard

No build step. Serve the directory with anything that serves static files:

```bash
python -m http.server 8000
open http://localhost:8000/                       # all four sections
open http://localhost:8000/?view=breadth          # founder view: breadth (shallow, bigger n)
open http://localhost:8000/#section-atlas         # jump to Apps Atlas
```

## Regenerating the Apps Atlas dataset

```bash
# Stage 1 — discover Lovable-deployed apps from public sources (~50s)
python scripts/discover.py           # → data/discovered_apps.json

# Stage 2 — classify each live app to ESCO occupation via Ollama + ESCO API
ollama pull nemotron-3-nano:4b       # local model for JSON-schema inference
python scripts/classify.py --limit 60 --workers 2
                                      # → data/apps_classified.json
```

Stage 2 requires [Ollama](https://ollama.com) running locally. `nemotron-3-nano:4b` is the default because it reliably produces valid JSON via `format:"json"` on an Apple-Silicon Mac — other models may require tuning.

## Data model

Every record in both datasets follows the same schema. Breadth records only require the minimum fields + `narrative_short` + one source; balanced records add `narrative_long` (150–400 words) and multiple sources. See `data/taxonomy.json` for the category and tier enums.

### Required fields

`id`, `name`, `is_european`, `founders[0].name`, `problem_category`, `traction_tier`, `built_with_lovable_confidence`, `narrative_short`, `sources[0]`, `last_verified`, `status`, `dataset`.

### `built_with_lovable_confidence` — coding rubric

- **confirmed** — founder or Lovable has publicly stated the product is built on Lovable (blog post, interview, social).
- **likely** — strong indicators (Lovable URL pattern in history, founder's prior posts, Lovable featured it) but not explicitly stated.
- **partial** — Lovable was used for part of the build (prototype, landing page) but the live product is on another stack.

Records marked `partial` are kept in the dataset but excluded from headline stats via a dashboard filter.

### `traction_metric.source_quality` — coding rubric

- **disclosed_by_founder** — founder stated the number themselves, on the record, with a date.
- **press_reported** — reputable publication reported the number, ideally with a direct quote.
- **self_reported_social** — founder said it on X/LinkedIn/Discord; rendered with a "claimed" label.
- **estimated** — our inference from proxies (team size, funding, traffic); italicized with tooltip.
- **unknown** — no figure available; record sorts to bottom and is excluded from revenue aggregations.

## Adding or updating a record

1. Add/edit the record in the appropriate JSON file (follow the schema in the plan file).
2. Run `python scripts/validate.py` — fail fast on missing fields / bad enums / bad ISO-2.
3. Log the source you used in `research/sources.md` with today's date.
4. Bump `last_verified` on the record.

Normalize monetary figures to EUR. When two sources disagree on revenue, store the **lower** number and note the discrepancy in `notes`.

## Research passes

The current dataset was seeded via four passes (see the plan file for detail):

1. **Official surfaces** — `madewithlovable.com`, `lovable.dev/blog`, `lovable.dev/videos/Community`, `lovable.dev/solutions`.
2. **Press / analyst** — TechCrunch, Euronews, EU-Startups, Sifted, Growth Unhinged, Contrary Research, Get Latka.
3. **Founder-generated** — X, LinkedIn, YouTube founder interviews, Lovable Discord, Reddit.
4. **Verification** — dedup, URL spot-checks, source-excerpt requirement for T3+ claims.

To refresh the dataset, repeat each pass and bump `last_verified` on every record you confirm is still accurate.

## Known limitations

- **Survivorship bias.** Official showcases only surface winners. The breadth dataset targets ≥10–15% non-winner records (dead / pivoted / T0–T1) from founder-community sources to counterbalance.
- **Revenue-claim inflation.** Founders round up and conflate MRR vs ARR. Every T3+ claim carries a dated `source_excerpt`.
- **"Built with Lovable" ambiguity.** `built_with_lovable_confidence` separates native Lovable businesses from Lovable-adjacent ones.

## License / use

Research artifact for internal analysis. Source excerpts are quoted under fair use. Check before redistributing.
