# Product Hunt — morning digest

Daily auto-updating tracker of new Product Hunt launches, published at
[cepsai.github.io/producthunt-tracker/docs/](https://cepsai.github.io/producthunt-tracker/docs/).

## What it does

Every morning at 08:00 UTC (09:00 / 10:00 Brussels), a GitHub Action pulls the
public Product Hunt Atom feed, normalizes each launch, merges new ones into a
rolling history, and rebuilds `docs/data.json`. The dashboard at `docs/index.html`
groups launches by Brussels-local date (today, yesterday, the past 7 days),
supports text search, and remembers which products you've already tried via
`localStorage`.

## Layout

```
producthunt-tracker/
├── scripts/fetch.py        # pulls feed, merges history, writes dashboard JSON
├── data/history.json       # rolling history of every product seen
├── docs/index.html         # dashboard (GitHub Pages)
└── docs/data.json          # rendered payload the dashboard reads
```

The Atom feed is unauthenticated and gives:
**title · tagline · maker · product URL · publish timestamp**.

That is enough to decide what to try. If you later create a Product Hunt
developer token (https://api.producthunt.com/v2/oauth/applications), add it as
a repo secret named `PH_API_TOKEN` and `fetch.py` will enrich each launch with
vote count, comment count, thumbnail, and topic tags via GraphQL — no code
changes needed.

## Run locally

```bash
python3 producthunt-tracker/scripts/fetch.py
open producthunt-tracker/docs/index.html
```

The script is idempotent. Re-running on the same day only updates `last_seen`
on existing entries and inserts truly new ones.

## Tweaking what you see

- Bucket timezone — `DISPLAY_TZ_OFFSET_HOURS` at the top of `fetch.py`.
- Refresh time — the cron in `.github/workflows/producthunt-daily.yml`.
- "Tried" toggle persistence is per-browser (`localStorage` key `ph-tried-v1`).
