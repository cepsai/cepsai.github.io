"""build_v28.py — Digital AI Lexicon v28.

Scaffold-only release: identical behaviour to v27 (byte-equivalent output)
so that subsequent user stories (article-link audit, superscript FLOPs,
terminology fixes) can land as targeted modifications on a fresh build
file rather than a heavily-overloaded v27 module.

Lands on top of v26 with the same xlsx-driven copy swaps as v27:

  1. Home — replace the intro/landing prose with the three body
     paragraphs from About!A1 (verbatim, drop the heading line).
  2. Regulations — replace each `law-card-v2-desc` with the matching
     Description cell from Methodology rows 18-29; refresh the
     `Effective` meta date from column D.
  3. Methodology — replace each `method-step` body with the matching
     paragraph + numbered list from Methodology!A1 (steps 1-6).
     Step 3 keeps the v26-added GL bullet as the 5th list-item.

v28 (this scaffold) operates as a pure HTML post-process on v26:
    1. Read v26 HTML.
    2. Read xlsx sheets via openpyxl.
    3. Perform precise `html.replace()` swaps with idempotency guards.
    4. Write digital_lexicon_v28.html and mirror to ../final_tool.html
       and ../final_lexicon_tool.html.

Build chain:
    v13 → v15 → v16 → v17 → v18 → v20 → v21 → v22 → v23 → v24 → v25 →
    v26 → v27 → **v28**.

Run:
    python3 build_v28.py
"""
from __future__ import annotations

import html as _html
import shutil
import sys
from pathlib import Path

import openpyxl

HERE          = Path(__file__).parent
HTML_V26      = HERE / "digital_lexicon_v26.html"
HTML_V28      = HERE / "digital_lexicon_v28.html"
FINAL_TOOL    = HERE.parent / "final_tool.html"
FINAL_LEXICON = HERE.parent / "final_lexicon_tool.html"
XLSX          = Path("/Users/robertpraas/Downloads/"
                     "Cross-checked_AI terminology and taxonomy_analysis.xlsx")


# --------------------------------------------------------------------------- #
# xlsx helpers                                                                #
# --------------------------------------------------------------------------- #

def _esc(text: str) -> str:
    """HTML-escape a body of plain xlsx text. Preserve curly quotes,
    em-dashes and Unicode superscripts as-is; only convert reserved
    HTML characters (`&`, `<`, `>`, `"`)."""
    return _html.escape(text, quote=True)


def _date_str(dt) -> str:
    """Render an Effective-from date as 'D MMM YYYY'."""
    if dt is None:
        return ""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{dt.day} {months[dt.month - 1]} {dt.year}"


def load_xlsx_data():
    wb = openpyxl.load_workbook(XLSX, data_only=True)

    # ---- About sheet ------------------------------------------------------- #
    about_a1 = wb["About the Digital AI Lexicon"]["A1"].value
    # Split into paragraphs separated by blank lines. The first is the H1.
    blocks = [b.strip() for b in about_a1.split("\n\n") if b.strip()]
    # blocks[0] = "About the Digital AI Lexicon tool"
    # blocks[1..3] = the three body paragraphs
    # The xlsx contains "NDICI FPN FPI /2022/432 -762" with an extra
    # space; normalise to the canonical "NDICI FPN FPI /2022/432-762".
    body_paras = [
        p.replace("/2022/432 -762", "/2022/432-762").rstrip()
        for p in blocks[1:4]
    ]

    # ---- Methodology sheet ------------------------------------------------- #
    ws = wb["Methodology"]

    # The A1 cell holds all six step blocks.
    method_a1 = ws["A1"].value

    # Slice A1 by step header. Headers begin with "Step N. ".
    steps_text: dict[int, str] = {}
    headers = [f"Step {i}." for i in range(1, 7)]
    for i, hdr in enumerate(headers):
        start = method_a1.index(hdr)
        end = (method_a1.index(headers[i + 1])
               if i + 1 < len(headers) else len(method_a1))
        steps_text[i + 1] = method_a1[start:end].strip()

    # Regulations table rows 18-29.
    regs: dict[int, dict] = {}
    for r in range(18, 30):
        regs[r] = {
            "title":  ws.cell(row=r, column=2).value,
            "desc":   ws.cell(row=r, column=3).value,
            "date":   ws.cell(row=r, column=4).value,
        }

    return {
        "about_paras":  body_paras,
        "steps":        steps_text,
        "regs":         regs,
    }


# --------------------------------------------------------------------------- #
# Step text -> HTML rendering                                                 #
# --------------------------------------------------------------------------- #

def _render_step_body(step_text: str) -> tuple[str, str | None, list[str], str | None]:
    """Parse a step block (e.g. 'Step 1. Title\\n<lead>\\n1. Foo\\n...').

    Return (heading_title, lead_paragraph, items, trailing_paragraph).
    `items` is a list of plain-text numbered-list entries.
    """
    lines = step_text.splitlines()
    # First line: "Step N. <heading title>"
    head_line = lines[0].strip()
    # heading title: text after the first ". "
    _, _, head_title = head_line.partition(". ")
    head_title = head_title.strip()

    body_lines = lines[1:]

    lead_parts: list[str] = []
    items: list[str] = []
    trail_parts: list[str] = []
    seen_first_item = False
    seen_last_item = False

    def _is_numbered(s: str) -> bool:
        s = s.lstrip()
        if len(s) < 2 or not s[0].isdigit():
            return False
        # support "1." "1\t" "1.\t" "1)"
        for sep in (".", "\t", ")"):
            if sep in s[:3]:
                return True
        return False

    # In the xlsx, each numbered item lives on its own line. As soon as we
    # see a non-numbered line after we've started the list, close the list
    # and treat the remaining lines as trailing paragraph content.
    in_list = False
    for raw in body_lines:
        line = raw.rstrip()
        if not line.strip():
            # blank line — separator only
            continue

        if _is_numbered(line):
            in_list = True
            seen_first_item = True
            # strip the leading "N." or "N.\t" or "N)" then whitespace
            stripped = line.lstrip()
            i = 0
            while i < len(stripped) and stripped[i].isdigit():
                i += 1
            if i < len(stripped) and stripped[i] in ".)\t":
                i += 1
            stripped = stripped[i:].lstrip()
            items.append(stripped)
            continue

        if not in_list:
            lead_parts.append(line.strip())
        else:
            # Non-numbered line after numbered list — trailing paragraph.
            trail_parts.append(line.strip())
            seen_last_item = True

    lead = " ".join(lead_parts).strip() or None
    trail = " ".join(trail_parts).strip() or None
    return head_title, lead, items, trail


def _step_body_html(num: int, lead: str | None,
                    items: list[str], trail: str | None,
                    extra_li_html: str | None = None) -> str:
    """Render the inner HTML of a `.method-step-body` (without the
    enclosing `<h2>` heading — the script preserves the existing h2)."""
    out: list[str] = []
    if lead:
        out.append(f"        <p>{_esc(lead)}</p>")
    if items:
        out.append("        <ol>")
        for it in items:
            out.append(f"          <li>{_esc(it)}</li>")
        if extra_li_html:
            out.append(extra_li_html.rstrip())
        out.append("        </ol>")
    if trail:
        out.append(f"        <p>{_esc(trail)}</p>")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# v26 anchor strings -> v28 replacement strings                               #
# --------------------------------------------------------------------------- #

# ---- HOME ----------------------------------------------------------------- #
HOME_TAGLINE_OLD = (
    '    <p class="landing-tagline">The Digital AI Lexicon is a searchable '
    'digital database on key AI governance terms present in regulatory '
    'frameworks on AI in the European Union and the United States.</p>\n'
    '    <div class="landing-sub about-body"><p>The Digital AI Lexicon takes '
    'the EU\'s AI Act as a benchmark, juxtaposing and organising the other '
    'jurisdictions\' terms based on the EU regulatory framework for AI. It '
    'covers a total of 43 terms across 12 regulatory frameworks and relevant '
    'guidance documents. For each term, it catalogues the definition, scope, '
    'enforcement context, and authoritative source, with side-by-side EU–US '
    'comparisons and interpretive notes.</p>\n'
    '<p>The Digital AI Lexicon allows the user to consult key AI governance '
    'terms in two modes:</p>\n'
    '<ul class="about-bullets"><li>Comparative analysis: provides at-a-glance '
    'comparative tables alongside interpretative notes.</li>\n'
    '<li>Legal text: provides side-by-side verbatim regulatory text, keeping '
    'the original detail and language of selected regulations.</li></ul>\n'
    '<p>The Digital AI Lexicon was produced by the Centre for European Policy '
    'Studies (CEPS) in the context of the EU-US Trade and Technology Dialogue '
    '(TTD), funded by the European Commission. Study reference: NDICI FPN FPI '
    '/2022/432 -762.</p></div>\n'
)


def _build_home_block(about_paras: list[str]) -> str:
    p1, p2, p3 = about_paras  # body paragraphs from About!A1
    tagline_html = (
        f'    <p class="landing-tagline">{_esc(p1)}</p>\n'
    )
    sub_html = (
        '    <div class="landing-sub about-body">'
        f'<p>{_esc(p2)}</p>\n'
        f'<p>{_esc(p3)}</p></div>\n'
    )
    return tagline_html + sub_html


# ---- REGULATION CARDS ----------------------------------------------------- #
# We swap each card by its unique title anchor inside <article class=...>.
# Each card maps to an xlsx Methodology row.
CARD_ANCHORS: list[tuple[str, int]] = [
    # (title-substring used to locate the card, xlsx Methodology row)
    ('Artificial Intelligence Act (2024)', 18),
    ('Guidelines on the scope of the obligations for general-purpose '
     'AI models established by AIA (2025)', 20),
    ('Code of Practice for General-purpose AI Models (2025)', 19),
    ('SB 53 (2025) — Transparency in Frontier Artificial Intelligence (TFAI)', 21),
    ('SB 942 (2024) — California AI Transparency Act', 22),
    ('SB 24-205 (2024) — Colorado AI Act (CAIA)', 23),
    ('SB 25B-004 (2026)', 24),
    ('A6453B (2025) — Responsible AI Safety and Education Act (RAISE Act)', 25),
    ('S8828 (2025)', 26),
    ('HB 149 (2025) — Texas Responsible Artificial Intelligence '
     'Governance Act (TRAIGA)', 27),
    ('SB 149 (2024) — Artificial Intelligence Policy Act (AIPA)', 28),
    ('SB 226 (2025)', 29),
]


def _format_desc_html(text: str) -> str:
    """Render an xlsx Description cell as one or more <p
    class="law-card-v2-desc"> blocks. Multi-paragraph cells are split
    on blank lines."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]
    out_paras = []
    for p in paragraphs:
        # Replace any internal single newlines with a space.
        clean = " ".join(line.strip() for line in p.splitlines()).strip()
        out_paras.append(f'<p class="law-card-v2-desc">{_esc(clean)}</p>')
    return "\n        ".join(out_paras)


def _replace_card(html: str, title_substr: str, row: dict) -> str:
    """Locate the law-card-v2 article whose title contains `title_substr`,
    then replace its description and Effective-date meta entry."""
    title_pos = html.find(title_substr)
    if title_pos == -1:
        raise RuntimeError(
            f"build_v28: card title not found: {title_substr!r}"
        )
    # Walk back to the <article class="law-card-v2"...> open tag.
    art_open = html.rfind("<article class=\"law-card-v2", 0, title_pos)
    if art_open == -1:
        raise RuntimeError(
            f"build_v28: <article> open not found for {title_substr!r}"
        )
    art_close = html.find("</article>", title_pos)
    if art_close == -1:
        raise RuntimeError(
            f"build_v28: </article> close not found for {title_substr!r}"
        )
    card = html[art_open:art_close]

    # ---- Replace description block --------------------------------------- #
    new_desc_html = _format_desc_html(row["desc"])
    # The description block is a single <p class="law-card-v2-desc">...</p>
    # in v26. Find and replace it.
    desc_open = card.find('<p class="law-card-v2-desc">')
    if desc_open == -1:
        raise RuntimeError(
            f"build_v28: <p class=\"law-card-v2-desc\"> not found in card "
            f"for {title_substr!r}"
        )
    desc_close = card.find("</p>", desc_open) + len("</p>")
    new_card = card[:desc_open] + new_desc_html + card[desc_close:]

    # ---- Replace Effective date entry ------------------------------------ #
    if row["date"] is not None:
        new_eff = _date_str(row["date"])
        eff_idx = new_card.find("<strong>Effective:</strong>")
        if eff_idx == -1:
            raise RuntimeError(
                f"build_v28: <strong>Effective:</strong> not found in card "
                f"for {title_substr!r}"
            )
        # The line is e.g. '<strong>Effective:</strong> 1 Aug 2024</span>'.
        # Replace from after the </strong>+space up to the next </span>.
        after_label = new_card.index("</strong>", eff_idx) + len("</strong>")
        # skip exactly one space if present
        i = after_label
        if i < len(new_card) and new_card[i] == " ":
            i += 1
        end_span = new_card.index("</span>", i)
        new_card = (
            new_card[:after_label] + " " + new_eff + new_card[end_span:]
        )

    return html[:art_open] + new_card + html[art_close:]


# ---- METHODOLOGY STEPS ---------------------------------------------------- #
# Each method-step body is replaced by the parsed step text. Step 3 keeps
# the v26 GL bullet as the 5th `<li>`.

GL_LI_HTML = (
    '          <li>Cross-reference the <strong>Commission Guidelines '
    'on the scope of obligations for providers of general-purpose '
    'AI models</strong> (C(2025) 7719, 19 Nov 2025; cited as '
    '&quot;(GL)&quot; in the comparative analysis).</li>'
)


def _replace_step_body(html: str, num: int, step_text: str,
                       extra_li: str | None = None) -> str:
    """Replace the body content (everything between </h2> and the closing
    </div></section>) of method-step #step-N with rendered xlsx text."""
    anchor = f'id="step-{num}"'
    a_pos = html.find(anchor)
    if a_pos == -1:
        raise RuntimeError(f"build_v28: step-{num} anchor not found")
    sec_open = html.rfind("<section", 0, a_pos)
    sec_close = html.find("</section>", a_pos)
    if sec_open == -1 or sec_close == -1:
        raise RuntimeError(f"build_v28: step-{num} section bounds not found")

    section = html[sec_open:sec_close]
    # Find </h2> to preserve the heading.
    h2_close = section.find("</h2>")
    if h2_close == -1:
        raise RuntimeError(f"build_v28: step-{num} </h2> not found")
    after_h2 = h2_close + len("</h2>")

    # Find the closing </div> of method-step-body. The structure is:
    #   <section ...>
    #     <div class="method-step-num"...>NN</div>
    #     <div class="method-step-body">
    #       <h2>...</h2>
    #       <p>...</p>
    #       ...
    #     </div>
    #   </section>
    # So we need the LAST </div> before </section>.
    body_div_close = section.rfind("</div>")
    if body_div_close == -1 or body_div_close < after_h2:
        raise RuntimeError(f"build_v28: step-{num} body </div> not found")

    head_title, lead, items, trail = _render_step_body(step_text)
    body_html = _step_body_html(num, lead, items, trail, extra_li_html=extra_li)

    new_section = (
        section[:after_h2]
        + "\n"
        + body_html
        + "\n      "
        + section[body_div_close:]
    )
    return html[:sec_open] + new_section + html[sec_close:]


# --------------------------------------------------------------------------- #
# Main build                                                                  #
# --------------------------------------------------------------------------- #

def main() -> None:
    print("== v28 build ==")
    if not HTML_V26.exists():
        print("  digital_lexicon_v26.html missing — running build_v26 …")
        sys.path.insert(0, str(HERE))
        import build_v26 as _v26
        _v26.main()

    html = HTML_V26.read_text(encoding="utf-8")
    print(f"  read v26:                  {len(html):,} bytes")

    data = load_xlsx_data()

    # ---- HOME ------------------------------------------------------------- #
    new_home = _build_home_block(data["about_paras"])
    if HOME_TAGLINE_OLD in html:
        html = html.replace(HOME_TAGLINE_OLD, new_home, 1)
        print("  home:                      swapped tagline + sub block")
    elif new_home in html:
        print("  home:                      already updated (idempotent)")
    else:
        raise RuntimeError("build_v28: home tagline anchor not found")

    # ---- REGULATIONS CARDS ------------------------------------------------ #
    updated: list[str] = []
    for title_substr, row_idx in CARD_ANCHORS:
        row = data["regs"][row_idx]
        if row["desc"] is None:
            continue
        # Idempotency: if the new desc is already present in the card,
        # skip. Use the first 60 chars of the new desc as a fingerprint.
        fingerprint = _esc(row["desc"].split("\n\n")[0].strip())[:60]
        # Find the card and check if its current description starts with
        # the fingerprint.
        title_pos = html.find(title_substr)
        if title_pos == -1:
            raise RuntimeError(f"build_v28: card not found: {title_substr!r}")
        art_close = html.find("</article>", title_pos)
        card = html[html.rfind("<article", 0, title_pos):art_close]
        if fingerprint in card and _date_str(row["date"]) in card:
            updated.append(f"{title_substr.split(' ')[0]}(skip)")
            continue
        html = _replace_card(html, title_substr, row)
        # Short label
        short = title_substr.split(" ")[0] + " " + title_substr.split(" ")[1] \
            if " " in title_substr else title_substr
        updated.append(short)
    print(f"  regs:                      updated {len(updated)} cards")

    # ---- METHODOLOGY STEPS ----------------------------------------------- #
    for n in range(1, 7):
        extra = GL_LI_HTML if n == 3 else None
        html = _replace_step_body(html, n, data["steps"][n], extra_li=extra)
    print("  methodology:               swapped steps 1-6")

    HTML_V28.write_text(html, encoding="utf-8")
    shutil.copy2(HTML_V28, FINAL_TOOL)
    shutil.copy2(HTML_V28, FINAL_LEXICON)
    print(f"\n  wrote {HTML_V28.name}        ({len(html):,} bytes)")
    print(f"  wrote {FINAL_TOOL.name}            (mirror)")
    print(f"  wrote {FINAL_LEXICON.name}    (mirror)")


if __name__ == "__main__":
    main()
