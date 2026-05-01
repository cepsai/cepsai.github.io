# Ralph Progress Log

This file tracks progress across iterations. Agents update this file
after each iteration and it's included in prompts for context.

## Codebase Patterns (Study These First)

- **Reuse `build_reference_lookup.parse_atomic` for citation parsing.** It
  already maps things like `EU AI Act, Article 6(1)` / `Colorado SB 24-205,
  §6-1-1701` / `(GL, (17))` to canonical `(law_id, article_id)` tuples and
  knows about every law slug used in the project. Importing it from
  `iterations/` (after adding `ITER_DIR` to `sys.path`) avoids re-implementing
  the LAW_PATTERNS / SECTION_RE / ARTICLE_RE machinery in each new module.
- **Excel structure is heterogeneous — inspect each sheet, don't assume.**
  Verbatim sheets mix 4-col blocks (Risk, Substantial modification) and 5-col
  blocks (Provider, Deployer, GPAI, etc.). The jurisdiction header row is on
  row 1 in some sheets and row 2 in others (Risk, Incident, Substantial
  modification have an empty row 1). Detect the layout by locating the row
  with ≥2 jurisdiction-keyword cells (`EU`, `U.S. -`, `Colorado`, ...) and
  finding the `Reference` column inside each block to determine block width.
- **Analysis sheets group cells under a `Term` row in column A.** Multi-section
  sheets (Provider_Developer_Analysis, Deployer_Supplier_Analysis) repeat the
  Term row for each sub-concept. Walk every `Term`-labelled row and treat the
  immediately preceding row as the jurisdiction header to handle both single-
  and multi-section sheets uniformly. Continuation rows (col A blank, juris
  cols populated) belong to the previous dimension's text.
- **Always replace pandas NaN with Python None** at the loader boundary
  (`df.astype(object).where(df.notna(), None)`). The PRD explicitly forbids
  the literal string `"nan"` leaking through, and downstream `is None` checks
  break against `numpy.nan`. Note this also means callers must use `pd.isna`
  or `is None` rather than `== ""` for emptiness.
- **Preserve "NA" (Namibia) as a string** anywhere ISO codes might appear.
  Use a custom `_norm_str` that only treats truly empty / whitespace cells as
  None, never relying on `pd.read_*`'s default na_values which strips "NA".

---

## 2026-05-01 - US-001
- Implemented `iterations/load_lexicon_sources.py` exposing `load_analyses()`
  and `load_verbatim()`, returning normalised pandas DataFrames keyed by
  `(term, law_id, article_id)`.
- Added `iterations/test_load_lexicon_sources.py` (13 tests, all passing).
- Files changed/created:
  - `iterations/load_lexicon_sources.py` (new)
  - `iterations/test_load_lexicon_sources.py` (new)
- Validation:
  - `python iterations/load_lexicon_sources.py` runs and prints summary +
    5-row sample for both DataFrames (analyses: 356 rows, 28 unique terms,
    9 law_ids; verbatim: 255 rows, 16 unique terms, 10 law_ids).
  - `python -m pytest iterations/` — the 13 new tests pass; 2 pre-existing
    failures (`test_lexicon_v17.py::test_v17_static_structure`,
    `test_lexicon_v29.py::test_home_text_from_xlsx`) are unrelated to US-001
    and fail identically on `main` before this change.
  - `python iterations/audit_excel_correspondence.py` runs end-to-end and
    writes its markdown + CSV reports. Its exit code is `1` because of
    105 + 43 + 23 + 20 + 9 pre-existing v28 HTML ↔ Excel discrepancies that
    also exist before this change; that's the audit script's intended
    behaviour for v28 (the new loader doesn't touch v28's data path).
- **Learnings:**
  - The audit script's reuse of inline `(law_id, article_id)` parsing
    (via `parse_atomic`) is more reliable than mapping jurisdiction-header
    text to a default law: e.g. `California` resolves to SB 53 / SB 942 /
    AB 2013 only when the actual citation specifies. The loader uses the
    header-text fallback only when no parenthesised citation can be parsed.
  - openpyxl's `read_only=True` mode is materially faster for both files
    (~2s vs ~10s) and `wb.close()` releases the mmap promptly.
  - `df.astype(object).where(df.notna(), None)` is the cleanest way to
    swap NaN for None across all columns at once. `df.fillna(None)` does
    not work because pandas re-coerces None back to NaN when the dtype is
    numeric.
---

