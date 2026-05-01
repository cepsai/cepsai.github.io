# NeurIPS Papers CSV — Data Source Documentation

## Overview

Two CSV files (`neurips_2024_papers_with_institutions_v4.csv` and `neurips_2025_papers_with_institutions_v4.csv`) are the primary data sources powering the NeurIPS institution leaderboard visualizations on this site. They are loaded at runtime by the HTML files via `fetch()` and parsed client-side using PapaParse.

---

## File Locations

Each CSV exists in **two identical copies** — one per serving context:

| Copy | Path | Served by |
|------|------|-----------|
| A | `huggingface/2025/neurips_2025_papers_with_institutions_v4.csv` | `2025/2.html` and its variants |
| B | `huggingface/neurips/neurips_2025_papers_with_institutions_v4.csv` | `neurips/viz_neurips.html`, `neurips/viz_neurips_.html` |

Both copies of each CSV are **byte-for-byte identical** (confirmed via `diff`). The duplication exists because each HTML file loads the CSV via a relative path, and the HTML files live in different directories.

The same pattern applies to the 2024 file:
- `huggingface/2025/neurips_2024_papers_with_institutions_v4.csv`
- `huggingface/neurips/neurips_2024_papers_with_institutions_v4.csv`

> **Note:** When updating the CSVs, both copies must be updated together.

---

## CSV Schema

Both files share the same 16-column schema (sourced from OpenReview):

| Column | Description |
|--------|-------------|
| `id` | OpenReview submission ID (same as `forum`) |
| `forum` | OpenReview forum ID |
| `number` | Submission number within the conference |
| `title` | Paper title |
| `abstract` | Full abstract text |
| `authors` | Semicolon-separated author display names |
| `authorids` | Semicolon-separated OpenReview author IDs (tilde format) |
| `venue` | Human-readable venue string (e.g. `NeurIPS 2025 poster`) |
| `venueid` | Machine venue ID (e.g. `NeurIPS.cc/2025/Conference`) |
| `primary_area` | Submission topic area (e.g. `applications`, `neuroscience_and_cognitive_science`) |
| `pdf` | Relative path to PDF on OpenReview |
| `cdate_iso` | Creation/submission date (ISO 8601) |
| `pdate_iso` | Publication date (ISO 8601) |
| `mdate_iso` | Last modification date (ISO 8601) |
| `openreview_url` | Full URL to the OpenReview forum page |
| `institutions` | Semicolon-separated institution names resolved for each author |

The `institutions` column is the enriched field — it is **not** from OpenReview directly but was resolved in a separate processing step (see `neurips/data_selection.ipynb`) by mapping author affiliations to canonical institution names.

---

## Row Counts

| File | Rows (excl. header) | Conference |
|------|---------------------|------------|
| `neurips_2024_papers_with_institutions_v4.csv` | 9,181 | NeurIPS 2024 |
| `neurips_2025_papers_with_institutions_v4.csv` | 12,370 | NeurIPS 2025 |

---

## Companion Data Files

Each year's CSV is paired with an institution JSON file that provides aggregated venue/institution metadata:

| Year | CSV | Institution JSON |
|------|-----|-----------------|
| 2024 | `neurips_2024_papers_with_institutions_v4.csv` | `institution_venues_2024_v14.json` |
| 2025 | `neurips_2025_papers_with_institutions_v4.csv` | `institution_venues_v14.json` |

The JSON files live alongside the HTML that uses them (in `2025/` or `neurips/` depending on the copy). They are pre-aggregated counts used to power the institution ranking bars. The CSV provides the raw paper-level records used for drill-down tables.

---

## HTML Files That Consume These CSVs

### `huggingface/2025/2.html`
- **Primary production viz** for the `2025/` directory.
- Generated from R/knitr (note the knitr CSS classes at the top of the file).
- `currentYear` defaults to `"2025"`, `currentTopLimit` defaults to `50`.
- Loads CSV relative to `2025/` directory.

### `huggingface/neurips/viz_neurips.html`
- **Main viz** in the `neurips/` directory — likely the canonical/embedded version.
- `currentYear` defaults to `"2025"`, `currentTopLimit` defaults to `"All"`.
- Loads CSV relative to `neurips/` directory.

### `huggingface/neurips/viz_neurips_.html`
- **Alternate/prior version** in the `neurips/` directory.
- Identical `yearConfigs` structure, `currentTopLimit` defaults to `"All"`.
- Likely a development or backup copy — `viz_neurips.html` is the authoritative version.

### `huggingface/neurips/viz_neurips_old.html`
- Older version — does **not** reference the v4 CSVs (uses earlier data format).

---

## How the CSVs Are Used at Runtime

Each HTML file defines a `yearConfigs` object:

```js
var yearConfigs = {
  "2024": {
    label: "2024",
    institutionFile: "institution_venues_2024_v14.json",
    paperCsv: "neurips_2024_papers_with_institutions_v4.csv",
    sourceUrl: "https://openreview.net/group?id=NeurIPS.cc/2024"
  },
  "2025": {
    label: "2025",
    institutionFile: "institution_venues_v14.json",
    paperCsv: "neurips_2025_papers_with_institutions_v4.csv",
    sourceUrl: "https://openreview.net/group?id=NeurIPS.cc/2025"
  }
};
```

When the user selects a year in the dropdown UI, the viz fetches the corresponding CSV and JSON, parses them client-side, and re-renders the institution leaderboard. The CSV is used for the paper-level detail panel; the JSON drives the main ranking bars.

---

## Data Pipeline

The CSVs are produced upstream (not in this repo) and then placed here manually. The processing notebook `huggingface/neurips/data_selection.ipynb` shows the enrichment logic for resolving the `institutions` column. Supporting mapping files used in that pipeline:

- `neurips/institution_merged_mapping.json` — maps raw affiliation strings to canonical names
- `neurips/institution_merged_mapping_update.json` — incremental corrections/additions
- `neurips/sortnames_mapping.json` — display name normalization
- `neurips/country_to_continent.json` — geographic grouping

---

## Key Invariants for Any Agent Working on This

1. **Both copies must stay in sync.** The `2025/` and `neurips/` copies of each CSV must be identical. If you update one, update both.
2. **The `institutions` column is the enriched field.** It is not raw OpenReview data — it has been processed through the institution mapping pipeline.
3. **The JSON companion files are pre-aggregated.** They are not auto-generated from the CSV at runtime; they must be regenerated separately if the CSV changes.
4. **`viz_neurips_old.html` is legacy.** Do not update it; it does not use the v4 schema.
5. **`2025/2.html` is knitr-generated.** Its CSS/structure differs from the pure-HTML `neurips/viz_neurips.html` — they are not interchangeable templates.
