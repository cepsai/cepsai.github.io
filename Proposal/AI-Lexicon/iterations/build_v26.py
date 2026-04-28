"""build_v26.py — Digital AI Lexicon v26.

Lands on top of v25. v26 closes one display gap:

  1. **EU Regulations page miscount** — the EU `juris-block` header
     advertises "3 frameworks" but only 2 `law-card-v2` cards are
     rendered (AIA 2024 and CoP 2025). The third framework — the
     **Commission Guidelines on the Scope of Obligations for Providers
     of General-Purpose AI Models** (C(2025) 7719 final, 19.11.2025) —
     is wired into the law-blob and Law Sources nav metadata in v25
     but has no visible card on the Regulations page. v26 adds the
     missing card chronologically between AIA (2024) and CoP (2025-08).

  2. **Methodology Step 3** — Step 3 currently mentions only the EU AI
     Act. v26 appends a sibling list-item that flags the Commission
     Guidelines as a 2025-11 supplementary EU framework cited as "(GL)"
     in the comparative analysis.

Build chain:
    v13 → v15 → v16 → v17 → v18 → v20 → v21 → v22 → v23 → v24 → v25 → **v26**.

v26 operates as a pure HTML post-process on v25:
    1. Read v25 HTML.
    2. Idempotency guard: if the new card title is already present, write
       through unchanged.
    3. Inject the GL card after the AIA `cited-AIA` boundary and before
       the CoP card opening.
    4. Inject the methodology bullet inside Step 3's <ul>.
    5. Write digital_lexicon_v26.html and mirror to ../final_tool.html
       and ../final_lexicon_tool.html.

Run:
    python3 build_v26.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

HERE          = Path(__file__).parent
HTML_V25      = HERE / "digital_lexicon_v25.html"
HTML_V26      = HERE / "digital_lexicon_v26.html"
FINAL_TOOL    = HERE.parent / "final_tool.html"
FINAL_LEXICON = HERE.parent / "final_lexicon_tool.html"


# --------------------------------------------------------------------------- #
# The new EU framework card (chronological position: AIA 2024 → GL 2025-11    #
# → CoP 2025-08). Title/subtitle/description verbatim from the xlsx           #
# Methodology sheet R20.                                                      #
# --------------------------------------------------------------------------- #

GL_CARD_TITLE = (
    "Guidelines on the scope of the obligations for general-purpose "
    "AI models established by AIA (2025)"
)
GL_CARD_SUBTITLE = "C(2025) 7719 final"
GL_CARD_DESC = (
    "These guidelines (hereafter, GL) provide clarification on the "
    "definition and scope of obligations in place in the AIA related "
    "to GPAI models and GPAI models with systemic risks (GPAISR)."
)

GL_CARD_HTML = (
    '      <article class="law-card-v2">\n'
    '        <div class="law-card-v2-header">\n'
    '          <div>\n'
    f'            <div class="law-card-v2-title">{GL_CARD_TITLE}</div>\n'
    f'            <div class="law-card-v2-subtitle">{GL_CARD_SUBTITLE}</div>\n'
    '          </div>\n'
    '          <span class="status-pill voluntary">Interpretive guidance</span>\n'
    '        </div>\n'
    f'        <p class="law-card-v2-desc">{GL_CARD_DESC}</p>\n'
    '        <div class="law-card-v2-meta">\n'
    '          <span><strong>Effective:</strong> 19 Nov 2025</span>\n'
    '        </div>\n'
    '        <div class="law-cited-in" id="cited-GL"></div>\n'
    '      </article>\n'
)

# We anchor the insertion at the closing tag of the AIA card. The AIA
# card ends with the unique `cited-AIA` div followed by `</article>`, so
# we splice the GL card after that boundary.
ANCHOR_AFTER_AIA = (
    '        <div class="law-cited-in" id="cited-AIA"></div>\n'
    '      </article>\n'
)

# Methodology Step 3 — append a sibling <li> that mentions the GL.
METHOD_LI_OLD = (
    '          <li>Identify key terms in the <strong>EU AI Act</strong> '
    '— the baseline for comparative analysis — particularly in '
    '<a href="#/primary-sources#juris-eu" onclick="go(\'laws\');return false">'
    '<strong>Articles 3, 17, 52 and Annex III</strong></a>.</li>\n'
)
METHOD_LI_NEW = (
    METHOD_LI_OLD
    + '          <li>Cross-reference the <strong>Commission Guidelines '
      'on the scope of obligations for providers of general-purpose '
      'AI models</strong> (C(2025) 7719, 19 Nov 2025; cited as '
      '&quot;(GL)&quot; in the comparative analysis).</li>\n'
)


def _inject_card(html: str) -> str:
    """Inject the GL card after the AIA card. Idempotent."""
    if GL_CARD_TITLE in html:
        return html  # already injected
    if ANCHOR_AFTER_AIA not in html:
        raise RuntimeError(
            "build_v26: AIA card closing anchor not found — "
            "v25 HTML structure changed?"
        )
    # Insert the GL card between AIA's closing </article> and the CoP card.
    # Replace exactly once to keep idempotent and safe.
    return html.replace(
        ANCHOR_AFTER_AIA,
        ANCHOR_AFTER_AIA + GL_CARD_HTML,
        1,
    )


def _inject_methodology(html: str) -> str:
    """Append the GL bullet to Step 3's list. Idempotent."""
    if "Cross-reference the <strong>Commission Guidelines" in html:
        return html  # already added
    if METHOD_LI_OLD not in html:
        raise RuntimeError(
            "build_v26: methodology Step 3 anchor not found — "
            "v25 HTML structure changed?"
        )
    return html.replace(METHOD_LI_OLD, METHOD_LI_NEW, 1)


def main() -> None:
    print("== v26 build ==")
    if not HTML_V25.exists():
        print("  digital_lexicon_v25.html missing — running build_v25 …")
        sys.path.insert(0, str(HERE))
        import build_v25 as _v25
        _v25.main()

    html = HTML_V25.read_text(encoding="utf-8")
    print(f"  read v25:                  {len(html):,} bytes")

    before_card = GL_CARD_TITLE in html
    before_method = "Cross-reference the <strong>Commission Guidelines" in html
    print(f"  card already present:      {before_card}")
    print(f"  methodology bullet present: {before_method}")

    html = _inject_card(html)
    html = _inject_methodology(html)

    HTML_V26.write_text(html, encoding="utf-8")
    shutil.copy2(HTML_V26, FINAL_TOOL)
    shutil.copy2(HTML_V26, FINAL_LEXICON)
    print(f"\n  wrote {HTML_V26.name}        ({len(html):,} bytes)")
    print(f"  wrote {FINAL_TOOL.name}            (mirror)")
    print(f"  wrote {FINAL_LEXICON.name}    (mirror)")


if __name__ == "__main__":
    main()
