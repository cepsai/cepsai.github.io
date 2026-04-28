# Ralph Progress Log

This file tracks progress across iterations. Agents update this file
after each iteration and it's included in prompts for context.

## Codebase Patterns (Study These First)

- **Excel reference for the lexicon lives at `/Users/robertpraas/Downloads/Cross-checked_AI terminology and taxonomy_analysis_final.xlsx`** (NOT in the project tree). It is the source of truth for terms, regulatory texts, article references, and terminology resolutions. See `iterations/v28_excel_inventory.md`.
- **Excel structure is sparse**: analysis sheets have header rows at row 1–2, attribute labels in column A, and article references inline in data cells. Continuation rows (no label in col A) extend the cell above — extraction must walk them, not assume one row per attribute.
- **Sheet name gotcha**: sheet 5 is `" High-risk AI system_ANALYSIS"` with a **leading space**. Always `sheet.strip()` when looking up by name.
- **Anchor-term pattern**: every U.S. state term has an EU-AIA "anchor" (e.g., Colorado "Developer" → "Provider of limited-risk AI systems"). The `Provider_Developer_Analysis` and `Deployer_Supplier_Analysis` sheets are 4 and 3 stacked sub-tables respectively, each defining one anchor → its U.S. equivalents. Without the anchor, "Developer"/"Deployer" appear ambiguously across multiple contexts.
- **CoP three-chapter routing**: Excel cites CoP CC (copyright), CoP TC (transparency), CoP SSC (safety/security) inline; v27 HTML splits these into three separate `law-blob`s (`eu-gpai-cop-copyright`, `eu-gpai-cop-transparency`, `eu-gpai-cop-safety`). When parsing inline citations, route by chapter prefix.
- **"12 regulatory frameworks" (per About sheet) vs Methodology's 13 rows**: the canonical count is 12 (Utah's SB 149 + SB 226 collapse to one Utah framework). v27 currently wires 15 blobs because it splits CoP into 3 and adds two extra Commission Guidelines (`eu-guidelines-ai-definition`, `eu-guidelines-prohibited`) that are NOT in Excel scope.
- **"Limited-risk" is not a defined AIA legal category** — it's a Commission classificatory label tied to Article 50 + Recital 132. Surface this caveat in the UI rather than treating it as a statutory term.

---

## 2026-04-28 - US-001 — Inventory the Excel reference and document expected mappings
- Read all 13 sheets of the Excel file directly via openpyxl (data_only=True) — no inference from filename.
- Echoed the structure back to the user (sheets, dimensions, sub-table layout) before producing the doc.
- Wrote `iterations/v28_excel_inventory.md` (~700 lines): the 12 regulatory texts, the 11 EU-AIA anchor terms with their U.S.-state equivalents, the per-text article references for every analysis sheet, and a 12-issue conflict register against v27 HTML.
- Files changed: `iterations/v28_excel_inventory.md` (new), `.ralph-tui/progress.md` (this entry).
- **Learnings:**
  - Patterns: see "Codebase Patterns" above (Excel layout, sheet-name gotcha, anchor terms, CoP chapter routing).
  - Gotchas: (a) v27 HTML adds two extra Commission Guidelines that are out of Excel scope — do not preserve as primary frameworks in v28; (b) v27 HTML is missing `law-blob`s for SB 25B-004 and SB 149 even though Excel lists them; (c) "Frontier model" is in the Excel cluster matrix as a standalone term but v27 does not surface it as its own term entry; (d) terminology decisions (e.g., Developer/Deployer for limited-risk) are *symmetrical* — Colorado and Texas both have "Developer" AND "Deployer", not one term doing double duty.
---

## 2026-04-28 - US-002 — Set up v28 scaffold from v27
- Created `iterations/build_v28.py` as a copy of `build_v27.py` with HTML_V27 → HTML_V28, docstring/version labels, and RuntimeError prefixes updated. XLSX path, transformations, and v26 starting input are unchanged.
- Created `iterations/test_lexicon_v28.py` as a copy of `test_lexicon_v27.py` with HTML path pointed to `digital_lexicon_v28.html`.
- Verified byte-equivalence: SHA-256 of `digital_lexicon_v28.html` matches `digital_lexicon_v27.html` (`735f39487bc8...`); the `final_tool.html` / `final_lexicon_tool.html` mirrors share the same hash.
- All 5 tests pass (`python3 test_lexicon_v28.py` → 5/5; `pytest -q` → `.....`).
- Files changed: `iterations/build_v28.py` (new), `iterations/test_lexicon_v28.py` (new), `iterations/digital_lexicon_v28.html` (build output, byte-identical to v27).
- **Learnings:**
  - The v27 `len(html)` print reports character count (3,123,682), not byte count — UTF-8 multi-byte chars (em-dash, curly quotes, ²⁵, ²⁶) push the on-disk size to 3,137,366 bytes. Don't compare by `print` output; use `wc -c` / `shasum`.
  - `shutil.copy2` to `final_tool.html` / `final_lexicon_tool.html` happens unconditionally in the v27 build pattern. v28 preserves this — for a scaffold release this is a no-op (byte-equivalent overwrite), but be aware future xx + 1 versions will overwrite the published mirrors on every run.
---

