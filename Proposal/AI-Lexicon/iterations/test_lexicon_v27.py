"""test_lexicon_v27.py — acceptance tests for v27.

v27 swaps in cross-checked authoritative copy from
`Cross-checked_AI terminology and taxonomy_analysis.xlsx` onto
the Home, Regulations, and Methodology pages.

Tests:
  T1. Home page shows "43 terms across 12 regulatory frameworks".
  T2. Home page shows "NDICI FPN FPI /2022/432-762".
  T3. Regulations page descs spot-check (AIA / GL / SB 53).
  T4. Methodology Step 1 body contains "EO 14179 (2025)" and
      "Export of the American AI Technology Stack".
  T5. Methodology Step 3 keeps the v26 GL bullet (Commission Guidelines
      / "(GL)" notation).

Run:
    python3 -m pytest test_lexicon_v27.py -q
or standalone:
    python3 test_lexicon_v27.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
HTML = HERE / "digital_lexicon_v27.html"


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
    # The Unicode superscript is preserved.
    assert "10²⁵ FLOPs" in aia, (
        "AIA card description missing literal 10²⁵ FLOPs typography."
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
        "obligations for providers of frontier models (over 10²⁶ FLOPs"
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
