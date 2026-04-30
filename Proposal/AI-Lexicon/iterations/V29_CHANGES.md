# Digital AI Lexicon — v29 changes

`iterations/digital_lexicon_v29.html` (~3.5 MB, forked from v28 at commit `cc52e23`).

## 1. Bill labels in the concepts matrix

The Concepts page matrix now shows the bill in brackets next to every non-EU jurisdiction term, e.g. *Foundation model (SB 53)*, *High-risk AI system (SB 24-205)*, *Developer (HB 149)*. The EU column stays bill-free.

- New JS helpers `_v29FormatBill` and `_v29CellLabel` in `renderMatrix`
- Bill format normalised: `SB24-205` → `SB 24-205`, `SB942` → `SB 942`, `HB149` → `HB 149`, `AB2013` → `AB 2013`. Single-letter prefixes (`S8828`, `A6453B`) kept as-is.
- Comma-joined bills (e.g. `AB2013, SB942`) take the first entry.
- The cluster-matrix variant pill renderer (`_renderClusterMatrix`) was patched in the same way.

## 2. Status pills removed from the Regulations page

Removed all 13 `<span class="status-pill ...">` labels (*In effect*, *Interpretive guidance*, *Voluntary guidance*, *Amendment*) from `law-card-v2` headers. The CSS rules are kept — they're inert without consumers and removing them would touch unrelated lines.

## 3. Drawer renders law-blob articles, not verbatim text

The drawer that opens when you click an analysis cell now displays the actual article text from the embedded law-blob, replacing the per-cell `verbatim` field.

- Stripped the *Explore in full law →* button (it's now the default behaviour).
- Drawer header label changed: *Verbatim citation* → *From the law*.
- One card per resolvable atomic reference (cells with `;`-joined references render multiple stacked articles).
- Each card shows: citation key, link to the official source URL, article/section title, body text.
- Graceful fallback for citations whose anchor isn't separately ingested:
    - recitals lookup → `blob.recitals[id]`
    - annexes lookup → `blob.annexes` array
    - else → searchable raw bill text with a hint to use ⌘F / Ctrl+F.

### 3a. Body formatting (nested indentation)

Added `_formatBody(text)` in the IIFE so the drawer body matches the EUR-Lex layout:

- Splits on blank lines.
- Orphan `(a)` / `(b)` / `(ii)` markers merge with their following paragraph.
- Paragraphs get a level class (`v29-p0` flush, `v29-p1` for single letters, `v29-p2` for multi-character roman numerals).
- CSS uses `padding-left + text-indent` for hanging-indent bullets and `<span class="v29-marker">` to align the marker.

## 4. Concept-page column subtitles use the bill

The per-jurisdiction column subtitle on the analysis table previously showed the law name (e.g. *California*, *New York*) — duplicating the column header. v29 shows the bill instead, so:

- EU → `EU AI Act` (unchanged)
- CA → `SB 53` / `SB 942` / `AB 2013` (depends on sub-concept variant)
- CO → `SB 24-205` · NY → `S8828` / `A6453B` · TX → `HB 149` · UT → `SB 226`

Patched all four `renderAnalysisTable` sites (the original + three later wrappers) to branch on `j === 'eu'`. Bill formatter reused from the matrix change.

## 5. REF_MAP swapped for the generated lookup

The embedded `window.REF_MAP` is now the 191-entry build from `outputs/reference_lookup_atomic_map.json`.

- Bare anchors: `"3"` instead of `"3-3"` (paragraphs/subparagraphs are kept as separate fields rather than joined into the anchor).
- Coverage: 95% of cell references match a real article/section in the law-blob; the remaining 5% are external statute references (Colorado Consumer Protection Act, Civil Code, Utah Code) that don't have a separate ingestable doc.

## 6. Law-blob refreshes

| Blob | Source | What changed |
|---|---|---|
| `laws/eu-ai-act.json` | web.archive.org snapshot of EUR-Lex CELEX:32024R1689 | Rebuilt all 113 article bodies (the previous `text` fields were artificialintelligenceact.eu navigation cruft); added 180 recitals (was 4); added 13 annexes (was 0). Cleaned `10(^25)` → `10²⁵` artifacts. |
| `laws/ny-s8828.json` | web.archive.org of nysenate.gov/bills/2025/S8828 | Replaced (the file was actually populated with S6953 content, missing §1426–1429); now §1420–1429. |
| `laws/tx-hb149.json` | existing data, cleanup pass | Collapsed `\n \n \n` whitespace runs from PDF extraction. |

Plus two re-runnable refresh scripts:

- `iterations/laws/refresh_eu_ai_act.py`
- `iterations/laws/refresh_ny_s8828.py`

Cached source HTML kept in `iterations/laws/eu-ai-act-eurlex.html` (1.2 MB) and `iterations/laws/ny-s8828-source.html` (124 KB) so the refresh is idempotent.

## 7. GPAI guidelines disambiguation

`(GL, (17))`, `(GL, (59))`, `(GL, (60))`, `(GL, 3.2)` references now resolve to `eu-guidelines-gpai-scope` (all five live in GPAI-model concepts in the current dataset). The build script (`iterations/build_reference_lookup.py`) maps numeric markers to a paragraph-kind anchor with a `preamble` fallback when the exact anchor isn't separately parsed.

## Files changed

```
iterations/digital_lexicon_v29.html        (new, ~3.5 MB)
iterations/test_lexicon_v29.py             (new — fork of v28 + 8 v29-specific tests)
iterations/build_reference_lookup.py       (new, builds outputs/reference_lookup_*.json)
iterations/laws/refresh_eu_ai_act.py       (new, fetches & parses EUR-Lex)
iterations/laws/refresh_ny_s8828.py        (new, fetches & parses NY Senate page)
iterations/laws/eu-ai-act.json             (rebuilt: 113 articles + 180 recitals + 13 annexes)
iterations/laws/ny-s8828.json              (refreshed: §1420–1429)
iterations/laws/tx-hb149.json              (whitespace cleanup)
iterations/laws/eu-ai-act-eurlex.html      (cached snapshot)
iterations/laws/ny-s8828-source.html       (cached snapshot)
outputs/reference_lookup.json              (canonical lookup, raw-keyed)
outputs/reference_lookup_atomic_map.json   (REF_MAP-shape, 191 entries)
outputs/reference_lookup_atomic.json       (per-atomic provenance)
outputs/reference_lookup_unmatched.csv     (8 external-statute refs)
outputs/reference_lookup_delta.csv         (diff against v28 REF_MAP)
outputs/reference_lookup_summary.md        (coverage stats)
```

## Coverage summary

| law_id | matched / total | notes |
|---|---|---|
| eu-ai-act | 140 / 140 (100%) | up from 130/140 in v28 |
| co-sb24205 | 39 / 39 (100%) | |
| ny-s8828 | 30 / 30 (100%) | up from 0/28 in v28 (S6953 stub fixed) |
| ca-sb53 | 23 / 23 (100%) | |
| ut-sb226 | 18 / 18 (100%) | |
| tx-hb149 | 16 / 16 (100%) | |
| ca-sb942 | 11 / 11 (100%) | |
| ca-ab2013 | 11 / 11 (100%) | up from 0/11 in v28 (parser bill-id fix) |
| ny-a6453 | 11 / 11 (100%) | up from 0/11 in v28 (parser bill-id fix) |
| eu-guidelines-gpai-scope | 7 / 7 (100%) | up from 0/7 in v28 (GL disambiguation) |
| eu-gpai-cop-* | 9 / 9 (100%) | |
| (external statutes) | 0 / 8 | CCPA, Civil Code, Utah Code — no separate ingestable docs |

**315 / 323 atomic citations matched · 49/49 tests passing** (16 v28 + 24 v29 + 9 rendering/correspondence).

## Tests

`iterations/test_lexicon_v29.py` — fork of `test_lexicon_v28.py` retargeted to `digital_lexicon_v29.html`, plus 8 new tests:

- `test_v29_bill_label_helpers_present` — `_v29FormatBill` and `_v29CellLabel` exist; cluster-matrix branches on `j !== 'eu'`.
- `test_v29_status_pills_removed_from_regulations` — no `<span class="status-pill` anywhere; no `law-card-v2` references the class.
- `test_v29_drawer_renders_articles_not_verbatim` — `__v29_udc_patched` flag, `_renderDrawerArticles` defined, *Explore in full law* string absent, drawer label is *From the law*.
- `test_v29_drawer_body_formatter_present` — `_formatBody` defined, used by `_renderArticle`, CSS classes `.v29-p0/p1/p2` present.
- `test_v29_concept_subtitles_show_bill` — header subtitle branches on `j === 'eu'`; bill formatter pattern appears ≥4×.
- `test_v29_ref_map_has_bare_anchors` — REF_MAP ≥180 entries, `EU AI Act, Article 3 (3)` anchored at `"3"`, `NY S8828 §1428` resolvable.
- `test_v29_eu_ai_act_blob_has_annexes_and_full_recitals` — 13 annexes (incl. III/IV/XI/XII), 180 recitals (incl. recital 100).
- `test_v29_ny_s8828_blob_has_full_sections` — §1420, §1425, §1426, §1427, §1428, §1429 all present.

Run: `python3 -m pytest test_lexicon_v29.py -q`
