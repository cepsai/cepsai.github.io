# NeurIPS dataset — cheatsheet

Path: `/Users/robertpraas/Documents/GitHub/cepsai.github.io/huggingface/neurips/`

## What's here

### Paper-level CSVs (one row per paper)
- `neurips_2024_papers_with_institutions_v4.csv` — 4,510 papers
- `neurips_2025_papers_with_institutions_v4.csv` — 5,825 papers

Columns: `id, forum, number, title, abstract, authors, authorids, venue, venueid, primary_area, pdf, cdate_iso, pdate_iso, mdate_iso, openreview_url, institutions`

- `institutions` is a `; `-separated list, aligned 1:1 with `authors`/`authorids` (one entry per author, so same institution can appear multiple times on one paper).
- `venue` is the definitive paper-type field — values below.

### Venue types

**2024:**
- `NeurIPS 2024 poster` (3,648), `NeurIPS 2024 spotlight` (326), `NeurIPS 2024 oral` (61)
- `NeurIPS 2024 Track Datasets and Benchmarks Poster` (392), `… Spotlight` (56), `… Oral` (11)
- `NeurIPS 2024 Competition Track` (16)

**2025:**
- `NeurIPS 2025 poster` (4,524), `NeurIPS 2025 spotlight` (687), `NeurIPS 2025 oral` (77)
- `NeurIPS 2025 Datasets and Benchmarks Track poster` (434), `… spotlight` (56), `… oral` (7)
- `NeurIPS 2025 Position Paper Track` (31), `NeurIPS 2025 Position Paper Track Oral` (9)

### Institution → country mapping

Per-year JSON (list of dicts, one per institution):
- `institution_venues_2024_v14.json` (1,732 institutions)
- `institution_venues_v14.json` (1,929 institutions — 2025)

Fields per institution: `name, name2, country` (ISO-2, e.g. `US`, `CN`, `GB`, `NL`), `parent` (region: `China`, `United States`, `Europe`, `Rest of the world`), `parent2` (sub-region), `urban_zone`, `urban_id`, `color`, `venues` (dict of venue-name → paper count).

**Name normalization layers** (apply in order for ~99% coverage):
1. Look up raw name directly in the per-year JSON (`name` or `name2`).
2. Fall back to `sortnames_mapping.json` (1,930 entries, maps variant → canonical short name like "UT Austin", "UC Berkeley", "JAIST"). **This layer is essential** — raw mapping alone is ~63%, with sortnames it jumps to ~99%.
3. Fall back to `institution_merged_mapping_update.json` (canonical → list of variant strings).

Reminder: pandas NaN vs the ISO code `"NA"` (Namibia) — guard when reading country codes.

### Other files
- `country_to_continent.json` — ISO-2 → continent mapping.
- `lala_*.csv`, `old.csv` — older / working CSVs, superseded by `*_v4.csv`.
- `data_selection.ipynb`, `test.ipynb` — exploration notebooks.
- `proportion_viz_*.json`, `viz_*.html` — D3/vega visualizations.
- `neurips_china_share.md` — prior analysis: institution-level shares (China/US/Europe/RoW) per venue subset.
- `neurips_spotlight_oral_2025.csv` — filtered subset for 2025 oral+spotlight.

## Recipe: paper-level country presence

```python
import json, pandas as pd

def load_country_map(path):
    m = {}
    for it in json.load(open(path)):
        if it.get('country'):
            if it.get('name'):  m[it['name']]  = it['country']
            if it.get('name2'): m[it['name2']] = it['country']
    return m

sortnames = json.load(open('sortnames_mapping.json'))
merged = json.load(open('institution_merged_mapping_update.json'))
variant_to_canonical = {v: c for c, vs in merged.items() for v in vs}
variant_to_canonical.update({c: c for c in merged})

def resolve(name, cmap):
    if name in cmap: return cmap[name]
    if sortnames.get(name) in cmap: return cmap[sortnames[name]]
    if variant_to_canonical.get(name) in cmap: return cmap[variant_to_canonical[name]]
    return None

def paper_countries(inst_str, cmap):
    if pd.isna(inst_str): return set()
    return {c for i in inst_str.split(';') if (c := resolve(i.strip(), cmap))}
```

Use `load_country_map('institution_venues_2024_v14.json')` for 2024 papers,
`load_country_map('institution_venues_v14.json')` for 2025.

## Prior findings (see `neurips_china_share.md`)

- Institution-level: China overtook the US in 2025 (36.4% vs 32.1%, flipped from 30.0% vs 38.3% in 2024).
- China led posters in 2025 (37.6% vs 30.7%); US still led Oral+Spotlight but gap narrowed to <3pp.

## Known caveats

- Coverage: ~98.3% of institution mentions resolved to a country in 2024, ~99.4% in 2025. Remaining unresolved are dominated by a few institutions (Max Planck Institute for Software Systems, Bosch, South China University, a leading-comma "Johannes Kepler Universität Linz", etc.) — add these to the mapping manually if needed.
- The `institutions` column has duplicates (one per author). Deduplicate per-paper before counting institution-level things; for paper-level country-presence it doesn't matter.
- 4 papers in 2024 have null `institutions` — drop or skip.
