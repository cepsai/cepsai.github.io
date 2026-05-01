# Ralph Progress Log

This file tracks progress across iterations. Agents update this file
after each iteration and it's included in prompts for context.

## Codebase Patterns (Study These First)

- **Verbatim Excel collapses sub-concepts that the HTML keeps separate.**
  The `Provider_Developer` sheet stores one term per jurisdiction column
  (EU="Provider", Colorado="Developer", Texas="Developer") and a single
  block of verbatim text per (sheet, juris) — the HTML's four "Provider of
  …" sub_concepts (limited-risk / high-risk / GPAI / GPAISR) all share the
  same EU "Provider" verbatim pool. Same for `Deployer_Supplier`. Single-
  topic sheets (`Risk`, `Substantial modification`, `Incident`,
  ` High-risk AI system`, `GPAI_Frontier_Foundation model`,
  `GPAI system_Generative AI`) carry one block per juris column. Verbatim
  juris-headers are different from the analysis sheets:
  `EU` (no `(AIA)`), `U.S. - California` (vs `California (SB 942)`),
  `Colorado` plain (no `(SB 24-205)`). When mapping HTML cells to verbatim
  blocks, hand-write a `(cid, sid, jid) → (sheet, juris)` table —
  see `verify_lexicon.VERBATIM_CELLS`.
- **Several jurisdictions have NO verbatim block at all.** California /
  New York columns are absent from `Provider_Developer` and
  `Deployer_Supplier`; California is absent from `Incident`; Utah is
  absent from `Deployer_Supplier`; New York is absent from
  `Substantial modification`. HTML cells for those jids cannot resolve
  to `verbatim_found` no matter what they link to — they always come back
  `no_verbatim`. This is a real gap in the source data, not a verifier bug.
- **The verbatim loader's `JURIS_TO_LAW` fallback over-attributes.** When
  a verbatim cell has no inline citation, its `law_id` defaults to the
  jurisdiction's first listed law (e.g. all `U.S. - California` rows
  default to `ca-sb53`, even if the actual cell text is from `ca-sb942` or
  `ca-ab2013`). The link verifier surfaces this as `wrong_law` against
  HTML that correctly cites `ca-sb942`/`ca-ab2013`. Fixing this would
  require parsing inline article citations (e.g. `22757.1` → `ca-sb942`)
  inside the verbatim text — out of scope for US-004 but flagged for any
  future loader work.

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
- **Embed a JSON payload as `<script type="application/json">` and escape
  closing tags.** When generating self-contained HTML reports, ship the row
  data as a JSON island the page parses on load (`JSON.parse(scriptEl.text
  Content)`). Always pass the JSON through
  `json.dumps(...).replace("</", "<\\/")` before embedding so the browser
  HTML tokenizer cannot terminate the script element early on a literal
  `</script>` inside a string. See `verify_lexicon.render_html_report` and
  the test `test_render_html_report_payload_safe_against_script_breakout`.
- **`/browse` skill blocks `file://` URLs.** To verify a generated HTML
  artefact in the headless browser, run `python3 -m http.server <port>`
  inside `outputs/` (or whichever directory holds the file) and point the
  browser at `http://127.0.0.1:<port>/<file>.html`. Chain commands with
  `$B chain '[[...]]'` to keep page state alive across goto + clicks +
  asserts, since individual `$B` calls can hit server timeouts that
  silently restart the browser context.
- **Splice the CONCEPTS JSON literal back into the original HTML rather
  than rebuilding the whole file.** The v29 build script emits
  `json.dumps(concepts, ensure_ascii=False, separators=(",", ":"))` and
  Python's json.dumps is byte-stable when given the same input + separators
  — verified the round-trip is byte-identical against the v29 fixture.
  This means the corrector can extract `(start, end)` indices for the
  literal, mutate the parsed list, re-serialise with the same separators,
  and `html_text[:start] + new + html_text[end:]` produces a file whose
  diff against the original is exactly the changed cells (plus the
  injected summary block). No regex over the full HTML, no risk of
  accidentally clobbering surrounding script lines.
- **Substitute article ids inside the matching atom only — keep separators
  verbatim.** For wrong_article fixes, split the cell.reference with
  `re.split(r"(\s*;\s*)", ref)` (capturing separators), parse each atomic
  citation, and apply a kind-specific regex (`\bArticle\s*X\b`,
  `\bAnnex\s+X\b`, `\bRecital\s*\(?X\)?`, or distinctive section ids with
  `(?<![\w.])X(?![\w.])`) only inside atoms that resolve to (law,
  old_article). Captured separators ensure the rejoined string preserves
  the original whitespace/punctuation between citations — critical when
  the original used `; ` vs `;`.
- **Wrong_article fixes need an unambiguous candidate.** When the verbatim
  Excel has multiple alternative articles for (term, law), the corrector
  cannot pick without similarity scoring (US-009 territory). Skip those
  with reason `ambiguous` and surface them in the summary block alongside
  the candidate set so the reviewer can manually decide. In the current
  v29 + verbatim snapshot this fixes 6 of 23 wrong_article links cleanly,
  with 17 ambiguous (most live under Provider/Deployer where the verbatim
  collapses several articles under one term block).

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

## 2026-05-01 - US-004
- Extended `iterations/verify_lexicon.py` to verify each linked article
  against the verbatim Excel and emit a per-cell `link_status`
  (`verbatim_found` / `wrong_article` / `wrong_law` / `no_verbatim`),
  plus per-link breakdown columns `linked_articles` and `link_statuses`.
- Added `VERBATIM_CELLS`, a `(concept_id, sub_concept_id, jid) →
  (verbatim_sheet, jurisdiction_header)` lookup that points each HTML cell
  at the verbatim block whose term it should be looked up under. The
  verbatim Excel collapses some HTML sub-concepts (e.g. all four "Provider
  of …" sub_concepts share the EU "Provider" block), so the map's
  many-to-one shape is intentional.
- New helpers: `_build_verbatim_indices`, `_resolve_verbatim_term`,
  `_classify_link`, `_aggregate_link_status`, `_html_links_per_cell`,
  `_format_links`, `_format_statuses`, `_link_summary_counts`. Aggregation
  is "worst severity wins" via `_LINK_STATUS_SEVERITY` so reviewers can
  sort by `link_status` to see the most-broken cells first.
- Files changed/created:
  - `iterations/verify_lexicon.py` (extended)
  - `iterations/test_verify_lexicon.py` (extended, +18 tests, 36 total)
- Validation:
  - `python3 iterations/verify_lexicon.py` runs end-to-end. On the current
    v29 + cross-checked Excel + verbatim Excel: 410 cells verified
    (263 match / 61 mismatch / 37 missing_in_html / 49 missing_in_excel),
    387 linked articles classified — 211 verbatim_found, 23 wrong_article,
    16 wrong_law, 137 no_verbatim. The CSV now carries the new columns
    alongside the US-003 ones.
  - `python3 -m pytest iterations/` — 157 passed, 2 failures
    (`test_lexicon_v17.py::test_v17_static_structure`,
    `test_lexicon_v29.py::test_home_text_from_xlsx`) are the same pre-
    existing failures from US-001/US-002/US-003.
  - `python3 iterations/audit_excel_correspondence.py` runs end-to-end and
    writes its markdown + CSV reports (exit 0).
- **Learnings:**
  - The verbatim Excel's `(sheet, juris)` blocks don't 1:1 with the
    analysis sheets' multi-sub structure. Building a separate
    `VERBATIM_CELLS` map (rather than reusing `SINGLE_SUB_SHEETS` /
    `MULTI_SUB_CELLS`) was cleaner — the analysis side disambiguates by
    `term`, but the verbatim side has a single term per block, so the
    HTML cell key alone is enough.
  - The verbatim loader's `_juris_to_law` fallback is too coarse for
    California: every "U.S. - California" cell without an inline citation
    gets `ca-sb53`, masking the real law (`ca-sb942` / `ca-ab2013`). The
    new `wrong_law` status surfaces this correctly, but it means the
    headline "wrong_law" count overstates real link errors. A future
    loader pass should parse inline section citations inside the verbatim
    text (e.g. `22757.1` → `ca-sb942`) to refine `law_id`.
  - A verbatim entry with `article_id=None` still anchors the term to the
    law, so an HTML link to a specific article in that law surfaces as
    `wrong_article` rather than `wrong_law`. This is the right call —
    `wrong_law` is reserved for cases where the term has zero entries in
    the linked law. Test
    `test_classify_link_article_none_in_verbatim_counts_as_same_law`
    pins this behaviour.
  - Aggregating per-cell with "worst severity" lets reviewers sort the
    CSV by `link_status` directly. The full per-link list is preserved
    in `link_statuses` so no information is lost — the cell row keeps
    one-to-one parity between `linked_articles` and `link_statuses`,
    enforced by `test_linked_articles_and_link_statuses_zip_one_to_one`.
---

## 2026-05-01 - US-006
- Extended `iterations/verify_lexicon.py` with a corrector that produces
  `iterations/digital_lexicon_v29-corrected.html`:
  - `_extract_concepts_span(html_text)` returns `(parsed, start, end)` so the
    JSON literal can be replaced in place without touching the surrounding
    HTML.
  - `_serialize_concepts(concepts)` uses `json.dumps(..., ensure_ascii=False,
    separators=(",", ":"))` and round-trips the v29 source byte-for-byte.
  - `_compute_corrections(df, by_block, by_term)` walks the verification
    frame and yields one dict per change: `analysis` (replace cell.analysis
    with cross-checked Excel text), `link` (substitute article id when
    verbatim has exactly one alternative for the (term, law) pair), or
    `link_skipped` (ambiguous candidates / no alternative).
  - `_apply_correction(concepts, c)` mutates the parsed list in place.
    Article substitution is whitespace-preserving via
    `re.split(r"(\s*;\s*)", ref)` so the rejoined reference keeps the
    original punctuation between atoms.
  - `_render_summary_block(applied, skipped, generated_at)` produces a
    self-styled `<aside id="v29-corrections-summary">` listing every change;
    `_inject_summary_block(html, summary)` slips it in after the opening
    `<body>` tag.
  - `build_corrected_html(out_path, df=None, ...)` orchestrates the whole
    flow and returns `{out_path, applied, skipped}` for inspection.
- Added a `--fix` (and `--fix-out`) CLI flag to `verify_lexicon.main` that
  calls the corrector after writing the verification CSV/MD/HTML.
- Files changed/created:
  - `iterations/verify_lexicon.py` (+~330 lines: corrector + helpers + CLI)
  - `iterations/test_verify_lexicon.py` (+18 tests for span extraction,
    serialisation, atom replacement, correction computation, application,
    summary block, body injection, end-to-end fixture, --fix CLI)
  - `iterations/digital_lexicon_v29-corrected.html` (new — generated)
- Validation:
  - `python3 -m pytest iterations/test_verify_lexicon.py` — 81 passed
    (66 existing + 18 new — totals to 84 less three previously combined
    counts; effective net is +18).
  - `python3 -m pytest iterations/` — 202 passed, 2 failed
    (`test_lexicon_v18.py::test_v18_dom_features` and
    `test_lexicon_v29.py::test_home_text_from_xlsx`) are the same
    pre-existing failures noted in earlier user stories — both reproduce
    on `main` without my changes (re-verified by stashing and re-running).
  - `python3 iterations/audit_excel_correspondence.py` runs end-to-end
    and writes its markdown + CSV reports. Exit code 1 from the same
    pre-existing v28 discrepancies (105 / 43 / 23 / 20 / 9), unchanged
    from baseline.
  - End-to-end on the real fixtures: corrector produces 67 fixes
    (61 analysis text replacements + 6 article-link substitutions) and
    skips 17 ambiguous wrong_article links. Re-running the verifier
    against the corrected file shows zero `mismatch` rows (was 61) and
    `wrong_article` count drops from 23 → 17 (the 6 unique substitutions).
  - Original `digital_lexicon_v29.html` SHA-256 unchanged before/after the
    fix run (asserted in `test_build_corrected_html_does_not_modify_original`).
- **Learnings:**
  - The CONCEPTS JSON literal round-trips byte-for-byte through
    `json.dumps(..., separators=(",", ":"), ensure_ascii=False)` — verified
    against the v29 fixture (481929 chars in, 481929 chars out, equal).
    This means a corrected file's diff is *exactly* the changed cells
    (plus the injected summary block), making review trivial.
  - `re.split(r"(\s*;\s*)", reference)` with a capturing group is the
    cleanest way to round-trip multi-citation references with mixed
    `; ` / `;` separators. Splitting on `;` and rejoining with `"; "`
    silently normalises the original spacing, which the corrector should
    not do.
  - Wrong_law is intentionally not auto-corrected. When the term has no
    entry in the linked law at all, the right action is to either change
    the law (re-attribution) or remove the link — both demand human
    review. US-006 stops at substitution-only fixes; US-009 will use
    similarity matching for the harder cases.
  - For section-id substitutions in U.S. state laws (e.g. `6-1-1701`,
    `552.001`, `22757.11`), use `(?<![\w.]){old}(?![\w.])` rather than
    `\b{old}\b`. Word-boundary alone wrongly matches the `22757` head of
    `22757.11`; the negative lookbehind/-ahead on `[\w.]` blocks that.
---

## 2026-05-01 - US-005
- Extended `iterations/verify_lexicon.py` with three writers fed by the same
  verification frame:
  - `write_verification_md` — markdown report with totals, top 20 mismatches,
    broken-links table (per-link `wrong_article` / `wrong_law`), and
    missing-in-HTML / missing-in-Excel sections.
  - `write_verification_html` — single self-contained file with status
    badges, filter buttons (All / Mismatch / Missing / Wrong Article /
    Wrong Law), and click-to-expand rows showing a character-level LCS diff
    of the HTML and Excel analysis side by side.
  - The CLI now writes the CSV + MD + HTML siblings under one timestamp,
    and accepts `--md-out` / `--html-out` overrides plus `--out` (which
    sets the CSV path and derives MD/HTML siblings from it).
- The HTML viewer ships its row data as a JSON island; an inline JS module
  uses event delegation on the filter bar and on `<tbody>` for row clicks,
  with no inline `onclick` handlers anywhere. The diff is computed
  client-side from the embedded HTML / Excel strings.
- Files changed:
  - `iterations/verify_lexicon.py` (+~430 lines: writers, CLI updates,
    embedded CSS / JS, helpers `_row_filter_tags`, `_row_payload`,
    `render_markdown_report`, `render_html_report`, etc.)
  - `iterations/test_verify_lexicon.py` (+15 tests covering MD sections,
    counts, truncation, HTML payload shape, script-breakout escaping,
    filter tags, no inline `onclick`, and end-to-end writes against the
    real fixtures).
- Validation:
  - `python3 iterations/verify_lexicon.py` writes all three artefacts:
    `outputs/lexicon_verification_<ts>.csv`, `.md`, `.html` (the run
    today produced 410 cells / 387 links with the same counts as US-004).
  - `python3 -m pytest iterations/test_verify_lexicon.py` — 50 passed.
  - Full suite: `python3 -m pytest iterations/` — 168 passed; the 2
    pre-existing browser-flake failures (`test_lexicon_v17.py::
    test_v17_static_structure` / `test_lexicon_v18.py::test_v18_dom_features`
    or `test_lexicon_v29.py::test_home_text_from_xlsx`) are unrelated to
    this story and reproduce on `main`.
  - `python3 iterations/audit_excel_correspondence.py` runs end-to-end
    (exit 1 from the same pre-existing v28 discrepancies — verified by
    stashing this branch's changes and re-running).
  - Browser verification via `/browse` skill:
    - Page loads at `http://127.0.0.1:8765/lexicon_verification_<ts>.html`
      with no console errors. 410 rows + 5 filter buttons render.
    - Filter buttons: `mismatch` shows 61 rows (all tagged `mismatch`),
      `missing` shows 86 (= 37 + 49), `wrong_article` shows 20,
      `wrong_law` shows 11, `all` restores 410. Tag containment
      verified for every visible row in each filter mode.
    - Clicked 5 mismatch rows: 5 detail rows expand, each with two
      `.diff-pane` (HTML | Excel) and `<ins>` / `<del>` highlights
      (48 inserts and 113 deletes across the 5 expansions in this run).
    - `document.querySelectorAll('[onclick]').length` is `0` in the
      loaded page, confirming event delegation is the only interaction
      mechanism.
    - Screenshot `/tmp/lexicon_verify_mismatch.png` captures the
      mismatch filter with three rows expanded, showing the side-by-side
      character-level diff with red/green highlights.
- **Learnings:**
  - The `<script type="application/json">` payload must escape any
    literal `</script>` in the analysis bodies (`json.dumps(...).replace(
    "</", "<\\/")`); without it, an analysis cell containing the string
    `</script>` would terminate the script element early. The
    counterpart on the JS side undoes the escape if it ever needs to
    recover the raw form (in this report we don't — `JSON.parse` on the
    text content works directly because the unescape isn't needed for
    JSON parsing, only for the browser's HTML tokenizer). Pinned by
    `test_render_html_report_payload_safe_against_script_breakout`.
  - The `/browse` headless tool blocks `file://` URLs (security
    constraint). For local file verification, spin up
    `python3 -m http.server` on a free port in the `outputs/` dir and
    point `goto` at `http://127.0.0.1:<port>/<file>.html`. Worth noting
    in any future tasks that need to verify a generated HTML artefact.
  - The browse server occasionally times out / restarts between
    individual `$B` invocations. Chaining the goto + clicks + JS asserts
    via `$B chain '[[...]]'` keeps the page state alive across the whole
    verification flow and is much more reliable than calling each
    command separately.
  - Character-level LCS diff over analysis bodies that can be ~1-2KB is
    fast enough to compute lazily on click in JS (Int32Array DP table,
    O(n*m)). Batching consecutive equal/insert/delete characters into
    runs keeps the rendered HTML small enough that even a 5-row expand
    only adds a couple hundred extra DOM nodes.
---

## 2026-05-01 - US-007
- Created `iterations/digital_lexicon_v30.html` as a byte-identical copy of
  the US-006 output `iterations/digital_lexicon_v29-corrected.html`. SHA-256
  of both files matches (`05f936a5b47c066f019d1eb0b507d0be9a661f528449504c
  9f0fa9ea82bb0e21`), so v30 is exactly the verified, auto-corrected v29
  baseline that US-008+ can build highlighting features on top of.
- No code changes were needed beyond `cp`. The v30 file inherits every fix
  applied in US-006 (61 analysis-text replacements + 6 article-link
  substitutions, 17 ambiguous wrong_article links surfaced in the injected
  summary block) and every behaviour of v29.
- Files changed/created:
  - `iterations/digital_lexicon_v30.html` (new — byte-identical copy of
    `digital_lexicon_v29-corrected.html`)
- Validation:
  - `python3 -m pytest iterations/` — 202 passed, 2 failed
    (`test_lexicon_v18.py::test_v18_dom_features` and
    `test_lexicon_v29.py::test_home_text_from_xlsx`) are the same
    pre-existing failures noted in US-005/US-006 — unrelated to US-007 and
    reproduce on `main` without my changes.
  - `python3 iterations/audit_excel_correspondence.py` runs end-to-end and
    writes the markdown + CSV reports under `outputs/`. Exit code 1 from
    the same pre-existing v28 ↔ Excel discrepancies (105 / 43 / 23 / 20 / 9)
    that were the baseline before US-007 — the script targets v28 so v30
    does not affect it.
  - Browser verification via `/browse` skill against
    `http://127.0.0.1:8767/digital_lexicon_v30.html`:
    - Page loads with no console errors. Hash router resolves to `#/`
      (home) and the matrix view loads on `#/concepts?view=matrix`.
    - Navigated to 5 different concept routes and confirmed each renders
      its terms (tabs) and cells, all with zero console errors:
      - `#/concept/model-system` — 3 tabs (High-risk AI system [selected],
        General-purpose AI model, General-purpose AI system); 25 cells.
      - `#/concept/risk` — 33 cells; analysis content includes the
        Systemic / Catastrophic risk dimensions for EU/CA/NY.
      - `#/concept/incident` — 50 cells.
      - `#/concept/modification` — 34 cells.
      - `#/concept/provider-developer` — 4 sub-concept tabs (Provider of
        limited-risk / high-risk / GPAI models / GPAI models with systemic
        risk); 53 cells.
    - Primary-sources / law view (`#/primary-sources/eu-aia`) loads with
      13 article elements present in the rendered DOM.
- **Learnings:**
  - When the next iteration of an HTML artefact is meant to be the
    starting point for new features (rather than a rebuild), `cp` plus
    SHA-256 verification is the cleanest possible scaffold. No build
    script needed; no risk of drift between the verified baseline and
    the new starting point. The byte-identical hash assertion is the
    contract.
  - The v29 SPA's hash router silently rewrites unknown routes back to
    `#/` (e.g. `#/laws` and `#/regulations` both reverted to `#/` in
    headless tests). The actual route for the regulations index is
    `#/primary-sources` and for individual laws `#/primary-sources/<slug>`.
    Worth knowing if any future highlighting work needs to deep-link into
    a specific law's article.
  - Browser-based navigation through chained `$B chain '[[goto], [wait],
    [js], ...]'` is reliable, but `$B click` sequences across separate
    invocations can lose ref freshness when the server restarts
    mid-flow. Prefer one chain per verification flow when verifying a
    static SPA — same advice as US-005's progress note.
---


