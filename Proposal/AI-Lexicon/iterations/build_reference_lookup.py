"""Build a lookup dictionary linking every article reference in the analysis
cells of digital_lexicon_v28.html to its corresponding law-blob anchor.

Inputs
------
- digital_lexicon_v28.html  (CONCEPTS array → cell.reference strings)
- laws/*.json               (law-blob article/section IDs)

Outputs (under ../outputs/)
---------------------------
- reference_lookup.json         canonical lookup keyed by raw reference string
- reference_lookup_atomic.json  one row per atomic citation (with provenance)
- reference_lookup_unmatched.csv  atomic refs that failed to resolve to a law-blob entry
- reference_lookup_summary.md   coverage summary

Design notes
------------
* A "raw reference" is a full cell.reference string (possibly semicolon-joined).
* An "atomic" reference is one citation, e.g. "EU AI Act, Article 13 (1)".
* Each atomic ref resolves to {law, kind, article_id, paragraphs[], anchor, display}.
* `anchor` is the ID matching law_blob.articles[].id or law_blob.sections[].id.
  When a paragraph is cited (e.g. Article 3 (4)), we still anchor at the article
  so the renderer can scroll to the full article body. The paragraphs[] array
  is preserved for future paragraph-level highlighting.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ITER_DIR = Path(__file__).resolve().parent
HTML_PATH = ITER_DIR / "digital_lexicon_v28.html"
LAWS_DIR = ITER_DIR / "laws"
OUT_DIR = ITER_DIR.parent / "outputs"
OUT_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Law-blob loading
# ---------------------------------------------------------------------------

def load_law_blobs() -> dict[str, dict]:
    """Return {law_id: blob_dict} for every laws/*.json with an id field."""
    blobs: dict[str, dict] = {}
    for path in sorted(LAWS_DIR.glob("*.json")):
        try:
            with path.open() as f:
                blob = json.load(f)
        except json.JSONDecodeError:
            print(f"WARN: skipping invalid JSON {path}", file=sys.stderr)
            continue
        if isinstance(blob, dict) and "id" in blob:
            blobs[blob["id"]] = blob
    return blobs


def index_law_blob(blob: dict) -> dict:
    """Return {item_kind: {item_id_str: title}} maps for fast existence checks."""
    idx = {"articles": {}, "sections": {}, "annexes": {}, "recitals": {}}
    for art in blob.get("articles", []) or []:
        if isinstance(art, dict) and "id" in art:
            idx["articles"][str(art["id"])] = art.get("title", "")
    for sec in blob.get("sections", []) or []:
        if isinstance(sec, dict) and "id" in sec:
            idx["sections"][str(sec["id"])] = sec.get("title", "")
    annexes = blob.get("annexes")
    if isinstance(annexes, list):
        for an in annexes:
            if isinstance(an, dict) and "id" in an:
                idx["annexes"][str(an["id"])] = an.get("title", "")
    elif isinstance(annexes, dict):
        for k, v in annexes.items():
            idx["annexes"][str(k)] = v if isinstance(v, str) else ""
    recitals = blob.get("recitals")
    if isinstance(recitals, dict):
        for k in recitals.keys():
            idx["recitals"][str(k)] = ""
    elif isinstance(recitals, list):
        for r in recitals:
            if isinstance(r, dict) and "id" in r:
                idx["recitals"][str(r["id"])] = r.get("title", "")
    return idx


# ---------------------------------------------------------------------------
# Reference parser
# ---------------------------------------------------------------------------

# Map various textual forms to canonical law_id.
# Order matters: most specific first. Pattern match consumes the matched span
# so that subsequent section/article extraction does not mistake bill numbers
# (e.g. "AB 2013", "S8828", "HB 149") for section identifiers.
LAW_PATTERNS: list[tuple[re.Pattern, str | None]] = [
    (re.compile(r"Code of Practice for GPAI\s*-\s*Copyright(?:\s+Chapter)?", re.I), "eu-gpai-cop-copyright"),
    (re.compile(r"Code of Practice for GPAI\s*-\s*Transparency(?:\s+Chapter)?", re.I), "eu-gpai-cop-transparency"),
    (re.compile(r"Code of Practice for GPAI\s*-\s*Safety(?:\s+and\s+Security)?(?:\s+Chapter)?", re.I), "eu-gpai-cop-safety"),
    (re.compile(r"\bColorado\s+SB\s*24-?205\b", re.I), "co-sb24205"),
    (re.compile(r"\bCO\s+SB\s*24-?205\b", re.I), "co-sb24205"),
    (re.compile(r"\bCalifornia\s+SB\s*942\b", re.I), "ca-sb942"),
    (re.compile(r"\bCA\s+SB\s*942\b", re.I), "ca-sb942"),
    (re.compile(r"\bCalifornia\s+SB\s*53\b", re.I), "ca-sb53"),
    (re.compile(r"\bCA\s+SB\s*53\b", re.I), "ca-sb53"),
    (re.compile(r"\bCalifornia\s+AB\s*2013\b", re.I), "ca-ab2013"),
    (re.compile(r"\bCA\s+AB\s*2013\b", re.I), "ca-ab2013"),
    (re.compile(r"\bNew\s+York\s+S\s*8828\b(?:\s*\(pending\))?", re.I), "ny-s8828"),
    (re.compile(r"\bNY\s+S\s*8828\b", re.I), "ny-s8828"),
    (re.compile(r"\bNew\s+York\s+A\s*6453\b(?:\s*\(pending\))?", re.I), "ny-a6453"),
    (re.compile(r"\bNY\s+A\s*6453\b", re.I), "ny-a6453"),
    (re.compile(r"\bTexas\s+HB\s*149\b", re.I), "tx-hb149"),
    (re.compile(r"\bTX\s+HB\s*149\b", re.I), "tx-hb149"),
    (re.compile(r"\bUtah\s+SB\s*226\b", re.I), "ut-sb226"),
    (re.compile(r"\bUT\s+SB\s*226\b", re.I), "ut-sb226"),
    # EU AI Act — match last so it doesn't gobble GPAI-CoP titles.
    (re.compile(r"\bEU\s+AI\s+Act\b", re.I), "eu-ai-act"),
    (re.compile(r"\bAI\s+Act\b", re.I), "eu-ai-act"),
    (re.compile(r"\bAIA\b", re.I), "eu-ai-act"),
    # External / unmapped — strip the marker but report no blob.
    (re.compile(r"Colorado Consumer Protection Act", re.I), None),
    (re.compile(r"\bUtah Code\b", re.I), None),
    (re.compile(r"Civil Code\b", re.I), None),
]


def detect_and_strip_law(text: str) -> tuple[str | None, str]:
    """Detect the law marker in ``text`` and return (law_id, residual_text).

    The residual is the text with the matched marker removed so that section
    regexes won't pick up bill numbers (e.g. "AB 2013" → section "2013").
    """
    law_id: str | None = None
    residual = text
    for pat, candidate in LAW_PATTERNS:
        m = pat.search(residual)
        if m:
            if law_id is None:
                law_id = candidate
            residual = (residual[: m.start()] + " " + residual[m.end():]).strip()
    return law_id, residual


# Atomic patterns for the kind of citation
ARTICLE_RE = re.compile(
    r"""
    Article\s*
    (?P<num>\d+)                          # article number
    (?P<tail>(?:\s*,?\s*\(\s*[^)]+?\s*\))*)  # optional trailing (X) groups
    """,
    re.I | re.VERBOSE,
)
ARTICLE_TAIL_RE = re.compile(r"\(\s*([^)]+?)\s*\)")
RECITAL_RE = re.compile(r"Recital\s*\(?(?P<num>\d+)\)?", re.I)
ANNEX_RE = re.compile(
    r"Annex\s+(?P<id>[IVXLCDM]+|\d+)(?:\s*\(\s*(?P<sub>[^)]+?)\s*\))?",
    re.I,
)
# State section: capture id like "13-75-101", "6-1-1701", "552.001", "1420", "22757.11"
SECTION_RE = re.compile(
    r"""
    (?:§|Section|Sec\.?)?\s*                 # optional § / Section prefix
    (?P<id>
        \d+-\d+-\d+(?:\.\d+)? |              # 13-75-101, 6-1-1701
        \d{3}\.\d+(?:\.\d+)? |               # 552.001, 22757.11
        \d{4,}(?:\.\d+)?                     # 1420, 22757
    )
    \.?                                      # trailing dot ("1701.")
    (?:\s*\(\s*(?P<para>[^)]+?)\s*\))?       # optional (4) or (b)
    (?:\s*\(\s*(?P<sub>[^)]+?)\s*\))?        # second paren e.g. (c)(1)
    """,
    re.I | re.VERBOSE,
)
# Loose state section without § prefix when separator-style "Texas HB149, 552.001. (2)"
LOOSE_SECTION_RE = re.compile(
    r"""
    (?<![\w.])                                # not preceded by word/dot
    (?P<id>
        \d+-\d+-\d+(?:\.\d+)? |
        \d{3}\.\d+(?:\.\d+)? |
        \d{4,}(?:\.\d+)?
    )
    \.?
    (?:\s*\(\s*(?P<para>[^)]+?)\s*\))?
    (?:\s*\(\s*(?P<sub>[^)]+?)\s*\))?
    """,
    re.I | re.VERBOSE,
)
# Guidelines: "(GL, (17))" or "(GL, 3.2)"
GUIDELINES_RE = re.compile(
    r"\(\s*GL\s*,\s*\(?(?P<id>[\w.-]+)\)?\s*\)",
    re.I,
)
# CoP: "Code of Practice for GPAI - Copyright Chapter"
COP_RE = re.compile(
    r"Code of Practice for GPAI\s*-\s*(?P<chapter>Copyright|Transparency|Safety)\b",
    re.I,
)


def split_atomic(raw: str) -> list[str]:
    """Split a cell reference into atomic citations on ';'."""
    return [p.strip().rstrip(",") for p in raw.split(";") if p.strip()]


def parse_para_list(s: str | None) -> list[str]:
    """Parse '1, 2', '1 - 4', '1)(2', etc. into a list of paragraph tokens."""
    if not s:
        return []
    s = s.strip()
    # range "1 - 4"
    m_range = re.match(r"^(\d+)\s*-\s*(\d+)$", s)
    if m_range:
        a, b = int(m_range.group(1)), int(m_range.group(2))
        return [str(i) for i in range(a, b + 1)]
    # comma list
    if "," in s:
        return [p.strip() for p in s.split(",") if p.strip()]
    # single token
    return [s]


def normalise_anchor(law: str | None, kind: str, ids: list[str]) -> str:
    """Build a canonical anchor (matches what _findArticle expects)."""
    return ids[0] if ids else ""


def parse_atomic(atomic: str) -> dict:
    """Return a parsed citation dict with law, kind, anchor, paragraphs."""
    text = atomic.strip()
    law_id, residual = detect_and_strip_law(text)
    info = {
        "raw": text,
        "law": law_id,
        "kind": None,
        "article_id": None,
        "paragraphs": [],
        "subparagraphs": [],
        "anchor": None,
        "label": text,
    }

    # Guidelines reference "(GL, (17))" or "(GL, 3.2)" — match against original
    # text. All (GL, ...) citations in the current dataset live inside GPAI-model
    # concepts, so we resolve them to the GPAI-scope guidelines blob. The
    # numeric "(17)" form is a paragraph number (anchored to the first segment
    # so the renderer scrolls to the containing section); "3.2" is a section
    # path whose first component matches a parsed section id.
    m = GUIDELINES_RE.search(text)
    if m:
        ident = m.group("id")
        info["law"] = "eu-guidelines-gpai-scope"
        if "." in ident:
            head = ident.split(".")[0]
            info["kind"] = "section"
            info["article_id"] = head
            info["anchor"] = head
            info["paragraphs"] = parse_para_list(ident.split(".", 1)[1])
        else:
            info["kind"] = "paragraph"
            info["article_id"] = ident
            info["anchor"] = ident
        info["label"] = f"Commission Guidelines on the scope of GPAI obligations, ({ident})"
        return info

    # CoP chapter reference resolves to the preamble of the matching CoP blob.
    if law_id and law_id.startswith("eu-gpai-cop-"):
        info["kind"] = "chapter"
        info["article_id"] = "preamble"
        info["anchor"] = "preamble"
        return info

    # Recitals (EU only) — search residual so we don't mistake bill numbers
    m = RECITAL_RE.search(residual)
    if m and law_id in (None, "eu-ai-act"):
        info["law"] = "eu-ai-act"
        info["kind"] = "recital"
        info["article_id"] = m.group("num")
        info["anchor"] = m.group("num")
        return info

    # Annex (EU AI Act)
    m = ANNEX_RE.search(residual)
    if m and law_id in (None, "eu-ai-act"):
        info["law"] = "eu-ai-act"
        info["kind"] = "annex"
        info["article_id"] = m.group("id").upper()
        info["anchor"] = m.group("id").upper()
        if m.group("sub"):
            info["paragraphs"] = parse_para_list(m.group("sub"))
        return info

    # EU Article (must come after recital/annex)
    m = ARTICLE_RE.search(residual)
    if m and law_id in (None, "eu-ai-act"):
        info["law"] = "eu-ai-act"
        info["kind"] = "article"
        info["article_id"] = m.group("num")
        info["anchor"] = m.group("num")
        # Walk every (X) group in the tail. Numeric tokens go to paragraphs,
        # single-letter tokens (a, b, c) go to subparagraphs.
        paras: list[str] = []
        subs: list[str] = []
        for tail_match in ARTICLE_TAIL_RE.finditer(m.group("tail") or ""):
            for tok in parse_para_list(tail_match.group(1)):
                if re.fullmatch(r"\d+", tok):
                    paras.append(tok)
                elif re.fullmatch(r"[a-z]", tok, re.I):
                    subs.append(tok)
                else:
                    paras.append(tok)
        info["paragraphs"] = paras
        info["subparagraphs"] = subs
        return info

    # State section — only valid once a state law has been detected. Search
    # the residual so we don't grab the bill number.
    if law_id and not law_id.startswith("eu-"):
        m = SECTION_RE.search(residual) or LOOSE_SECTION_RE.search(residual)
        if m:
            info["kind"] = "section"
            info["article_id"] = m.group("id")
            info["anchor"] = m.group("id")
            if m.group("para"):
                info["paragraphs"] = parse_para_list(m.group("para"))
            if m.group("sub"):
                info["subparagraphs"] = parse_para_list(m.group("sub"))
            return info

    return info


# ---------------------------------------------------------------------------
# CONCEPTS extraction
# ---------------------------------------------------------------------------

def load_concepts(html: str) -> list[dict]:
    """Return the CONCEPTS JS array as Python."""
    m = re.search(r"const CONCEPTS = (\[.*?\]);\s*\n", html, re.DOTALL)
    if not m:
        raise RuntimeError("CONCEPTS array not found in HTML")
    return json.loads(m.group(1))


def collect_cells(concepts: list[dict]) -> list[dict]:
    """Walk the concept tree and yield rows for every cell with a reference."""
    rows = []
    for c in concepts:
        for sc in c.get("sub_concepts", []):
            for d in sc.get("dimensions", []):
                cells = d.get("cells", {})
                for jid, cell in cells.items():
                    if not isinstance(cell, dict):
                        continue
                    ref = cell.get("reference") or ""
                    if not ref:
                        continue
                    rows.append({
                        "concept_id": c.get("id"),
                        "concept_title": c.get("title", ""),
                        "sub_concept_id": sc.get("id"),
                        "sub_concept_title": sc.get("title", ""),
                        "dimension_id": d.get("id"),
                        "dimension_label": d.get("label", ""),
                        "jurisdiction": jid,
                        "raw_reference": ref,
                    })
    return rows


# ---------------------------------------------------------------------------
# Build & validate
# ---------------------------------------------------------------------------

def resolve_against_blob(parsed: dict, blob_idx: dict) -> dict:
    """Mutate ``parsed`` with a `match` field describing blob coverage."""
    match = {"found": False, "title": None, "fallback": None}
    law = parsed.get("law")
    anchor = parsed.get("anchor")
    if law and anchor and law in blob_idx:
        idx = blob_idx[law]
        kind = parsed.get("kind")
        # Map our kind labels to blob index keys.
        kind_to_idx = {
            "article": "articles",
            "section": "sections",
            "annex": "annexes",
            "recital": "recitals",
            "chapter": "sections",
            "paragraph": "sections",  # paragraph numbers in guidelines map by section
        }
        idx_key = kind_to_idx.get(kind)
        if idx_key and anchor in idx.get(idx_key, {}):
            match["found"] = True
            match["title"] = idx[idx_key][anchor] or None
        else:
            # Fallback: try article id without paragraph (e.g. "6-1-1701" exists,
            # but only article id "6" survived — check first segment).
            short = str(anchor).split("-")[0]
            if idx_key and short in idx.get(idx_key, {}):
                match["found"] = True
                match["fallback"] = short
                match["title"] = idx[idx_key][short] or None
            elif kind == "paragraph" and "preamble" in idx.get("sections", {}):
                # Paragraph numbers in guideline preambles fall back to the
                # whole document — better than nothing for the renderer.
                match["found"] = True
                match["fallback"] = "preamble"
                match["title"] = idx["sections"]["preamble"] or None
    parsed["match"] = match
    return parsed


def main() -> None:
    print("Loading HTML and law blobs ...")
    html = HTML_PATH.read_text()
    concepts = load_concepts(html)
    blobs = load_law_blobs()
    blob_idx = {k: index_law_blob(b) for k, b in blobs.items()}
    print(f"  loaded {len(concepts)} top-level concepts, {len(blobs)} law blobs")

    cell_rows = collect_cells(concepts)
    print(f"  collected {len(cell_rows)} cells with references")

    # Build canonical lookup (raw reference string → atomic resolutions list).
    # We also build a flat per-atomic table for unmatched/coverage analysis.
    raw_to_atomics: dict[str, list[dict]] = {}
    atomic_rows: list[dict] = []

    for row in cell_rows:
        raw = row["raw_reference"]
        if raw in raw_to_atomics:
            continue  # parsed once, reuse
        atomics = []
        last_law: str | None = None
        for atom in split_atomic(raw):
            parsed = parse_atomic(atom)
            # Orphan fix-up: bare "§1425" after "NY S8828 §1420(...)" inherits
            # the last-detected law within this same raw reference string.
            if parsed.get("law") is None and last_law and parsed.get("anchor") is None:
                m_orphan = SECTION_RE.search(atom)
                if m_orphan:
                    parsed["law"] = last_law
                    parsed["kind"] = "section"
                    parsed["article_id"] = m_orphan.group("id")
                    parsed["anchor"] = m_orphan.group("id")
                    if m_orphan.group("para"):
                        parsed["paragraphs"] = parse_para_list(m_orphan.group("para"))
                    if m_orphan.group("sub"):
                        parsed["subparagraphs"] = parse_para_list(m_orphan.group("sub"))
            if parsed.get("law"):
                last_law = parsed["law"]
            resolve_against_blob(parsed, blob_idx)
            atomics.append(parsed)
        raw_to_atomics[raw] = atomics

    # Provenance: per-atomic rows tied back to the cell they came from
    for row in cell_rows:
        for atom in raw_to_atomics[row["raw_reference"]]:
            atomic_rows.append({
                **row,
                **{f"atom_{k}": v for k, v in atom.items() if k != "match"},
                "atom_match_found": atom["match"]["found"],
                "atom_match_title": atom["match"]["title"],
                "atom_match_fallback": atom["match"]["fallback"],
            })

    # Coverage stats — parse-success vs blob-coverage are distinct.
    total_atoms = sum(len(v) for v in raw_to_atomics.values())
    parsed_ok = sum(
        1 for v in raw_to_atomics.values() for a in v
        if a.get("law") and a.get("anchor")
    )
    matched = sum(1 for v in raw_to_atomics.values() for a in v if a["match"]["found"])
    by_law = defaultdict(lambda: [0, 0, 0])  # [matched, parsed_ok, total]
    for v in raw_to_atomics.values():
        for a in v:
            law = a.get("law") or "(unknown)"
            by_law[law][2] += 1
            if a.get("law") and a.get("anchor"):
                by_law[law][1] += 1
            if a["match"]["found"]:
                by_law[law][0] += 1

    # Atomic-keyed lookup (same shape as the existing window.REF_MAP).
    # Last writer wins: many atoms repeat across cells with identical resolution.
    atomic_lookup: dict[str, dict] = {}
    for v in raw_to_atomics.values():
        for a in v:
            atomic_lookup[a["raw"]] = {
                "law": a["law"],
                "kind": a["kind"],
                "anchor": a["anchor"] or "",
                "paragraphs": a["paragraphs"],
                "subparagraphs": a["subparagraphs"],
            }

    # Write canonical lookup JSON keyed by raw reference
    lookup_json = {
        "_meta": {
            "generated": datetime.now().isoformat(timespec="seconds"),
            "html_source": HTML_PATH.name,
            "raw_count": len(raw_to_atomics),
            "atomic_count": total_atoms,
            "atomic_parsed": parsed_ok,
            "atomic_matched_blob": matched,
        },
        "lookup": {
            raw: [
                {
                    "law": a["law"],
                    "kind": a["kind"],
                    "anchor": a["anchor"],
                    "paragraphs": a["paragraphs"],
                    "subparagraphs": a["subparagraphs"],
                    "label": a["label"],
                    "matched": a["match"]["found"],
                    "fallback_anchor": a["match"]["fallback"],
                }
                for a in atomics
            ]
            for raw, atomics in raw_to_atomics.items()
        },
    }
    out_json = OUT_DIR / "reference_lookup.json"
    with out_json.open("w") as f:
        json.dump(lookup_json, f, indent=2, ensure_ascii=False)

    # Atomic lookup (REF_MAP-shape) for direct drop-in use by the HTML.
    out_atomic_lookup = OUT_DIR / "reference_lookup_atomic_map.json"
    with out_atomic_lookup.open("w") as f:
        json.dump(atomic_lookup, f, indent=2, ensure_ascii=False, sort_keys=True)

    # Delta report vs the existing window.REF_MAP embedded in the HTML.
    existing_map: dict[str, dict] = {}
    m_existing = re.search(
        r"window\.REF_MAP\s*=\s*(\{.*?\});", html, re.DOTALL,
    )
    if m_existing:
        try:
            existing_map = json.loads(m_existing.group(1))
        except json.JSONDecodeError:
            existing_map = {}
    delta_rows = []
    for k in sorted(set(existing_map) | set(atomic_lookup)):
        e = existing_map.get(k)
        n = atomic_lookup.get(k)
        if e is None:
            status = "new"
        elif n is None:
            status = "obsolete"
        elif (e.get("law") != n.get("law")
              or e.get("anchor") != n.get("anchor")
              or e.get("kind") != n.get("kind")):
            status = "changed"
        else:
            continue
        delta_rows.append({
            "status": status,
            "raw_reference": k,
            "existing_law": (e or {}).get("law"),
            "existing_kind": (e or {}).get("kind"),
            "existing_anchor": (e or {}).get("anchor"),
            "new_law": (n or {}).get("law"),
            "new_kind": (n or {}).get("kind"),
            "new_anchor": (n or {}).get("anchor"),
            "new_paragraphs": ",".join((n or {}).get("paragraphs", []) or []),
        })
    out_delta = OUT_DIR / "reference_lookup_delta.csv"
    with out_delta.open("w", newline="") as f:
        if delta_rows:
            w = csv.DictWriter(f, fieldnames=list(delta_rows[0].keys()))
            w.writeheader()
            w.writerows(delta_rows)

    # Atomic provenance JSON (for quick inspection)
    out_atomic = OUT_DIR / "reference_lookup_atomic.json"
    with out_atomic.open("w") as f:
        json.dump(atomic_rows, f, indent=2, ensure_ascii=False)

    # Unmatched CSV
    out_csv = OUT_DIR / "reference_lookup_unmatched.csv"
    fields = [
        "concept_id", "sub_concept_id", "dimension_label", "jurisdiction",
        "raw_reference", "atom_raw", "atom_law", "atom_kind", "atom_anchor",
        "atom_paragraphs", "reason",
    ]
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in atomic_rows:
            if row["atom_match_found"]:
                continue
            reason = []
            if not row["atom_law"]:
                reason.append("law-not-detected")
            if not row["atom_anchor"]:
                reason.append("no-anchor")
            if row["atom_law"] and row["atom_law"] not in blobs:
                reason.append("law-blob-missing")
            elif row["atom_law"] and row["atom_anchor"]:
                reason.append("anchor-not-in-blob")
            w.writerow({
                "concept_id": row["concept_id"],
                "sub_concept_id": row["sub_concept_id"],
                "dimension_label": row["dimension_label"],
                "jurisdiction": row["jurisdiction"],
                "raw_reference": row["raw_reference"],
                "atom_raw": row["atom_raw"],
                "atom_law": row["atom_law"],
                "atom_kind": row["atom_kind"],
                "atom_anchor": row["atom_anchor"],
                "atom_paragraphs": ",".join(row["atom_paragraphs"]) if row["atom_paragraphs"] else "",
                "reason": "|".join(reason) or "unknown",
            })

    # Summary markdown
    out_md = OUT_DIR / "reference_lookup_summary.md"
    lines = [
        f"# Reference lookup — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"- Raw cell-reference strings: **{len(raw_to_atomics)}**",
        f"- Atomic citations: **{total_atoms}**",
        f"- Parsed (law + anchor identified): **{parsed_ok}** "
        f"({parsed_ok/total_atoms:.0%})",
        f"- Matched against a law-blob article/section: **{matched}** "
        f"({matched/total_atoms:.0%})",
        "",
        "Parse-success and blob-coverage are distinct: a citation can be parsed "
        "correctly to e.g. `eu-ai-act/annex/IV` but still not match because the "
        "annex isn't ingested into the law blob yet.",
        "",
        "## Coverage by law",
        "",
        "| law_id | matched | parsed | total | match-rate |",
        "| --- | --- | --- | --- | --- |",
    ]
    for law, (m, p, t) in sorted(by_law.items(), key=lambda x: -x[1][2]):
        rate = f"{m/t:.0%}" if t else "-"
        lines.append(f"| {law} | {m} | {p} | {t} | {rate} |")
    delta_counts = defaultdict(int)
    for r in delta_rows:
        delta_counts[r["status"]] += 1
    lines.extend([
        "",
        "## Delta vs current `window.REF_MAP`",
        "",
        f"- new keys produced by parser: **{delta_counts['new']}**",
        f"- existing keys no longer used (orphans in HTML): **{delta_counts['obsolete']}**",
        f"- entries with changed law/kind/anchor: **{delta_counts['changed']}**",
        "",
        "Anchor format note: the parser emits bare article/section IDs "
        "(e.g. `\"3\"`) with paragraphs/subparagraphs as separate fields, "
        "whereas the current `REF_MAP` uses joined anchors (e.g. `\"3-3\"`). "
        "Most `changed` rows reflect this convention difference, not a "
        "semantic disagreement.",
        "",
        "## Outputs",
        f"- `{out_json.name}` — canonical lookup keyed by raw reference",
        f"- `{out_atomic_lookup.name}` — atomic-keyed REF_MAP-shape lookup (drop-in for the HTML)",
        f"- `{out_atomic.name}` — per-atomic rows with concept provenance",
        f"- `{out_csv.name}` — unmatched citations needing review",
        f"- `{out_delta.name}` — diff against existing `window.REF_MAP`",
    ])
    out_md.write_text("\n".join(lines) + "\n")

    print()
    print(f"  raw refs: {len(raw_to_atomics)}, atoms: {total_atoms}, "
          f"parsed: {parsed_ok}, blob-matched: {matched}")
    print(f"  → {out_json.relative_to(ITER_DIR.parent)}")
    print(f"  → {out_atomic_lookup.relative_to(ITER_DIR.parent)}")
    print(f"  → {out_atomic.relative_to(ITER_DIR.parent)}")
    print(f"  → {out_csv.relative_to(ITER_DIR.parent)}")
    print(f"  → {out_md.relative_to(ITER_DIR.parent)}")


if __name__ == "__main__":
    main()
