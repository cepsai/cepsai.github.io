# Ralph Progress Log

This file tracks progress across iterations. Agents update this file
after each iteration and it's included in prompts for context.

## Codebase Patterns (Study These First)

- **Build pipeline is post-processing-on-v26**: `iterations/build_v28.py` reads `digital_lexicon_v26.html` then applies a chain of in-place text fixes (terminology, limited-risk Provider, EU/US-state article links, superscripts) before writing v28. Each fix function is idempotent — anchors must match exactly once, and `if old in html` plus `elif new in html` handles re-runs.
- **CONCEPTS extraction**: the v28 HTML embeds the entire lexicon dataset as `const CONCEPTS = [...]` in a single literal. Parse it by scanning from `const CONCEPTS = [` to its matching `]`, respecting JSON string escapes. Helper at `iterations/audit_eu_links.py` and the verification script at `iterations/outputs/us006_browser_verify.py` both use this scanner.
- **Cell triple anchor rule**: when patching a specific cell that shares its `reference` string with other cells (e.g. `"(GL, (17))"` appears in multiple cells), anchor on the full `analysis + verbatim + reference` JSON triple. When `reference` is unique site-wide, anchor on it alone. Never anchor on dimension ids (e.g. `scope-1-0`) — those encode positional row order and shift if rows are added.
- **EU regulatory texts (5 in v28 scope)**: `eu-ai-act`, `eu-gpai-cop-copyright`, `eu-gpai-cop-transparency`, `eu-gpai-cop-safety`, `eu-guidelines-gpai-scope`. Two extra Commission Guidelines blobs (`eu-guidelines-ai-definition`, `eu-guidelines-prohibited`) live in the HTML but are out-of-Excel-scope per `v28_excel_inventory.md` §7 issue #1.

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

