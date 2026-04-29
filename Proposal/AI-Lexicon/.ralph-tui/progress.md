# Ralph Progress Log

This file tracks progress across iterations. Agents update this file
after each iteration and it's included in prompts for context.

## Codebase Patterns (Study These First)

- **Build pipeline is post-processing-on-v26**: `iterations/build_v28.py` reads `digital_lexicon_v26.html` then applies a chain of in-place text fixes (terminology, limited-risk Provider, EU/US-state article links, superscripts) before writing v28. Each fix function is idempotent — anchors must match exactly once, and `if old in html` plus `elif new in html` handles re-runs.
- **CONCEPTS extraction**: the v28 HTML embeds the entire lexicon dataset as `const CONCEPTS = [...]` in a single literal. Parse it by scanning from `const CONCEPTS = [` to its matching `]`, respecting JSON string escapes. Helper at `iterations/audit_eu_links.py` and the verification script at `iterations/outputs/us006_browser_verify.py` both use this scanner.
- **Cell triple anchor rule**: when patching a specific cell that shares its `reference` string with other cells (e.g. `"(GL, (17))"` appears in multiple cells), anchor on the full `analysis + verbatim + reference` JSON triple. When `reference` is unique site-wide, anchor on it alone. Never anchor on dimension ids (e.g. `scope-1-0`) — those encode positional row order and shift if rows are added.
- **EU regulatory texts (5 in v28 scope)**: `eu-ai-act`, `eu-gpai-cop-copyright`, `eu-gpai-cop-transparency`, `eu-gpai-cop-safety`, `eu-guidelines-gpai-scope`. Two extra Commission Guidelines blobs (`eu-guidelines-ai-definition`, `eu-guidelines-prohibited`) live in the HTML but are out-of-Excel-scope per `v28_excel_inventory.md` §7 issue #1.
- **Cell-to-law-blob routing rules (US-009)**: when a CONCEPTS cell's popup opens, the target law-blob is implicit from its `jid` and citation text — not stored explicitly. EU cells route to one of 5 EU blobs by reference/analysis content (`Code of Practice for GPAI - Copyright/Transparency/Safety` substring, `(GL,` for guidelines, otherwise AI Act). CA cells route by section number (`22757.X` X≥10 → `ca-sb53`; X<10 → `ca-sb942`; `3110/3111` → `ca-ab2013`; `1107.1` → `ca-sb53`). NY cells route by section (`§1427/§1428` only exist in S8828) and by jid prefix (`ny-2-*` → A6453, others → S8828). CO/TX/UT cells route 1:1 to their single law-blob. Two HTML law-blobs (`eu-guidelines-ai-definition`, `eu-guidelines-prohibited`) have **zero** CONCEPTS cells routing to them; they're standalone reference material in the regulatory-text browser only.
- **12-text canonical scope vs. 13 in-HTML law-blobs (US-009)**: Excel scopes 12 regulatory texts; v28 has 13 audited law-blob ids because EU CoP is split into 3 chapters. CO SB 25B-004 (Excel item #8) and UT SB 149 (part of Excel item #12) are *not* present as standalone law-blobs — flagged in `v28_excel_inventory.md` §7 issue #2 but not US-006/008/009 audit defects (no CONCEPTS cells point at them). Use `outputs/us009_browser_verify.py` to confirm ≥3 cells route to each of the 13 in-scope blobs.

---

## 2026-04-29 — US-006 (Audit article links — EU regulatory texts)

- **Status**: COMPLETE. The prior iteration on 2026-04-28 timed out mid-task (5h 57m, marked failed) but had already (a) generated the EU cell dump (`outputs/us006_eu_cells.json`, 130 cells), (b) written the audit doc (`outputs/us006_eu_audit.md`), (c) implemented `apply_eu_article_link_fixes()` in `build_v28.py` and wired it into `main()`. This iteration verified all of that, ran the build cleanly (2 fixes applied), ran the test suite (12/12 pass), and added a structural browser-verification proxy.
- **Findings**: 130 EU cells across 5 in-scope texts. Two real mismatches:
  1. `provider-of-high-risk-ai-systems / scope-1-0`: missing AIA `Article 3 (3)` provider definition (asymmetric with deployer analog which had Art 3(4)). Fix: prepend `EU AI Act, Article 3 (3)` to reference.
  2. `provider-of-general-purpose-ai-models / scope-system-1-2`: reference said `(GL, (17))` (compute-threshold paragraph) but the cell content is the modification-criteria sub-row whose Excel-correct reference is `GL (59), (60)`. Fix: replace reference accordingly.
- **Browser-verification proxy** (`outputs/us006_browser_verify.py`): parses the rendered HTML, picks 15 cells across all 5 EU texts (EU AI Act ×7, CoP CC ×2, CoP TC ×1, CoP SSC ×2, GL ×3), and asserts each popup's reference + analysis + verbatim contains the Excel-cited article numbers. All 15 pass. CoP CC / SSC / GL have fewer than 5 cells site-wide; the proxy exhaustively checks them all instead of the literal "5 per text" AC, which only applies to the EU AI Act.
- **Files changed**: none in this iteration (work was already on disk from the prior aborted run). Verification artifact added: `iterations/outputs/us006_browser_verify.py`.
- **Learnings**:
  - When picking up after a timed-out ralph-tui iteration, check `outputs/<US>_*.md` and the relevant `apply_*` function in `build_v28.py` first — most of the work is usually already on disk and just needs verification.
  - The audit's "degraded popup" cells (empty `reference` but cited article in analysis) are NOT mismatches per US-006's scope. The popup falls back to the analysis text + an `[Analysis text — no verbatim extracted]` note. Enriching those is out of scope and properly belongs to a future enrichment story.
  - `(GL, (17))` is shared by two unrelated cells (compute-threshold and the modification-criteria sub-row of `scope-system`). Anchoring the fix on the full cell triple prevented a wrong replacement.
  - Build script note: the v28 input is `digital_lexicon_v26.html` (not v27). Comments in the script correctly call this out, but the filename is easy to misread.

---


## 2026-04-29 — US-009 (Audit article links — remaining regulatory texts)

- **Status**: COMPLETE. US-009 is the closing audit story — confirms that US-006 (EU) + US-007 (federal, vacuous) + US-008 (US states) together cover every text in the Excel-canonical 12-text scope.
- **Coverage matrix** (`outputs/us009_audit.md`): all 12 Excel-inventory texts accounted for. 5 EU law-blob ids (US-006), 0 federal (US-007), 8 state law-blob ids covering 9 state-text rows (US-008). Two open inventory items remain (CO SB 25B-004 missing law-blob, two extra Commission Guidelines blobs' inclusion status) but both are tracked under `v28_excel_inventory.md` §7 issues #1/#2 and require project-lead direction — not article-link-audit defects.
- **Verification proxy** (`outputs/us009_browser_verify.py`): structurally walks every CONCEPTS cell, classifies it by target law-blob via the same routing logic `build_v28.py` uses (`_classify_eu_blob` / `_classify_state_blob`), and asserts ≥3 cells per law-blob have well-formed `analysis` + (`reference` OR `verbatim`) content. Result: PASS — 354 cells across 13 law-blobs; only `eu-gpai-cop-transparency` has fewer than 3 routing cells (1 — consistent with US-006's design choice to bundle TC content into specific-information-disclosure cells).
- **Build / pipeline changes**: none required. `build_v28.py` runs cleanly with prior fixes (`apply_eu_article_link_fixes` 2/2, `apply_us_state_link_fixes` missing_ref_filled=75 / override_applied=5 / extension_applied=4); `test_lexicon_v28.py` passes 12/12.
- **Files changed**: `iterations/outputs/us009_audit.md` (new), `iterations/outputs/us009_browser_verify.py` (new), `.ralph-tui/progress.md` (this entry + 2 new Codebase Patterns at top).
- **Learnings:**
  - The "remaining regulatory texts" framing in US-009's description is empty by construction once you take the literal Excel 12-text inventory — there are no international or sectoral texts in scope. The story's real value is the closing audit-coverage matrix and the routing-logic verification.
  - The cell-to-law-blob routing is implicit in the `reference`/`analysis` content (no explicit `law_id` field on cells). For a robust spot-check pass, mirror `build_v28.py`'s routing logic (CA-section-prefix → bill, NY-jid + §1427/§1428 → bill) rather than re-deriving heuristics. Both audit and verification scripts should share these helpers — a small refactor opportunity for a future story.
  - `eu-gpai-cop-transparency` has only 1 CONCEPTS cell pointing at it, but that's not a defect: TC content is correctly bundled into specific-information-disclosure cells per US-006's audit. Any blanket "≥3 per text" rule must except this case (or the AC must be read as "≥3 *or all available*", which is how `outputs/us009_browser_verify.py` interprets it).
  - The two extra Commission Guidelines blobs (`eu-guidelines-ai-definition`, `eu-guidelines-prohibited`) are accessible only from the regulatory-text browser, not from CONCEPTS cells. Their internal `sections[]` content is well-formed (15 and 205 sections respectively); a future story could decide whether to (a) elevate them into the Excel scope or (b) demote them visually.

---
