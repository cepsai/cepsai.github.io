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
- **Drawer verbatim is rendered via `textContent`, not `innerHTML`** (`drawer-verbatim` element, around line 1966 of the v28 HTML). HTML markup placed inside any `verbatim` field of a law-blob will appear literally to the user. For exponents and other typography that must render as glyphs in the verbatim drawer, use Unicode characters (e.g. `²⁵`), not `<sup>` markup. Analysis cells and CEPS-notes themes/summary, by contrast, are rendered via `innerHTML` and accept HTML markup safely.
- **Exponent rendering pipeline (US-003)**: `build_v28.py` runs a final `apply_superscripts(html)` pass after all other swaps. Outside `<script>` blocks every form (`10^25`, `10**25`, `10(^25)`, Unicode `10²⁵`) becomes `10<sup>25</sup>` markup. Inside `<script>` blocks (CONCEPTS literal + `<script type="application/json">` law-blobs) only ASCII forms are converted, and they go to Unicode superscripts so the `textContent`-rendered drawer still shows proper glyphs. The pass is idempotent: existing `<sup>` markup and existing Unicode superscripts are never re-wrapped.

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

## 2026-04-28 - US-003 — Render all exponent notation as HTML superscript
- Catalogued every exponent occurrence in `digital_lexicon_v28.html`: 78 Unicode-superscript runs (`10²⁵`, `10²⁶`, `10²³`) and 33 ASCII forms — 31 `10^N` plus 2 parenthesised `10(^N)` (no `**` forms anywhere). 3 of the Unicode runs live in static HTML (AIA / SB 53 / RAISE Act law cards); the rest live in CONCEPTS data + law-blob JSON inside `<script>` blocks.
- Added `apply_superscripts(html)` to `build_v28.py` (alongside `_exponents_to_sup_html` and `_ascii_exp_to_unicode` helpers). The pass is invoked as the final transformation in `main()` so it sees the fully-assembled HTML after Home / Cards / Methodology swaps. Output: 3 static Unicode → `<sup>` rewrites + 33 script ASCII → Unicode rewrites; static-ASCII count is 0 because v26 didn't carry any plain ASCII exponents into the static HTML body.
- Verified rendering via `gstack /browse` against `python3 -m http.server 8765`:
  - Regulations page: `<sup>25</sup>` in the AIA card description, `<sup>26</sup>` in SB 53, `<sup>26</sup>` in RAISE Act — all three render as proper superscript glyphs and are scoped to the correct `<article class="law-card-v2">` parent (verified via `closest('.law-card-v2')` query).
  - Concepts → "Provider of GPAI models with systemic risk" analysis table: 10 Unicode-superscript exponents in the rendered tbody (from CONCEPTS analysis cells), zero ASCII forms.
  - Home page: still byte-clean (no exponents on Home but the build runs the same pipeline so future Home copy benefits automatically).
- Test suite: `python3 test_lexicon_v28.py` 6/6 PASS, `python3 -m pytest test_lexicon_v28.py -q` 6/6 PASS. Updated T3 to expect `<sup>` markup instead of literal `10²⁵` Unicode and added T6 (`test_exponents_render_as_superscript`) which asserts no ASCII forms remain anywhere and the three known static-HTML thresholds are `<sup>`-wrapped.
- Files changed: `iterations/build_v28.py` (added `re` import, exponent helpers, and final `apply_superscripts` step in `main`), `iterations/test_lexicon_v28.py` (T3 updated, T6 added, docstring updated), `iterations/digital_lexicon_v28.html` (rebuilt — 3 static `<sup>` + Unicode-superscripts in scripts), `final_tool.html` / `final_lexicon_tool.html` (mirrors), `.ralph-tui/progress.md` (this entry + two new Codebase Patterns at top).
- **Learnings:**
  - Patterns: see "Codebase Patterns" above (textContent vs innerHTML rendering paths, two-track exponent pipeline).
  - Gotchas: (a) the v27 HTML mixes ASCII (`10^25`) and Unicode (`10²⁵`) exponent forms within the same JSON law-blob, so a single regex pass that targets only one form leaves the other behind — always handle both. (b) The parenthesised form `10(^25)` shows up in `law-blob-eu-ai-act` (verbatim Article 51 quote) and is easy to miss if the regex only looks for `\d+\^\d+`. (c) `<sup>` inside a `verbatim` field would break the drawer because `drawer-verbatim` is set via `textContent`; the build pipeline therefore *cannot* universally swap to `<sup>` markup — it has to switch strategy at the `<script>` boundary. (d) `chain` JSON commands keep the browse session alive across calls — individual `$B js` calls were resetting `about:blank` between commands and dropping state. Use `chain` when verifying multi-step navigation.
---

