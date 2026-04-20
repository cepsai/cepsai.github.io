# Digital AI Lexicon — progress log & lessons learned

Ongoing notes on the v11 → v14 evolution, the decisions behind each version, and
gotchas worth remembering next time we touch this pipeline.

## Versions shipped

| Version | What it is |
|---|---|
| `digital_lexicon_v11.html` | Original hand-crafted single-file SPA. Tab-per-concept-family layout with expandable concept cards. All data inlined. |
| `digital_lexicon_v12.html` | `build_v12.py` patcher: v11 + xlsx v5 content. Added 2 new tabs (`highrisk`, `gpai-system`), Utah jurisdiction, 13-card `ANALYSIS_DATA`, About/Glossary nav pages, Methodology text. All xlsx cells visible; 708/708 coverage. |
| `digital_lexicon_v13.html` | v12 + embedded law texts. Added side drawer on citation click, Laws nav page, Utah & NY filled in, reference→law-article deep links, theme toggle (light/dark/auto + localStorage), many perf fixes. |
| `digital_lexicon_v14.html` | Rewrote on top of `digital_lexicon_v12_draft.html` (CEPS's own cleaner rewrite). 4-item nav (Home / Concepts / Laws / Methodology), unified Matrix+List Concepts page, per-dimension cell drawer with jurisdiction switcher, CEPS notes below the table, global search + `/` shortcut. Retained v13's embedded laws + theme toggle + prev/next TOC in the law drawer. Always opens on Home. |
| `digital_lexicon_v15.html` | Curated "New concepts" matrix (6 families instead of v14's 8 legal-sheet tabs), cluster-summary table per concept with variant pills, analysis-sheet-sourced dim tables with bill-code column headers, rich-text interpretative notes, prose-driven Home + Methodology pages, base font 16px. |
| `digital_lexicon_v16.html` | **Current.** v15 + four improvements: (1) **lighter** (≈90 KB saved via shadow-const dedup + CSS minify + rich-text run merging), (2) **"Explore in full law" button** on the verbatim drawer that routes via REF_MAP to the law drawer's article view, (3) **wider concept-page dim table** that fits without horizontal scroll at ≥901px viewports (mobile still scrolls), (4) **matrix pill click** on both the Concepts landing matrix and the concept-page cluster summary routes to the correct concept + sub-tab (with the clicked jurisdiction column briefly highlighted). |

## v16 change detail (2026-04-19, revised after first feedback pass)

Built on top of v15 via `build_v16.py` (imports `build_v15` + `build_v13`, monkey-patches `cell_runs` to merge adjacent same-bold runs, post-processes the v15 HTML). v14/v15 still regenerate byte-for-byte.

### Fixes applied in the follow-up pass

- **Pill routing**: Robert noticed clicking "Large developer (A6453B)" took you to the "Provider" sub-tab instead of "Provider of general-purpose AI models with systemic risk". Root causes: v15's `cluster_summary_from_matrix` used **exact** title matching (`"Provider of GPAI models with systemic risk"` ≠ `"Provider of general-purpose AI models with systemic risk"`), and continuation rows (blank `term_label`) fell through to the first sub-concept. Fixed in `_rewrite_concepts_const()`: normalizes "GPAI" ↔ "general-purpose AI" and forward-fills `sub_id` across continuation rows. 9 rows were remapped on the current workbook; all 8 pills sampled now route to the right sub-tab.
- **Law anchor**: "Explore in full law" on a Colorado cell was passing `"6-1-1701".split('-')[0]` = `"6"` to `openLawDrawerById`, so the drawer titled it "Article 6" and fell back to raw_text. Now only EU AI Act article anchors get the `-paragraph` suffix stripped (since the EU renderer indexes by article number only); every other law receives the full section ID.
- **Law-drawer whitespace**: Colorado's blob has empty `sections`, and its `raw_text` was the scraped bill-index navigation (Menu / Search / Visit & Learn / Contact Us / Privacy Policy…) — not bill text. The drawer rendered pages of blank-run boilerplate. `_clean_law_blobs()` now strips known nav lines + collapses blank runs, and if the remaining text has too few `\bshall\b` + section-symbol hits to plausibly be legal text, swaps it for a one-line fallback: "Full law text is not embedded inline for this source. Use the official link above to read the bill as enacted." Saves another ~8 KB and the drawer now fits one viewport.
- **Home page scroll**: `.landing` was 994 px tall at the 900 px viewport — a small but noticeable scroll. Trimmed `.landing` padding `72px/100px → 32px/40px`, `.prose-title` size `32 → 26 px`, paragraph `margin-bottom 14 → 10 px`, and `.landing-stats` padding/margin. Page now measures exactly 900 px (no scroll).

### Size (final)

| | Bytes | Δ vs v15 |
|---|---:|---:|
| v15 | 4,527,949 | — |
| v16 | 4,419,508 | −108,441 (−2.4%) |

**Size:** v15 4,527,949 → v16 4,439,603 bytes (−88,346, −2.0%). Gains came from:

- Shadow consts (`DATA` 26 KB, `ANALYSIS_DATA` 76 KB, `MATRIX` 2.5 KB — coverage-test-only) folded into a single dedup'd `<script type="application/json" id="__v16_coverage__">` plain-string blob. Net: ≈88 KB.
- `<style>` block minification (comments, whitespace). Small (≈2 KB).
- Rich-text run merging at build time: absorbed into overall size; not individually meaningful.

**Deferred (not done in v16):** law-blob externalization (breaks single-file offline guarantee); JS minify (loses debuggability); dropping `paras`/`recitals` duplication inside EU AI Act blob (needs renderer trace).

**UX changes (all injected via `_v16_overrides()` before `</body>`):**

- `updateDrawerContent` wrapped to append an "Explore in full law →" button to `.drawer-actions` iff `cell.reference` resolves via `REF_MAP` (tries whole string first, then `;`-split fragments — REF_MAP keys contain commas so splitting on `,` was a bug in the first attempt).
- `renderMatrix` and `__openVariantDrawer` both rewritten to call `go('concept', cId, subIdx)` instead of opening a side drawer. Lanes-to-sub-concept mapping reused from the cluster-summary `row.sub_id` already present in v15's data.
- `renderAnalysisTable` wrapped to scroll + briefly flash the jurisdiction column matching `state.focusJid` after pill navigation. `focusJid` is cleared on first render so it doesn't persist.
- CSS: `.concept-page { max-width: min(1760px, calc(100vw - 64px)) }`, drop `white-space: nowrap` on dim-table `th` and first-column `td`, drop `overflow-x: auto` on `.analysis-wrap` at ≥901px.

**Verified:**
- Coverage test: 708/708 cells visible, 167/172 refs resolve (same as v15).
- `build_v14.py` and `build_v15.py` regenerate byte-identical outputs (MD5 match).
- Clicking a Colorado "Developer (SB24-205)" pill from the Concepts matrix → lands on "Provider / Developer" → Provider sub-tab, CO column flashed.
- Clicking a verbatim cell referencing `EU AI Act, Article 3 (3); EU AI Act, Article 50 (1, 2); ...` → drawer shows "Explore in full law →" → clicking opens law drawer on Article 3.
- Wrap fits at 1280 (1142px wrap, overflow-x: visible) and at 800 (overflow-x: auto restored).



## Pipeline

```
AI terminology and taxonomy-5.xlsx
        │
        ├── build_v13.py → digital_lexicon_v13.html   (v11 shell + xlsx data + embedded laws)
        │
        └── build_v14.py → digital_lexicon_v14.html   (v12_draft shell + xlsx data + embedded laws)
                              │
                              └── reuses build_v13.parse_legal_sheet / parse_analysis_sheet / load_laws

laws/
 ├── fetch_laws.py                     (downloads + parses the 9 bills)
 ├── eu-ai-act.json, …                 (one JSON per law)
 └── → embedded as <script type="application/json"> inside each HTML build
```

## Decisions & trade-offs

### "Patcher" over "regenerator"
v13 was a patcher that surgically edited v11's embedded JSON. v14 switched base to v12_draft (which CEPS already built as a clean rewrite) and essentially re-populates `CONCEPTS` / `LAWS` with our richer data. Lesson: **when a cleaner shell exists, don't keep patching the crufty one**. v11's bespoke CSS/JS was a drag on every change.

### Inline JSON for law texts
Tried three storage strategies for the full law texts (~2.8 MB for EU AI Act alone):

1. **Everything in a top-level `const LAWS = {...}`** — clean but blocks first paint with a giant JSON parse at page load. Felt laggy.
2. **`fetch()` sibling files (`laws/*.full.json`)** — fast page load but breaks offline (`file://` URLs) and adds a round-trip on first drawer open.
3. **Inline `<script type="application/json" id="law-blob-…">` ← ended up here.** The browser treats these as inert text until you call `JSON.parse` on them, so page load cost is ~0. First drawer open for a given law parses that one blob and caches the result. Works offline, self-contained, lazy.

Lesson: **inline `<script type="application/json">` is the right way to embed heavy optional data in a single-file tool.**

### Coverage testing
`test_lexicon_coverage.py` walks the target HTML, extracts every inline JSON const (plus the `<script type="application/json">` blobs), and asserts that every non-trivial xlsx cell normalized-substring-matches somewhere in the corpus. Two tests:

- `test_all_xlsx_content_visible_in_html` (708 cells)
- `test_reference_resolution_ratio` (≥90 % of xlsx references must resolve to an embedded law anchor via `REF_MAP`)

This was invaluable: every data-model migration (v12 → v13 → v14) went through it. If coverage dropped, I knew immediately that a field had been renamed/omitted. For v14 I added "shadow" constants (`DATA`, `ANALYSIS_DATA`, `MATRIX`, `GLOSSARY`, `ABOUT_PROSE`, `METHODOLOGY_PROSE`) inline alongside the v12_draft-native `CONCEPTS` — the draft's renderer ignores them but the test sees every xlsx cell.

Lesson: **write the content-coverage test early, keep it cheap, run it on every build.**

## Lessons learned — gotchas

### Python subprocess silently truncates large responses through pipes
`subprocess.run(cmd, capture_output=True)` truncates archive.org's 200+ KB responses at ~150 KB. The pipe closes before `curl` finishes writing. **Fix**: use `curl -o /tmp/file` and read the file back. Burned an hour on this one.

### Wayback snapshots are not stable
Requesting `web.archive.org/web/TIMESTAMP/URL` with the same timestamp can return **different** content on different fetches: sometimes the real page (~200 KB), sometimes a redirect-to-error stub (~151 KB). The `id_` mode — `web.archive.org/web/TIMESTAMP**id_**/URL` — returns the raw captured bytes without the iframe wrapper and is much more stable. Also added a retry loop with a "sub-1 KB = error stub" detector.

### nysenate.gov is Cloudflare-protected for curl
No UA spoofing, header tweaks, or cookie tricks bypass the JS challenge. Archive.org mirrors the clean HTML — use those. `assembly.state.ny.us` and `legislation.nysenate.gov` both timed out entirely from this IP.

### xlsx cites bills whose numbers have drifted
- "NY S8828" in the xlsx ≠ the RAISE Act. S8828 in the 2023-24 NY session is an affordable-housing bill. The RAISE Act Senate version is **S6953 (2025)**.
- "Utah SB226" in the xlsx refers to chapter 13-75 sections that exist in the **2025** SB 226, not the 2024 one (which is the School of General Education Act).
- We kept `law_id = "ny-s8828"` / `"ut-sb226"` internally so `REF_MAP` still works against the xlsx labels; the content served is the correct RAISE Act / 2025 amendments regardless.

Lesson: **treat analyst-supplied bill numbers as hints, not identifiers. Verify section identifiers match the body.**

### v11's renderer expects fields we renamed
v11's comparative-analysis view calls `escH(j.term)` on each jurisdiction. When we produced analysis objects without a `term` field, the UI printed the literal word "undefined". Add back any v11 schema field our parser drops, or patch the renderer. We now always emit `term` (pulled from the xlsx's "Term" row for the analysis).

### Function-declaration binding quirk when monkey-patching
`function renderCAView() {...}` at a script's top level creates both `renderCAView` and `window.renderCAView`. Assigning `window.renderCAView = wrapper` in another IIFE *doesn't* intercept bare `renderCAView(...)` calls from v11's own code — the parse-time binding has already been captured by those callers. Solution: listen for the user-action events that trigger a re-render (`.concept-name`, `.toc-item`, tab clicks, etc.) and inject post-render via a MutationObserver-free approach.

### Injection-anchor bug after adding `<script type="application/json">` blobs
`html.rindex("</script>")` was suddenly landing my render_js *inside* the last JSON blob's closing tag, silently disabling half the code (including the `openLawRef` monkey-patch). **Fix**: walk each `</script>` and skip ones whose opening tag has `type="application/json"`.

### `@media (prefers-color-scheme: dark)` overrides explicit `data-theme='light'`
v12_draft has a `@media (prefers-color-scheme: dark)` rule in the base stylesheet. On a dark-OS machine, it fires regardless of whether the user explicitly picked light. **Fix**: declare a matching-specificity `html[data-theme='light'] { … light tokens … }` selector so explicit user preference wins. Same cascade trick for the `auto` case: `html[data-theme='auto']:where([data-os-dark])` for dark-when-OS-dark.

### `loadState()` restoring `state.page = 'concepts'`
v12_draft persists the active page in localStorage so reloads feel sticky. For a document-style tool users expect to land on Home. **Fix**: a small `forceHomeOnLoad()` that runs after `loadState()` and resets only the `page` field (preserving other preferences).

### Performance
Three things that mattered most:

1. **Lazy-parse law texts** (inline `<script type="application/json">` — see above). Biggest win, removed ~2.8 MB of blocking parse.
2. **`content-visibility: auto`** on `.concept-card` so off-screen cards skip layout/paint. Dropped it from `.ca-table` rows — with frequent re-renders, the per-row cost added up.
3. **Debounced/event-driven notes injection.** The first pass used a broad `MutationObserver` on `#p-lexicon` with `subtree: true`, which fires hundreds of times per interaction. Replaced with click handlers on `.concept-name / .toc-item / .tab-btn` that schedule one `requestIdleCallback` pass.

After these, Lexicon clicks are 1–20 ms end-to-end.

## Scripts & entry points

| File | Purpose |
|---|---|
| `build_v13.py` | Patches v11 into v13. Exposes `parse_legal_sheet`, `parse_analysis_sheet`, `load_laws`, etc. v14 imports these. |
| `build_v14.py` | Builds v14 from `digital_lexicon_v12_draft.html` + xlsx + laws. |
| `laws/fetch_laws.py` | Downloads each of the 9 bills. `python3 fetch_laws.py <id> [--force]` or `all`. |
| `test_lexicon_coverage.py` | Pytest-style + standalone: asserts every xlsx cell is visible + 90 %+ references resolve. Run with `python3 -m pytest …`. |
| `LAWS_TODO.md` | Per-law provenance (now closed). |

## Recurring rebuild recipe

```bash
cd "/Users/robertpraas/CEPS-DST Dropbox/Robert Praas/cb_sep_25/AI-Lexicon"

# Refetch law texts if the xlsx references drift
python3 laws/fetch_laws.py all --force

# Build both versions
python3 build_v13.py
python3 build_v14.py

# Sanity check
python3 -m pytest test_lexicon_coverage.py -q
```

## Backlog / nice-to-haves

- **Utah SB 0149 (2024 enabling law)** as a second Utah blob so citations to chapter 13-75 sections not in the 2025 amendment file can still be deep-linked.
- **Per-dimension notes display** in v14 (currently the draft shows a single CEPS framing panel below each concept; the `rows[i].notes` for individual dimensions aren't broken out separately).
- **GPAI Code of Practice** full text (non-statutory, would need scraping + curation).
- **Law drawer search** — v13 had a simple in-drawer find-next; v14 currently relies on browser built-in Find.
- **"View all usages of this citation"** — reverse lookup from a law article back to every concept cell that cites it.
