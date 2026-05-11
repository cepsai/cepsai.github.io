"""parse_v29.py — Extract analyses and article references from v29 HTML.

US-002: a parser that walks ``digital_lexicon_v29.html`` and emits one row
per (term, analysis_text, law_id, article_id) tuple so the verifier can
compare HTML state against the Excel ground truth.

Public API
----------
- parse_v29(path: Path | None = None) -> pandas.DataFrame

The data we care about lives in a JS literal::

    const CONCEPTS = [{...}, ...];

Each concept has ``sub_concepts``, each sub-concept has ``dimensions``, and
each dimension has a ``cells`` map keyed by jurisdiction id (``eu``, ``co``,
``ca-...``, etc.). A cell with an ``analysis`` field is what we extract;
the cell's ``reference`` field carries the citation(s) used to compute the
``law_id`` / ``article_id`` columns via ``build_reference_lookup.parse_atomic``.

Per the PRD the parser uses BeautifulSoup to find the script element rather
than scraping the raw text — that way we cope with multiple script tags or
attribute variations without regex-only parsing of HTML.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

ITER_DIR = Path(__file__).resolve().parent
if str(ITER_DIR) not in sys.path:
    sys.path.insert(0, str(ITER_DIR))

from build_reference_lookup import parse_atomic, split_atomic  # noqa: E402

DEFAULT_HTML = ITER_DIR / "digital_lexicon_v29.html"

PARSE_V29_COLUMNS = [
    "concept_id", "sub_concept_id", "jurisdiction",
    "term", "dim_id", "dim_label",
    "analysis_text", "reference", "law_id", "article_id",
]


# --------------------------------------------------------------------------- #
# CONCEPTS extraction                                                         #
# --------------------------------------------------------------------------- #

_NEEDLE = "const CONCEPTS = "


def _find_concepts_script(html_text: str) -> str:
    """Use BeautifulSoup to locate the <script> that defines CONCEPTS."""
    soup = BeautifulSoup(html_text, "html.parser")
    for script in soup.find_all("script"):
        body = script.string
        if body is None:
            # ``string`` is None for scripts with mixed children; fall back
            # to the concatenated text content.
            body = script.get_text() or ""
        if _NEEDLE in body:
            return body
    raise ValueError("CONCEPTS literal not found in any <script> element")


def _extract_concepts_json(html_text: str) -> list[dict]:
    """Return the parsed CONCEPTS list embedded in the HTML.

    The literal is JSON-shaped (the build script emits ``json.dumps``
    output), so once we isolate the bracketed span we can hand it directly
    to ``json.loads`` without any JS-to-JSON translation.
    """
    body = _find_concepts_script(html_text)
    head = body.find(_NEEDLE)
    start = head + len(_NEEDLE)
    if start >= len(body) or body[start] != "[":
        raise ValueError(
            f"Expected '[' after `{_NEEDLE.strip()}` (got "
            f"{body[start:start + 1]!r})"
        )
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(body)):
        c = body[i]
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
                    return json.loads(body[start:i + 1])
    raise ValueError("Unbalanced CONCEPTS literal")


# --------------------------------------------------------------------------- #
# Reference parsing                                                           #
# --------------------------------------------------------------------------- #

def _explode_reference(reference: str | None) -> list[dict]:
    """Split a cell.reference string into one entry per atomic citation.

    Returns an empty list when no atomic citation parses cleanly (caller
    decides whether to emit a None-law row anyway).
    """
    if not reference:
        return []
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for atom in split_atomic(reference):
        parsed = parse_atomic(atom)
        if not (parsed.get("law") and parsed.get("anchor")):
            continue
        key = (parsed["law"], str(parsed["anchor"]))
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "law_id": parsed["law"],
            "article_id": str(parsed["anchor"]),
            "raw_ref": parsed["raw"],
        })
    return out


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #

def parse_v29(path: Path | str | None = None) -> pd.DataFrame:
    """Extract every analysis cell from the v29 HTML as a DataFrame.

    Each row corresponds to one (term, analysis_text, law_id, article_id)
    citation. Cells whose ``reference`` parses to multiple atomic citations
    are exploded — one row per (law_id, article_id) pair. Cells that have
    an analysis but no parseable reference still produce a single row with
    ``law_id = article_id = None`` so downstream verification can spot them.

    The ``analysis_text`` value is the exact string stored in the JSON
    literal — no whitespace normalisation, no quote re-escaping, no
    punctuation drift.
    """
    src = Path(path) if path else DEFAULT_HTML
    html_text = src.read_text(encoding="utf-8")
    concepts = _extract_concepts_json(html_text)

    rows: list[dict] = []
    for concept in concepts:
        cid = concept.get("id")
        for sc in concept.get("sub_concepts", []) or []:
            sid = sc.get("id")
            sc_title = sc.get("title")
            jurisdictions = sc.get("jurisdictions") or {}
            for dim in sc.get("dimensions", []) or []:
                dim_id = dim.get("id")
                dim_label = dim.get("label")
                for jid, cell in (dim.get("cells") or {}).items():
                    if not isinstance(cell, dict):
                        continue
                    analysis = cell.get("analysis")
                    if not analysis:
                        continue
                    reference = cell.get("reference") or None
                    juris_term = (jurisdictions.get(jid) or {}).get("term")
                    term = juris_term or sc_title
                    base = {
                        "concept_id": cid,
                        "sub_concept_id": sid,
                        "jurisdiction": jid,
                        "term": term,
                        "dim_id": dim_id,
                        "dim_label": dim_label,
                        "analysis_text": analysis,
                        "reference": reference,
                    }
                    refs = _explode_reference(reference)
                    if not refs:
                        rows.append({**base, "law_id": None,
                                     "article_id": None})
                        continue
                    for ref in refs:
                        rows.append({
                            **base,
                            "law_id": ref["law_id"],
                            "article_id": ref["article_id"],
                        })

    df = pd.DataFrame(rows, columns=PARSE_V29_COLUMNS)
    return df.astype(object).where(df.notna(), None)


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--html", default=str(DEFAULT_HTML))
    args = p.parse_args(argv)

    print(f"Parsing v29 HTML: {args.html}")
    df = parse_v29(args.html)

    analysis_key = ["concept_id", "sub_concept_id", "jurisdiction", "dim_id"]
    n_analyses = df.drop_duplicates(subset=analysis_key).shape[0]
    n_laws = df["law_id"].dropna().nunique()
    n_terms = df["term"].dropna().nunique()
    n_with_article = int(df["article_id"].notna().sum())

    print(f"\n=== PARSE_V29 ({len(df)} rows) ===")
    print(f"  total analyses: {n_analyses}")
    print(f"  unique laws referenced: {n_laws}")
    print(f"  unique terms: {n_terms}")
    print(f"  rows with article_id: {n_with_article}")

    if len(df):
        with pd.option_context(
            "display.max_columns", None,
            "display.max_colwidth", 60,
            "display.width", 200,
        ):
            print("\nFirst 5 rows:")
            print(df.head(5).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
