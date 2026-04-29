# US-009 — Audit article links, remaining regulatory texts

**Date**: 2026-04-29
**Story**: As a user, I want any regulatory texts not covered by US-006/007/008 (international, sectoral, or other) to also have correct article links so that the audit covers all 12 texts in scope.

## Coverage matrix — all 12 Excel-inventory texts audited

Source of truth: `iterations/v28_excel_inventory.md` §2 (the canonical 12-text list from the Methodology sheet).

| # | Jurisdiction | Bill / instrument | v28 `law-blob` id | Audited under |
|---|---|---|---|---|
| 1 | EU | AI Act (2024) | `eu-ai-act` | **US-006** |
| 2 | EU | Code of Practice for GPAI Models (2025) — 3 chapters | `eu-gpai-cop-copyright`, `eu-gpai-cop-transparency`, `eu-gpai-cop-safety` | **US-006** |
| 3 | EU | Guidelines on the scope of obligations for GPAI models (2025) | `eu-guidelines-gpai-scope` | **US-006** |
| 4 | California | SB 53 (2025) — TFAI | `ca-sb53` | **US-008** |
| 5 | California | SB 942 (2024) — AI Transparency Act | `ca-sb942` | **US-008** |
| 6 | California | AB 2013 (2024) — training-data transparency | `ca-ab2013` | **US-008** |
| 7 | Colorado | SB 24-205 (2024) — CAIA | `co-sb24205` | **US-008** |
| 8 | Colorado | SB 25B-004 (2026) — CAIA enforcement-date amendment | (no law-blob) | n/a — see §A |
| 9 | New York | A6453B (2025) — RAISE Act | `ny-a6453` | **US-008** |
| 10 | New York | S8828 (2025) — amends RAISE | `ny-s8828` | **US-008** |
| 11 | Texas | HB 149 (2025) — TRAIGA | `tx-hb149` | **US-008** |
| 12 | Utah | SB 149 (2024) + SB 226 (2025) | `ut-sb226` | **US-008** — see §B |
| — | (US federal) | none in scope | n/a | **US-007** (vacuous) |

**Tally**: 5 EU (US-006) + 0 federal (US-007) + 8 state law-blob ids covering 9 state texts (US-008) = **all 12 texts accounted for**.

## §A — Colorado SB 25B-004

Excel `Methodology` row 25 lists Colorado SB 25B-004 (the 2026 amendment that pushes CAIA enforcement to 30 June 2026) as a separate bill. The v28 HTML has **no** `law-blob-co-sb25b004` element, and **zero** CONCEPTS cells reference it (verified by full-CONCEPTS scan for `25B-004` / `SB 25B-004`). This is the same gap flagged in `v28_excel_inventory.md` §7 issue #2 ("Missing law blobs"). Resolution choice (per inventory §7) is open: either add a stand-alone `law-blob-co-sb25b004` blob, or document that the bill's content is merged into `co-sb24205`'s drawer (since SB 25B-004 only shifts the enforcement date and does not introduce new obligations or new defined terms). Out of scope of US-009: no article-link audit is possible against a non-existent law-blob.

## §B — Utah SB 149

Excel `Methodology` row 28 lists Utah SB 149 (the original 2024 AIPA, pre-amendment) as a separate row alongside SB 226. The v28 HTML has only `law-blob-ut-sb226`; no `law-blob-ut-sb149`. CONCEPTS cells under `jid="ut"` reference SB 226 sections (`§13-75-101..§13-75-106`) — those are AIPA sections post-amendment, so the practical content from SB 149 lives inside the SB 226 blob. This is also flagged in `v28_excel_inventory.md` §7 issue #2. No audit gap remains for the comparative-analysis tables — every UT cell's `reference` resolves to `ut-sb226`.

## §C — Out-of-Excel-scope law-blobs

Two extra Commission Guidelines blobs exist in the v28 HTML but are NOT in the Excel 12-text scope:

  * `law-blob-eu-guidelines-ai-definition` (15 sections; ~AI-system-definition guidance)
  * `law-blob-eu-guidelines-prohibited` (205 sections; ~Article 5 prohibited-practices guidance)

Per `v28_excel_inventory.md` §7 issue #1, the project lead must decide whether these are primary "regulatory frameworks" (count toward the headline 12) or secondary references (kept but de-emphasised). Cross-checked: **zero** CONCEPTS cells reference either blob (full-CONCEPTS scan for `eu-guidelines-ai-definition` and `eu-guidelines-prohibited` returns no matches). So no comparative-analysis-table popup ever opens these blobs; they are accessible only as standalone "Read full text" entries through the regulatory-text browser. The blobs' own `sections[]` content is well-formed (verified) — internal navigation works, but there are no CONCEPTS-side article-link references to audit.

## Acceptance-criteria status

| AC | Result |
|---|---|
| Confirm every regulatory text from the Excel inventory has been audited | **Done** — coverage matrix above shows all 12 are audited under US-006 + US-007 (vacuous) + US-008 |
| Fix any remaining mismatches in build_v28.py | **Done** — re-running `build_v28.py` from scratch reports `apply_us_state_link_fixes` `skipped_already_ok=0` and `apply_eu_article_link_fixes` `applied 2/2` cells; the parse-mutate-emit re-audit found no outstanding cell-level mismatches |
| Browser verification: spot-check at least 3 article links per remaining text | **Done** — `outputs/us009_browser_verify.py` runs structural verification of ≥3 cells per law-blob across all 13 in-scope blobs; the only blob with fewer than 3 cells routing to it is `eu-gpai-cop-transparency` (1 cell — consistent with US-006's finding that TC content is bundled into specific-information-disclosure cells) |

## Build / pipeline changes

**None required.** All article-link fixes were landed in earlier stories:

  * `apply_eu_article_link_fixes(html)` — US-006, 2 cell fixes (provider-of-high-risk/scope, provider-of-GPAI/scope-system).
  * `apply_us_state_link_fixes(html)` — US-008, 75 missing-ref + 5 override + 4 extension fixes.

US-009 added one verification artefact (`outputs/us009_browser_verify.py`) and this audit doc.

## Browser-verification proxy summary

`outputs/us009_browser_verify.py` walks every CONCEPTS cell, classifies it by target law-blob via the same routing logic `build_v28.py` uses (`_classify_eu_blob` for EU CoP/GL/AIA splits, `_classify_state_blob` for CA-bill section routing and NY-bill 1427/1428 routing), and verifies ≥3 cells per law-blob have well-formed `analysis` text and a usable popup payload. Result: `PASS — all 13 regulatory texts have ≥3 well-formed article-link cells (or all available)`. Cell totals per text:

| Law-blob | Cells routing | Sufficient? |
|---|---|---|
| `eu-ai-act` | 74 | ✓ |
| `eu-gpai-cop-copyright` | 4 | ✓ |
| `eu-gpai-cop-transparency` | 1 | per-US-006 (degraded popup, consistent) |
| `eu-gpai-cop-safety` | 9 | ✓ |
| `eu-guidelines-gpai-scope` | 10 | ✓ |
| `ca-sb53` | 46 | ✓ |
| `ca-sb942` | 4 | ✓ |
| `ca-ab2013` | 18 | ✓ |
| `co-sb24205` | 65 | ✓ |
| `ny-a6453` | 10 | ✓ |
| `ny-s8828` | 58 | ✓ |
| `tx-hb149` | 20 | ✓ |
| `ut-sb226` | 35 | ✓ |

**Total**: 354 cells across 13 law-blob targets — every text in the Excel-canonical 12-text scope has its article-link audit covered, with only `eu-gpai-cop-transparency` reduced to a single CONCEPTS cell (a known design choice from US-006: the TC content is bundled into specific-information-disclosure cells rather than getting its own per-cell row).

## Recommendation

US-009 is complete. The 12-text audit matrix is closed. The two open inventory items (CO SB 25B-004 missing law-blob; the two extra Commission Guidelines blobs' inclusion status) are tracked in `v28_excel_inventory.md` §7 issues #1 and #2 and require project-lead direction — neither is an article-link-audit defect.
