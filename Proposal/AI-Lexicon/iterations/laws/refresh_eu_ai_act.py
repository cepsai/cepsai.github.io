"""Refresh laws/eu-ai-act.json with full annexes (I-XIII) and recitals (1-180).

Source: web.archive.org snapshot of EUR-Lex consolidated CELEX 32024R1689
(EUR-Lex itself is currently behind a CloudFront WAF challenge that blocks
non-browser clients).

Strategy:
1. Download the archived HTML.
2. Strip script/style and convert to plain text.
3. Slice the recital block (between "Whereas:" and "HAVE ADOPTED THIS REGULATION")
   and parse "(N)" markers into a {id: text} dict.
4. Slice the annex section (from "ANNEX I" to end-of-document) and split on
   "ANNEX <ROMAN>" markers. The first non-empty line after the marker is the
   annex title, the rest is the body.
5. Merge into the existing eu-ai-act.json (preserving articles).
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from html import unescape
from pathlib import Path

ARCHIVE_URL = (
    "https://web.archive.org/web/2025/"
    "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024R1689"
)
LAWS_DIR = Path(__file__).resolve().parent
TARGET = LAWS_DIR / "eu-ai-act.json"
HTML_CACHE = LAWS_DIR / "eu-ai-act-eurlex.html"


def fetch_html() -> str:
    if HTML_CACHE.exists() and HTML_CACHE.stat().st_size > 100_000:
        return HTML_CACHE.read_text()
    print(f"  downloading {ARCHIVE_URL}")
    req = urllib.request.Request(ARCHIVE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    HTML_CACHE.write_text(body)
    return body


_SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def html_to_text(s: str) -> str:
    # Convert superscript markup to Unicode superscripts BEFORE stripping
    # tags, so "10<sup>25</sup>" becomes "10²⁵" rather than "10(^25)".
    def _sup(m: re.Match) -> str:
        return m.group(1).translate(_SUP)
    s = re.sub(r"<sup[^>]*>([^<]+)</sup>", _sup, s, flags=re.I)
    # EUR-Lex uses <span class="oj-super"> for superscripts.
    s = re.sub(r'<span class="oj-super">([^<]+)</span>', _sup, s, flags=re.I)
    s = re.sub(r"<script.*?</script>", " ", s, flags=re.DOTALL | re.I)
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.DOTALL | re.I)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</?p[^>]*>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    text = unescape(s).replace("\xa0", " ")
    # Catch any "10(^N)" fallback forms that slipped past the <sup> rewrite.
    def _ascii_sup(m: re.Match) -> str:
        return "10" + m.group(1).translate(_SUP)
    text = re.sub(r"10\(\^(-?\d+)\)", _ascii_sup, text)
    text = re.sub(r"10\^(-?\d+)\b", _ascii_sup, text)
    return text


def clean_paragraph(body: str) -> str:
    body = re.sub(r"\n[ \t]+", "\n", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def parse_recitals(text: str) -> dict[str, str]:
    ws = text.find("Whereas:")
    adopted = text.find("HAVE ADOPTED THIS REGULATION", ws)
    if ws < 0 or adopted < 0:
        raise RuntimeError("could not locate Whereas: / HAVE ADOPTED THIS REGULATION")
    block = text[ws:adopted]
    pat = re.compile(r"\n\s*\((\d+)\)\s*\n", re.MULTILINE)
    matches = list(pat.finditer(block))
    recitals: dict[str, str] = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(block)
        recitals[m.group(1)] = clean_paragraph(block[m.end():end])
    return recitals


def parse_articles(text: str) -> list[dict]:
    """Slice articles 1-113 from the consolidated text. Each article starts
    with a line ``Article N`` followed by a newline, then the title, then the
    body. The next article boundary is the next ``Article N+1``."""
    pat = re.compile(r"\n\s*Article\s+(\d+)\s*\n", re.MULTILINE)
    matches = list(pat.finditer(text))
    if not matches:
        return []
    annex_pos = text.find("\nANNEX I\n")
    end_of_articles = annex_pos if annex_pos > 0 else len(text)
    articles: list[dict] = []
    for i, m in enumerate(matches):
        next_start = matches[i + 1].start() if i + 1 < len(matches) else end_of_articles
        chunk = text[m.end():next_start]
        lines = chunk.split("\n")
        title = ""
        body_start = 0
        for j, ln in enumerate(lines):
            if ln.strip():
                title = ln.strip()
                body_start = j + 1
                break
        body = "\n".join(lines[body_start:])
        articles.append({
            "id": m.group(1),
            "title": f"Article {m.group(1)}: {title}" if title else f"Article {m.group(1)}",
            "text": clean_paragraph(body),
        })
    return articles


def parse_annexes(text: str) -> list[dict]:
    # Find the first ANNEX I marker (skip any "Annex I" mentions in body text by
    # requiring it to be on its own line followed by a blank line and a title).
    pat = re.compile(r"\n\s*ANNEX\s+([IVXLCDM]+)\b\s*\n", re.MULTILINE)
    matches = list(pat.finditer(text))
    if not matches:
        return []
    annexes: list[dict] = []
    for i, m in enumerate(matches):
        # Skip cross-reference matches (very short content). We only keep matches
        # whose distance to the next ANNEX is large enough to contain real content.
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[m.end():end]
        if len(block) < 200:
            continue
        # Title is the first non-empty line.
        lines = [ln.strip() for ln in block.split("\n")]
        title = ""
        for ln in lines:
            if ln:
                title = ln
                break
        annexes.append({
            "id": m.group(1),
            "title": title,
            "text": clean_paragraph(block),
        })
    # Deduplicate by id, keeping the longest text (in case of false matches).
    by_id: dict[str, dict] = {}
    for a in annexes:
        if a["id"] not in by_id or len(a["text"]) > len(by_id[a["id"]]["text"]):
            by_id[a["id"]] = a
    return [by_id[k] for k in sorted(by_id, key=lambda r: roman_to_int(r))]


def roman_to_int(s: str) -> int:
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total, prev = 0, 0
    for ch in reversed(s):
        v = vals.get(ch, 0)
        total += -v if v < prev else v
        prev = max(prev, v)
    return total


def main() -> None:
    text = html_to_text(fetch_html())
    print(f"  text length: {len(text)}")
    recitals = parse_recitals(text)
    annexes = parse_annexes(text)
    articles = parse_articles(text)
    print(f"  recitals: {len(recitals)} (first id={min(recitals, key=int)}, last id={max(recitals, key=int)})")
    print(f"  annexes:  {len(annexes)} ({', '.join(a['id'] for a in annexes)})")
    print(f"  articles: {len(articles)} ({articles[0]['id']}-{articles[-1]['id']})")

    if not TARGET.exists():
        print(f"ERROR: {TARGET} missing", file=sys.stderr)
        sys.exit(1)
    blob = json.loads(TARGET.read_text())
    # Keep the existing per-article ``paras`` field (paragraph-by-paragraph
    # text from artificialintelligenceact.eu) but replace the corrupted
    # ``text`` field with the clean EUR-Lex body.
    new_text_by_id = {a["id"]: (a["title"], a["text"]) for a in articles}
    for art in blob.get("articles", []):
        hit = new_text_by_id.get(str(art.get("id")))
        if hit:
            art["title"] = hit[0]
            art["text"] = hit[1]
    blob["recitals"] = recitals
    blob["annexes"] = annexes
    TARGET.write_text(json.dumps(blob, indent=2, ensure_ascii=False) + "\n")
    print(f"  wrote {TARGET} ({TARGET.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
