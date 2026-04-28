# Lessons learned — Digital AI Lexicon build chain

Cross-cutting lessons from the v16 → v21 iteration. Companion to
`PROGRESS.md` (per-version changelog). If you're picking this project
up, read this first.

---

## 1. The build-chain caching trap

Each layer is a wrapper:
`build_v13 → build_v15 → build_v16 → build_v17 → build_v18 → build_v20 → build_v21`.
Every `build_vN.py` has this pattern at the top of `main()`:

```python
if not HTML_V{N-1}.exists():
    build_v{N-1}.main()
```

**Consequence:** if `digital_lexicon_v{N-1}.html` already exists on disk,
the predecessor layer is NOT rebuilt — even if the xlsx or law JSON
changed. Downstream HTML ships with stale data silently.

This bit us hard on v18 (a build_v15 fix for the "no verbatim" bug
didn't propagate because v17 and v18 reused cached predecessor HTML).

**Rule of thumb:** after editing xlsx, law JSON, or any build_vN
before the tip:

```bash
rm -f digital_lexicon_v1{6,7,8,9}.html digital_lexicon_v2*.html
python3 build_v21.py
```

Each build_vN docstring now calls this out. If you add build_v22, keep
the reminder.

---

## 2. Window events: `useCapture` doesn't guarantee priority

I wrote v19 assuming `window.addEventListener('hashchange', fn, true)`
would fire BEFORE the shell's bubble-phase listener. It doesn't. For
events dispatched directly to `window` (no tree to traverse), listeners
fire in **registration order**, and `useCapture` is effectively
ignored.

Empirical test (minimal page, bubble listener registered first, capture
second): fire order = `[bubble, capture]`.

**What works instead:** if you need to intercept a window event before
the shell's listener, `removeEventListener` the shell's handler and
re-add your wrapper. This worked because the shell declared
`function handleHash(){...}` (creates `window.handleHash`). `let` /
`const` declarations wouldn't have been reachable.

```js
var orig = window.handleHash;
window.removeEventListener('hashchange', orig);
window.handleHash = function(){ /* ... */ orig.call(this); /* ... */ };
window.addEventListener('hashchange', window.handleHash);
```

---

## 3. Top-level `let` / `const` ARE visible across `<script>` tags,
## but NOT on `window`

The shell has `let state = {...}` at top-level inside its `<script>`.
Later `<script>` tags can reference `state` directly (`typeof state`
returns `"object"`), but `window.state` is `undefined`.

Contrast with `function foo(){}` at top-level: reachable BOTH as `foo`
and as `window.foo`. That's why we can wrap `window.handleHash` but
can't wrap `window.state`.

Implication: my early v19/v20 IIFEs have `if (typeof state === 'undefined') return;`
as a safety bail. That works. `if (!window.state) return;` would NOT
work — it'd bail even though state exists.

---

## 4. `history.replaceState` is silent — it does not fire `hashchange`

Great when you want to normalize the URL without retriggering your
routing. Important because:

- The shell's `go()` uses `history.replaceState` to write the
  canonical hash (`#/concept/<id>?sub=N`). This strips any query param
  the shell doesn't know about (like our `?view=verbatim`).
- My capture-listener approach (v19) assumed hashchange would fire
  after `go()` rewrites the hash — it doesn't.

**Pattern that worked (v20):** snapshot the view param via
`_getViewFromHash()` inside `handleHash` BEFORE calling `origHH` (which
strips it), then re-apply via `history.replaceState` on the next
`requestAnimationFrame`.

---

## 5. Analysis sheet loses parent-dim info; the legal sheet has it

The xlsx has two sheet types per concept:
- `*_Analysis` (e.g. `Deployer_Supplier_Analysis`) — col A = dim label
  (usually just the sub-dim, no parent), col B+ = per-jurisdiction
  analysis text.
- `*` (e.g. `Deployer_Supplier`) — col A = parent dim, col B = sub-dim,
  col C+ = per-jurisdiction verbatim.

`sc.dimensions[*].label` in the built JSON comes from the analysis
sheet (via `build_v15`) and is therefore **lossy** for hierarchy.
v15's code already sets `dim.sub_label` (e.g. Incident's two Scope rows
correctly get "High-risk AI systems" / "GPAI models with systemic
risks"), but `dim.parent_label` is always None.

**Solution (v19/v20/v21):** re-parse the legal sheets at build time,
emit `V20_DIM_PARENTS` keyed by `(concept_id, sub_label_lowercased)`,
with a global-fallback lookup that merges votes across concepts +
a hardcoded map for curator-only abstractions (Regulatory trigger,
Compute threshold, etc. — these never appear in the legal sheet).

Without the hardcoded map, rowspan grouping breaks: `Transparency` and
`AI literacy` resolve to "Obligations", but `Risk management` (between
them) doesn't — split into three separate single-rowspan "Obligations"
cells instead of one rowspan=4.

---

## 6. openpyxl merged cells ≠ blank cells, but for this xlsx they look the same

`ws.cell(r, c).value` returns `None` for:
- A truly blank cell, AND
- A cell that's part of a merge but isn't the top-left anchor.

If you assume merged cells via "None means continuation", you'll be
wrong half the time. Check `ws.merged_cells.ranges` explicitly.

**For this xlsx specifically:** the curator doesn't merge cells in
col A. They repeat the value across rows (`Obligations` / `Obligations`
/ `Obligations`) OR leave true blank rows as spacing. So rowspan
grouping reduces to "consecutive rows with the same col-A value" —
simpler than the merged-cell handling I originally planned.

---

## 7. Wrap vs. replace: different idioms for different situations

- **Wrap when you want the original's side effects.** `renderAnalysisTable`
  updates CEPS notes, installs focus highlight, etc. — we want all
  that, then override the table body. Pattern: `orig.apply(this, args); _myExtra()`.
- **Replace when you need to intercept BEFORE the original runs.**
  `handleHash` had to re-read the view param before `go()` stripped
  it. Pattern: `removeEventListener(orig); wrap; addEventListener(wrap)`.

Getting this wrong leads to subtle ordering bugs where the original
runs with the "wrong" state.

---

## 8. Test flakiness: `go is not defined` under batch runs

The `/browse` daemon sometimes evaluates `go('concept', ...)` before
the shell's script has finished executing, especially on rapid repeat
runs. Standalone runs almost always pass; sequential batch runs fail.

**Fix (applied in test_lexicon_v21):** poll `typeof go === 'function'`
for up to 3 seconds after `goto` + `wait --load`:

```python
for _ in range(30):
    out = _browse("js", "typeof go").strip()
    if "function" in out: break
    time.sleep(0.1)
time.sleep(0.3)
```

Any new test that calls `go(...)` should start with this poll.

---

## 9. rAF chains don't survive rapid-fire clicks in tests

My first v20 test tried to click 5 verbatim cells in sequence then
check for `.v17-full-article`. Each cell click opens the drawer and
schedules a `requestAnimationFrame` callback to click the Explore
button. But subsequent clicks beat the rAF callbacks — the callback
for cell[0] fires after cell[4]'s drawer has opened. Test was
unreliable.

**Fix:** click ONE cell, `time.sleep(0.5)`, then assert. Don't loop.

---

## 10. UX feedback loop: v19 → v20 → v21

The design changed substantially across three iterations based on
user feedback, not pre-planning:

- **v19**: Top-level Analysis + Verbatim nav tabs → confusing, both
  landed on identical matrix views.
- **v20**: Single top nav, Analysis / Legal text tabs INSIDE the
  concept page (underline style, below sub-concept tabs) → clearer
  hierarchy.
- **v21**: Legal text view with dim/sub filter + one-row-at-a-time
  + full unclamped text → focused for actual legal reading.

The wrapper-layer pattern made this painless: each version reads the
previous HTML, adds overrides, doesn't touch predecessors. v19 still
works standalone; v20 skips v19 and reads v18 directly.

**Lesson:** when iterating UX, lean on additive wrappers. Don't ship
a grand plan — ship a thin layer, get feedback, ship another layer.

---

## 11. Two render strategies for "single-source-of-truth" displays

**v20's full-matrix Legal text view** (dropped in v21): all rows, all
jurisdictions, cells clamped to 6 lines. Good for bird's-eye
comparison, bad for actual reading.

**v21's filtered single-row view**: two dropdowns + prev/next +
unclamped full text. Good for detailed reading, bad for scanning the
full structure at a glance.

Both are valid for different purposes. The user asked for v21 because
they'd actually read the text, not scan it. Don't assume overviews
beat drill-downs — it depends on the task.

---

## 12. Inline SVGs beat icon fonts for single-file HTML

v20's mode tabs initially had inline SVG icons. The user asked for
plain text tabs (matching their screenshot). Removing the SVGs was
one commit. Had they been font-icon references, we'd have needed to
strip a font file too.

General pattern for this project: keep everything inline. The
single-file offline guarantee is valuable for a static research tool.

---

## Appendix: files + their jobs

- `build_v13.py` — xlsx parser. Produces per-concept JSON with
  `sub_concepts[*].dimensions[*].cells[jid]{analysis, verbatim,
  reference}`. Also sets `dim.sub_label` (not `parent_label`).
- `build_v15.py` — shell JSON population. Matches analysis-sheet dims
  to legal-sheet entries via `legal_by_dim` lookup (fixed in the v18
  session to also index by sub-label tail, not just rowLabel — the
  "no verbatim for Deployer/AI literacy" bug).
- `build_v16.py` — post-processing: sub_id remapping, orphan row
  cleanup, law-blob cleanup, "Explore in full law" button, pill
  navigation rewiring.
- `build_v17.py` — reference-shell swap. Replaces the v14 layout with
  the designer's cleaner shell while preserving v16's data.
- `build_v18.py` — final edits: About-sheet home copy, Laws →
  Regulations rename, cited-paragraph highlight, Incident two-col dim
  split.
- `build_v20.py` — in-page Analysis / Legal-text mode tabs. (v19
  shipped but was reshaped per user feedback; build_v19 left in repo
  for history.)
- `build_v21.py` — single-row Legal-text view with dim/sub filter +
  prev/next. **Current tip.**

Each test file (`test_lexicon_*.py`) pins its layer's behavior.
Seven test suites total at tip: correspondence, rendering, v17, v18,
v19, v20, v21. All pass standalone; rapid sequential batch can trip
the pre-existing "go is not defined" flake on v17's DOM test.
