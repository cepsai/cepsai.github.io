# Occupational AI Exposure Heatmap

Replicates the ISCO 1-digit heatmap visualization showing percentile-ranked exposure scores across AI, GenAI, and wider-tech measures.

---

## Files

| File | Description |
|------|-------------|
| `occ_exposure_db.csv` | Source data: ~350 ISCO 4-digit occupations × 17 exposure scores (2017–2025) |
| `generate_heatmap.py` | Processing script — run to regenerate all outputs |
| `occ_exposure_pct_rank.csv` | Output: ISCO 1-digit averages + percentile ranks |
| `occ_exposure_heatmap.html` | Output: interactive heatmap visualization |

---

## Method

### 1. Aggregation to ISCO 1-digit level
For each of the 9 ISCO 1-digit categories (1 Managers → 9 Elementary; armed forces excluded), the raw exposure scores of all constituent 4-digit occupations are averaged, ignoring missing values.

### 2. Percentile ranking
For each exposure measure (column), the 9 ISCO 1-digit means are ranked against each other using `pandas.Series.rank(pct=True)`. A value of 1.0 means the most exposed category for that measure; 0.11 (= 1/9) means the least exposed.

### 3. Output CSV (`occ_exposure_pct_rank.csv`)
Contains 9 rows (one per ISCO 1-digit category) and 34 columns:
- `ISCO1D`, `ISCO1Dname`
- 16 raw mean columns (one per exposure measure)
- 16 `_pct` percentile-rank columns

---

## Exposure measures

Grouped as in the visualization:

| Section | Sub-group | Column |
|---------|-----------|--------|
| **AI** | Early | `2017_Frey_autom`, `2018_Brynjolfsson_mSML`, `2020_Webb_AI` |
| **AI** | Mid | `2021_Tolan_AI`, `2021_Felten_AIOE`, `2024_Engberg_DAIOE` |
| **AI** | Recent | `2024_Loaiza_augm`, `2024_Loaiza_autom` |
| **GenAI** | — | `2023_Felten_genAIOE`, `2023_Gmyrek_LLM`, `2024_Eloundou_GPT` |
| **wider-tech** | Robots/software | `2020_Webb_robot`, `2020_Webb_software` |
| **wider-tech** | Recent | `2024_Autor_augm`, `2024_Autor_autom`, `2024_Prytkova_digital` |

---

## Visualization (`occ_exposure_heatmap.html`)

Standalone HTML/JS file (no external dependencies).

- **Color scale**: white → medium purple → dark indigo, matching the source figure
- **Layout**: three panels (AI, GenAI, wider-tech) with black vertical separators between sub-groups
- **Tooltips**: hover over any cell to see the exact percentile rank
- **Missing data**: shown in grey

To regenerate after updating the source data:
```bash
python3 generate_heatmap.py
```
