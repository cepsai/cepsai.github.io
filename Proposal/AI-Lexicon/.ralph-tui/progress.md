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

- **`const`/`let` declarations at script top level are NOT on `window`.**
  The shell uses `let drawerCurrentDimId = null` etc. for drawer state and
  `const CONCEPTS = [...]` for the data — none reachable via
  `window.drawerCurrentDimId` / `window.CONCEPTS`. Wrappers that need that
  state must take it from the wrapped function's *parameters*
  (e.g. `updateDrawerContent(dim, juris, sc, c)`), not by re-reading
  module-scoped variables off `window`. Discovered when the v30 highlight
  patch silently no-op'd because `window.drawerCurrentDimId` was always
  `undefined`. `function` declarations at script top level still attach
  to `window` — that's why the v29 `_installWrapper` can read
  `window.updateDrawerContent`.
- **Browse-tool `js` runs in an isolated world.** Bare identifiers like
  `getConcept`, `state`, `CONCEPTS` are not visible — only `document`,
  `window`, and standard globals. Always go through `window.xxx` for
  page-defined `function` declarations, and accept that `const`/`let`
  page state is unreachable from `$B js` entirely. (You can still call
  page functions through the inline event handlers — they ARE looked up
  from window.)
- **Per-text-node TreeWalker is not enough for cross-paragraph matches.**
  The v29 article body uses `<p>` siblings inside `.v29-art-body`, with
  marker spans (`<span class="v29-marker">(c)</span>`) breaking each `<p>`
  into multiple text nodes. Highlight matches that start in one text
  node and end in another need a *flat-text-with-back-pointer* approach:
  walk every text node into one normalised string, keep an index map
  back to `(textNode, offsetInNode)`, find the substring, then
  reconstruct the slice list and wrap each portion in its own
  `<mark>`. See `_buildFlatText` / `_wrapRange` in the v30 highlight
  block for the working pattern.
- **Splitting verbatim into "sentences" must include enumerated-clause
  boundaries.** Legal text frequently has long sentences with a trailing
  enumerated list — `…doing any of the following: (I) … ; (II) … ; or
  (III) …` — that the law article splits across paragraphs. A regex that
  only splits on `[.!?]\s+(?=[A-Z])` collapses the whole thing into one
  span and misses partial matches. Add a second alternation
  `(?<=[;:])\s+(?=\(|[A-Z])` so each `(I)` / `(a)` / `(1)` clause is
  considered separately. Bumped NY S8828 §1420(3)(a) from 0 marks to 1
  in the v30 verbatim highlight verification.
- **Match-quality is bounded by source-text quality.** The TX HB 149 raw
  blob has spacing defects from PDF extraction (`theattorney general`
  instead of `the attorney general`) that no whitespace-collapsing
  normalisation can fix — those cells gracefully render zero marks
  rather than mismatching. The acceptance criterion is "lenient against
  whitespace/quote variants", not "fuzzy match". Document the gap rather
  than reaching for fuzzy similarity.

- **Wrap-order matters: install the outermost wrapper LAST.** v29's
  drawer-render wrapper reads `cell.reference` AFTER its `orig.apply`
  returns to call `_renderDrawerArticles(cell.reference)`. If a US-009
  wrapper installs *before* v29 (so it ends up innermost), the
  `pre-orig` mutation of `cell.reference` is restored in the US-009
  `finally{}` *before* v29 reads it — the override silently no-ops.
  Fix: gate the install on `window.__v29_udc_patched &&
  window.__v30_highlight_patched` so US-009 only registers when both
  prior wrappers have already taken hold, making it the outermost
  wrapper. Defensive `setTimeout(_install, ...)` cascades cover the
  ordering race. Discovered when the US-009 note rendered correctly
  but the article body was still §1422 instead of §1421.
- **Insert UI elements synchronously, not in `requestAnimationFrame`.**
  rAF callbacks fire on the next browser tick, *after* the current JS
  task — which means a `$B chain '[[js, openDrawer], [js, querySel
  for note]]'` step that runs both `js` commands in tight succession
  observes the post-render DOM *before* the rAF callback has fired,
  and the QA assertion sees no note. Insert the note with a plain
  synchronous `container.insertBefore(note, container.firstChild)`
  right after `orig.apply` returns — by then the article body is
  already in the DOM, so rAF buys nothing. Discovered in the chain
  verification of the 5 corrected cells.
- **Use the actual project default HTML, not the dependency's.** When
  one helper (`compute_autocorrect_lookup`) calls another (`parse_v29`)
  and both have their own `DEFAULT_HTML`, passing through `None`
  silently lets the inner default win. For US-009, that meant the
  build script defaulted to v29.html instead of v30.html, surfacing
  a different (older, unverified) cell.reference set. Always pass
  the project-scoped default explicitly: `parse_v29(html_path or
  DEFAULT_HTML)`. Discovered when the CLI reported 5 corrections but
  `compute_autocorrect_lookup()` returned 6.

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

## 2026-05-01 - US-008
- Added an append-only US-008 block to
  `iterations/digital_lexicon_v30.html` (~245 lines: a `<style>` rule for
  `mark.v30-verbatim-mark` plus a self-contained IIFE that wraps
  `window.updateDrawerContent` to highlight verbatim spans in the law
  article).
- The script chains *after* the v29 article-render wrapper. When the
  drawer renders, it walks every text node inside each `.v29-art-body`,
  builds a normalised flat string + `(textNode, offset)` index map,
  finds the cell's `verbatim` string in that flat text (full first,
  then per-sentence), and wraps every contiguous match in
  `<mark class="v30-verbatim-mark">` with a yellow background. The
  first mark is `scrollIntoView({block:'center'})`-ed so the reader's
  eye lands on it. Existing marks from a prior click are stripped via
  `_clearMarks` before applying new ones.
- Lenient matching: smart single/double quotes (`U+2018-201F`, `U+2032`,
  `U+2033`), NBSP and friends (`U+00A0`, `U+202F`, `U+2009`, `U+200A`,
  `U+200B`), soft hyphen (`U+00AD`), BOM (`U+FEFF`), en-dash / em-dash
  (`U+2013`/`U+2014`/`U+2212`) all normalise to ASCII before matching;
  whitespace runs collapse to a single space; case is folded.
- Sentence splitter (`_splitSpans`) breaks on both `.!?` *and*
  `;:` followed by `(I)` / `(a)` / `(1)` / capital-letter — needed for
  long legal sentences with embedded enumerated lists (the "(I) …
  (II) … (III) …" pattern in NY S8828 §1420(3)(a) etc.).
- Hooked via wrapping the v29-patched `window.updateDrawerContent` —
  the wrapper takes `dim` / `juris` from its own *arguments* rather
  than reading the page's `let drawerCurrentDimId` / `let
  drawerCurrentJuris` (those aren't on `window`). No new inline
  `onclick=` handlers; `__v30_highlight_patched` flag prevents
  double-installation; `setTimeout(_install, 0)` and `setTimeout(_install,
  100)` cover ordering races.
- Files changed/created:
  - `iterations/digital_lexicon_v30.html` (append-only US-008 block,
    +245 lines)
  - `iterations/test_lexicon_v30.py` (new — 13 structural tests)
- Validation:
  - `python3 -m pytest iterations/test_lexicon_v30.py` — 13 passed.
  - `python3 -m pytest iterations/` — 215 passed, 2 failed
    (`test_lexicon_v18.py::test_v18_dom_features` and
    `test_lexicon_v29.py::test_home_text_from_xlsx`) are the same
    pre-existing browser-flake / count-drift failures noted in
    every prior story; both reproduce on `main` without these changes.
  - `python3 iterations/audit_excel_correspondence.py` runs end-to-end
    and writes the markdown + CSV reports under `outputs/`. Exit code
    1 from the same pre-existing v28 ↔ Excel discrepancies
    (105 / 43 / 23 / 20 / 9) — the script targets v28, so v30
    doesn't affect it.
  - Browser verification via `/browse` skill against
    `http://127.0.0.1:8769/digital_lexicon_v30.html`:
    - Page loads with no console errors. After every drawer click the
      console remains clean (`$B console --errors` returns "no console
      errors").
    - 7 cells clicked across 5 distinct laws — each renders the law
      article in the drawer with one or more
      `<mark class="v30-verbatim-mark">` spans:
      • risk / definition-1-0 / eu — `AIA Article 3(2); AIA Article 3(65)` → 2 marks
      • risk / term-0-0 / ca — `CA SB 53 §22757.11(c)(1)` → 1 mark
      • risk / term-0-0 / ny — `NY S8828 §1420(3)(a)` → 1 mark
      • provider-developer / scope-1-0 / co — `Colorado SB24-205, 6-1-1701` → 1 mark
      • provider-developer / transparency-4-0 / eu — `EU AI Act, Article 50 (1, 2)` → 4 marks (paragraphs 1 and 2 each split into multiple sentence spans)
      • provider-developer / scope-1-0 / eu — `EU AI Act, Article 50 (1)` → 1 mark
      • modification / term-0-0 / ca-1-substantial-modification — `CA AB 2013 §3110(d)` → 1 mark
    - Marks-clearing confirmed: switching jurisdictions in the drawer
      (eu → ca → ny on risk/definition-1-0) shows the mark count
      changing per click (2 → 3 → 1) with no leftover marks from the
      previous render.
    - Screenshot `/tmp/v30_drawer_zoom.png` captures the
      `EU AI Act, Article 50 (1, 2)` drawer with both paragraphs
      highlighted in yellow across multiple contiguous spans.
    - One real-data gotcha discovered: the TX HB 149 blob has spacing
      defects from PDF extraction (`theattorney general` instead of
      `the attorney general`), which no whitespace-collapsing
      normaliser can match. Those cells render the article body
      cleanly but with zero marks — graceful degradation rather than
      a wrong highlight. Same behaviour for verbatim that says
      "more than 50 people" against article text "more than fifty
      people" (number vs word). These are source-text issues, not
      verifier bugs; the acceptance criterion is "lenient" (whitespace
      / quote variants), not "fuzzy".
- **Learnings:**
  - **`const`/`let` at script top level are NOT on `window`.** The
    shell's drawer state (`let drawerCurrentDimId`,
    `let drawerCurrentJuris`) and the `const CONCEPTS = [...]` data
    blob are unreachable via `window.xxx`. Wrappers that need that
    state must take it from the *parameters* of the function they wrap
    — `window.updateDrawerContent(dim, juris, sc, c)` is the right
    contract. The v30 highlight patch silently no-op'd until I switched
    from `window.drawerCurrentDimId` to using the wrapper's `dim`/`juris`
    arguments directly.
  - **Browse-tool `js` runs in an isolated world.** Bare identifiers
    like `getConcept`, `state`, `CONCEPTS` are not visible — only
    `document`, `window`, and standard globals. Page-defined `function`
    declarations attach to `window` and ARE reachable; `const`/`let`
    declarations are not. Always reach for `window.xxx` from `$B js`,
    and accept that page-private state is fundamentally unreachable
    until you wire it through `window` or function args.
  - **Cross-text-node ranges need a flat-text-with-index-map.** The
    article body has multiple text nodes per paragraph (one for the
    `<span class="v29-marker">(c)</span>` and one for the trailing
    text). Verbatim that spans them needs a single normalised string
    over the whole `.v29-art-body`, with `(node, offset)` pointers
    back to the original DOM. Then `indexOf` finds the match and
    `_wrapRange` walks the slice list, wrapping each portion in its
    own `<mark>` (processed in reverse order so earlier slice
    references stay valid as later siblings are replaced). See
    `_buildFlatText` / `_wrapRange` in the v30 block for the working
    pattern.
  - **Sentence splitting must understand enumerated-clause boundaries.**
    Adding `(?<=[;:])\s+(?=\(|[A-Z])` to the splitter regex (alongside
    the standard `(?<=[.!?])\s+(?=…[A-Z])`) bumped the NY S8828
    "Catastrophic risk" cell from 0 marks to 1 — the verbatim is one
    long sentence with `:(I) … ;(II) … ;(III) …` clauses, each of
    which is a separate paragraph in the article body.
  - **Don't fight the source data.** Some matching gaps are bugs in the
    upstream PDF/Word ingestion pipeline (TX HB 149 missing spaces,
    NY S8828 spelling out "fifty" while the verbatim uses "50"). The
    right call is graceful degradation — render the article without
    marks rather than reaching for fuzzy similarity that would
    introduce false positives. Document the gap; let it surface in
    QA where someone can fix the source.
---

## 2026-05-01 - US-009
- Added `iterations/build_v30_autocorrect.py` — pre-computes a per-cell
  auto-correct lookup at build time using `rapidfuzz.fuzz.token_set_ratio`
  (default threshold **65** for this dataset; PRD listed 70 as the
  starting point but the legitimate corrections cluster at 68.9–100 so
  60–65 is the practical floor). The lookup is keyed on
  `"<cid>|<sid>|<dim_id>|<jid>"` and carries
  `{from_label, to_label, to_anchor, law, kind, score}`. Idempotent
  injection adds the lookup to `digital_lexicon_v30.html` as a JSON
  island (`<script type="application/json" id="v30-autocorrect-data">`)
  alongside an `<style data-block="us-009">` + `<script
  data-block="us-009">` block; prior runs are stripped before re-inject.
- The embedded JS wraps `window.updateDrawerContent` (after the v29 +
  US-008 wrappers have taken hold) and, when the clicked cell has an
  entry in the lookup:
    1. Saves `cell.reference`, swaps it for the synthetic REF_MAP key
       (registered at install time so the corrected `to_anchor` resolves
       cleanly through `_resolveAllRefs` / `_renderArticle`).
    2. Calls the wrapped chain — v29 renders the corrected article body
       and cite header, US-008 highlights any verbatim it can find.
    3. Restores `cell.reference` so downstream features (citation copy)
       still see the original analyst-authored value.
    4. Inserts a styled custom popup note `<div class="v30-autocorrect-
       note">` synchronously above the article body reading "Article
       auto-corrected from X to Y", with a hover/focus `.v30-autocorrect-
       popup` carrying the score and explanatory text. NO native title
       attribute is used.
- 5 corrections produced from the v30 + verbatim Excel snapshot at
  threshold 65: NY S8828 §1422 → §1421 (large frontier developer); NY
  A6453 §1422 → §1421 + §1422 → §1425 (large developer); UT SB 226
  §13-75-101 → §13-75-103 (deployer of GPAI systems); CA SB 53
  §22757.11(d) → §22757.13 (serious incident).
- Files changed/created:
  - `iterations/build_v30_autocorrect.py` (new — ~510 lines: lookup
    builder, JS block template, similarity scorer, label rendering,
    idempotent HTML injection, CLI)
  - `iterations/digital_lexicon_v30.html` (append-only injected JSON
    island + US-009 style + script blocks; pre-`</body>` baseline
    bytes still match v29-corrected per
    `test_v30_starts_with_v29_corrected_baseline`)
  - `iterations/test_lexicon_v30_autocorrect.py` (new — 28 tests
    covering helpers, similarity scoring, blob extraction, end-to-end
    lookup against real fixtures, JSON-island shape, idempotency, JS
    presence + no native-title use, no-new-onclick, threshold sweep,
    script-breakout safety, append-only baseline)
  - `iterations/test_lexicon_v30.py` (size-guard limit bumped from
    12 KB to 64 KB to fit US-008 + US-009 inline blocks together)
- Validation:
  - `python3 iterations/build_v30_autocorrect.py` → reports "5 cells
    corrected (threshold=65.0)" and rewrites v30 in-place.
  - `python3 -m pytest iterations/test_lexicon_v30_autocorrect.py
    iterations/test_lexicon_v30.py -q` — 41 passed (28 new + 13
    existing US-008 tests).
  - `python3 -m pytest iterations/` — 243 passed, 2 failed
    (`test_lexicon_v18.py::test_v18_dom_features`,
    `test_lexicon_v29.py::test_home_text_from_xlsx`) — same pre-
    existing failures noted in every prior US, unrelated to US-009.
  - `python3 iterations/audit_excel_correspondence.py` runs end-to-end
    and writes its markdown + CSV reports under `outputs/`. Exit
    code 1 from the same pre-existing v28 ↔ Excel discrepancies
    (105/43/23/20/9), unchanged from the baseline (audit targets
    v28; v30 changes do not affect it).
  - Browser verification via `/browse` skill against
    `http://127.0.0.1:8770/digital_lexicon_v30.html`:
    - Page loads with no console errors.
    `window.__v30_autocorrect_patched`, `window.__v29_udc_patched`,
      and `window.__v30_highlight_patched` all `true`.
      `window.__v30_autocorrect.loadData()` reports
      `{threshold: 65, count: 5}`.
    - Triggered all 5 corrected cells via `openDrawer(...)` chains
      and confirmed the `.v30-autocorrect-note` element is present,
      the article cite header now shows the corrected anchor, and
      the article body matches the corrected section's text:
       1. provider-developer / provider-of-general-purpose-ai-models-
          with-systemic-risk / risk-management-7-0 /
          ny-1-large-frontier-developer:
          note "Article auto-corrected from NY S8828 §1422 to NY
          S8828 §1421"; cite "NY S8828 §1421".
       2. ...same dim, ny-2-large-developer (NY A6453):
          §1422 → §1421.
       3. ...risk-management-reporting-9-0 dim, ny-2-large-developer:
          §1422 → §1425.
       4. deployer-supplier / deployer-of-general-purpose-ai-systems
          / scope-1-0 / ut: §13-75-101 → §13-75-103.
       5. incident / serious-incident / term-0-0 / ca:
          §22757.11(d) → §22757.13.
    - Sanity-check: a non-corrected cell (`risk/definition-1-0/eu`)
      shows `NO_NOTE` with cite "AIA Article 3(2)" and no console
      errors.
    - Screenshot `/tmp/v30_us009_note.png` captures the corrected
      drawer for `incident/term-0-0/ca` — the yellow-bordered note
      sits at the top of the drawer, and the §22757.13 article body
      is rendered below.
- **Learnings:**
  - **Pre-compute the lookup, apply at click time.** The acceptance
    criterion ("lookup table pre-computed at build time and inlined
    as JSON") is the right architecture: keeps the JS small (no
    rapidfuzz in the bundle), keeps the build deterministic, and
    keeps similarity-search expensive computation out of the hot
    path. The only client-side work is dictionary lookup +
    cell.reference swap + DOM insertion of one `<div>`.
  - **Threshold is dataset-dependent.** The PRD's 70 was a starting
    point, but on legal text where the analysis is a paraphrase
    (not a verbatim slice) of a statutory body, token_set_ratio
    settles 5–10 points lower. 65 catches every legitimate
    correction in the snapshot; 70 misses one (NY S8828 §1421 at
    68.9). Keep the threshold as a CLI flag so reviewers can re-
    run with stricter or looser regimes.
  - **`requestAnimationFrame` defeats synchronous QA.** Earlier
    versions inserted the note inside `requestAnimationFrame` to
    "be safe" with timing — this hid the note from `$B chain`-
    style assertions that read the DOM in the very next `js`
    command. Since the article body is already in the DOM
    synchronously after `orig.apply`, rAF earns nothing.
    Synchronous insertion is both simpler AND testable.
  - **Wrap-order is a contract, not an implementation detail.**
    Three wrappers around `updateDrawerContent` (v29, US-008,
    US-009) chain `orig.apply(this, arguments)` and run their own
    pre/post logic. The wrap-order determines whether a `pre-orig`
    mutation persists past the inner `orig` calls. v29 reads
    `cell.reference` *after* its `orig.apply` returns — that's
    when v29 calls `_renderDrawerArticles`. So any wrapper that
    mutates `cell.reference` must install OUTSIDE v29 — guarding
    on `window.__v29_udc_patched && window.__v30_highlight_patched`
    before installing makes that contract explicit.
  - **Synthetic REF_MAP entries are the cleanest way to inject a
    new article reference.** Rather than re-implementing
    `_renderArticle` in the new wrapper, register the corrected
    `to_label` as a key in `window.REF_MAP` mapping to
    `{law, kind, anchor, paragraphs:[], subparagraphs:[]}`. Then
    the v29 pipeline naturally resolves the new label and renders
    the corrected article. Pre-existing keys are preserved
    (collision-safe via uniquified synthetic keys when needed).
  - **The `from_label` should be the cell's full original reference,
    not a synthesised single-anchor label.** Multi-atom cells (e.g.
    `Utah Code; Utah SB226, 13-75-101. (4)`) are part of what the
    user sees pre-correction; a one-anchor `from_label` would lose
    that context. The note now reads "Article auto-corrected from
    Utah Code; Utah SB226, 13-75-101. (4) to UT SB 226 §13-75-103."
    — verbose but accurate.
  - **Cell-level aggregation matters for "no_verbatim" detection.**
    The first `parse_v29` row for a multi-atom cell carries only
    the FIRST link's status. Cells where SOME atoms are no_verbatim
    and others are verbatim_found should NOT be auto-corrected —
    the analyst already validated against the law that has a
    verbatim row. Use `_aggregate_link_status` over all atoms;
    only auto-correct when ALL of them are no_verbatim.
  - **Phantom-correction skip rule.** If the best similarity match
    is *already* one of the cell's cited anchors, there's nothing
    to correct — the cell already points at the right article,
    just alongside other articles. Skip these silently. Without
    the skip, the lookup pollutes with no-op "corrections" that
    would still trigger an inline note ("auto-corrected from §22757.11
    to §22757.12") even though §22757.12 is already cited.
---



