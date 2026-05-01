# PRD: Lexicon Verifier + v30 with Verbatim Highlighting

## Overview
Two-part feature for the AI Lexicon project. Part 1 builds a verifier that audits `iterations/digital_lexicon_v29.html` against the cross-checked analysis Excel (`Cross-checked_AI terminology and taxonomy_analysis-2.xlsx`) and the verbatim source Excel (`AI terminology and taxonomy_verbatim excel.xlsx`), confirming each analysis is present, correctly worded, and correctly linked to its source law article. Part 2 ships `digital_lexicon_v30.html`, which adds verbatim highlighting in the law-article view and auto-corrects article selection when no verbatim is available.

## Goals
- Provide a reproducible verification pass that proves v29 uses the exact analyses from the cross-checked Excel
- Confirm every analysis in v29 links to the correct article in the corresponding law
- Produce a triple-output verification artefact: markdown report, CSV, and interactive HTML diff viewer
- Generate `v29-corrected.html` with auto-applied fixes for any mismatches found
- Ship v30 that highlights verbatim spans inside the law article using `<mark>` when an analysis is clicked
- Auto-correct article selection in v30 when no verbatim is found, falling back to a markdown warning log

## Quality Gates

These commands must pass for every user story:
- `python -m pytest iterations/` — existing test suite
- `python iterations/audit_excel_correspondence.py` — Excel correspondence audit

For UI stories (v30 highlighting, diff viewer), also include:
- Verify in browser using `/browse` skill: open the artefact, click ≥5 analyses across different laws, confirm highlights appear and links resolve to the correct article

## User Stories

### US-001: Load and normalise the two Excel sources
As a developer, I want a single loader module that reads both the cross-checked analysis Excel and the verbatim Excel into normalised pandas DataFrames so that every downstream task works from one canonical representation.

**Acceptance Criteria:**
- [ ] New module `iterations/load_lexicon_sources.py` exposes `load_analyses()` and `load_verbatim()` returning pandas DataFrames
- [ ] Loader handles the actual column structure of both files (inspect first, do not infer)
- [ ] Each row is keyed by `(term, law_id, article_id)` so analyses and verbatim can be joined
- [ ] Empty/missing verbatim cells are preserved as `None`, not `NaN` strings
- [ ] Country code edge case: if any `law_id` uses ISO codes, `"NA"` (Namibia) is not treated as null
- [ ] Module prints row counts and a 5-row sample when run as `__main__`

### US-002: Extract analyses and article references from v29 HTML
As a developer, I want a parser that extracts every `(term, analysis_text, linked_law, linked_article)` tuple from `digital_lexicon_v29.html` so that the verifier can compare HTML state against Excel ground truth.

**Acceptance Criteria:**
- [ ] New module `iterations/parse_v29.py` returns a DataFrame with columns: `term`, `analysis_text`, `law_id`, `article_id`
- [ ] Uses BeautifulSoup (or lxml) — no regex-only HTML parsing
- [ ] Round-trips analysis text without whitespace/punctuation drift (preserves the exact string)
- [ ] Handles entries that have multiple linked articles
- [ ] Prints total analyses found and unique laws referenced when run as `__main__`

### US-003: Verify analyses match the cross-checked Excel exactly
As a developer, I want a verification pass that compares each analysis in v29 against the cross-checked Excel so that I can prove v29 uses the exact analyses from the source.

**Acceptance Criteria:**
- [ ] New module `iterations/verify_lexicon.py` produces a per-analysis status: `match`, `mismatch`, `missing_in_html`, `missing_in_excel`
- [ ] Comparison is exact-text after normalising whitespace
- [ ] Mismatches include both the HTML version and the Excel version side by side
- [ ] Output saved to `outputs/lexicon_verification_<timestamp>.csv`
- [ ] Console summary shows counts per status

### US-004: Verify analysis-to-article links resolve to verbatim entries
As a developer, I want each `(term, law, article)` link in v29 verified against the verbatim Excel so that I know every analysis points to a real source article.

**Acceptance Criteria:**
- [ ] For each linked article, look up the `(law_id, article_id)` pair in the verbatim DataFrame
- [ ] Status values: `verbatim_found`, `no_verbatim`, `wrong_article`, `wrong_law`
- [ ] `wrong_article` is set when verbatim Excel has the term in the same law but a different article
- [ ] `wrong_law` is set when the term has no entry in the linked law but exists in another
- [ ] Results merged into the same CSV from US-003

### US-005: Generate markdown report + interactive HTML diff viewer
As a user, I want a human-readable report and a clickable diff viewer so that I can review verification results without parsing CSV.

**Acceptance Criteria:**
- [ ] `outputs/lexicon_verification_<timestamp>.md` summarises totals, top mismatches, and broken links
- [ ] `outputs/lexicon_verification_<timestamp>.html` is a self-contained page that lists every analysis with status badges
- [ ] HTML viewer supports filter buttons: All / Mismatch / Missing / Wrong Article / Wrong Law
- [ ] Clicking a mismatch row shows the HTML text and Excel text side by side with character-level diff
- [ ] No inline `onclick` handlers — use `addEventListener` and event delegation

### US-006: Produce v29-corrected.html with auto-applied fixes
As a user, I want a corrected copy of v29 with mismatches resolved so that I can review and adopt fixes without manual editing.

**Acceptance Criteria:**
- [ ] `iterations/digital_lexicon_v29-corrected.html` is generated when verifier runs in `--fix` mode
- [ ] Mismatched analysis text is replaced with the cross-checked Excel text
- [ ] Wrong article links are updated to point to the article confirmed by the verbatim Excel
- [ ] Original v29 file is not modified
- [ ] A summary block at the top of the corrected file lists every change applied

### US-007: Build digital_lexicon_v30.html scaffold
As a user, I want v30 to start as a verified copy of v29-corrected.html so that highlighting features build on a known-good base.

**Acceptance Criteria:**
- [ ] `iterations/digital_lexicon_v30.html` exists in the iterations folder
- [ ] All v29 functionality preserved (term list, analysis panel, law/article view)
- [ ] No regressions: clicking any term still loads its analysis and law
- [ ] Verified in browser using `/browse` skill across ≥5 terms

### US-008: Highlight verbatim spans in the law article on analysis click
As a user, I want the verbatim text from the source Excel highlighted inside the displayed law article so that I can see exactly which words back the analysis.

**Acceptance Criteria:**
- [ ] When an analysis is clicked, the law article view scrolls to and wraps the verbatim text in `<mark>` with yellow background
- [ ] If the verbatim string contains multiple sentences, every contiguous span is wrapped
- [ ] Whitespace/quote variants (smart quotes, non-breaking spaces) are matched leniently
- [ ] Existing `<mark>` from a previous click is cleared before applying new highlight
- [ ] Verified in browser via `/browse` skill: click ≥5 analyses across different laws and confirm highlights

### US-009: Auto-correct article selection when no verbatim exists
As a user, I want v30 to automatically pick the correct article when an analysis has no verbatim entry so that I never see an analysis pointing to the wrong article.

**Acceptance Criteria:**
- [ ] When clicked analysis has no verbatim row, run a similarity search against all articles in the linked law
- [ ] Use token-overlap or fuzzy match (rapidfuzz) — score threshold configurable, default 70
- [ ] If a better article is found, update the displayed article and show a small inline note: "Article auto-corrected from X to Y"
- [ ] If no candidate scores above threshold, fall back to US-010 logging
- [ ] Auto-correction logic lives in JS embedded in v30, with the lookup table pre-computed at build time and inlined as JSON

### US-010: Log warnings to a markdown file when auto-correct fails
As a developer, I want a markdown log of every analysis where verbatim is missing and auto-correct could not confidently pick an article so that I can manually review them.

**Acceptance Criteria:**
- [ ] `outputs/v30_unresolved_articles.md` is generated by the build step (a Python script that pre-computes the JSON lookup)
- [ ] Each entry shows: term, linked law, originally selected article, top 3 candidate articles with scores
- [ ] File is overwritten on each build with a timestamped header
- [ ] Empty file is not produced — if all analyses resolve, the file says "No unresolved articles."

## Functional Requirements
- FR-1: The verifier must run end-to-end with `python iterations/verify_lexicon.py` and exit non-zero on any mismatch
- FR-2: The verifier must accept `--fix` to also produce `v29-corrected.html`
- FR-3: All output artefacts (CSV, MD, HTML report) must be written to `outputs/` with a timestamp suffix
- FR-4: The v30 page must work as a self-contained file (no external network calls at runtime)
- FR-5: Verbatim highlighting must clear previous marks before applying new ones to avoid accumulation
- FR-6: Auto-correction must never silently change the displayed article — always show a visible note
- FR-7: Source Excel files are read-only inputs; the pipeline must never write to `~/Downloads`
- FR-8: All HTML interactivity must use `addEventListener` — no inline `onclick`
- FR-9: Tooltips and notes in v30 must use styled custom popups, not native `title` attributes

## Non-Goals
- Editing the source Excel files
- Modifying `digital_lexicon_v29.html` in place (only `v29-corrected.html` is written)
- Translating verbatim text or normalising languages
- Live-editing analyses inside the v30 UI
- Building a server-side API — everything runs locally as static files
- Supporting laws not present in the verbatim Excel

## Technical Considerations
- Reuse loaders/utilities from existing `iterations/audit_excel_correspondence.py` and `iterations/build_reference_lookup.py` rather than re-implementing
- Inspect both Excel files (sheet names, column headers, hierarchy) before coding the loader — do not infer from filename
- Both Excel files live in `~/Downloads/` and may move; the loader should accept paths as args with defaults pointing to current locations
- Pre-compute the verbatim lookup table at build time and embed as JSON in v30 to avoid runtime XLSX parsing in the browser
- For fuzzy article matching, prefer `rapidfuzz` over `fuzzywuzzy` (faster, no LGPL)
- Browser verification of v30 must use the `/browse` skill, not `mcp__claude-in-chrome__*`

## Success Metrics
- 100% of analyses in v29 either match the cross-checked Excel exactly or are flagged in the report
- 100% of analysis→article links in v30 either show a verbatim highlight or display the auto-correct note
- Verifier completes in under 30 seconds on the full corpus
- `outputs/v30_unresolved_articles.md` contains zero unresolved entries after one round of corrections

## Open Questions
- Should `v29-corrected.html` be promoted to replace v29, or kept as a separate review artefact only?
- For US-009, is 70 a sensible default fuzzy threshold, or should it be calibrated against a labelled sample first?
- Should the diff viewer (US-005) be committed to the repo or kept in `outputs/` as a build artefact?