# Resilience Index 2025 – Candidate Countries Visualisation

## Overview

Comparative visualisation of the **Resilience Index 2025** for ten EU candidate countries against the **EU-27 average** rank and the **best EU performer** per dimension, covering the overall index and nine sub-pillars.

---

## Source Data

Two Excel files in this folder:

| File | Contents |
|---|---|
| `ResilienceIndexRegions-2025.xlsx` | Overall country rank, overall score, Macro Score, Physical Score — 130 countries |
| `ResilienceIndexRegions-2025-factors.xlsx` | Scores for 9 sub-pillar factors — same 130 countries, no pre-computed ranks |

### Countries in scope

**Candidate countries (9):** Albania, Bosnia and Herzegovina, Georgia, Moldova, Montenegro, North Macedonia, Serbia, Türkiye, Ukraine
> Kosovo was excluded — absent from both source files.

**EU-27 member states** used to compute the EU average and identify best performers.

---

## Methodology

### Overall index ranks
Candidate country ranks were taken directly from `Country Rank` in the main file (global ranking across 130 countries).

### EU-27 average rank
1. Computed the **mean score** of the 27 EU member states for each dimension (overall index + 9 sub-pillars).
2. Determined where that average score would **rank among all 130 countries** by counting how many countries score higher — this gives a hypothetical "where would the EU average place globally" rank.

### Sub-pillar ranks
The factors file contains scores only. Ranks for each dimension were derived by applying the same method: for every country and for the EU-27 average, count countries with a higher score to obtain the global rank.

### Best EU performer per dimension
For each dimension, the EU member state with the **highest score** was identified and its global rank computed from the same pool of 130 countries.

---

## Output Files

| File | Description |
|---|---|
| `overall_ranks.csv` | Global rank on the overall index: 9 candidates + EU-27 Average + Best EU |
| `factor_ranks.csv` | Global ranks across all 10 dimensions for every entity |
| `best_eu_details.csv` | Best EU country and global rank per dimension |
| `resilience_viz.html` | **Bump chart** (rank profiles across all dimensions) + **bar chart** (overall rank) |
| `resilience_subpillar_bars.html` | **Small-multiples bar chart**: one panel per dimension, bars for candidates + EU avg, gold dashed reference line for best EU performer |

---

## Key Findings

| Country | Overall Rank |
|---|---|
| Türkiye | 53 |
| Serbia | 61 |
| Georgia | 62 |
| Montenegro | 63 |
| North Macedonia | 71 |
| Ukraine | 79 |
| Albania | 82 |
| Bosnia & Herz. | 83 |
| Moldova | 87 |
| **EU-27 Average** | **25** |
| **Best EU (Denmark)** | **1** |

Selected sub-pillar highlights:
- **Cybersecurity**: Serbia ranks 21st globally (best candidate); Bosnia ranks 123rd (worst)
- **Climate Risk Exposure**: Türkiye ranks 21st globally (best candidate)
- **Political Risk**: Ukraine (122) and Türkiye (118) rank near the bottom globally
- **GHG Emissions** and **Urbanization Rate**: several candidates rank competitively with or above the EU-27 average

---

## Tools

Python · pandas · HTML + SVG (no external libraries)
