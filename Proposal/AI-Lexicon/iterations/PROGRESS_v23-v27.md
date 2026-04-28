# Digital AI Lexicon — progress log v23 → v27

Notes for the 2026-04-26 review cycle. Each version is a post-process on the
previous HTML; the canonical chain runs from v11 → v22 (existing) → v23 → v24
→ v25 → v26 → v27 (this round).

All v23+ work lives in `iterations/`. The Dropbox sibling workspace
(`~/CEPS-DST Dropbox/.../cb_sep_25/AI-Lexicon/`) is an older parallel tree and
is not part of the deploy chain.

## Versions shipped

| Version | What it is |
|---|---|
| `digital_lexicon_v23.html` | v22 + regulation #12 wired in (`eu-guidelines-gpai-scope` / GUIDEL~2.PDF). Anchor-resolution patch (progressive suffix-strip) so e.g. `22757.11-c` resolves to `22757.11`. NY A6453 parser anchor extraction fixed. Aggressive cell-text re-sync from xlsx (+9 cells). |
| `digital_lexicon_v24.html` | Adds new sub-concept "Provider of limited-risk AI systems" (xlsx Provider_Developer_Analysis R1–R20). Multi-strategy cell matcher (+92 cells beyond v23). Coverage 86.3% → 95.3%. |
| `digital_lexicon_v25.html` | Closes the remaining xlsx → HTML gap. `parse_reference` learns `(GL, n)` / `(GL, n.m)` notation routing to `eu-guidelines-gpai-scope`. 5 specific GPAISR/Modification body cells re-synced. Truncation prevention. Coverage 95.3% → 100%. |
| `digital_lexicon_v26.html` | Regulations page EU section now has 3 cards (was 2 with header still saying "3 frameworks"). New card: "Guidelines on the scope of the obligations for general-purpose AI models established by AIA (2025)" placed AIA → GL → CoP. Methodology Step 3 gains a sibling list-item referencing "(GL)". |
| `digital_lexicon_v27.html` | **Current.** Home, Regulations, and Methodology copy now sourced from the Cross-checked xlsx ("About the Digital AI Lexicon" + "Methodology" sheets). 12 regulation cards swapped to xlsx-authoritative descriptions. 6 methodology steps replaced with verbatim xlsx narrative. Build is byte-identical idempotent. |

## v23 change detail (2026-04-26)

`build_v23.py` post-processes v22.

**Reg #12 wiring.** `laws/eu-guidelines-gpai-scope.json` (GUIDEL~2.PDF, 6
sections + 99,870 chars raw_text) was already on disk but never embedded.
v23 inserts the `<script type="application/json" id="law-blob-eu-guidelines-gpai-scope">`
tag, extends the `LAW_STUBS` map, and adds an entry to the European Union
region of the Regulations nav (placed between AI-system Definition Guidelines
and the CoP — chronological by effective date). v23 also creates `final_tool.html`
and `final_lexicon_tool.html` mirrors at the parent path.

**JS anchor patch.** v22's `openLawDrawerById` did exact-match on `articles[].id`
or `sections[].id`. So anchors like `22757.11-c` (built by `parse_reference`
as `section-paragraph`) silently fell back to the first item — 49% land
accuracy across REF_MAP. v23 wraps the function with progressive
suffix-strip (drop trailing `-token` up to 2x) so `22757.11-c` → `22757.11`
finds the real section.

**NY A6453 parser fix.** `build_v13.parse_reference` returned an empty anchor
for any `New York A6453, …` reference. Now it extracts `§1420(...)` →
anchor `1420[-paragraph]`.

**Aggressive cell text updater.** v22's fuzzy concept-name matcher missed
~16% of analysis-cell updates because xlsx sub-section titles diverged from
v21 sub-concept names (e.g. "GPAI" ↔ "general-purpose AI"). v23 walks each
cell whose current text is not a substring of any xlsx cell, then re-fetches
by `(jid, dim_label)` index. +9 cells re-synced.

## v24 change detail (2026-04-26)

`build_v24.py` post-processes v23.

**New sub-concept "Provider of limited-risk AI systems".** The new
Cross-checked xlsx introduces this as rows 1–20 of `Provider_Developer_Analysis`.
v22's `_apply_concept_updates` only updates existing slots — it doesn't add
new sub_concepts. v24 builds the sub_concept fresh: 11 dimensions, 3
jurisdictions (eu/co/tx), verbatim/reference fields harvested from the OLD
xlsx `Provider_Developer` sheet. Inserted at the head of `provider-developer.sub_concepts`
(below the high-risk/GPAI variants).

**Continuation-aware xlsx parser.** v22's row walker stopped at blank-A rows.
v24 folds multi-line dim text (Penalties, Scope, Transparency continuations)
that v22 dropped, then runs a multi-strategy matcher: exact-section →
any-section → fuzzy-overlap. +92 cells re-synced beyond v23's 9.

Coverage rose from 86.3% to 95.3%.

## v25 change detail (2026-04-26)

`build_v25.py` post-processes v24. Closes the residual 4.7% gap.

**The `(GL, …)` notation.** The xlsx introduces inline reference tokens
like `(GL, (17))`, `(GL, 3.2)` referring to the Commission Guidelines on
GPAI scope (reg #12). `parse_reference` had no rule for them. v25 patches
`build_v13.parse_reference` in place:

| Input form | Routing |
|---|---|
| `(GL, N.M)` (e.g. `3.2`, `3.4`) | `eu-guidelines-gpai-scope` / parent section `N` |
| `(GL, (n))` paragraph reference | bucketed by paragraph range: 1–11→§1, 12–70→§2 (paragraph 17 lands here), 71–140→§3, 141–170→§4, 171+→§5 |
| `(GL,)` bare | whole law (anchor `""`) |

**Specific cells re-synced.** v25 hand-targets 5 missing cells where the
fuzzy matcher couldn't connect:

- `Provider_Developer_Analysis B97` → `Possibility to rebut GPAISR
  classification…` into the GPAISR sub-concept (new "Rebuttal" dim, EU column).
- `Modification_ANALYSIS B5/B12/B13` → GPAI-specific Modification continuations
  (Definition, Obligations triggered, GPAISR notification) — appended to EU
  cells of the modification concept.
- `GPAI_Frontier_Foundation_Analys B8` → `General-purpose AI model: 10^23
  FLOPs plus capability to generate language…` appended to the regular GPAI
  sub-concept's Compute-threshold dim, EU column.

**Truncation prevention.** Inspect built-up cells for v15-era abbreviated
versions; replace with the full xlsx text (high-risk B4 EU Definition was
the worst offender).

**`(GL, …)` in cell.reference.** For every dim cell whose `analysis` contains
a `(GL, …)` token, append the token to `cell.reference` if not already
there. The "See verbatim in full law" button now opens reg #12 from those
cells. 6 cells gained GL references.

Coverage: 257/257 = **100%** against the new xlsx.

## v26 change detail (2026-04-26)

`build_v26.py` post-processes v25.

**3rd EU framework card.** The Regulations page (`#p-laws`) EU section
header said "3 frameworks" but only rendered 2 `law-card-v2` articles
(AIA, CoP). v26 inserts a 3rd card between AIA and CoP for the GL
Guidelines: status pill `voluntary` ("Interpretive guidance"), description
verbatim from xlsx Methodology R20C3, effective `19 Nov 2025`,
`<div class="law-cited-in" id="cited-GL"></div>` mirroring the
`cited-AIA` / `cited-CoP` pattern.

**Methodology Step 3 cross-reference.** Added a sibling `<li>` under
`#step-3` immediately after the EU AI Act bullet:
`Cross-reference the Commission Guidelines on the scope of obligations for
providers of general-purpose AI models (C(2025) 7719, 19 Nov 2025; cited
as "(GL)" in the comparative analysis).`

## v27 change detail (2026-04-26)

`build_v27.py` post-processes v26. Aligns the user-facing prose on three
pages with the Cross-checked xlsx.

**Home page.** Replaced the `landing-tagline` + `landing-sub` block with the
About sheet's three body paragraphs (kept the H1; dropped the redundant
"two modes" intro and `about-bullets` list since they aren't in the xlsx).
Authoritative facts now: "43 terms across **12 regulatory frameworks**",
"EU's AI Act as a reference point", "side-by-side EU–U.S. comparisons",
study reference `NDICI FPN FPI /2022/432-762`.

**Regulations page.** 12 cards re-described from xlsx Methodology R18–R29:

| Card | xlsx row |
|---|---|
| AIA | R18 (2-paragraph desc, 10²⁵ FLOPs preserved) |
| CoP | R19 |
| GL | R20 (effective corrected to 2 Aug 2025) |
| SB 53 | R21 |
| SB 942 | R22 |
| Colorado SB24-205 (CAIA) | R23 (2-paragraph) |
| SB 25B-004 | R24 (date kept from v26 as xlsx D24 was empty) |
| NY A6453B | R25 |
| NY S8828 | R26 |
| TX HB149 (TRAIGA) | R27 |
| Utah SB 149 (AIPA) | R28 |
| Utah SB 226 | R29 |

Multi-paragraph descriptions render as multiple `<p class="law-card-v2-desc">`
to preserve the existing CSS hook.

**Methodology page.** All 6 step bodies replaced with xlsx Methodology A1
verbatim. Lead paragraph as `<p>`, numbered points as `<ol>`, trailing
paragraph as `<p>`. Step 3 keeps the v26 GL `<li>` as the 5th item
(after the 4 xlsx items). Headings + `step-N` ids preserved.

## Test surface (2026-04-26)

| Test file | Count | Targets |
|---|---|---|
| `test_lexicon_correspondence.py` | 5 | Existing (xlsx coverage, notes alignment, cluster summary, ref resolution, bill codes) |
| `test_lexicon_v23.py` | 12 | E1–E5 instruction-element acceptance: xlsx 1:1, CEPS notes, reg #12 wiring, anchor resolution rate, sample article references, click-flow correctness |
| `test_lexicon_v24.py` | 6 | Limited-risk sub-concept presence + dimensions; coverage threshold raised to 0.97 |
| `test_lexicon_v25.py` | 7 | GL routing (parse_reference returns `eu-guidelines-gpai-scope`), GL refs on ≥4 cells, no truncation, 5 specific cells present, coverage ≥97% |
| `test_lexicon_v26.py` | 4 | EU section has 3 cards; GL card text present; methodology mentions GL; status pill class |
| `test_lexicon_v27.py` | 5 | Home page xlsx text; study reference; regulation card descs match xlsx; methodology step copy from xlsx; v26 GL bullet retained |

**Run all:**

```bash
cd iterations
python3 -m pytest test_lexicon_correspondence.py test_lexicon_v23.py test_lexicon_v24.py test_lexicon_v25.py test_lexicon_v26.py test_lexicon_v27.py -q
# 39 passed in ~1.5s
```

## Recurring rebuild recipe

```bash
cd iterations

# v23 onward post-process the previous HTML; rebuilding from scratch:
python3 build_v22.py   # rebuilds v22 from v21
python3 build_v23.py   # v22 → v23 (reg #12, anchor patch, NY parser, +9 cells)
python3 build_v24.py   # v23 → v24 (limited-risk sub-concept, +92 cells)
python3 build_v25.py   # v24 → v25 (GL routing, 100% coverage)
python3 build_v26.py   # v25 → v26 (3rd EU card, methodology bullet)
python3 build_v27.py   # v26 → v27 (xlsx-sourced Home + Regs + Methodology copy)

# Or just run v27 since it cascades through the chain via subprocess.
python3 -m pytest test_lexicon_correspondence.py test_lexicon_v23.py test_lexicon_v24.py test_lexicon_v25.py test_lexicon_v26.py test_lexicon_v27.py -q
```

Each build writes `digital_lexicon_vNN.html` and mirrors v27 to
`../final_tool.html` and `../final_lexicon_tool.html`.

## Known gaps / nice-to-haves

- **`cited-LID` chip wiring** — v25/v26 created `<div class="law-cited-in"
  id="cited-GL">` containers mirroring the AIA/CoP pattern, but the page's
  JS doesn't yet populate any of these chips dynamically. They render as
  empty divs. Wiring would require iterating CONCEPTS, counting cells whose
  resolved REF_MAP law matches each `cited-LID`, and injecting chip text.
- **Annex coverage** — `eu-ai-act` blob has 0 annexes embedded; references
  to `Annex III/IV/XI/XII` in cell text resolve to law=eu-ai-act but no
  matching anchor (falls through to first article). Upstream
  `laws/fetch_laws.py` issue.
- **Texas HB149 sections** — only `552.104` is in the embedded blob;
  references to other 552.NNN sections silently fall back. Same upstream fix.
- **Colorado sections** — `co-sb24205` has empty `sections[]`, every CO
  link lands on `raw_text`. Same upstream fix.
- **Per-card "cited in N concepts" pills** — see first bullet.
- **Build chain consolidation** — 13 build files (`build_v13.py` through
  `build_v27.py`) is heavy. A clean refactor (single `build.py` + xlsx
  parser module + HTML emitter) was scoped in `CLEAN_BUILD_PLAN.md`; not
  yet executed.
