# US-006 — EU article-link audit findings

Source-of-truth Excel inventory: `iterations/v28_excel_inventory.md` (US-001).
Source-of-truth v28 cell dump: `outputs/us006_eu_cells.json` (130 EU cells across 6 concepts × multiple sub-concepts × dimensions).

## EU regulatory texts in scope (per Excel)

| Text | Excel short-code | v28 `law-blob` id |
|---|---|---|
| EU AI Act (2024) | `AIA` | `eu-ai-act` |
| Code of Practice — Copyright Chapter | `CoP CC` | `eu-gpai-cop-copyright` |
| Code of Practice — Transparency Chapter | `CoP TC` | `eu-gpai-cop-transparency` |
| Code of Practice — Safety & Security Chapter | `CoP SSC` | `eu-gpai-cop-safety` |
| Guidelines on the scope of obligations for GPAI models | `GL` | `eu-guidelines-gpai-scope` |

(Two extra Commission Guidelines exist in v27/v28 — `eu-guidelines-ai-definition` and `eu-guidelines-prohibited` — but Excel's "About" sheet flags them as out-of-scope of the canonical 12-text framework. Out-of-scope per Excel; not audited under US-006.)

## Audit method

For each of the 130 EU cells, compared the cell's `reference` field (and its analysis-text article citation) against the Excel attribute's expected article reference (per `v28_excel_inventory.md` §4–§6). Categorised:

- **Match**: reference + verbatim agree with Excel
- **Degraded popup**: reference empty but analysis cites the right article (popup falls back to analysis text + the "[Analysis text — no verbatim extracted]" note — content is consistent, header label missing). Per US-005's pattern, this is "consistent but not enriched"; not strictly a mismatch.
- **Mismatch**: reference cites an article that Excel does not list, or omits an article that Excel does list

## Findings

### EU AI Act (`eu-ai-act`)

110+ cells reference EU AI Act articles. Spot-checked:

- **Match**: `provider/scope` (Art 50(1)), `provider/transparency` (Art 50(1,2)), `provider/penalties` (Art 99(3,4,5)), `provider/AI literacy` (Art 4) — all already corrected in US-005.
- **Match**: `provider-of-high-risk-ai-systems/registration` (Art 16(i), 49(1)), `transparency` (Art 50(1,2), 13(1)), `rebuttal` (Art 6(4)), `penalties` (Art 99(4-5)).
- **Mismatch #1**: `provider-of-high-risk-ai-systems / scope-1-0`
  - Analysis cites: "Article 3, Article 6, Annex III"
  - Excel says: "Article 3, Article 6, Annex III"
  - HTML reference: `"AI Act, Article 6; AI Act, Annex III; EU AI Act, Article 25 (1)"`
  - **Missing**: Article 3 (3) provider definition. Asymmetric with the deployer analog (`deployer-of-high-risk-ai-systems / scope-1-0`) which correctly includes `EU AI Act, Article 3 (4)`.
  - **Fix**: prepend `EU AI Act, Article 3 (3)` to reference, prepend the Article 3(3) verbatim definition to verbatim.
- **Match**: `deployer-of-high-risk-ai-systems / scope-1-0` (already correct: includes Art 3(4), 25(1), 6, Annex III).
- **Match**: `deployer-of-high-risk-ai-systems / impact-assessment` (Art 27), `human-oversight` (Art 26(2)), `right-to-explanation` (Art 86(1)), `AI literacy` (Art 4), `transparency` (Art 26(11), 50(3,4)).
- **Match**: `deployer-of-general-purpose-ai-systems` term (Art 3(4), 3(66), 50, 4, 99(4-5)), `scope` (Art 3(4), 3(66)), `transparency` (Art 50), `AI literacy` (Art 4), `penalties` (Art 99(4-5)).
- **Match**: `provider-of-general-purpose-ai-models` term, `transparency` (Art 50(1,2)), `exemptions` (Art 53(2)), `penalties` (Art 99(4-5)).
- **Match**: `provider-of-general-purpose-ai-models-with-systemic-risk` term, `scope-provider` (Art 3(3)), `scope-model` (Art 51(1,2)), `notification` (Art 52(1,2)), `risk-management` (Art 55(1) + CoP SSC), `incident-reporting` (Art 55(1) + CoP SSC), `penalties` (Art 99(3,4,5)), `rebuttal-gpaisr` (Art 52).
- **Match**: `model-system / high-risk-ai-system` term/definition (AIA Art 6(1)(2)), `exemptions` (Art 6(1)(2),(3)(4)).
- **Match**: `model-system / general-purpose-ai-model` term/definition (Art 3(63), 3(65), 51(1)(2)), `exemption` (adds Art 52).
- **Match**: `model-system / general-purpose-ai-system` term/definition/scope (Art 3(66), Recital (100)).
- **Match**: `risk / systemic-risk` term/definition (Art 3(2), 3(65)), scope (Art 51(1)-(2)), exemptions (Art 51(1)-(2)).
- **Match**: `modification / substantial-modification` term/definition (Art 3(23), GL 3.2).
- **Match**: `incident / serious-incident` term/definition (Art 3(49)), scope-high-risk (Art 73(1)), reporting-mechanism-high-risk (Art 73(1),(5)), penalties (Art 99(4), 101(1)).

### Code of Practice — Copyright Chapter (`eu-gpai-cop-copyright`)

- **Match**: `provider-of-general-purpose-ai-models / copyright-8-0` — reference "Code of Practice for GPAI - Copyright Chapter", verbatim is the CoP CC copyright-policy commitments. Aligned with Excel `CoP CC 1.1`.
- **Match**: `provider-of-general-purpose-ai-models-with-systemic-risk / copyright-10-0` — same content, same alignment.

### Code of Practice — Transparency Chapter (`eu-gpai-cop-transparency`)

- The reference label "Code of Practice for GPAI - Transparency Chapter" appears in the term-aggregate ref strings of the two GPAI provider sub-concepts. No standalone TC-only popup cell — the TC content is bundled into specific-information-disclosure cells. Excel `CoP TC 1.1` is cited inline in analysis; reference is empty for those individual cells.
- **Degraded**: `provider-of-general-purpose-ai-models / specific-information-disclosure-7-0` cites "(Article 53; CoP TC 1.1)" in analysis but ref/verbatim empty. Per US-005 pattern this is "consistent but not enriched" — not a strict mismatch.

### Code of Practice — Safety & Security Chapter (`eu-gpai-cop-safety`)

- **Match**: `provider-of-general-purpose-ai-models-with-systemic-risk / risk-management-7-0` — reference "EU AI Act, Article 55 (1); Code of Practice for GPAI - Safety and Security Chapter", verbatim covers both. Aligned with Excel `CoP SSC 1.1`.
- **Match**: same sub-concept's `incident-reporting-11-0` — reference includes CoP SSC chapter twice (a minor duplication but not a content mismatch); verbatim covers Article 55(1)(c) + CoP SSC 9.2/9.3 timelines. Aligned with Excel `CoP SSC 9.3`.
- **Degraded**: `risk-management-review-8-0` cites "(CoP SSC 1.3)" in analysis but ref empty. Not a strict mismatch.
- **Degraded**: `whistleblower-protections-13-0` cites "(Article 87)" + "(CoP SSC 8.3)" but ref empty.

### Guidelines on the scope of obligations for GPAI models (`eu-guidelines-gpai-scope`, "GL")

- **Match**: `model-system / general-purpose-ai-model / compute-threshold-3-0` — ref `(GL, (17))`. Aligned with Excel `GL (17)`.
- **Match**: `model-system / general-purpose-ai-model / term-definition-0-0` — ref includes `(GL, (17))`. Aligned with Excel.
- **Match**: `provider-of-general-purpose-ai-models / scope-1-0` — ref `EU AI Act, Article 3 (3); (GL, (17))`. Excel says "Article 3 ; GL (17) ; GL (59), (60)". This first scope sub-row is specifically about "definition of provider" → Art 3(3) + GL (17). The other two scope sub-rows handle Art 3(63) and the modification criteria (GL (59), (60)).
- **Mismatch #2**: `provider-of-general-purpose-ai-models / scope-system-1-2` (3rd scope sub-row)
  - Analysis cites: "(Article 3) ... (GL, (17)) ... (GL (59)) ... (GL (60))"
  - This sub-row's content is the modification-criteria continuation
  - HTML reference: `"(GL, (17))"`
  - **Should be**: `"(GL, (59)); (GL, (60))"` (those are the article numbers the sub-row's content actually corresponds to per Excel)
  - **Fix**: replace reference accordingly. Verbatim stays empty (analysis-fallback is the right behavior here since GL doesn't have a structured sections blob).

## Out-of-scope cells (not fixed in US-006)

- Cells with empty `reference` whose analysis cites a specific article are NOT mismatches per the audit definition above (they're degraded popups, but consistent). Enriching every such cell with verbatim+reference is a separate task (likely US-007 or beyond) — would require pulling the full article text from `law-blob-eu-ai-act` for ~30 additional cells.
- The two extra Commission Guidelines (`eu-guidelines-ai-definition`, `eu-guidelines-prohibited`) are flagged in `v28_excel_inventory.md` §7 issue #1 as out-of-Excel-scope. Their popups are not audited here.
- The `model-system / general-purpose-ai-model / definition-1-0` cell uses the un-prefixed reference `AIA Article 3(63); AIA Article 3(65); AIA Article 51(1), (2)` while other cells use `EU AI Act, Article X` — citation-format inconsistency flagged in `v28_excel_inventory.md` §7 issue #8. Cosmetic; not changed in US-006.

## Browser-verification plan (5 spot-checks per EU text)

For each of the 5 in-scope EU texts, click into the relevant cell on the rendered HTML and confirm the popup's `drawer-ref.textContent` and `drawer-verbatim.textContent` match the cited article.

- **EU AI Act**: provider/scope (Art 50(1)), provider-of-high-risk/registration (Art 16(i)+49(1)), provider-of-high-risk/scope (after fix, Art 3(3)+6+Annex III+25(1)), GPAISR/notification (Art 52(1,2)), deployer-of-high-risk/right-to-explanation (Art 86(1)).
- **CoP CC**: GPAI/copyright (CC reference), GPAISR/copyright (CC reference) — both verify.
- **CoP TC**: term-aggregate strings only (no standalone TC popup at single-cell level).
- **CoP SSC**: GPAISR/risk-management (Art 55(1)+CoP SSC), GPAISR/incident-reporting (Art 55(1)+CoP SSC).
- **GL**: `compute-threshold-3-0` (GL (17)), provider-of-GPAI/scope-1-0 (Art 3(3)+GL (17)), after fix `scope-system-1-2` (GL (59)+(60)).
