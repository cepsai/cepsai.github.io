# Clean build — from-first-principles refactor plan

**TL;DR: Yes, we can.** About 2/3 of the existing build chain is legacy
artefacts from layers that were later overwritten. A clean build is
~600 lines, one Python file with three clearly-named modules, no
intermediate HTML files, no caching trap.

---

## The current chain, honestly mapped

### Dependency graph (what actually runs)

```
AI terminology and taxonomy-final.xlsx  ─┐
laws/*.json                              ├──► digital_lexicon_v21.html
reference_style_v16.html                 ┘

build_v13  ←── build_v14  (DEAD — not imported by anything)
build_v13  ←── build_v15  (xlsx → v12_draft.html patch)
build_v15  ←── build_v16  (data fixes, minify, feature overrides)
            ←── build_v13 (imports its parser utilities)
build_v16  ←── build_v17  (**SHELL SWAP**: discards v16's HTML, keeps only CONCEPTS)
build_v17  ←── build_v18  (xlsx re-read for About + final polish)
build_v18  ←── build_v20  (xlsx re-read for dim parents + mode tabs)
build_v20  ←── build_v21  (filter bar + single-row view)
```

### The critical observation

**`build_v17` is a hard shell swap.** It reads `digital_lexicon_v16.html`,
extracts *only* the `CONCEPTS` JSON constant, then uses
`reference_style_v16.html` as the layout shell and injects the data.

Everything `build_v13`, `build_v14`, and `build_v15` did to build HTML —
the theme CSS, the concept cards, the drawer markup, the matrix
rendering — is **thrown away by v17**. Only the parsed data survives.

So 3 layers are actually doing *data transformation*. The HTML they
emit is scaffolding for a tower that's demolished at floor 4.

### Per-layer responsibilities (what actually ends up in v21)

| Layer | Data contribution | HTML contribution to v21 |
|---|---|---|
| v13 | xlsx parsers, law loading, REF_MAP | **none** (HTML discarded at v17) |
| v14 | (not in chain) | (not in chain) |
| v15 | cluster summary, rich notes, dim tables | **none** (HTML discarded at v17) |
| v16 | sub_id remap, orphan row drop, law cleanup | Explore-in-full-law button, pill nav, minify |
| v17 | notes reshape for reference shell | Shell + data injection (the *real* HTML floor) |
| v18 | About sheet prose, cited-para highlight | Laws→Regulations rename, Incident two-col |
| v20 | dim-parent lookup (xlsx re-parse) | Analysis/Legal-text mode tabs, verbatim renderer |
| v21 | — | Filter bar + single-row view |

### What's dead

- **`build_v14.py`** — nothing imports it, output unused.
- **`digital_lexicon_v11.html`** — the v11 shell that v13 patched. Never reaches v21.
- **`digital_lexicon_v12_draft.html`** — the v12 shell that v15 patched. Never reaches v21.
- **`digital_lexicon_v14.html`**, **`v15.html`** — transitional outputs, never the end user's file.
- **v13's theme JS, v14's initial concept markup, v15's matrix CSS** — all replaced by the reference shell.

### What's alive

- **xlsx parsers** (v13's `parse_legal_sheet`, `parse_analysis_sheet`, `parse_matrix`, `cell_runs` for rich-text runs) — essential.
- **law loading + REF_MAP** (v13's `load_laws`, `build_ref_map`).
- **Cluster summary + dim-table + notes builders** (v15's `cluster_summary_from_matrix`, `build_sub_concepts_v15`, `collect_rich_notes`).
- **Data fixes** (v16's `_find_best_sub_id`, `_drop_orphan_continuation_rows`, `_clean_law_blobs`).
- **Notes reshape for reference shell** (v17's `_transform_concepts`).
- **About sheet parser** (v18's `_read_about_blocks`).
- **Dim-parent xlsx re-parse** (v20's `_build_parent_lookup`).
- **All feature JS/CSS override blocks** (v16 through v21).
- **`reference_style_v16.html`** — the actual design shell.

---

## Proposed clean architecture

### One file, three passes

```
iterations/
├── build.py                          # single entry point, ~80 lines
├── lexicon/
│   ├── __init__.py
│   ├── data.py                       # xlsx + laws → structured dict
│   ├── shell.py                      # reference shell loader + injector
│   └── features/                     # one module per feature
│       ├── __init__.py               # composes and emits the overrides block
│       ├── explore_in_full_law.py    # v16 + v18 cited-para combined
│       ├── matrix_pill_nav.py        # v16
│       ├── about_prose.py            # v18
│       ├── regulations_rename.py     # v18
│       ├── incident_two_col.py       # v18
│       ├── mode_tabs.py              # v20
│       └── single_row_view.py        # v21
└── reference_style_v16.html          # unchanged (the visual layer)
```

### `lexicon/data.py` (~400 lines, condensed from ~2,700 across v13/v15/v16/v18/v20)

One class that produces everything the shell needs:

```python
@dataclass
class LexiconData:
    concepts:         list[Concept]     # 6 families, fully populated
    matrix:           dict               # curated New-concepts matrix
    laws:             dict[str, dict]    # law_id -> {articles/sections, raw_text}
    ref_map:          dict[str, dict]    # "EU AI Act, Article 3 (3)" -> {law, kind, anchor}
    about_prose:      list[str]          # About sheet paragraphs
    methodology:      dict               # Methodology sheet text + regulations table
    dim_parents:      dict[str, dict]    # for the single-row filter view
    dim_parents_fb:   dict               # global fallback lookup

def load(xlsx_path: Path, laws_dir: Path) -> LexiconData:
    """Read everything. Apply data fixes inline. Return ready-to-inject."""
    ...
```

Internally, this pulls in:
- `cell_runs`, `parse_legal_sheet`, `parse_analysis_sheet`, `parse_matrix`, `parse_prose`, `load_laws`, `build_ref_map` from `build_v13`
- `cluster_summary_from_matrix`, `build_sub_concepts_v15`, `collect_rich_notes`, `extract_prose_blocks` from `build_v15`
- `_find_best_sub_id`, `_drop_orphan_continuation_rows`, `_clean_law_blobs`, `_rewrite_concepts_const` from `build_v16`
- `_transform_concepts` from `build_v17` (notes reshape)
- `_read_about_blocks` from `build_v18`
- `_build_parent_lookup` from `build_v20`

All of these already exist as pure functions. The refactor copies
them into `lexicon/data.py`, drops the HTML-building code surrounding
them, and wires them into a single `load()` that returns a populated
`LexiconData`.

### `lexicon/shell.py` (~80 lines)

```python
def load_shell(path: Path) -> str:
    """Read reference_style_v16.html."""
    ...

def inject_data(html: str, data: LexiconData) -> str:
    """Replace the reference shell's placeholder CONCEPTS / REF_MAP /
    law blobs / About prose / Methodology prose with real data."""
    ...

def inject_overrides(html: str, overrides: str) -> str:
    """Append CSS + JS overrides block before </body>."""
    ...
```

This is ~half of what build_v17 does today, minus the extraction from
a predecessor HTML (we emit data directly, no round-trip through
JSON-in-HTML).

### `lexicon/features/__init__.py` (~60 lines)

```python
FEATURES = [
    explore_in_full_law,
    matrix_pill_nav,
    about_prose,
    regulations_rename,
    incident_two_col,
    mode_tabs,
    single_row_view,
]

def emit_all(data: LexiconData) -> str:
    """Concatenate each feature's CSS + JS block. Feature modules may
    consume pieces of `data` (e.g. single_row_view uses data.dim_parents)."""
    parts = [f.emit(data) for f in FEATURES]
    return "\n".join(parts)
```

Each feature module exports a single `emit(data) -> str` function that
returns its `<style>...</style><script>...</script>` block. These are
direct lifts from the existing `_v16_overrides`, `_v17_law_drawer_js`,
`_v18_cited_js`, `_two_col_dim_js`, `_v20_overrides_css_js`,
`_v21_overrides_css_js`.

### `build.py` (~60 lines)

```python
HERE        = Path(__file__).parent
XLSX        = HERE / "AI terminology and taxonomy-final.xlsx"
LAWS        = HERE / "laws"
SHELL       = HERE / "reference_style_v16.html"
OUTPUT      = HERE / "digital_lexicon.html"       # just ONE file now

def main() -> None:
    data = lexicon.data.load(XLSX, LAWS)
    html = lexicon.shell.load_shell(SHELL)
    html = lexicon.shell.inject_data(html, data)
    html = lexicon.shell.inject_overrides(html, lexicon.features.emit_all(data))
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUTPUT}  ({len(html):,} bytes)")
```

---

## What's won

1. **No caching trap.** One input → one output. No `rm -f digital_lexicon_v1{6,7,8,9}.html` dance.
2. **Clear separation of concerns.** Data parsing, shell templating, and feature injection are three files with one job each.
3. **Features are additive units.** Adding "v22" is adding `lexicon/features/my_new_thing.py` to the `FEATURES` list. No new `build_vN.py`, no new wrapper layer.
4. **Smaller code surface.** Current chain is ~4,400 lines of Python across 7 files (v13, v15, v16, v17, v18, v20, v21). Estimated clean build: ~600 lines of Python + the feature blocks (which stay the same size, ~2,000 lines of embedded JS/CSS). Net reduction ~40% of Python.
5. **Tests get simpler.** Instead of seven "v17/v18/v19/v20/v21" test suites, one test per feature + one correspondence test on the final HTML. Drop the brittle "which predecessor HTML cached which data" concerns.
6. **Debugging is faster.** A bug in the verbatim cell click used to mean "walk v13 → v15 → v16 → v17 → v18 → v20 → v21 and figure out which layer owns it." Now it's "look at `lexicon/features/single_row_view.py`."
7. **No more `window.handleHash` wrapping for history reasons.** Features designed from scratch can register their routing cleanly instead of patching around predecessor behavior.

---

## What's lost / cost to consider

1. **Git history readability.** Each `build_v{N}.py` currently maps 1:1 to a user-feedback round. After refactor, the mapping is in commit messages. Minor.
2. **Byte-for-byte output parity.** The clean build will likely produce HTML that differs from v21 in CSS ordering, whitespace, and shadow-const placement. Functional equivalence should hold; byte equivalence won't. Existing correspondence tests (which check xlsx-cell presence) still pass. Some pixel-diff visual tests might flag cosmetic differences.
3. **Refactor risk.** About 2,700 lines of data-transformation code get copy-moved into `lexicon/data.py`. Unit tests during the move are essential.
4. **One-time effort.** Realistic estimate: 2–3 days of focused work to produce a clean build that matches v21's behavior, then 1 day to catch regression-test edge cases.

---

## Migration path (recommended: Option C from 3 considered)

### Option A: big-bang rewrite

Write clean build from scratch. Verify byte-identical or
behaviour-identical to v21. Delete old scripts.

**Risk:** high — any missed edge case ships broken.
**Reward:** fastest cleanup.
**Not recommended.**

### Option B: gradual collapse

Merge wrappers pairwise: v20+v21 → one module. Then v17+v18. Then
v13+v15. Incremental, each step testable.

**Risk:** low, but lots of intermediate states. Some wrappers
(especially v17's shell swap) don't compose naturally with neighbors.
**Reward:** steady progress.
**Not recommended** because it still leaves intermediate HTML files
and the caching trap along the way.

### Option C: parallel build, cut over

1. Build `lexicon/data.py`, `lexicon/shell.py`, `lexicon/features/`
   alongside the existing chain, targeting behavioural parity with
   v21. Don't delete anything yet.
2. Add a new entry point `build.py` that produces `digital_lexicon.html`.
3. Add one new test file (`test_lexicon_clean.py`) that runs ALL
   existing assertions (scoped through the current test suites) against
   the new output.
4. When the new build passes every assertion the old chain does,
   **cut over**: rename `digital_lexicon.html` to the canonical output
   and delete `build_v1{3,4,5,6,7,8,9}.py` + `build_v2{0,1}.py`.
5. Keep `digital_lexicon_v21.html` as a snapshot in git for one
   release cycle as a rollback anchor.

**Risk:** lowest — both paths exist simultaneously, diff-able.
**Reward:** decisive cleanup without leaps of faith.
**Recommended.**

### Concrete milestones

| Week | Deliverable | How to verify |
|---|---|---|
| 1.1 | `lexicon/data.py` producing a `LexiconData` dict structurally identical to what v20 injects (CONCEPTS, REF_MAP, law blobs, dim_parents) | `json.dumps(old) == json.dumps(new)` on CONCEPTS + a handful of spot checks |
| 1.2 | `lexicon/shell.py` injecting the data into reference_style_v16.html | produce HTML, diff against v17's output (ignoring the override block); should be very close |
| 1.3 | `lexicon/features/explore_in_full_law.py` etc. (one file per feature) | produce full HTML, diff against v21's output; behavioral tests pass |
| 1.4 | `build.py` wiring all three together | `python3 build.py` writes `digital_lexicon.html`; all 7 existing test suites pass when pointed at it |
| 2.1 | `test_lexicon_clean.py` consolidating assertions | single-file test that covers what v17/v18/v19/v20/v21 tests cover |
| 2.2 | Cut over: rename output, delete legacy builds, update `PROGRESS.md` + `LESSONS.md` | `git rm build_v1{3,4,5,6,7,8,9}.py build_v2{0,1}.py`; `git rm digital_lexicon_v1{6,7,8,9}.html digital_lexicon_v2{0}.html`; keep `v21` as one-release rollback anchor |

---

## Risks and things to double-check before cutover

1. **CEPS notes rich-text runs.** `cell_runs` + `collect_rich_notes`
   in v13/v15 are finicky — they merge adjacent same-bold runs, handle
   NBSP, etc. The refactor must preserve this behavior exactly or
   notes render differently. Direct copy-paste, no "improvements"
   during refactor.
2. **Law-blob cleanup heuristics.** v16's `_clean_law_blobs` strips
   scraped-page nav lines and decides if a raw_text is "plausibly legal
   text" by counting `shall` occurrences. Brittle. Copy verbatim; test
   against Colorado's SB24-205 blob specifically (it's the known edge
   case that drove the original heuristic).
3. **REF_MAP keys contain commas.** `build_ref_map` handles this
   correctly; make sure the clean version doesn't split on `,` when
   resolving references (a real bug found in v16's first implementation).
4. **Sub_id remapping.** v16's `_find_best_sub_id` is fuzzy matching —
   "GPAI" ↔ "general-purpose AI", etc. Known to map 9 rows on the
   current xlsx. Must preserve.
5. **Reference shell version.** `reference_style_v16.html` is the
   design source. If the designer ships v18.7 or v19 of their own
   file, the clean build makes it trivial to swap. Worth confirming
   the designer's versioning pace before locking in.
6. **openpyxl rich-text reading.** Two workbook loads happen today
   (one with `rich_text=True`, one without) because some parsers need
   plain values and others need runs. Preserve both.
7. **xlsx re-reads for About + dim parents.** build_v18 and build_v20
   each re-open the xlsx to read specific sheets. In the clean build,
   do all reads once in `lexicon/data.py` and cache the workbook
   object.

---

## Is it worth it?

**Yes.** The current chain is 2 layers of genuinely useful wrappers
(v17's shell swap, v21's feature tip) plus 5 layers of historical
accumulation. The shell-swap pattern already implies a two-stage
architecture (data → template). The clean build just makes that
architecture explicit.

**Short-term value**: every future feature addition is faster.
No new `build_vN.py`. No worrying about which previous version's JS
to `removeEventListener` to intercept. Just a new feature file.

**Long-term value**: a developer who didn't live through v11 → v21
can read `build.py` and understand the whole system in 5 minutes. The
current chain takes hours to map.

**When to do it**: after the next round of user feedback settles (so
the refactor doesn't race against active feature work). Allow one
planning session to scope `lexicon/data.py` precisely, then a 2–3 day
focused block to execute Option C.

---

## Appendix: dead-code inventory for immediate deletion

These can be removed today without risk (independent of the full
refactor):

- `build_v14.py` — not imported, not in the build chain.
- `digital_lexicon_v11.html`, `digital_lexicon_v12_draft.html` — source
  templates for layers whose output is discarded by v17. Keep a copy
  in git history; delete from working tree.
- `digital_lexicon_v14.html`, `v15.html` — transitional outputs, never
  served.

Files the clean build will eventually replace (but keep for now as
Option C rollback anchors):

- `build_v13.py` through `build_v21.py`
- `digital_lexicon_v16.html` through `digital_lexicon_v21.html`
