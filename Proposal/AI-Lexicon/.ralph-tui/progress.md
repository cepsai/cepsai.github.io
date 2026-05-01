# Ralph Progress Log

This file tracks progress across iterations. Agents update this file
after each iteration and it's included in prompts for context.

## Codebase Patterns (Study These First)

- **The v29 (and v28) HTML embeds all data as a `const CONCEPTS = [...]`
  JSON literal inside a `<script>` tag.** Use BeautifulSoup to find the
  right `<script>` element (iterate `soup.find_all("script")` and pick the
  one whose body contains `"const CONCEPTS = "`), then a small depth-tracking
  scanner over the script body to balance `[`/`]` (skipping `[`/`]` that
  appear inside `"..."` JSON strings, and respecting `\\` escapes). The
  enclosed span parses cleanly with `json.loads` — the build script emits
  `json.dumps` output, so no JS-to-JSON translation is needed.
- **Concept JSON shape:** `concept.sub_concepts[].dimensions[].cells[jid]`
  with `cell.analysis`, `cell.verbatim`, `cell.reference`. Per-jurisdiction
  display terms live in `sub_concept.jurisdictions[jid].term`; fall back to
  `sub_concept.title` when missing. The same dim-label can appear twice
  (e.g. duplicated "Term" rows), so prefer `dim.id` for cell lookup.
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
- **Excel sheet names are truncated to ~31 chars.** Two analysis sheets in
  the cross-checked workbook (`GPAI_Frontier_Foundation_Analys`,
  `GPAI system_Generative AI_ANALY`) lose the trailing "is" of "ANALYSIS",
  so a substring filter for `"analysis"` silently drops them. Match against
  `"_analy"` (with underscore to avoid catching `"Methodology"`) instead, or
  list the analysis sheets explicitly.
- **Map Excel rows to HTML cells via `(sheet, term, jurisdiction_header)`.**
  The Excel `term` is jurisdiction-specific (per-column value of the section's
  Term row), so the same `term` ("Developer") legitimately means different
  HTML sub-concepts depending on which `(sheet, jurisdiction_header)` it
  appears under. For multi-sub sheets (Provider/Deployer) the term is what
  disambiguates sections; for single-sub sheets `(sheet, jurisdiction_header)`
  alone is enough. See `verify_lexicon.SINGLE_SUB_SHEETS` and
  `verify_lexicon.MULTI_SUB_CELLS` for the canonical lookup tables — they
  isolate the cross-source identity in one place.

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

## 2026-05-01 - US-002
- Implemented `iterations/parse_v29.py` exposing `parse_v29()` which returns a
  pandas DataFrame keyed by `(term, analysis_text, law_id, article_id)` (plus
  `concept_id`, `sub_concept_id`, `jurisdiction`, `dim_id`, `dim_label`,
  `reference` for downstream verification).
- The parser uses BeautifulSoup (`html.parser`) to locate the `<script>`
  element that defines `const CONCEPTS = ...`, then a depth-tracking scanner
  to extract the JSON-literal span and `json.loads` it directly. Cells whose
  `reference` field has multiple semicolon-joined atomic citations are
  exploded into one row per `(law_id, article_id)`. Cells with an analysis
  but no parseable reference still emit a single None-law row.
- Added `iterations/test_parse_v29.py` (15 tests, all passing). Tests cover:
  pure helpers, BeautifulSoup-based extraction (including `[` inside JSON
  strings), schema, no `"nan"` strings leaking, exact analysis-text
  round-trip, multi-article fan-out, and known v29 spot checks.
- Files changed/created:
  - `iterations/parse_v29.py` (new)
  - `iterations/test_parse_v29.py` (new)
- Validation:
  - `python3 iterations/parse_v29.py` runs end-to-end and reports
    563 rows, 406 unique analyses, 13 unique laws referenced, 29 unique
    terms, 415 rows with article_id.
  - `python3 -m pytest iterations/` — 121 passed, 2 failures
    (`test_lexicon_v17.py::test_v17_static_structure`,
    `test_lexicon_v29.py::test_home_text_from_xlsx`) are the same pre-
    existing failures noted in US-001 and unrelated to US-002.
  - `python3 iterations/audit_excel_correspondence.py` runs end-to-end and
    writes its markdown + CSV reports. Exit code is 1 because of the same
    pre-existing v28 HTML ↔ Excel discrepancies that existed before
    (same as US-001's run — verified by stashing this branch's changes and
    re-running).
- **Learnings:**
  - The legacy audit script's manual JSON extractor (depth-tracking over the
    raw HTML text) is correct, but BeautifulSoup is a stronger contract for
    new code — it survives reorderings of `<script>` tags and ignores
    HTML-level attributes that a raw `text.find` would be sensitive to. The
    depth scanner still needs to live on top of bs4's script-body string,
    because the JSON literal is embedded in a wider JS file (other top-level
    statements follow the `]`).
  - Inside `_explode_reference`, dedupe `(law, anchor)` per cell — otherwise
    references like `"AIA Article 6(1), (2)"` (article 6, paragraphs 1 and 2)
    that are both written as one `Article 6` atomic citation by `parse_atomic`
    plus an article 6 paragraph variant don't generate phantom duplicate
    rows. parse_atomic's article match collapses paragraph tails into a
    single article anchor anyway, so the dedupe is mostly belt-and-braces.
  - `BeautifulSoup` `script.string` returns `None` when the script element
    has multiple text-node children (rare but possible if there's a comment
    inside). Falling back to `script.get_text()` covers that case.
---

## 2026-05-01 - US-003
- Implemented `iterations/verify_lexicon.py` exposing `verify_lexicon()` which
  outer-joins `parse_v29()` against `load_analyses()` and emits one row per
  `(concept_id, sub_concept_id, dim_label, jid)` cell with a `status` of
  `match`, `mismatch`, `missing_in_html`, or `missing_in_excel`. The CLI
  writes `outputs/lexicon_verification_<timestamp>.csv` and prints status
  counts.
- Comparison is exact-text after whitespace normalisation
  (`re.sub(r"\s+", " ", text).strip()`); mismatches keep both bodies for
  side-by-side review.
- Static lookup tables `SINGLE_SUB_SHEETS` and `MULTI_SUB_CELLS` map
  `(sheet, term, jurisdiction_header)` → `(concept_id, sub_concept_id, jid)`
  so the verifier joins Excel rows to HTML cells even when the displayed
  term differs ("GPAI systems" vs "general-purpose AI systems").
- Small fix to `iterations/load_lexicon_sources.py`: the sheet filter
  `"analysis" not in sn.lower()` silently dropped the two GPAI analysis
  sheets whose names Excel truncated at 31 chars
  (`GPAI_Frontier_Foundation_Analys`, `GPAI system_Generative AI_ANALY`).
  Replaced with an `"_analy"`-aware filter so all 8 analysis sheets are
  loaded; analyses row count goes from 356 → 377.
- Files changed/created:
  - `iterations/verify_lexicon.py` (new)
  - `iterations/test_verify_lexicon.py` (new, 18 tests)
  - `iterations/load_lexicon_sources.py` (sheet-filter fix)
- Validation:
  - `python3 iterations/verify_lexicon.py` runs end-to-end. On the current
    v29 + cross-checked Excel: 410 cells verified — 263 match, 61 mismatch,
    37 missing_in_html, 49 missing_in_excel.
  - `python3 -m pytest iterations/` — 137 passed, 2 failures
    (`test_lexicon_v17.py::test_v17_static_structure`,
    `test_lexicon_v29.py::test_home_text_from_xlsx`) are the same pre-
    existing failures from US-001/US-002, unrelated to US-003.
  - `python3 iterations/audit_excel_correspondence.py` runs end-to-end and
    writes its markdown + CSV reports (same exit code 1 as before, driven
    by pre-existing v28 discrepancies).
- **Learnings:**
  - The loader bug above (truncated sheet filter) was invisible until the
    verifier joined Excel against HTML and reported every GPAI analysis as
    "missing_in_excel". Cross-source verification is a good way to surface
    silent loader gaps.
  - Section-header rows leak into the previous section's `dim_label` via the
    loader's `_walk_analysis_section` (the row immediately before a new
    Term row in a multi-sub sheet contains the next section's header in
    column A, and the previous section's `_walk_analysis_section` treats
    it as a dim_label). These show up as `missing_in_html` rows in the
    verifier with dim_labels like `"Deployer / supplier of high-risk AI
    systems"` — they're loader artefacts, not real cells. Out of scope for
    US-003 to fix; flagged here so US-004 can decide whether to filter them.
  - Mismatches in the v29 vs cross-checked Excel comparison reveal real
    drift: the EU `Transparency` analysis for `deployer-of-high-risk-ai-
    systems` has the Excel side carrying additional sentences that the
    HTML version dropped — exactly the kind of finding the verifier exists
    to surface.
---

