# v1 (3-way) vs v3.1 (4-way ensemble) — what changed?

Both classifications run on the **exact same 191,466 source rows** — the 12 "priority target" recipients across 32 donors, 1990–2024. This is not a new dataset: v3.1 is a re-classification of the v1 input. That makes it a clean row-level comparison joined on `orig_idx`.

**Input file:** `5-taiwan/experiments_v2/priority_target_recipients.csv`
**v1 labels:** carried in its `tech_category` column (Nemotron-3-Nano-30B, 3-way)
**v3.1 labels:** `5-taiwan/experiments_v2/results_v3_1/priority_target_v3_1_classified_ensemble.csv` (3-model soft ensemble + top-3-digital rule at threshold=20)

Remap used for comparison (v1 → v3.1 space):
- `digital_governance` → `digital_governance_and_rights`
- `digital_inclusion`  → `digital_human_development`
- `hard_infrastructure` → `hard_infrastructure`

## Headline: 3.6× more rows are now "digital"

|                             |   v1 (3-way) | v3.1 (4-way ensemble) |     Δ |
|-----------------------------|-------------:|----------------------:|------:|
| total rows                  |      191,466 |               191,466 |    0  |
| digital                     |        5,124 |                18,370 | **+3.58×** |
| non_digital                 |      186,342 |               173,096 |  −13,246 |
| digital_governance_and_rights | 1,701      |                 5,972 |  +3.51× |
| digital_human_development   |        2,863 |                 9,305 |  +3.25× |
| hard_infrastructure         |          560 |                 3,093 |  +5.52× |

Hard infrastructure is the biggest mover. v1 barely caught physical-digital rails; v3.1's binary ensemble (E2B ∪ Qwen) plus the top-3 rule surfaces 5.5× more.

## Row-level flip matrix

|                          |   v3.1 gov+rights | v3.1 human dev | v3.1 hard infra | v3.1 non_digital | v1 total |
|--------------------------|-----:|-----:|----:|------:|-----:|
| v1 gov+rights            | 1,069 | 501 | 18 | 113 | 1,701 |
| v1 human dev             | 104 | **2,447** | 19 | 293 | 2,863 |
| v1 hard infra            | 55 | 116 | **350** | 39 | 560 |
| v1 non_digital           | **4,744** | **6,241** | **2,706** | 172,651 | 186,342 |
| **v3.1 total**           | 5,972 | 9,305 | 3,093 | 173,096 | 191,466 |

**Bold** cells are the interesting ones.

### Of the 4,564 rows where both call it "digital" (4,266 agree on category, 298 disagree):
- Human development is the stickiest: 2,447 / 2,863 = **85.5% stable** (hd→hd)
- Governance & rights: 1,069 / 1,701 = 62.8% stable; 501 shifted to human_dev (end-user reframing)
- Hard infra: 350 / 560 = 62.5% stable; 116 shifted to human_dev, 55 to governance

### Non-digital → digital rescues (the bulk of movement):
13,691 rows v1 tagged `is_digital=no` but v3.1 rescued:
- 4,744 → governance_and_rights
- 6,241 → human_development
- 2,706 → hard_infrastructure

This is driven by two changes upstream of the 4-way classifier:
1. **Binary filter widened.** v1 used a single Qwen3-4B binary. v3.1 took the **union** of Qwen3-4B + Nemotron-E2B binary classifiers.
2. **Top-3-digital rule at threshold=20.** If the max soft weight across the three digital labels ≥ 20, primary = argmax(digital). Non-digital is a reject bucket, not just argmax.

### Digital → non_digital demotions:
Only 445 rows went the other way. v3.1 is more permissive but not wildly so.

## Overall label flip rate: 7.81% (14,949 of 191,466)

92.2% of rows carry the same label in both. The movement is concentrated in the newly-digital rescues; within-digital reshuffling is a smaller story.

## Per-country deltas

| recipient     | v1 digital | v3.1 digital | Δ    | Δ gov+rights | Δ human_dev | Δ hard_infra |
|---------------|-----------:|-------------:|-----:|-------------:|------------:|-------------:|
| Viet Nam      |        677 |        3,518 | +2,841 | +732       | +1,461      | +648         |
| Indonesia     |        732 |        3,285 | +2,553 | +1,028     | +868        | +657         |
| Kenya         |      1,318 |        3,862 | +2,544 | +669       | +1,617      | +258         |
| Uganda        |      1,023 |        2,536 | +1,513 | +490       | +858        | +165         |
| Nigeria       |        400 |        1,586 | +1,186 | +383       | +649        | +154         |
| Philippines   |        472 |        1,609 | +1,137 | +368       | +368        | +401         |
| Côte d'Ivoire |        277 |        1,027 |   +750 | +318       | +225        | +207         |
| Thailand      |        117 |          582 |   +465 | +145       | +290        | +30          |
| Timor-Leste   |         59 |          215 |   +156 | +86        | +62         | +8           |
| Eswatini      |         36 |           91 |    +55 | +29        | +25         | +1           |
| Fiji          |         11 |           55 |    +44 | +22        | +18         | +4           |
| Palau         |          2 |            4 |    +2  | +1         | +1          |  0           |

No country lost net digital rows. The ranking also re-orders: v3.1 puts Kenya > Viet Nam > Indonesia at the top, where v1 had Kenya > Indonesia > Viet Nam.

## Caveats and notes

- **Scope shrank from v1's published universe.** The April-7 dashboards in `../` covered all 32 priority recipients. v3.1 ran only on the 12 "priority target" subset. `classification_v2/` therefore shows 12 countries, not 32. Re-running the ensemble on the other 20 would take ~3 runs × ~1 hour on an A100 at 19k-row scale (or ~10 hours for the full 427k-row parent file).
- **UI still renders 3-way, with relabelled axes.** The v3.1 4-way collapses into the existing 3 UI slots (`digital_governance_and_rights`→gov, `digital_human_development`→inc, `hard_infrastructure`→inf). A native 4-way UI with soft-weight stacked bars would be a follow-up.
- **Commitment dollars not yet compared here.** All counts above are project-row counts on the full (pre-dedup) CSV. The HTML dashboards apply the 8-column dedup (→ 12,440 distinct digital project groups in v3.1). That is what the DATA totals in the rebuilt HTMLs reflect.
- **Dedup comparison, for reference:** v1 digital (12 targets, pre-dedup) 5,124 rows → dedup count not computed here. v3.1 digital 18,370 → 12,440 distinct groups after 8-col dedup (32% compression, typical for CRS repeats).

## Files in this folder

| file | size | what |
|---|---|---|
| `tech_overview.html` | 55 KB | v3.1 version of the integrated dashboard |
| `all_country_profiles_v2.html` / `v2a.html` / `v3.html` | 61 KB | v3.1 single-country deep dives |
| `country_comparison_v2.html` | 54 KB | v3.1 cross-country comparison |
| `v3_1_aggregates.json` | — | country-level aggregates fed into the HTMLs |
| `per_country_delta.csv` | — | per-country Δ between v1 and v3.1 |
| `flip_matrix.csv` | — | 4×4 confusion of v1 vs v3.1 labels |
| `build_v2.py` | — | HTML rebuild script |
| `analyze_v1_vs_v3_1.py` | — | this analysis |

All HTMLs carry a yellow banner linking back to the v1 (3-way) dashboard for visual comparison.
