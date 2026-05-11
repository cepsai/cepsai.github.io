# ICLR 2026 Institution Leaderboard — Methodology

## Overview

This document describes how the ICLR 2026 institution leaderboard (`viz_iclr.html`) was built — from raw OpenReview data to the interactive treemap. The pipeline has two stages: **data wrangling** (Python/Jupyter) and **visualization** (client-side JavaScript with D3 and d3plus).

---

## Stage 1: Data Collection

### Source
All data comes from the [OpenReview API v2](https://api2.openreview.net). ICLR 2026 uses the venue group `ICLR.cc/2026/Conference`.

### What was fetched
Two datasets were collected using the OpenReview Python client:

**Papers** (`iclr_2026_papers.csv`, 11,398 rows):
Each submission to ICLR 2026, including title, abstract, authors, author IDs, venue decision, and submission metadata.

| Column | Description |
|--------|-------------|
| `id` / `forum` | OpenReview submission ID |
| `venue` | Decision label (e.g. `ICLR 2026 Poster`, `ICLR 2026 Oral`, `ICLR 2026 Conference Withdrawn Submission`) |
| `authors` | Semicolon-separated display names |
| `authorids` | Semicolon-separated OpenReview profile IDs (`~FirstName_LastName1`) |
| `title`, `abstract`, `primary_area` | Paper content metadata |

**Affiliations** (`iclr_2026_affiliations.csv`):
Each author profile's institutional history, one row per affiliation entry. Fields include `authorid`, `institution`, `country`, `start`, `end`. The `end` field is `NaN` for current affiliations.

### Accepted venues
The leaderboard counts only accepted papers:
- `ICLR 2026 Oral` (223 papers)
- `ICLR 2026 Poster` (5,117 papers)
- `ICLR 2026 ConditionalOral` (1 paper)
- `ICLR 2026 ConditionalPoster` (14 papers)

Withdrawn (5,136) and desk-rejected (907) submissions are excluded.

---

## Stage 2: Institution Mapping

### The problem
OpenReview author profiles contain free-text affiliation strings entered by authors themselves. The same institution appears in hundreds of variants:

```
"MIT"
"Massachusetts Institute of Technology"
"MIT CSAIL"
"Massachusetts Institute of Technology (MIT)"
"Computer Science, MIT"
```

All of these must resolve to a single canonical name before counting papers per institution.

### Mapping files
Three JSON files define the canonical → variants mapping (format: `{"Canonical Name": ["variant 1", "variant 2", ...]}`):

| File | Contents |
|------|----------|
| `neurips/institution_merged_mapping.json` | 2,903 canonicals from prior NeurIPS work (read-only) |
| `neurips/institution_merged_mapping_update.json` | 2,797 additional NeurIPS canonicals (read-only) |
| `iclr_2026/iclr_institution_mapping.json` | **946 ICLR-specific additions** (new institutions + ICLR-specific variants) |

The combined inverse lookup maps ~50,000 lowercase variant strings to their canonical name.

### Current affiliation resolution
Each author has potentially many affiliation entries (historical and current). To pick the most recent one, `end` dates are sorted descending with `NaN` treated as `9999` (still active):

```python
aff["end_sort"] = pd.to_numeric(aff["end"], errors="coerce").fillna(9999)
current = (
    aff.sort_values("end_sort", ascending=False)
       .drop_duplicates("authorid", keep="first")
       .set_index("authorid")[["institution", "country"]]
)
```

### Lookup with normalization fallback
The `resolve()` function first tries an exact lookup, then applies normalization rules before a second attempt:

```python
def resolve(raw):
    key = str(raw).lower().strip()
    if key in inv:
        return inv[key]           # exact match
    norm = _normalize(raw)        # strip suffixes, dedup halves
    return inv.get(norm.lower().strip(), raw)   # normalized match or raw fallthrough
```

Normalization rules (applied in order):
1. Strip trailing country suffixes: `"Tsinghua University, China"` → `"Tsinghua University"`
2. Strip leading `, ` artifact
3. Strip corporate suffixes: `" Inc."`, `" Ltd."`, `" GmbH"`, etc.
4. Collapse duplicate comma-halves: `"Seoul National University, Seoul National University"` → `"Seoul National University"`

### Building the ICLR-specific mapping
The `resolve_mappings.ipynb` notebook identified unmapped strings in accepted papers using rapidfuzz fuzzy matching (token-sort ratio + WRatio, best-of-two):

- **Tier A (score ≥ 90):** likely variant of existing canonical — reviewed and added
- **Tier B (score 78–89):** near-match — manually verified
- **Tier C (score < 78):** genuinely new organisation — added as new canonical

False positives from fuzzy matching (e.g. "Canva" matching "DataCanvas") were manually overridden. The final ICLR mapping covers 946 canonical entries.

### Coverage result

| Metric | Value |
|--------|-------|
| Accepted paper author slots | 33,708 |
| Resolved to canonical | 33,664 (99.87%) |
| Institutions with count ≥ 3 unmapped | 0 |
| Top-50 institutions with country code | 50/50 |

---

## Stage 3: Building the Output Files

Notebook: `data_selection_v2.ipynb`

### `iclr_2026_papers_with_institutions_v4.csv`
The original papers CSV enriched with an `institutions` column: one resolved canonical per author, semicolon-separated and positionally aligned with `authorids`.

```
id; ...; authors; authorids; venue; ...; institutions
abc123; ...; Alice; Bob; ~Alice1; ~Bob1; ICLR 2026 Poster; ...; MIT; Stanford University
```

### `institution_venues_iclr_2026_v14.json`
Pre-aggregated institution records, one per canonical, sorted by total paper count:

```json
{
  "name":      "MIT",
  "name2":     "MIT",
  "canonical": "Massachusetts Institute of Technology",
  "parent":    "US",
  "country":   "US",
  "venues": {
    "ICLR 2026 Oral":   12,
    "ICLR 2026 Poster": 143
  }
}
```

Key design decisions:
- **`name`**: display name, potentially abbreviated via `sortnames_mapping.json` (e.g. `"Massachusetts Institute of Technology"` → `"MIT"`)
- **`canonical`**: the exact string that appears in the CSV `institutions` column — used by the JS drill-down to look up papers
- **Deduplication**: each institution is counted once per paper, not once per author (so a paper with three MIT authors counts as 1 MIT paper)
- **Country**: taken from the most common non-null country code across the institution's author rows

---

## Stage 4: Visualization (`viz_iclr.html`)

The visualization is a single self-contained HTML file using [D3 v5](https://d3js.org) and [d3plus-hierarchy v1](https://github.com/d3plus/d3plus-hierarchy) for the treemap.

### Layout
Three stacked rows managed by CSS Grid (`grid-template-rows: 17fr 2fr 1fr`):

| Row | Content |
|-----|---------|
| `#container1` | Main treemap (fills ~85% of viewport height) |
| `#container2` | Region legend (China / US / Europe / Rest of World) |
| `#container3` | Source link, country dropdown, venue dropdown, year / org type / top-N controls |

### Treemap hierarchy
Three grouping levels:

```
Region (China / US / Europe / Rest of World)
  └── Country (CN, US, GB, DE, ...)
        └── Institution (Tsinghua University, Stanford, ...)
```

Each tile is sized by paper count for the selected venue filter.

### Region classification
Country ISO codes are mapped to four top-level regions client-side:

```javascript
function getRegion(countryCode) {
  if (["CN","HK","MO"].includes(countryCode)) return "China";
  if (countryCode === "US") return "US";
  if (EUROPE_CODES.has(countryCode))          return "Europe";
  return "Rest of World";
}
```

Colors: China = terracotta, US = blue, Europe = green, Rest of World = purple.

### Venue filtering
Raw venue strings are merged into clean options:

| Dropdown option | Sources |
|-----------------|---------|
| All | All four accepted venue types |
| Oral | `ICLR 2026 Oral` + `ICLR 2026 ConditionalOral` |
| Poster | `ICLR 2026 Poster` + `ICLR 2026 ConditionalPoster` |

The raw conditional venues are hidden from the dropdown.

### Org type filter
Client-side keyword classification, applied before rendering:

| Type | Keywords matched in institution name |
|------|--------------------------------------|
| University | `university`, `universit`, `institute`, `college`, `school`, `academy`, `polytechnic`, ... |
| Research | `laboratory`, `national lab`, `max planck`, `inria`, `cnrs`, `fraunhofer`, ... |
| Company | Everything else (default) |

### Drill-down on institution click
Clicking any institution tile opens a modal with a second treemap. The CSV is loaded in full at startup (all 11,398 rows, ~6 MB) and kept in memory as `allPaperRows`.

**Papers view**: filters rows where `institutions` contains the clicked institution's canonical name; each tile = one paper, sized by number of authors from that institution on that paper; grouped by venue (Oral / Poster).

**Authors view**: enumerates all authors whose positional institution entry matches the canonical; each tile = one author, sized by number of papers.

The `canonical` field in the JSON bridges the display name (e.g. "MIT") to the CSV lookup key ("Massachusetts Institute of Technology").

---

## File Map

```
cepsai.github.io/huggingface/iclr/
├── viz_iclr.html                          # visualization (this file)
├── institution_venues_iclr_2026_v14.json  # pre-aggregated institution data
└── iclr_2026_papers_with_institutions_v4.csv  # paper-level data with institutions

Code/Crunchbase/hf/iclr_2026/
├── data_selection_v2.ipynb    # main pipeline: mapping → CSV → JSON
├── resolve_mappings.ipynb     # fuzzy analysis of unmapped strings
├── iclr_institution_mapping.json  # 946 ICLR-specific canonical entries
├── iclr_2026_papers.csv       # raw OpenReview submissions
└── iclr_2026_affiliations.csv # raw OpenReview author affiliations

cepsai.github.io/huggingface/neurips/
├── institution_merged_mapping.json         # NeurIPS base mapping (read-only)
├── institution_merged_mapping_update.json  # NeurIPS update mapping (read-only)
├── sortnames_mapping.json                  # canonical → short display name
└── country_to_continent.json              # ISO country → continent
```
