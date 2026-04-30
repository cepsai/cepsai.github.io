# Reference lookup — 2026-04-30 09:25

- Raw cell-reference strings: **141**
- Atomic citations: **323**
- Parsed (law + anchor identified): **315** (98%)
- Matched against a law-blob article/section: **315** (98%)

Parse-success and blob-coverage are distinct: a citation can be parsed correctly to e.g. `eu-ai-act/annex/IV` but still not match because the annex isn't ingested into the law blob yet.

## Coverage by law

| law_id | matched | parsed | total | match-rate |
| --- | --- | --- | --- | --- |
| eu-ai-act | 140 | 140 | 140 | 100% |
| co-sb24205 | 39 | 39 | 39 | 100% |
| ny-s8828 | 30 | 30 | 30 | 100% |
| ca-sb53 | 23 | 23 | 23 | 100% |
| ut-sb226 | 18 | 18 | 18 | 100% |
| tx-hb149 | 16 | 16 | 16 | 100% |
| ca-sb942 | 11 | 11 | 11 | 100% |
| ca-ab2013 | 11 | 11 | 11 | 100% |
| ny-a6453 | 11 | 11 | 11 | 100% |
| (unknown) | 0 | 0 | 8 | 0% |
| eu-guidelines-gpai-scope | 7 | 7 | 7 | 100% |
| eu-gpai-cop-safety | 4 | 4 | 4 | 100% |
| eu-gpai-cop-copyright | 3 | 3 | 3 | 100% |
| eu-gpai-cop-transparency | 2 | 2 | 2 | 100% |

## Delta vs current `window.REF_MAP`

- new keys produced by parser: **51**
- existing keys no longer used (orphans in HTML): **32**
- entries with changed law/kind/anchor: **121**

Anchor format note: the parser emits bare article/section IDs (e.g. `"3"`) with paragraphs/subparagraphs as separate fields, whereas the current `REF_MAP` uses joined anchors (e.g. `"3-3"`). Most `changed` rows reflect this convention difference, not a semantic disagreement.

## Outputs
- `reference_lookup.json` — canonical lookup keyed by raw reference
- `reference_lookup_atomic_map.json` — atomic-keyed REF_MAP-shape lookup (drop-in for the HTML)
- `reference_lookup_atomic.json` — per-atomic rows with concept provenance
- `reference_lookup_unmatched.csv` — unmatched citations needing review
- `reference_lookup_delta.csv` — diff against existing `window.REF_MAP`
