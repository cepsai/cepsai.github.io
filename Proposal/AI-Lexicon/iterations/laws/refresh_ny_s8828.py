"""Refresh laws/ny-s8828.json with the full §1420-1429 of NY S8828.

The current blob was actually populated from S6953 (the prior bill version)
and only contains §1420-1425. The references in the lexicon analysis cells
cite §1426-1428, which are present in S8828 but missing from the blob.

NYSenate.gov is currently behind a Cloudflare challenge (HTTP 403 for
non-browsers), so we use a web.archive.org snapshot.
"""
from __future__ import annotations

import json
import re
import urllib.request
from html import unescape
from pathlib import Path

ARCHIVE_URL = (
    "https://web.archive.org/web/2026/"
    "https://www.nysenate.gov/legislation/bills/2025/S8828"
)
LAWS_DIR = Path(__file__).resolve().parent
TARGET = LAWS_DIR / "ny-s8828.json"
HTML_CACHE = LAWS_DIR / "ny-s8828-source.html"

SECTION_TITLES = {
    "1420": "Definitions",
    "1421": "Transparency requirements",
    "1422": "Reporting",
    "1423": "Loss of equity",
    "1424": "Duties and obligations",
    "1425": "Scope",
    "1426": "Exceptions",
    "1427": "Violations",
    "1428": "Large frontier developer disclosure",
    "1429": "Rulemaking authority",
}


def fetch() -> str:
    if HTML_CACHE.exists() and HTML_CACHE.stat().st_size > 50_000:
        return HTML_CACHE.read_text()
    print(f"  downloading {ARCHIVE_URL}")
    req = urllib.request.Request(ARCHIVE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    HTML_CACHE.write_text(body)
    return body


def html_to_text(s: str) -> str:
    s = re.sub(r"<script.*?</script>", " ", s, flags=re.DOTALL | re.I)
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.DOTALL | re.I)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</?p[^>]*>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    return unescape(s).replace("\xa0", " ")


def clean(body: str) -> str:
    # Remove page-number artifacts inserted mid-text (e.g. "S. 8828   8").
    body = re.sub(r"\n\s*S\.\s*8828\s+\d+\s*\n", "\n", body)
    body = re.sub(r"\n[ \t]+", "\n", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def parse_sections(text: str) -> list[dict]:
    pat = re.compile(r"§\s+(1\d{3})\.")
    matches = list(pat.finditer(text))
    sections: list[dict] = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_text = clean(text[m.start():end])
        sections.append({
            "id": m.group(1),
            "title": SECTION_TITLES.get(m.group(1), ""),
            "text": section_text,
        })
    return sections


def main() -> None:
    text = html_to_text(fetch())
    print(f"  text length: {len(text)}")
    sections = parse_sections(text)
    if len(sections) != 10:
        raise RuntimeError(
            f"expected 10 sections (1420-1429), parsed {len(sections)}: "
            f"{[s['id'] for s in sections]}"
        )
    print(f"  sections: {[s['id'] for s in sections]}")
    for s in sections:
        print(f"    §{s['id']} ({len(s['text'])} chars)")

    blob = {
        "id": "ny-s8828",
        "title": "New York S8828 (RAISE Act, 2025-2026 chapter amendment)",
        "url": "https://www.nysenate.gov/legislation/bills/2025/S8828",
        "sections": sections,
        "raw_text": text[text.find("ARTICLE 44-B"):],
    }
    # Keep raw_text bounded so the blob doesn't bloat with navigation cruft.
    cutoff = blob["raw_text"].find("§ 3.")
    if cutoff < 0:
        cutoff = blob["raw_text"].find("S 3.")
    if cutoff < 0:
        # Stop after the §1429 body — find the first non-bill paragraph.
        last_section_end = text.find("§ 1429.")
        if last_section_end >= 0:
            cutoff = text.find("\n \n", last_section_end + 2000) - text.find("ARTICLE 44-B")
    if cutoff > 0:
        blob["raw_text"] = blob["raw_text"][:cutoff].strip() + "\n"
    TARGET.write_text(json.dumps(blob, indent=2, ensure_ascii=False) + "\n")
    print(f"  wrote {TARGET} ({TARGET.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
