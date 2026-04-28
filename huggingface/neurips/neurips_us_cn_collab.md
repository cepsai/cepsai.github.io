# NeurIPS US × China co-authored papers (2024 vs 2025)

Counts papers with **at least one US institution and at least one Chinese institution** among their affiliations, broken down by paper type. Greater China (CN + HK + MO) is treated as "China". Companion to `neurips_china_share.md`, which reports the institution-level share view.

## Results

| Paper type | 2024 | % | 2025 | % | Δpp |
|---|---:|---:|---:|---:|---:|
| Main — oral | 15/61 | 24.6% | 9/77 | 11.7% | −12.9 |
| Main — spotlight | 30/325 | 9.2% | 94/686 | 13.7% | +4.5 |
| Main — poster | 478/3,645 | 13.1% | 579/4,523 | 12.8% | −0.3 |
| Datasets & Benchmarks — oral | 2/11 | 18.2% | 1/7 | 14.3% | −3.9 |
| Datasets & Benchmarks — spotlight | 13/56 | 23.2% | 11/56 | 19.6% | −3.6 |
| Datasets & Benchmarks — poster | 79/392 | 20.2% | 81/434 | 18.7% | −1.5 |
| Competition Track | 3/16 | 18.8% | — | — | — |
| Position Paper Track (all) | — | — | 4/40 | 10.0% | — |
| **Overall** | **620/4,506** | **13.8%** | **779/5,823** | **13.4%** | **−0.4** |

Excluding the small Competition and Position Paper tracks doesn't meaningfully change the totals (2024: 13.74%; 2025: 13.40%).

## Headline

**US–China collaboration rate is flat year-over-year (~13.5%)** despite a much larger underlying pool. Total volume of collaborative papers grew ~26% (+159), but so did total NeurIPS volume (+1,317 papers).

Paired with the institution-share trend in `neurips_china_share.md` (China 30.0% → 36.4%, US 38.3% → 32.1%), the reading is: Chinese researchers wrote more papers in 2025, but proportionally **not more of them with US co-authors** — consistent with decoupling at the margin even while absolute collaboration kept rising.

### What shifted within the aggregate

- **Main oral collapsed** (24.6% → 11.7%) but only 15 → 9 papers, small n.
- **Main spotlight jumped** (9.2% → 13.7%), the biggest bucket that moved with n large enough to be real. NeurIPS 2025 accepted 2× more spotlights than 2024 (325 → 686), so interpretation is confounded by category re-routing.
- **Datasets & Benchmarks** consistently the most collaborative track (~18–23%) and drifted slightly down across all three sub-tiers.
- **Main poster**, the dominant bucket by volume, is flat (13.1% → 12.8%).

## Methodology

### Data
- `neurips_2024_papers_with_institutions_v4.csv` (4,510 papers; 4 dropped for null `institutions`)
- `neurips_2025_papers_with_institutions_v4.csv` (5,825 papers; 2 dropped for null `institutions`)
- Institution → country via `institution_venues_2024_v14.json` and `institution_venues_v14.json`
- Name normalization: `sortnames_mapping.json` (essential — lifts resolution from 63% → 98–99%) and `institution_merged_mapping_update.json`

### Per-paper classification
1. Split the `institutions` column on `;`, strip and de-duplicate.
2. Resolve each institution name to an ISO-2 country code through: manual overrides → per-year JSON direct lookup → sortnames fallback → merged-mapping fallback.
3. Collect the set of unique countries represented on the paper.
4. Count the paper as "US+CN" if the set contains **both** `US` and `CN` (where `CN` has been expanded to include `HK` and `MO`).

### Greater China
`HK` and `MO` are collapsed into `CN` at the country-map stage. This means a paper with authors from CUHK + MIT counts as US+CN. Defensible for "Greater China vs US" framing; inconsistent with sources that keep HK separate (e.g., Nature Index, OECD). Taiwan (`TW`) is **not** included — 36 papers in 2024, 25 in 2025 would shift if TW were added.

### Name-collision handling (Meta bug fix)
The 2025 JSON contains two records literally named "Meta": one `US` (San Francisco, 217 venue hits) and one `CN` (Beijing, 1 hit). Naive dict-building by name lost the US record to the CN record, mis-classifying every Meta-affiliated 2025 paper as CN — e.g. "Memory Mosaics at scale" (NYU + Meta, both authors in New York) was flagged as US+CN when in reality it was a US-only paper.

The fix: the loader now collapses multiple records sharing a `name`, tallies venue-counts per country, and keeps the dominant country (with `Unknown Country` demoted when real countries exist). All collisions found:

| Year | Name | Countries | Picked | Notes |
|---|---|---|---|---|
| 2024 | Amazon | US (144) vs DE (6) | US | heuristic correct |
| 2024 | IBM Research | CH (8) vs US (2) | US (manual override) | heuristic picked CH; IBM's AI labs are mostly Yorktown/Almaden |
| 2025 | Amazon | US (166) vs DE (8) | US | correct |
| 2025 | Meta | US (217) vs CN (1) | US | the bug |
| 2025 | Chinese Academy of Sciences | Unknown (2) vs CN (1) | CN (manual override) | |
| 2025 | City University of Hong Kong | HK vs CN (Dongguan) | CN | HK→CN treatment makes it moot |
| 2025 | Hong Kong Baptist University | CN (Zhuhai) vs HK | CN | same |
| 2025 | Skywork AI | SG (1) vs CN (2) | CN | correct |
| 2025 | LUT University | FI (1) vs CN (1) | FI | correct (Finnish-origin) |
| 2025 | Valence Labs | CA (2) vs GB (1) | CA | doesn't affect US+CN |

### Manual overrides applied

For ambiguous / historically mis-mapped names:
- `South China University`, `South China University of Technology`, `Chinese Academy of Sciences` → `CN`
- `IBM Research`, `IBM Research AI`, `IBM T. J. Watson Research Center` → `US`

For institutions the sortnames/merged mappings missed:
- US: `Apple AI Research`, `Hewlett Packard Labs`, `Together.ai`
- CN: `ByteDance AILab`, `Du Xiaoman Technology(BeiJing)`, `Shanghai Aircraft Design and Research Institute`, `inspir.ai`, `Hithink Research`, `Agibot`, `Cambricon Techonologies`, `, Cambricon Techonologies`

## Caveats (real limits on interpreting these numbers)

1. **Microsoft Research Asia is invisible in this data.** Only 1 paper in 2024 and 0 in 2025 explicitly list "Microsoft Research Asia"; all 889 other Microsoft-affiliated mentions say just `Microsoft` and are classified as US. MSRA papers with Chinese universities therefore count as US+CN when the work is effectively all-in-China. Same risk (smaller magnitude) for Apple, Google, NVIDIA — all single-entry US in the JSON. Huawei is the only multinational properly split (`Huawei`, `Huawei Noah's Ark Lab`, `Huawei Canada`). Not fixable without author-level affiliations.

2. **US universities' Chinese campuses are attributed to CN.** NYU Shanghai, Duke Kunshan, and Xi'an Jiaotong-Liverpool all resolve to `CN`. Defensible (research physically conducted in China) but the branded name can mislead readers.

3. **Binary paper-level metric.** A paper with 1 US author + 10 Chinese authors counts the same as a 5+5 split. This inflates apparent collaboration versus weighted alternatives (majority-country, corresponding-author, dyadic share).

4. **Coverage ~98–99%.** Remaining unresolved institution strings (~100 mentions across both years) are dominated by non-US-non-CN entities like "Max Planck Institute for Software Systems", "Bosch", "Johannes Kepler Universität Linz" — so the effect on US+CN is small but not zero.

5. **Author-level affiliations are collapsed 1-to-1 with the `institutions` column.** Dual affiliations per author are not split; the data treats one author = one institution.

6. **Spotlight category grew 2× between years** (325 → 686 papers), so YoY comparison within that bucket mixes the underlying rate with a change in what "spotlight" means.

## Companion artifact

`us_cn_papers.html` — self-contained filterable HTML of all 1,399 US+CN papers. Filter by year, paper type, or search by title/institution. Each paper shows its US institutions (blue pills), CN institutions (red pills), and other-country institutions (gray).

---

Source: OpenReview NeurIPS 2024 & 2025 paper metadata.
