# US-007 — US federal regulatory text audit

**Date**: 2026-04-29
**Story**: As a user, I want every article reference to US federal regulatory texts to open the correct passage so that US-context citations are reliable.

## Finding

**There are no US federal regulatory texts within the scope of v27 / v28 of the Digital AI Lexicon.** All US-context regulatory texts are US **state** laws.

## Enumeration of every US federal text covered by v27

Per the Excel inventory (`iterations/v28_excel_inventory.md` §2, "Overview of Selected Regulations" from the Methodology sheet), the canonical 12-text list is:

| # | Jurisdiction | Bill / instrument |
|---|---|---|
| 1 | European Union | AI Act (2024) |
| 2 | European Union | Code of Practice for GPAI Models (2025) — 3 chapters |
| 3 | European Union | Guidelines on the scope of obligations for GPAI models (2025) |
| 4 | California (US state) | SB 53 (2025) |
| 5 | California (US state) | SB 942 (2024) |
| 6 | California (US state) | AB 2013 (2024) |
| 7 | Colorado (US state) | SB 24-205 (2024) |
| 8 | Colorado (US state) | SB 25B-004 (2026) |
| 9 | New York (US state) | A6453B (2025) |
| 10 | New York (US state) | S8828 (2025) |
| 11 | Texas (US state) | HB 149 (2025) |
| 12 | Utah (US state) | SB 149 (2024) / SB 226 (2025) |

US federal texts in this list: **zero**.

The set of `law-blob-*` IDs actually wired into `digital_lexicon_v28.html` is:

```
ca-ab2013   ca-sb53   ca-sb942        (California — state)
co-sb24205                              (Colorado — state)
ny-a6453    ny-s8828                    (New York — state)
tx-hb149                                (Texas — state)
ut-sb226                                (Utah — state)
eu-ai-act
eu-gpai-cop-copyright
eu-gpai-cop-safety
eu-gpai-cop-transparency
eu-guidelines-ai-definition
eu-guidelines-gpai-scope
eu-guidelines-prohibited                (EU)
```

No `law-blob-us-*` or `law-blob-fed-*` (or comparable federal-jurisdiction) blob exists. No federal regulation, executive order, OMB memo, NIST framework, FTC act, sector-specific federal statute, or other US federal instrument is referenced as a primary regulatory text in the lexicon's data layer.

## Excel-side cross-check for "federal"

A full-workbook scan for the substring `federal` (case-insensitive) returned only two hits, neither of which introduces a federal text into scope:

1. **Methodology sheet, row 4** — generic prose: *"...identifying overlaps and differences between EU and U.S. regulatory texts..."*. No federal instrument named.
2. **Risk_ANALYSIS sheet, exemptions row** — content *within* California SB 53's catastrophic-risk exemption: *"lawful activity of the federal government"*. This phrase is part of an SB 53 (state law) cell, not a citation to a federal text.

## Acceptance-criteria status

| AC | Result |
|---|---|
| Enumerate every US federal text covered by v27 (per the Excel inventory) | Done — set is **empty**, see enumeration above |
| Verify every article reference against the Excel reference | Vacuously satisfied — there are no references to verify |
| Fix every mismatch in build_v28.py | Vacuously satisfied — no mismatches exist |
| Browser verification: spot-check at least 3 article links per US federal text | Vacuously satisfied — no texts to spot-check |

No build-pipeline changes are required for this story.

## Implication for the rest of US-00X audit stories

The remaining audit stories in this PRD presumably split the per-jurisdiction audit work as:

- US-006 — EU regulatory texts (AI Act, CoP CC/TC/SSC, Guidelines)
- US-007 — US **federal** texts → **this story, empty scope**
- (later) — US **state** texts (CA, CO, NY, TX, UT), most likely split per state

If the project lead intended US-007 to cover *all* US texts (i.e., state-level inclusive), they should rescope or rename the story; under the literal reading "US federal regulatory texts" the answer is empty by construction because the Excel reference does not include any federal instrument.

## Recommendation

Mark US-007 complete. If the project later expands the lexicon to include US federal AI-related texts (e.g., the OMB AI Memos M-24-10 / M-24-18, NIST AI RMF, NIST GenAI Profile, FTC Section 5 enforcement statements, EO 14179, or sector-specific federal AI rules from EEOC/FDA/HUD/CFPB), a new audit story should be opened that mirrors US-006's per-text article-link verification approach.
