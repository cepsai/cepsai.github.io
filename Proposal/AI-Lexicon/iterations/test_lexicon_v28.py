"""test_lexicon_v28.py — acceptance tests for v28.

v28 starts as a byte-equivalent scaffold of v27. It reuses the same
xlsx-driven copy swaps onto the Home, Regulations, and Methodology
pages. Subsequent user stories will modify v28 with article-link audit
fixes, superscript FLOPs, and terminology adjustments.

Tests:
  T1. Home page shows "43 terms across 12 regulatory frameworks".
  T2. Home page shows "NDICI FPN FPI /2022/432-762".
  T3. Regulations page descs spot-check (AIA / GL / SB 53), with
      exponents rendered as <sup> markup (US-003).
  T4. Methodology Step 1 body contains "EO 14179 (2025)" and
      "Export of the American AI Technology Stack".
  T5. Methodology Step 3 keeps the v26 GL bullet (Commission Guidelines
      / "(GL)" notation).
  T6. US-003 — every exponent occurrence renders as either <sup>
      markup (static HTML) or a Unicode superscript run (script
      blobs); no plain ASCII `10^25` / `10**25` / `10(^25)` remains.
  T7. US-004 — opening category-table EU cells for the limited-risk
      anchor terms read "Provider of limited-risk AI systems" and
      "Deployer of limited-risk AI systems" (Excel-canonical;
      "Deployer", not "Developer").
  T8. US-005 — limited-risk Provider table cells link to the article
      cited in their analysis text (Scope EU → Art. 50; Transparency
      EU → Art. 50; AI literacy EU → Art. 4; Reg trigger / General
      info / Risk management TX → 552.103; Transparency CO → §6-1-1704)
      and the misplaced Article 3 (3) verbatim no longer appears under
      Scope EU.
  T9. US-008 — every US-state cell whose analysis text cites an article
      / section has a non-empty `reference` field, and a handful of
      manually-corrected cells (CA modification REF_MISMATCH, CO
      modification scope, TX rebuttal extension, CA penalties
      extension) carry the corrected references.

Run:
    python3 -m pytest test_lexicon_v28.py -q
or standalone:
    python3 test_lexicon_v28.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
HTML = HERE / "digital_lexicon_v28.html"


def _html() -> str:
    return HTML.read_text(encoding="utf-8")


def _section(html: str, page_id: str) -> str:
    """Return the `<div class="page" id="{page_id}">...</div>` block."""
    needle = f'id="{page_id}"'
    start = html.find(needle)
    assert start != -1, f"page block {page_id} not found"
    div_open = html.rfind("<div", 0, start)
    assert div_open != -1, f"<div> open not found for {page_id}"
    # Walk forward, balancing <div> ... </div>.
    depth = 0
    i = div_open
    while i < len(html):
        if html.startswith("<div", i):
            depth += 1
            i = html.index(">", i) + 1
            continue
        if html.startswith("</div>", i):
            depth -= 1
            i += len("</div>")
            if depth == 0:
                return html[div_open:i]
            continue
        i += 1
    raise AssertionError(f"unbalanced <div> block for {page_id}")


def _card_html(html: str, title_substr: str) -> str:
    pos = html.find(title_substr)
    assert pos != -1, f"card title not found: {title_substr!r}"
    art_open = html.rfind('<article class="law-card-v2', 0, pos)
    assert art_open != -1, f"card <article> open not found for {title_substr!r}"
    art_close = html.find("</article>", pos)
    assert art_close != -1, f"card </article> close not found for {title_substr!r}"
    return html[art_open:art_close]


def _step_html(html: str, num: int) -> str:
    anchor = f'id="step-{num}"'
    pos = html.find(anchor)
    assert pos != -1, f"step-{num} anchor not found"
    sec_open = html.rfind("<section", 0, pos)
    sec_close = html.find("</section>", pos)
    assert sec_open != -1 and sec_close != -1, f"step-{num} bounds not found"
    return html[sec_open:sec_close]


# --------------------------------------------------------------------------- #
# T1.  Home shows "43 terms across 12 regulatory frameworks".                  #
# --------------------------------------------------------------------------- #

def test_home_text_from_xlsx():
    home = _section(_html(), "p-home")
    assert "43 terms across 12 regulatory frameworks" in home, (
        "Home page does not contain the canonical "
        "'43 terms across 12 regulatory frameworks' phrase from "
        "About!A1."
    )


# --------------------------------------------------------------------------- #
# T2.  Home shows the study reference verbatim.                                #
# --------------------------------------------------------------------------- #

def test_home_study_reference():
    home = _section(_html(), "p-home")
    assert "NDICI FPN FPI /2022/432-762" in home, (
        "Home page is missing the study reference NDICI FPN FPI "
        "/2022/432-762."
    )


# --------------------------------------------------------------------------- #
# T3.  Regulations descs spot-check (AIA / GL / SB 53).                       #
# --------------------------------------------------------------------------- #

def test_regs_descs_from_xlsx():
    html = _html()

    # AIA card — xlsx C18 first paragraph fingerprint.
    aia = _card_html(html, "Artificial Intelligence Act (2024)")
    assert (
        "The AI Act (hereafter, AIA) puts in place obligations for "
        "providers and deployers of AI systems in the EU"
    ) in aia, "AIA card description does not match xlsx C18."
    # US-003: exponents render as <sup> markup in static HTML.
    assert "10<sup>25</sup> FLOPs" in aia, (
        "AIA card description missing 10<sup>25</sup> FLOPs typography."
    )

    # GL card — xlsx C20.
    gl = _card_html(
        html,
        "Guidelines on the scope of the obligations for general-purpose "
        "AI models established by AIA (2025)",
    )
    assert (
        "These guidelines (hereafter, GL) provide clarification on the "
        "definition and scope of obligations in place in the AIA"
    ) in gl, "GL card description does not match xlsx C20."

    # SB 53 card — xlsx C21.
    sb53 = _card_html(
        html,
        "SB 53 (2025) — Transparency in Frontier Artificial Intelligence (TFAI)",
    )
    assert (
        "This bill puts in place safety, reporting and risk management "
        "obligations for providers of frontier models (over 10<sup>26</sup> FLOPs"
    ) in sb53, "SB 53 card description does not match xlsx C21."


# --------------------------------------------------------------------------- #
# T4.  Methodology Step 1 contains EO 14179 + "Export of the American         #
#      AI Technology Stack" verbatim from xlsx.                                #
# --------------------------------------------------------------------------- #

def test_methodology_step_copy_matches_xlsx():
    step1 = _step_html(_html(), 1)
    assert "EO 14179 (2025)" in step1, (
        "Methodology Step 1 does not mention EO 14179 (2025) verbatim."
    )
    assert "Export of the American AI Technology Stack" in step1, (
        "Methodology Step 1 does not contain "
        "'Export of the American AI Technology Stack' verbatim from xlsx."
    )


# --------------------------------------------------------------------------- #
# T5.  Methodology Step 3 still mentions Commission Guidelines / (GL).        #
# --------------------------------------------------------------------------- #

def test_methodology_step3_keeps_gl_item():
    step3 = _step_html(_html(), 3)
    assert "Commission Guidelines" in step3, (
        "Methodology Step 3 lost the v26-added GL bullet."
    )
    assert ("(GL)" in step3 or "&quot;(GL)&quot;" in step3), (
        "Methodology Step 3 lost the (GL) notation."
    )


# --------------------------------------------------------------------------- #
# T6.  US-003 — every exponent renders as <sup> markup or Unicode             #
#      superscripts; no plain ASCII forms remain.                              #
# --------------------------------------------------------------------------- #

def test_exponents_render_as_superscript():
    html = _html()

    # No plain ASCII exponent forms anywhere.
    ascii_caret = re.findall(r'\d+\^\d+', html)
    ascii_paren = re.findall(r'\d+\(\^-?\d+\)', html)
    ascii_star  = re.findall(r'\d+\*\*\d+', html)
    assert not ascii_caret, (
        f"Plain ASCII 10^N exponents still present: "
        f"{sorted(set(ascii_caret))[:5]}"
    )
    assert not ascii_paren, (
        f"Parenthesised 10(^N) exponents still present: "
        f"{sorted(set(ascii_paren))[:5]}"
    )
    assert not ascii_star, (
        f"ASCII 10**N exponents still present: "
        f"{sorted(set(ascii_star))[:5]}"
    )

    # The three known static-HTML FLOPs thresholds are <sup>-wrapped.
    aia = _card_html(html, "Artificial Intelligence Act (2024)")
    assert "10<sup>25</sup>" in aia, "AIA static exponent is not <sup>-wrapped."
    sb53 = _card_html(
        html,
        "SB 53 (2025) — Transparency in Frontier Artificial Intelligence (TFAI)",
    )
    assert "10<sup>26</sup>" in sb53, "SB 53 static exponent is not <sup>-wrapped."
    raise_card = _card_html(
        html,
        "A6453B (2025) — Responsible AI Safety and Education Act (RAISE Act)",
    )
    assert "10<sup>26</sup>" in raise_card, (
        "RAISE Act static exponent is not <sup>-wrapped."
    )

    # Script blobs retain Unicode superscripts (rendered via textContent
    # for verbatim drawer).  Confirm a few representative cells.
    assert "10²⁶ FLOPs" in html or "10²⁵ FLOPs" in html, (
        "Script-embedded Unicode superscripts unexpectedly missing."
    )


# --------------------------------------------------------------------------- #
# T7.  US-004 — limited-risk anchor labels in opening category table.         #
# --------------------------------------------------------------------------- #

def test_opening_table_limited_risk_labels():
    html = _html()

    # The opening category table renders each cluster_summary row's
    # EU cell as the row label. The two limited-risk anchor cells must
    # carry the full Excel-canonical labels.
    assert (
        '"name":"Provider of limited-risk AI systems",'
        '"bill":"","sub_id":"provider","jid":"eu"'
    ) in html, (
        "Opening category table EU cell for the limited-risk Provider "
        "row is missing the canonical 'Provider of limited-risk AI "
        "systems' label."
    )
    assert (
        '"name":"Deployer of limited-risk AI systems",'
        '"bill":"","sub_id":"deployer","jid":"eu"'
    ) in html, (
        "Opening category table EU cell for the limited-risk Deployer "
        "row is missing the canonical 'Deployer of limited-risk AI "
        "systems' label (Excel says 'Deployer', not 'Developer')."
    )

    # The bare "Deployer" name must NOT appear as the EU cell for the
    # limited-risk row anymore.
    assert (
        '"name":"Deployer","bill":"","sub_id":"deployer","jid":"eu"'
    ) not in html, (
        "Opening category table still has the bare 'Deployer' label for "
        "the limited-risk EU cell — the US-004 fix did not apply."
    )

    # Colorado/Texas U.S.-state Deployer cells must remain bare "Deployer"
    # — those are the state-equivalents per Excel §3.3.
    assert (
        '"name":"Deployer","bill":"SB24-205","sub_id":"deployer","jid":"co"'
    ) in html, (
        "Colorado limited-risk Deployer cell should remain 'Deployer' "
        "(not renamed). The US-004 fix is over-broad."
    )
    assert (
        '"name":"Deployer","bill":"HB149","sub_id":"deployer","jid":"tx"'
    ) in html, (
        "Texas limited-risk Deployer cell should remain 'Deployer' "
        "(not renamed). The US-004 fix is over-broad."
    )


# --------------------------------------------------------------------------- #
# T8.  US-005 — limited-risk Provider table popups link to the right          #
#      regulatory text passages.                                               #
# --------------------------------------------------------------------------- #

def _lr_provider_section(html: str) -> str:
    """Slice the limited-risk Provider sub-concept JSON segment out of the
    minified CONCEPTS literal, the same way build_v28's
    apply_limited_risk_provider_fixes does."""
    start = html.find(
        '"id":"provider","title":"Provider of limited-risk AI systems"'
    )
    assert start != -1, "limited-risk Provider sub-concept header not found"
    end = html.find('"id":"provider-of-high-risk-ai-systems"', start)
    assert end != -1, "high-risk Provider sub-concept end-marker not found"
    return html[start:end]


def test_limited_risk_provider_popups_link_to_correct_articles():
    section = _lr_provider_section(_html())

    # 1. Scope EU — must reference Article 50 (1), and the misplaced
    #    Article 3 (3) verbatim must be gone.
    assert '"reference":"EU AI Act, Article 50 (1)"' in section, (
        "Scope EU is missing the corrected reference to Article 50 (1)."
    )
    assert '"reference":"EU AI Act, Article 3 (3)"' not in section, (
        "Scope EU still carries the misplaced Article 3 (3) reference; "
        "US-005 fix did not apply or was overwritten."
    )
    assert (
        '1. Providers shall ensure that AI systems intended to interact '
        'directly with natural persons'
    ) in section, (
        "Scope EU verbatim does not contain Article 50 (1) text."
    )

    # 2. Regulatory trigger TX — must reference 552.103 (a).
    assert '"reference":"Texas HB149, 552.103. (a)"' in section, (
        "Regulatory trigger TX is missing the 552.103 (a) reference."
    )

    # 3. Transparency EU — must reference Article 50 (1, 2) and contain
    #    both paragraph (1) and paragraph (2) text in verbatim.
    assert '"reference":"EU AI Act, Article 50 (1, 2)"' in section, (
        "Transparency EU is missing the Article 50 (1, 2) reference."
    )
    assert (
        '2. Providers of AI systems, including general-purpose AI '
        'systems, generating synthetic'
    ) in section, (
        "Transparency EU verbatim does not contain Article 50 (2) text."
    )

    # 4. Transparency CO — must reference §6-1-1704 (verbatim left empty
    #    because the CO law-blob has no embedded sections).
    assert '"reference":"Colorado SB24-205, 6-1-1704"' in section, (
        "Transparency CO is missing the §6-1-1704 reference label."
    )

    # 5+6. General info disclosure & Risk management TX — both reference
    #      552.103 (b). Must appear at least twice in the section (once
    #      per row).
    assert section.count('"reference":"Texas HB149, 552.103. (b)"') == 2, (
        "Expected exactly two cells (General info disclosure TX, Risk "
        "management TX) referencing Texas HB149, 552.103. (b)."
    )

    # 7. AI literacy EU — must reference Article 4 and quote it.
    assert '"reference":"EU AI Act, Article 4"' in section, (
        "AI literacy EU is missing the Article 4 reference."
    )
    assert (
        'Providers and deployers of AI systems shall take measures to '
        'ensure, to their best extent, a sufficient level of AI literacy'
    ) in section, (
        "AI literacy EU verbatim does not contain the Article 4 text."
    )

    # No cell in this sub-concept should still have an article cite in
    # its analysis text without a corresponding non-empty reference.
    # We check the remaining empty-reference cells — they must have
    # analysis text "-" (no obligation in this jurisdiction) or, in the
    # Provider/dev info TX case, the Excel-preserved "(§6-1-1702.)" typo
    # which is intentionally left without a reference.
    import re
    cell_re = re.compile(
        r'\{"analysis":"([^"\\]*(?:\\.[^"\\]*)*)",'
        r'"verbatim":"([^"\\]*(?:\\.[^"\\]*)*)",'
        r'"reference":"([^"\\]*(?:\\.[^"\\]*)*)"\}'
    )
    article_re = re.compile(
        r'\(Article\s+\d+\)|\(§\s*\d|\(\d+\.\d+|\(22757\.|'
        r'\(§\s*\d|Articles?\s+\d',
        re.IGNORECASE,
    )
    offenders = []
    for m in cell_re.finditer(section):
        analysis, _, reference = m.group(1), m.group(2), m.group(3)
        if reference:
            continue
        if analysis == '-' or analysis == '':
            continue
        # Permit the Excel-preserved §6-1-1702 typo on the TX provider/dev
        # info cell — see the docstring of apply_limited_risk_provider_fixes.
        if '§6-1-1702' in analysis:
            continue
        if article_re.search(analysis):
            offenders.append(analysis[:80])
    assert not offenders, (
        "Cells with article references in analysis but empty reference "
        f"field still present: {offenders}"
    )


# --------------------------------------------------------------------------- #
# T9.  US-008 — US-state article-link audit.                                   #
# --------------------------------------------------------------------------- #


def _us_state_jids() -> tuple[str, ...]:
    return ("ca", "co", "ny", "tx", "ut")


def _is_us_jid(jid: str) -> bool:
    if jid in _us_state_jids():
        return True
    return any(jid.startswith(p + "-") for p in _us_state_jids())


def _extract_concepts(html: str):
    import json
    needle = "const CONCEPTS = "
    head = html.find(needle)
    assert head != -1, "CONCEPTS literal not found"
    start = head + len(needle)
    assert html[start] == "[", "CONCEPTS does not start with '['"
    i = start
    depth = 0
    in_str = False
    esc = False
    while i < len(html):
        c = html[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    return json.loads(html[start:i + 1])
        i += 1
    raise AssertionError("CONCEPTS closing bracket not found")


# Citation patterns lifted from build_v28's audit logic.
_CITE_RE = {
    "co": re.compile(r"§\s*(6-1-170[1-7])"),
    "tx": re.compile(r"(?<![\w.])(552\.\d{3})"),
    "ca": re.compile(
        r"(?<![\w.])(?:§\s*)?(22757\.\d+|3110|3111|1107\.1)"
    ),
    "ny": re.compile(r"§\s*(14[2-3]\d)"),
    "ut": re.compile(r"§\s*(13-75-10[1-6])"),
}


def test_us_state_cells_have_reference_when_analysis_cites():
    """For every US-state cell whose analysis text cites an article or
    section, the `reference` field must be non-empty. (We don't require
    the reference to *match* the cite verbatim, since canonical reference
    formats vary across the corpus.)"""
    html = _html()
    concepts = _extract_concepts(html)

    offenders = []
    for c in concepts:
        cid = c.get("id", "")
        for sub in c.get("sub_concepts", []):
            sid = sub.get("id", "")
            for dim in sub.get("dimensions", []):
                did = dim.get("id", "")
                cells = dim.get("cells", {})
                for jid, cell in cells.items():
                    if not _is_us_jid(jid):
                        continue
                    analysis = (cell.get("analysis") or "").strip()
                    reference = (cell.get("reference") or "").strip()
                    if not analysis or analysis == "-":
                        continue
                    p = jid.split("-")[0]
                    pat = _CITE_RE.get(p)
                    if not pat:
                        continue
                    if not pat.search(analysis):
                        continue
                    if not reference:
                        offenders.append(
                            f"{cid}/{sid}/{did} ({jid}): analysis cites "
                            f"section but reference is empty"
                        )
    assert not offenders, (
        "US-state cells with article/section in analysis but empty "
        f"reference: {offenders[:8]}"
        + (f" (and {len(offenders) - 8} more)" if len(offenders) > 8 else "")
    )


def test_us008_overrides_applied():
    """Spot-check that the US-008 manual overrides landed (these were the
    REF_MISMATCH cases where the v26 baseline pointed at the wrong section)."""
    html = _html()
    concepts = _extract_concepts(html)

    # Locate cells by (concept, sub_concept, dim_id, jid)
    def _cell(cid, sid, did, jid):
        for c in concepts:
            if c.get("id") != cid:
                continue
            for sub in c.get("sub_concepts", []):
                if sub.get("id") != sid:
                    continue
                for dim in sub.get("dimensions", []):
                    if dim.get("id") != did:
                        continue
                    return dim.get("cells", {}).get(jid)
        return None

    # CA modification REF_MISMATCH overrides.
    ca0_def = _cell(
        "modification", "substantial-modification", "definition-1-0",
        "ca-0-substantially-modified-version-of-a-frontier-model-no-standalone-defined-term",
    )
    assert ca0_def is not None, "CA SB 53 modification definition cell missing"
    assert ca0_def["reference"] == "CA SB 53 §22757.12", (
        f"CA SB 53 modification/definition reference not corrected: "
        f"{ca0_def['reference']!r}"
    )

    ca1_scope = _cell(
        "modification", "substantial-modification", "scope-2-0",
        "ca-1-substantial-modification",
    )
    assert ca1_scope is not None
    assert ca1_scope["reference"] == "CA AB 2013 §3111", (
        f"CA AB 2013 modification/scope reference not corrected: "
        f"{ca1_scope['reference']!r}"
    )

    # CO modification scope-2-0 — Excel says §6-1-1701(9) (high-risk).
    co_scope = _cell(
        "modification", "substantial-modification", "scope-2-0", "co",
    )
    assert co_scope is not None
    assert co_scope["reference"] == "CO SB 24-205 §6-1-1701(9)", (
        f"CO modification/scope reference not corrected: "
        f"{co_scope['reference']!r}"
    )


def test_us008_extensions_applied():
    """Spot-check the EXTRA_IN_ANALYSIS extensions: TX rebuttal cells
    (552.104 + 552.105) and CA GPAI penalties (22757.4 + 22757.15)."""
    html = _html()
    concepts = _extract_concepts(html)

    def _cell(cid, sid, did, jid):
        for c in concepts:
            if c.get("id") != cid:
                continue
            for sub in c.get("sub_concepts", []):
                if sub.get("id") != sid:
                    continue
                for dim in sub.get("dimensions", []):
                    if dim.get("id") != did:
                        continue
                    return dim.get("cells", {}).get(jid)
        return None

    tx_reb_p = _cell(
        "provider-developer", "provider", "rebuttal-9-0", "tx",
    )
    assert tx_reb_p is not None
    assert "552.104" in tx_reb_p["reference"]
    assert "552.105" in tx_reb_p["reference"], (
        f"TX provider rebuttal reference missing 552.105: "
        f"{tx_reb_p['reference']!r}"
    )

    ca_pen = _cell(
        "provider-developer", "provider-of-general-purpose-ai-models",
        "penalties-10-0", "ca-0-covered-provider",
    )
    assert ca_pen is not None
    assert "22757.4" in ca_pen["reference"]
    assert "22757.15" in ca_pen["reference"], (
        f"CA GPAI penalties reference missing 22757.15: "
        f"{ca_pen['reference']!r}"
    )


def test_us008_spot_check_three_links_per_state():
    """Spot-check at least 3 article-link cells per state law have a
    non-empty reference. This is the structural guarantee for the
    audit — the popups will display a label rather than appearing
    blank."""
    html = _html()
    concepts = _extract_concepts(html)

    counts = {p: 0 for p in _us_state_jids()}
    for c in concepts:
        for sub in c.get("sub_concepts", []):
            for dim in sub.get("dimensions", []):
                for jid, cell in dim.get("cells", {}).items():
                    if not _is_us_jid(jid):
                        continue
                    if (cell.get("reference") or "").strip():
                        counts[jid.split("-")[0]] += 1

    for state, n in counts.items():
        assert n >= 3, (
            f"State {state.upper()} has only {n} cells with non-empty "
            "reference (need at least 3 for spot-check coverage)"
        )


# --------------------------------------------------------------------------- #
# T10. US-010 — every known exponent value renders as <sup> markup            #
#      (static HTML cards) and/or Unicode superscripts (script blobs).        #
# --------------------------------------------------------------------------- #

# v28 ships two distinct exponent values, both linked to FLOPs thresholds:
#   * 10^25  — AIA (Article 51) systemic-risk presumption.
#   * 10^26  — SB 53 / RAISE Act frontier-model trigger.
# Both must be discoverable in their rendered <sup> form. The 10^26 value
# also appears across the CONCEPTS data (analysis/verbatim cells) where
# textContent rendering requires the Unicode-superscript form (10²⁶).
_KNOWN_EXPONENT_VALUES = (25, 26)
_UNICODE_SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def test_known_exponents_render_as_superscript():
    html = _html()
    for n in _KNOWN_EXPONENT_VALUES:
        sup_form = f"10<sup>{n}</sup>"
        uni_form = "10" + str(n).translate(_UNICODE_SUP)
        assert sup_form in html or uni_form in html, (
            f"Known exponent value 10^{n} renders neither as "
            f"{sup_form!r} (static HTML) nor as {uni_form!r} "
            "(Unicode superscript). US-003 missed this value."
        )

    # Stronger check: the 10^25 value (AIA, sole occurrence) must use
    # the static <sup> form because that card ships as static HTML.
    aia = _card_html(html, "Artificial Intelligence Act (2024)")
    assert "10<sup>25</sup>" in aia, (
        "AIA card must carry 10<sup>25</sup>; static-HTML exponents "
        "should never fall back to Unicode in card descriptions."
    )

    # The 10^26 value must appear in BOTH forms in v28: static <sup>
    # in card descriptions, and Unicode in CONCEPTS analysis/verbatim
    # text (rendered via textContent).
    assert "10<sup>26</sup>" in html, (
        "10^26 missing static <sup> form (used by SB 53 / RAISE cards)."
    )
    assert "10²⁶" in html, (
        "10^26 missing Unicode-superscript form (used in CONCEPTS "
        "analysis/verbatim text rendered via textContent)."
    )


# --------------------------------------------------------------------------- #
# T11. US-010 — opening category-table EU labels are the agreed Excel-       #
#      canonical strings for every sub-concept anchor.                        #
# --------------------------------------------------------------------------- #

# (sub_id, EU-cell display name) pairs. These are the Excel-canonical
# strings rendered as the EU column of the opening category table —
# the limited-risk pair carries the post-US-004 corrected labels;
# the rest are the v26 baseline names. Together they pin down the
# 13 anchor rows across the 6 concepts.
_OPENING_TABLE_EU_LABELS = (
    # provider-developer
    ("provider", "Provider of limited-risk AI systems"),
    ("provider-of-high-risk-ai-systems", "Provider of high-risk AI systems"),
    ("provider-of-general-purpose-ai-models", "Provider of GPAI models"),
    (
        "provider-of-general-purpose-ai-models-with-systemic-risk",
        "Provider of GPAI models with systemic risk",
    ),
    # deployer-supplier
    ("deployer", "Deployer of limited-risk AI systems"),
    ("deployer-of-high-risk-ai-systems", "Deployer of high-risk AI systems"),
    ("deployer-of-general-purpose-ai-systems", "Deployer of GPAI systems"),
    # model-system
    ("high-risk-ai-system", "High-risk AI system"),
    ("general-purpose-ai-model", "GPAI model"),
    ("general-purpose-ai-system", "GPAI system"),
    # risk
    ("systemic-risk", "Systemic risk"),
    # modification
    ("substantial-modification", "Substantial modification"),
    # incident
    ("serious-incident", "Serious incident"),
)


def test_opening_table_labels_match_agreed_strings():
    html = _html()
    missing = []
    for sub_id, name in _OPENING_TABLE_EU_LABELS:
        anchor = f'"name":"{name}","bill":"","sub_id":"{sub_id}","jid":"eu"'
        if anchor not in html:
            missing.append(f"{sub_id} → {name!r}")
    assert not missing, (
        "Opening category table is missing the agreed EU labels for: "
        f"{missing}"
    )


# --------------------------------------------------------------------------- #
# T12. US-010 — smoke test: every CONCEPTS cell with a non-empty reference   #
#      resolves to a non-empty pop-up content block.                          #
# --------------------------------------------------------------------------- #

# The drawer popup body is rendered by `updateDrawerContent` (line ~1948
# in v28). It writes:
#   * `cell.reference` → `#drawer-ref` (label, may be blank).
#   * `cell.verbatim` → `#drawer-verbatim`. Falls back to
#     "[Analysis text — no verbatim extracted]\n\n" + `cell.analysis`
#     when verbatim is empty. Falls back to "No text available." when
#     both are empty.
#
# A "broken pop-up" in v28 means the drawer body is "No text available."
# despite a reference being set. This smoke test asserts that every
# article-link cell — i.e. every cell with a non-empty `reference` —
# has either non-empty `verbatim` or non-empty `analysis`.

def test_every_reference_resolves_to_non_empty_popup_content():
    html = _html()
    concepts = _extract_concepts(html)

    offenders = []
    total_refs = 0
    for c in concepts:
        cid = c.get("id", "")
        for sub in c.get("sub_concepts", []):
            sid = sub.get("id", "")
            for dim in sub.get("dimensions", []):
                did = dim.get("id", "")
                for jid, cell in dim.get("cells", {}).items():
                    ref = (cell.get("reference") or "").strip()
                    if not ref:
                        continue
                    total_refs += 1
                    ana = (cell.get("analysis") or "").strip()
                    vb = (cell.get("verbatim") or "").strip()
                    if not ana and not vb:
                        offenders.append(
                            f"{cid}/{sid}/{did}/{jid}: reference={ref!r} "
                            "but both analysis and verbatim are empty"
                        )
    assert total_refs > 0, (
        "Sanity check: no cells have a non-empty reference at all."
    )
    assert not offenders, (
        f"{len(offenders)} cell(s) carry a reference but render an empty "
        f"popup body (drawer would show 'No text available.'): "
        f"{offenders[:5]}"
    )


# --------------------------------------------------------------------------- #
# T13. US-010 — every regulatory-text law-blob in v28 is structurally well-  #
#      formed (parses as JSON, has id+title, has sections or raw_text).       #
# --------------------------------------------------------------------------- #

# When a user opens a regulatory table from the Regulations page, the
# law-blob JSON is read by `getLawBlob` and rendered. A malformed blob
# (invalid JSON, missing id/title, no sections AND no raw_text) would
# produce a broken table view. Walks every embedded blob to confirm.

def _iter_law_blobs(html: str):
    import json as _json
    needle = '<script type="application/json" id="law-blob-'
    i = 0
    while True:
        start = html.find(needle, i)
        if start < 0:
            return
        id_open = start + len(needle)
        id_close = html.find('"', id_open)
        blob_id = html[id_open:id_close]
        body_open = html.find(">", id_close) + 1
        body_close = html.find("</script>", body_open)
        body = html[body_open:body_close].strip()
        # Skip the placeholder template comment block left by build_v28.
        try:
            blob = _json.loads(body)
        except _json.JSONDecodeError:
            yield blob_id, None
        else:
            yield blob_id, blob
        i = body_close


def test_all_law_blobs_well_formed():
    html = _html()
    failures = []
    seen_ids = []
    for blob_id, blob in _iter_law_blobs(html):
        if blob_id == "X":
            continue  # template placeholder, ignored by `getLawBlob`.
        seen_ids.append(blob_id)
        if blob is None:
            failures.append(f"{blob_id}: invalid JSON")
            continue
        if not blob.get("id"):
            failures.append(f"{blob_id}: missing id")
        if not blob.get("title"):
            failures.append(f"{blob_id}: missing title")
        # Different blobs use different content keys:
        #   * State + CoP + Guidelines blobs:  sections / raw_text
        #   * EU AI Act:                       articles / recitals / annexes
        # Accept any of these as evidence of non-empty rendered content.
        sections = blob.get("sections") or []
        raw      = (blob.get("raw_text") or "").strip()
        articles = blob.get("articles") or []
        recitals = blob.get("recitals") or {}
        annexes  = blob.get("annexes")  or {}
        if not (sections or raw or articles or recitals or annexes):
            failures.append(
                f"{blob_id}: no sections / raw_text / articles / "
                "recitals / annexes — regulatory table would render empty"
            )
    # The 13 in-scope law-blobs (per progress.md) plus the 2 extra
    # Commission Guidelines blobs must all be present.
    expected = {
        "eu-ai-act",
        "eu-gpai-cop-copyright",
        "eu-gpai-cop-transparency",
        "eu-gpai-cop-safety",
        "eu-guidelines-gpai-scope",
        "eu-guidelines-ai-definition",
        "eu-guidelines-prohibited",
        "ca-sb53",
        "ca-sb942",
        "ca-ab2013",
        "co-sb24205",
        "ny-a6453",
        "ny-s8828",
        "tx-hb149",
        "ut-sb226",
    }
    missing = expected.difference(seen_ids)
    assert not missing, f"Expected law-blobs missing from HTML: {missing}"
    assert not failures, "Malformed law-blobs: " + "; ".join(failures)


# Standalone runner --------------------------------------------------------- #

if __name__ == "__main__":
    import inspect
    g = globals()
    tests = [(n, fn) for n, fn in g.items()
             if n.startswith("test_") and inspect.isfunction(fn)]
    failed = []
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except AssertionError as e:
            print(f"  FAIL  {name}: {e}")
            failed.append(name)
        except Exception as e:
            print(f"  ERROR {name}: {type(e).__name__}: {e}")
            failed.append(name)
    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
