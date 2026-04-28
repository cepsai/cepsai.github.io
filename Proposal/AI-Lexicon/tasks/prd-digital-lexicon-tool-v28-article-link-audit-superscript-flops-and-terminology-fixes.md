# PRD: Digital Lexicon Tool v28 — Article Link Audit, Superscript FLOPs, and Terminology Fixes

## Overview
v28 of the Digital AI Lexicon tool fixes three classes of issues found in v27: (1) incorrect article references in the regulatory pop-ups across all 12 regulatory texts (EU + US federal + US state laws), (2) inconsistent rendering of exponent notation (FLOPs thresholds, parameter counts) which should appear as proper HTML superscript, and (3) terminology inconsistencies in the opening category table. The single source of truth for all article→text mappings and terminology decisions is `/Users/robertpraas/Downloads/Cross-checked_AI terminology and taxonomy_analysis_final.xlsx`.

## Goals
- Every article reference in every table pop-up links to the correct regulatory text passage, verified against the cross-checked Excel reference.
- All exponent notation (10^25, 10^23, parameter counts, etc.) renders as HTML superscript across the entire tool.
- The opening category table uses the agreed labels: "provider of limited-risk AI systems" and "Developer of limited-risk AI systems" (lowercase "provider", capitalized "Developer" — per user's spec; verify "Developer" vs "Deployer" against the Excel before committing).
- The limited-risk AI systems provider table content matches the corrected Excel data.
- v28 lives in `iterations/` per project convention and ships with passing tests + browser verification.

## Quality Gates

These commands must pass for every user story:
- `python iterations/test_lexicon_v28.py` — pytest suite mirroring the v27 test pattern
- `pnpm typecheck` is N/A (Python + HTML project); skip

For UI stories, also include:
- Verify in browser using `/browse` skill — open `iterations/digital_lexicon_v28.html`, click through the affected tables, confirm pop-ups, terminology, and superscript rendering visually

## User Stories

### US-001: Inventory the Excel reference and document expected mappings
As a developer, I want a single document listing every regulatory text covered by the tool, every article reference per term, and every terminology decision so that downstream stories can be verified against a checked baseline.

**Acceptance Criteria:**
- [ ] Open `/Users/robertpraas/Downloads/Cross-checked_AI terminology and taxonomy_analysis_final.xlsx` and inspect every sheet; do not infer from filename
- [ ] Produce `iterations/v28_excel_inventory.md` listing: (a) the 12 regulatory texts the tool covers, (b) each term/row with its expected article references per regulatory text, (c) terminology resolutions (including "Developer" vs "Deployer" for limited-risk AI systems based on what the Excel actually says)
- [ ] Echo back the inventory structure to the user (sheets, columns, row counts) before proceeding to fixes
- [ ] Flag any rows where the Excel reference is ambiguous or conflicts with v27 HTML

### US-002: Set up v28 scaffold from v27
As a developer, I want `build_v28.py` and `digital_lexicon_v28.html` created in `iterations/` so that subsequent fixes have a working baseline to modify.

**Acceptance Criteria:**
- [ ] `iterations/build_v28.py` created by copying `iterations/build_v27.py`
- [ ] Running `python iterations/build_v28.py` produces `iterations/digital_lexicon_v28.html` byte-equivalent to the v27 output (no behavior changes yet)
- [ ] `iterations/test_lexicon_v28.py` created by copying the v27 test file with paths updated to v28
- [ ] All tests pass on the unchanged scaffold

### US-003: Render all exponent notation as HTML superscript
As a user reading the lexicon, I want exponent notation (FLOPs thresholds, parameter counts, any other powers) to render as proper superscript so that the values are unambiguous and look professional.

**Acceptance Criteria:**
- [ ] Identify every occurrence of exponent notation in `build_v28.py` source data (training compute thresholds like 10^25, 10^23; parameter counts; any other powers)
- [ ] Replace ASCII forms (e.g., `10^25`, `10**25`, `10²⁵`, plain "10 to the 25th") with HTML `<sup>` markup in the rendered output
- [ ] Superscript rendering verified in browser across at least 3 different tables and the opening overview table
- [ ] No regression in non-exponent numeric content

### US-004: Correct opening category table terminology
As a user, I want the opening category table to label the limited-risk roles consistently with CEPS' chosen terminology so that the categorization is clear at a glance.

**Acceptance Criteria:**
- [ ] In the opening category table only (per user spec 4C), the limited-risk row labels read "provider of limited-risk AI systems" and "Developer of limited-risk AI systems" — exact capitalization as stated, unless the Excel reference dictates otherwise
- [ ] If the Excel reference says "Deployer" rather than "Developer", flag this to the user before changing and document the resolution
- [ ] Detail tables (the dedicated provider/deployer tables) are NOT renamed in this story
- [ ] Visual check in browser confirms the opening table reads correctly

### US-005: Fix the "provider of limited-risk AI systems" table content
As a user, I want the limited-risk-AI-systems provider table to reflect the corrected content from the Excel reference so that the listed obligations and articles are accurate.

**Acceptance Criteria:**
- [ ] Diff the v27 limited-risk provider table against the Excel reference; document each discrepancy
- [ ] Apply all corrections (rows, articles, descriptions) to `build_v28.py`
- [ ] Pop-ups for every article in this table link to the correct regulatory text passage
- [ ] Browser verification: every article cell in this table opens the right pop-up

### US-006: Audit article links — EU regulatory texts
As a user, I want every article reference across all tables to open the correct passage from the cited EU regulatory text (AI Act, GDPR, DSA, DMA, and any other EU text covered by the tool).

**Acceptance Criteria:**
- [ ] Enumerate every EU regulatory text covered by v27 (per the Excel inventory from US-001)
- [ ] For each EU text, verify every article reference in every table pop-up against the Excel reference
- [ ] Fix every mismatch in `build_v28.py`
- [ ] Browser verification: spot-check at least 5 article links per EU text, confirming pop-up content matches the cited article

### US-007: Audit article links — US federal regulatory texts
As a user, I want every article reference to US federal regulatory texts to open the correct passage so that US-context citations are reliable.

**Acceptance Criteria:**
- [ ] Enumerate every US federal text covered by v27 (per the Excel inventory)
- [ ] Verify every article reference against the Excel reference
- [ ] Fix every mismatch in `build_v28.py`
- [ ] Browser verification: spot-check at least 3 article links per US federal text

### US-008: Audit article links — US state laws
As a user, I want every article reference to US state laws to open the correct passage so that state-level citations are reliable.

**Acceptance Criteria:**
- [ ] Enumerate every US state law covered by v27 (per the Excel inventory — e.g., Colorado AI Act, California laws, etc.)
- [ ] Verify every article reference against the Excel reference
- [ ] Fix every mismatch in `build_v28.py`
- [ ] Browser verification: spot-check at least 3 article links per state law

### US-009: Audit article links — remaining regulatory texts
As a user, I want any regulatory texts not covered by US-006/007/008 (international, sectoral, or other) to also have correct article links so that the audit covers all 12 texts in scope.

**Acceptance Criteria:**
- [ ] Confirm every regulatory text from the Excel inventory has been audited (US-006 + US-007 + US-008 + this story = 12 total)
- [ ] Fix any remaining mismatches in `build_v28.py`
- [ ] Browser verification: spot-check at least 3 article links per remaining text

### US-010: Update tests and run full quality gate
As a developer, I want the test suite extended to cover the v28-specific invariants so that future regressions are caught automatically.

**Acceptance Criteria:**
- [ ] Add tests asserting every `<sup>` superscript renders for known exponent values
- [ ] Add tests asserting opening-table labels match the agreed strings
- [ ] Add a smoke test that every article reference in the rendered HTML resolves to a non-empty pop-up content block
- [ ] `python iterations/test_lexicon_v28.py` passes
- [ ] Final browser verification via `/browse`: walk through the lexicon, click through all 12 regulatory tables, confirm no broken pop-ups

## Functional Requirements
- FR-1: The build script must regenerate the HTML deterministically from source data; no manual HTML edits to the rendered file.
- FR-2: Every article reference rendered in a table must, when clicked, open a pop-up containing the text of that exact article from the cited regulatory source.
- FR-3: Every exponent notation in the rendered HTML must use `<sup>` tags (no ASCII `^`, no `**`, no Unicode-superscript fallbacks).
- FR-4: The opening category table must use the labels specified in US-004; detail tables remain unchanged.
- FR-5: The Excel reference at `/Users/robertpraas/Downloads/Cross-checked_AI terminology and taxonomy_analysis_final.xlsx` is authoritative — when in doubt, defer to it and flag conflicts.
- FR-6: All v28 artifacts (`build_v28.py`, `digital_lexicon_v28.html`, `test_lexicon_v28.py`, `v28_excel_inventory.md`) live in `iterations/`.

## Non-Goals
- No changes to the tool's overall layout, navigation, or styling beyond what's needed for superscript rendering.
- No new regulatory texts added in v28 — this is a correctness pass on existing content only.
- No changes to detail tables' terminology (only the opening category table is renamed).
- No propagation to `final_tool.html` or `final_lexicon_tool.html` in this iteration (parent-folder files left untouched).
- No system-theme or accessibility refactor beyond what's already in v27.

## Technical Considerations
- The project follows a strict iterations convention (see `iterations/CLEAN_BUILD_PLAN.md` and `iterations/LESSONS.md`); v28 must mirror v27's structure.
- `openpyxl` or `pandas.read_excel` will be needed to load the cross-checked Excel; verify which is already used in adjacent build scripts.
- Pop-up content is likely embedded as data structures in `build_v27.py` rather than fetched at runtime — locate and modify the source data, not the rendered HTML.
- Use event delegation / `addEventListener` for any new JS hooks; do NOT use inline `onclick` (per project standard).
- Use styled custom popups, not native `title` attributes (per project standard).

## Success Metrics
- 100% of article references across all 12 regulatory texts verified against the Excel reference.
- Zero exponent values rendered without `<sup>` markup.
- All tests in `iterations/test_lexicon_v28.py` pass.
- Manual browser walkthrough surfaces zero broken pop-ups or incorrect article texts.

## Open Questions
- "Developer" vs "Deployer" for the limited-risk role label in the opening table — needs to be resolved against the Excel reference in US-001 and confirmed with the user before US-004 ships.
- The user mentioned "minor updates" beyond the three named issues — these should be enumerated during US-001's Excel walkthrough and either folded into the existing stories or surfaced as a follow-up list.
- Should `final_tool.html` / `final_lexicon_tool.html` in the parent folder be updated in a follow-up iteration once v28 is verified? (Out of scope for v28 per user spec 5A.)