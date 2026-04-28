"""test_lexicon_v26.py — acceptance tests for v26.

v26 closes one display gap on top of v25:

  V0. The EU `juris-block` on the Regulations page must contain
      exactly 3 `law-card-v2` cards (header already advertises
      "3 frameworks").
  V1. The new GL card carries the verbatim title and subtitle.
  V2. Methodology Step 3 references the Commission Guidelines /
      "(GL)" notation.
  V3. The new card carries a `status-pill` (interpretive guidance,
      using the `voluntary` pill class).

Run:
    python3 -m pytest test_lexicon_v26.py -q
or standalone:
    python3 test_lexicon_v26.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
HTML = HERE / "digital_lexicon_v26.html"


def _html() -> str:
    return HTML.read_text(encoding="utf-8")


def _eu_section(html: str) -> str:
    """Return the substring of `html` that spans the EU juris-block
    section — from `<section class="juris-block" id="juris-eu"` up to
    the matching `</section>` (the next `</section>` close)."""
    start = html.find('id="juris-eu"')
    assert start != -1, "juris-eu section not found in v26 HTML"
    # Walk back to the start of the <section ...> tag.
    open_tag = html.rfind("<section", 0, start)
    assert open_tag != -1, "Could not locate <section> open for juris-eu"
    end = html.find("</section>", start)
    assert end != -1, "Could not locate </section> close for juris-eu"
    return html[open_tag:end]


# --------------------------------------------------------------------------- #
# V0.  EU section has exactly three law-card-v2 cards.                        #
# --------------------------------------------------------------------------- #

def test_eu_section_has_three_cards():
    html = _html()
    eu = _eu_section(html)
    cards = re.findall(r'<article\s+class="law-card-v2"', eu)
    assert len(cards) == 3, (
        f"EU section has {len(cards)} law-card-v2 cards; expected 3. "
        f"Section length: {len(eu)} chars."
    )


# --------------------------------------------------------------------------- #
# V1.  Verbatim title and subtitle of the new GL framework.                    #
# --------------------------------------------------------------------------- #

def test_third_framework_text_present():
    html = _html()
    eu = _eu_section(html)
    assert "Guidelines on the scope of the obligations" in eu, (
        "GL framework title missing from EU section"
    )
    assert "C(2025) 7719" in eu, (
        "GL framework C(2025) 7719 reference missing from EU section"
    )


# --------------------------------------------------------------------------- #
# V2.  Methodology Step 3 mentions the Commission Guidelines / (GL).          #
# --------------------------------------------------------------------------- #

def test_methodology_mentions_gl():
    html = _html()
    # Locate Step 3 by its id.
    s3_start = html.find('id="step-3"')
    assert s3_start != -1, "method-step #step-3 not found"
    # Find the matching </section>.
    open_tag = html.rfind("<section", 0, s3_start)
    s3_end = html.find("</section>", s3_start)
    assert s3_end != -1, "Step 3 closing </section> not found"
    step3 = html[open_tag:s3_end]
    # Must mention either the new framework name or the (GL) notation.
    assert (
        "Commission Guidelines" in step3
        or "(GL)" in step3
        or "&quot;(GL)&quot;" in step3
    ), (
        "Methodology Step 3 does not mention Commission Guidelines or "
        "(GL) notation."
    )


# --------------------------------------------------------------------------- #
# V3.  New card carries a status-pill class.                                  #
# --------------------------------------------------------------------------- #

def test_law_card_status_pill():
    html = _html()
    eu = _eu_section(html)
    # Locate the GL card by its title; ensure a status-pill sits inside it.
    title = "Guidelines on the scope of the obligations"
    pos = eu.find(title)
    assert pos != -1, "GL card title not located"
    # Walk back to the enclosing <article> open tag.
    art_open = eu.rfind('<article class="law-card-v2"', 0, pos)
    assert art_open != -1, "GL card <article> open tag not located"
    # Walk forward to find the next </article>.
    art_close = eu.find("</article>", pos)
    assert art_close != -1, "GL card </article> close tag not located"
    card_html = eu[art_open:art_close]
    assert 'class="status-pill' in card_html, (
        "GL card does not carry a status-pill element."
    )
    # Cited-in container should also exist for chip wiring parity.
    assert 'id="cited-GL"' in card_html, (
        "GL card missing cited-GL container (chip wiring parity)."
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
