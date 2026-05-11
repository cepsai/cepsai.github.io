"""build_v30_autocorrect.py — Pre-compute the US-009 auto-correct lookup.

For every HTML analysis cell whose linked article has *no verbatim row*
in the cross-checked Excel (``link_status == 'no_verbatim'``), run a
similarity search over every article in the linked law's blob and pick
the best-scoring article above ``threshold``. Cells whose best match is
the same article they already point at don't need a correction; cells
with no candidate above ``threshold`` are dropped (they fall through to
US-010 logging in the JS).

The output is a JSON dict keyed by ``"<cid>|<sid>|<dim_id>|<jid>"`` with
entries like::

    {
      "from_anchor": "27",       # original anchor (display)
      "from_label":  "EU AI Act, Article 27",
      "to_anchor":   "6",        # corrected anchor (looked up via REF_MAP)
      "to_label":    "EU AI Act, Article 6",
      "law":         "eu-ai-act",
      "kind":        "article",
      "score":       82.4
    }

The dict is injected into ``digital_lexicon_v30.html`` as a
``<script type="application/json" id="v30-autocorrect-data">`` island
that the inlined US-009 JS reads at click time.

Public API
----------
- compute_autocorrect_lookup(threshold: float = 70.0,
                              html_path: Path | None = None,
                              verbatim_path: Path | None = None,
                              laws_dir: Path | None = None) -> dict[str, dict]
- inject_autocorrect_lookup(lookup: dict[str, dict],
                             html_path: Path | None = None,
                             out_path: Path | None = None,
                             threshold: float = 70.0) -> Path
- build_v30_autocorrect(threshold: float = 70.0,
                         html_path: Path | None = None,
                         out_path: Path | None = None,
                         verbatim_path: Path | None = None,
                         laws_dir: Path | None = None) -> dict
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

ITER_DIR = Path(__file__).resolve().parent
if str(ITER_DIR) not in sys.path:
    sys.path.insert(0, str(ITER_DIR))

from load_lexicon_sources import load_verbatim  # noqa: E402
from parse_v29 import parse_v29  # noqa: E402
from verify_lexicon import (  # noqa: E402
    STATUS_NO_VERBATIM,
    VERBATIM_CELLS,
    _build_verbatim_indices,
    _classify_link,
    _resolve_verbatim_term,
)

DEFAULT_HTML = ITER_DIR / "digital_lexicon_v30.html"
DEFAULT_LAWS_DIR = ITER_DIR / "laws"
REPO_OUTPUTS = ITER_DIR.parent / "outputs"
DEFAULT_UNRESOLVED_MD = REPO_OUTPUTS / "v30_unresolved_articles.md"
# rapidfuzz token_set_ratio threshold. The PRD lists 70 as the starting
# point. On the v30 + verbatim Excel snapshot the legitimate
# corrections cluster at 68.9–100.0 — a default of 65 picks them all
# up while still rejecting noise (next-best false-positive scores
# tail off below 60). The CLI ``--threshold`` flag lets stricter or
# looser regimes opt in.
DEFAULT_THRESHOLD = 65.0

DATA_SCRIPT_ID = "v30-autocorrect-data"
DATA_SCRIPT_OPEN = f'<script type="application/json" id="{DATA_SCRIPT_ID}">'
DATA_SCRIPT_CLOSE = "</script>"

# Map law_id → human-readable citation prefix used for the "from / to"
# labels rendered in the inline note.  These match the prefixes the
# analyst writes in cell.reference (e.g. ``EU AI Act, Article 50``).
LAW_LABEL_PREFIX: dict[str, tuple[str, str]] = {
    "eu-ai-act":                      ("EU AI Act", "Article"),
    "eu-gpai-cop-copyright":          ("Code of Practice for GPAI - Copyright", "Chapter"),
    "eu-gpai-cop-safety":             ("Code of Practice for GPAI - Safety and Security", "Chapter"),
    "eu-gpai-cop-transparency":       ("Code of Practice for GPAI - Transparency", "Chapter"),
    "eu-guidelines-gpai-scope":       ("Guidelines on GPAI scope", "Section"),
    "eu-guidelines-ai-definition":    ("Guidelines on AI definition", "Section"),
    "eu-guidelines-prohibited":       ("Guidelines on Prohibited AI", "Section"),
    "ca-sb53":                        ("CA SB 53", "§"),
    "ca-sb942":                       ("CA SB 942", "§"),
    "ca-ab2013":                      ("CA AB 2013", "§"),
    "co-sb24205":                     ("CO SB 24-205", "§"),
    "ny-s8828":                       ("NY S8828", "§"),
    "ny-a6453":                       ("NY A6453", "§"),
    "tx-hb149":                       ("TX HB 149", "§"),
    "ut-sb226":                       ("UT SB 226", "§"),
}


# --------------------------------------------------------------------------- #
# Law blob loading                                                            #
# --------------------------------------------------------------------------- #

def _load_law_blobs(laws_dir: Path) -> dict[str, dict]:
    """Return ``{law_id: blob}`` for every laws/*.json with an ``id``."""
    out: dict[str, dict] = {}
    for path in sorted(laws_dir.glob("*.json")):
        try:
            blob = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(blob, dict) and isinstance(blob.get("id"), str):
            out[blob["id"]] = blob
    return out


def _blob_articles(blob: dict) -> list[dict]:
    """Return the list of article-like entries to search across.

    Articles + sections + annexes are all considered. Each entry is
    ``{"id": str, "title": str, "text": str, "kind": str}``.
    """
    out: list[dict] = []
    for art in blob.get("articles", []) or []:
        if not isinstance(art, dict):
            continue
        aid = art.get("id")
        if aid is None:
            continue
        out.append({
            "id": str(aid),
            "title": str(art.get("title") or ""),
            "text": str(art.get("text") or ""),
            "kind": "article",
        })
    for sec in blob.get("sections", []) or []:
        if not isinstance(sec, dict):
            continue
        sid = sec.get("id")
        if sid is None:
            continue
        out.append({
            "id": str(sid),
            "title": str(sec.get("title") or ""),
            "text": str(sec.get("text") or ""),
            "kind": "section",
        })
    annexes = blob.get("annexes")
    if isinstance(annexes, list):
        for an in annexes:
            if not isinstance(an, dict):
                continue
            aid = an.get("id")
            if aid is None:
                continue
            out.append({
                "id": str(aid),
                "title": str(an.get("title") or ""),
                "text": str(an.get("text") or ""),
                "kind": "annex",
            })
    return out


# --------------------------------------------------------------------------- #
# Similarity search                                                           #
# --------------------------------------------------------------------------- #

_WS_RE = re.compile(r"\s+")


def _normalize_for_match(text: str | None) -> str:
    if not text:
        return ""
    return _WS_RE.sub(" ", str(text).replace("\xa0", " ")).strip().lower()


def best_article_match(
    query: str, articles: list[dict], threshold: float,
) -> tuple[dict | None, float]:
    """Return ``(best_article, score)`` or ``(None, best_below)``.

    ``score`` is rapidfuzz's ``token_set_ratio`` of the normalized query
    against ``title + " " + text``. We use ``token_set_ratio`` because
    the analysis paraphrase reorders and trims tokens but keeps
    legal-vocabulary in common with the article body.
    """
    if not query or not articles:
        return None, 0.0
    q = _normalize_for_match(query)
    if not q:
        return None, 0.0
    best: dict | None = None
    best_score = 0.0
    for art in articles:
        body = _normalize_for_match(
            (art.get("title") or "") + " " + (art.get("text") or "")
        )
        if not body:
            continue
        score = float(fuzz.token_set_ratio(q, body))
        if score > best_score:
            best_score = score
            best = art
    if best is None or best_score < threshold:
        return None, best_score
    return best, best_score


def top_n_article_matches(
    query: str, articles: list[dict], n: int = 3,
) -> list[tuple[dict, float]]:
    """Return up to ``n`` ``(article, score)`` pairs sorted by score desc.

    Same scoring rule as :func:`best_article_match` (token_set_ratio of
    normalized query vs ``title + " " + text``), but returns the ranked
    top-``n`` rather than only the best. Used by US-010 to surface the
    closest-but-not-confident-enough candidates for manual review.
    """
    if not query or not articles or n <= 0:
        return []
    q = _normalize_for_match(query)
    if not q:
        return []
    scored: list[tuple[dict, float]] = []
    for art in articles:
        body = _normalize_for_match(
            (art.get("title") or "") + " " + (art.get("text") or "")
        )
        if not body:
            continue
        score = float(fuzz.token_set_ratio(q, body))
        scored.append((art, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:n]


# --------------------------------------------------------------------------- #
# Lookup composition                                                          #
# --------------------------------------------------------------------------- #

def _make_label(law_id: str, kind: str, anchor: str) -> str:
    """Render a human-readable citation label like ``"EU AI Act, Article 50"``."""
    prefix = LAW_LABEL_PREFIX.get(law_id)
    if prefix is None:
        return f"{law_id} {kind} {anchor}"
    base, marker = prefix
    if kind == "article":
        return f"{base}, Article {anchor}"
    if kind == "annex":
        return f"{base}, Annex {anchor}"
    if kind == "section":
        # Bills use § marker; place a space when the marker is "§".
        sep = "" if marker == "§" else " "
        return f"{base} {marker}{sep}{anchor}".rstrip()
    if kind == "recital":
        return f"{base}, Recital ({anchor})"
    if kind == "chapter":
        return f"{base}, {marker} {anchor}"
    return f"{base} {anchor}"


def _key_for_cell(cid: str, sid: str, dim_id: str, jid: str) -> str:
    """Stable JSON-friendly composite key for a cell."""
    return f"{cid}|{sid}|{dim_id}|{jid}"


def _cells_with_no_verbatim(
    html_df, by_block, by_term,
) -> list[dict]:
    """Yield one record per HTML cell whose linked articles ALL have no
    verbatim row in the cross-checked Excel.

    Each record carries:
      * concept_id, sub_concept_id, dim_id, jid
      * analysis_text (used as the similarity query)
      * reference (raw cell.reference string for the inline note)
      * law_id (the cell's single linked law)
      * cited_anchors (set of every anchor the cell already cites in
        that law — used to suppress phantom corrections where the best
        similarity match is *already* one of the cell's citations)
    """
    # Group rows per cell.
    from collections import defaultdict
    cell_atoms: dict[tuple, list[tuple[str, str]]] = defaultdict(list)
    cell_meta: dict[tuple, dict] = {}
    for r in html_df.itertuples(index=False):
        cid = getattr(r, "concept_id", None)
        sid = getattr(r, "sub_concept_id", None)
        dim_id = getattr(r, "dim_id", None)
        jid = getattr(r, "jurisdiction", None)
        if cid is None or sid is None or dim_id is None or jid is None:
            continue
        key = (cid, sid, dim_id, jid)
        analysis = getattr(r, "analysis_text", None)
        reference = getattr(r, "reference", None)
        law_id = getattr(r, "law_id", None)
        article_id = getattr(r, "article_id", None)
        term = getattr(r, "term", None)
        dim_label = getattr(r, "dim_label", None)
        if law_id and article_id:
            cell_atoms[key].append((law_id, str(article_id)))
        if key not in cell_meta:
            cell_meta[key] = {
                "analysis_text": analysis,
                "reference": reference or "",
                "term": term or "",
                "dim_label": dim_label or "",
            }

    out: list[dict] = []
    for key, atoms in cell_atoms.items():
        cid, sid, dim_id, jid = key
        # Single-law constraint: similarity is meaningful only when we
        # know which law to search across. Multi-law cells already have
        # at least one citation per law, so the "wrong article in same
        # law" framing doesn't apply cleanly.
        laws = {law for (law, _) in atoms}
        if len(laws) != 1:
            continue
        law_id = next(iter(laws))
        meta = cell_meta.get(key) or {}
        analysis_text = meta.get("analysis_text") or ""
        if not analysis_text:
            continue
        # Cell-level aggregated link status: only auto-correct when
        # *every* parsed citation in the cell is no_verbatim. If even one
        # link resolved to a real verbatim row, the analyst already
        # validated the cell against that law — we leave it alone.
        verbatim_term = _resolve_verbatim_term(cid, sid, jid, by_block)
        statuses = [
            _classify_link(verbatim_term, law_id, art, by_term)
            for (_, art) in atoms
        ]
        if not all(s == STATUS_NO_VERBATIM for s in statuses):
            continue
        cited_anchors = {a for (_, a) in atoms}
        out.append({
            "cid": cid,
            "sid": sid,
            "dim_id": dim_id,
            "jid": jid,
            "analysis_text": analysis_text,
            "reference": meta.get("reference", ""),
            "term": meta.get("term", ""),
            "dim_label": meta.get("dim_label", ""),
            "law_id": law_id,
            "cited_anchors": cited_anchors,
        })
    return out


def compute_autocorrect_lookup(
    threshold: float = DEFAULT_THRESHOLD,
    html_path: Path | str | None = None,
    verbatim_path: Path | str | None = None,
    laws_dir: Path | str | None = None,
) -> dict[str, dict]:
    """Compute the (cell-key → correction) lookup.

    Cells with no candidate above ``threshold`` are dropped. Cells whose
    best match is already cited by the cell are also dropped — there is
    nothing to "correct".

    ``html_path`` defaults to the v30 artefact rather than falling
    through to ``parse_v29``'s v29 default; the auto-correct lookup is
    computed against the same file the JS island will be injected into.
    """
    threshold = float(threshold)
    html_df = parse_v29(html_path or DEFAULT_HTML)
    verbatim_df = load_verbatim(verbatim_path)
    by_block, by_term = _build_verbatim_indices(verbatim_df)
    blobs = _load_law_blobs(Path(laws_dir) if laws_dir else DEFAULT_LAWS_DIR)

    lookup: dict[str, dict] = {}
    for rec in _cells_with_no_verbatim(html_df, by_block, by_term):
        blob = blobs.get(rec["law_id"])
        if blob is None:
            continue
        articles = _blob_articles(blob)
        if not articles:
            continue
        best, score = best_article_match(
            rec["analysis_text"], articles, threshold,
        )
        if best is None:
            continue
        # Skip phantom corrections: when the best similarity match is
        # *already* one of the anchors the cell cites (multi-atom
        # references frequently include the right article alongside
        # weaker ones), there is nothing for the user to gain from a
        # rewrite.
        cited = rec.get("cited_anchors") or set()
        if str(best["id"]) in cited:
            continue
        kind = best["kind"]
        # Use the cell's full original reference as the "from" label so
        # the inline note shows what the user used to see, not just the
        # first parsed atom (multi-atom cells often cite a chain of
        # adjacent sections).
        from_label = (
            rec.get("reference")
            or _make_label(rec["law_id"], kind, sorted(cited)[0])
        )
        to_label = _make_label(rec["law_id"], kind, str(best["id"]))
        key = _key_for_cell(rec["cid"], rec["sid"], rec["dim_id"], rec["jid"])
        lookup[key] = {
            "from_anchor": sorted(cited)[0] if cited else "",
            "from_label": from_label,
            "to_anchor": str(best["id"]),
            "to_label": to_label,
            "law": rec["law_id"],
            "kind": kind,
            "score": round(score, 1),
        }
    return lookup


# --------------------------------------------------------------------------- #
# US-010: unresolved-article markdown log                                     #
# --------------------------------------------------------------------------- #

def compute_unresolved_articles(
    threshold: float = DEFAULT_THRESHOLD,
    html_path: Path | str | None = None,
    verbatim_path: Path | str | None = None,
    laws_dir: Path | str | None = None,
    top_n: int = 3,
) -> list[dict]:
    """Return one entry per cell whose verbatim is missing AND auto-correct
    could not pick a candidate above ``threshold``.

    Each entry carries the cell key, the displayed term, the linked law,
    the originally selected article string (the cell's raw ``reference``)
    and the top-``top_n`` candidate articles with their similarity scores.
    Cells whose top match is already one of the cell's citations are
    excluded — those are "phantom" successes where the analyst already
    points at the right article.
    """
    threshold = float(threshold)
    html_df = parse_v29(html_path or DEFAULT_HTML)
    verbatim_df = load_verbatim(verbatim_path)
    by_block, by_term = _build_verbatim_indices(verbatim_df)
    blobs = _load_law_blobs(Path(laws_dir) if laws_dir else DEFAULT_LAWS_DIR)

    out: list[dict] = []
    for rec in _cells_with_no_verbatim(html_df, by_block, by_term):
        blob = blobs.get(rec["law_id"])
        if blob is None:
            continue
        articles = _blob_articles(blob)
        if not articles:
            continue
        top = top_n_article_matches(rec["analysis_text"], articles, n=top_n)
        if not top:
            continue
        best_art, best_score = top[0]
        cited = rec.get("cited_anchors") or set()
        if best_score >= threshold:
            # Either a real correction (handled by lookup) or phantom
            # (best already cited — analyst pointed at the right article).
            # In either case, NOT unresolved.
            continue
        candidates = [
            {
                "to_label": _make_label(rec["law_id"], art["kind"], str(art["id"])),
                "to_anchor": str(art["id"]),
                "kind": art["kind"],
                "score": round(score, 1),
            }
            for (art, score) in top
        ]
        out.append({
            "cid": rec["cid"],
            "sid": rec["sid"],
            "dim_id": rec["dim_id"],
            "jid": rec["jid"],
            "term": rec.get("term") or "",
            "dim_label": rec.get("dim_label") or "",
            "law_id": rec["law_id"],
            "from_label": rec.get("reference") or "",
            "cited_anchors": sorted(cited),
            "best_score": round(best_score, 1),
            "candidates": candidates,
        })
    return out


def _format_unresolved_md(
    unresolved: list[dict],
    threshold: float,
    generated_at: datetime,
) -> str:
    """Render the markdown body for ``v30_unresolved_articles.md``."""
    stamp = generated_at.strftime("%Y-%m-%d %H:%M:%S UTC")
    lines: list[str] = []
    lines.append("# v30 Unresolved Articles")
    lines.append("")
    lines.append(f"_Generated {stamp} (threshold={threshold:g})._")
    lines.append("")

    if not unresolved:
        lines.append("No unresolved articles.")
        lines.append("")
        return "\n".join(lines)

    lines.append(
        f"{len(unresolved)} cell(s) where verbatim is missing and "
        f"auto-correct could not confidently pick an article (best "
        f"similarity below threshold {threshold:g})."
    )
    lines.append("")

    # Sort by best_score descending so the closest-but-not-quite candidates
    # are surfaced first for human review.
    ranked = sorted(unresolved, key=lambda r: -float(r.get("best_score", 0.0)))

    for i, rec in enumerate(ranked, 1):
        term = rec.get("term") or "(no term)"
        law_id = rec.get("law_id") or "(no law)"
        cell_path = (
            f"{rec.get('cid','?')}/{rec.get('sid','?')}/"
            f"{rec.get('dim_id','?')}/{rec.get('jid','?')}"
        )
        lines.append(f"## {i}. {term} — {law_id}")
        lines.append("")
        lines.append(f"- **Cell:** `{cell_path}`")
        if rec.get("dim_label"):
            lines.append(f"- **Dimension:** {rec['dim_label']}")
        lines.append(f"- **Term:** {term}")
        lines.append(f"- **Linked law:** `{law_id}`")
        from_label = rec.get("from_label") or "_(none)_"
        lines.append(f"- **Originally selected article:** {from_label}")
        lines.append("- **Top 3 candidate articles:**")
        cands = rec.get("candidates") or []
        if not cands:
            lines.append("    - _(none)_")
        else:
            for c in cands[:3]:
                lines.append(
                    f"    - {c['to_label']} — score "
                    f"{float(c['score']):.1f}"
                )
        lines.append("")

    return "\n".join(lines)


def write_unresolved_articles_md(
    unresolved: list[dict],
    out_path: Path | str | None = None,
    threshold: float = DEFAULT_THRESHOLD,
    generated_at: datetime | None = None,
) -> Path:
    """Write the unresolved-articles markdown log to ``out_path``.

    The file is overwritten on every call. When ``unresolved`` is empty the
    body is the literal string ``"No unresolved articles."`` under the
    timestamped header so the file is never empty.
    """
    dst = Path(out_path) if out_path else DEFAULT_UNRESOLVED_MD
    dst.parent.mkdir(parents=True, exist_ok=True)
    if generated_at is None:
        generated_at = datetime.now(timezone.utc)
    body = _format_unresolved_md(unresolved, threshold, generated_at)
    # Always end with a single trailing newline.
    if not body.endswith("\n"):
        body += "\n"
    dst.write_text(body, encoding="utf-8")
    return dst


# --------------------------------------------------------------------------- #
# HTML injection                                                              #
# --------------------------------------------------------------------------- #

_DATA_BLOCK_RE = re.compile(
    r'<script type="application/json" id="v30-autocorrect-data">'
    r'.*?</script>\n?',
    re.DOTALL,
)


def _serialise_lookup(
    lookup: dict[str, dict], threshold: float,
) -> str:
    """Return the JSON island body (script-breakout-safe)."""
    payload: dict[str, Any] = {
        "threshold": float(threshold),
        "lookup": lookup,
    }
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    # Defensive: prevent any literal </script> inside an analysis-derived
    # label from terminating the script element early.
    return text.replace("</", "<\\/")


def _strip_existing_block(html_text: str) -> str:
    """Remove any prior v30-autocorrect-data block (idempotent rebuilds)."""
    return _DATA_BLOCK_RE.sub("", html_text)


def _strip_existing_js_block(html_text: str) -> str:
    """Remove any prior US-009 JS block (idempotent rebuilds)."""
    pattern = re.compile(
        r"\n?<style data-block=\"us-009\">.*?</style>\n?"
        r"<script data-block=\"us-009\">.*?</script>\n?",
        re.DOTALL,
    )
    return pattern.sub("", html_text)


def inject_autocorrect_lookup(
    lookup: dict[str, dict],
    html_path: Path | str | None = None,
    out_path: Path | str | None = None,
    threshold: float = DEFAULT_THRESHOLD,
) -> Path:
    """Splice the lookup JSON + the US-009 JS block into the v30 HTML.

    The injection is *append-only* and idempotent: prior blocks with the
    same data-block / id markers are stripped before re-inserting, so
    re-running the build doesn't duplicate the script.
    """
    src = Path(html_path) if html_path else DEFAULT_HTML
    dst = Path(out_path) if out_path else src
    html_text = src.read_text(encoding="utf-8")
    html_text = _strip_existing_block(html_text)
    html_text = _strip_existing_js_block(html_text)

    body = _serialise_lookup(lookup, threshold)
    data_block = (
        f'\n{DATA_SCRIPT_OPEN}{body}{DATA_SCRIPT_CLOSE}\n'
    )
    js_block = _build_js_block()

    needle = "</body>"
    idx = html_text.rfind(needle)
    if idx < 0:
        # Append at end if no </body> tag is present.
        html_text = html_text.rstrip() + data_block + js_block + "\n"
    else:
        html_text = (
            html_text[:idx]
            + data_block
            + js_block
            + "\n"
            + html_text[idx:]
        )

    dst.write_text(html_text, encoding="utf-8")
    return dst


# --------------------------------------------------------------------------- #
# Embedded JS block                                                           #
# --------------------------------------------------------------------------- #

_JS_BLOCK = r"""
<style data-block="us-009">
/* US-009 — auto-correct note shown when the analysis cell had no
   verbatim row and a similarity search picked a better article. */
.v30-autocorrect-note{
  display:flex;
  align-items:flex-start;
  gap:10px;
  margin:0 0 14px;
  padding:10px 14px;
  background:#FFF8E1;
  border:1px solid #E6C36A;
  border-left:4px solid #B8943E;
  border-radius:6px;
  font-family:var(--sans);
  font-size:13px;
  color:#4F3D14;
  line-height:1.55;
  position:relative;
  cursor:help;
}
.v30-autocorrect-note .v30-ac-icon{
  flex:0 0 auto;
  width:18px;
  height:18px;
  display:flex;
  align-items:center;
  justify-content:center;
  border-radius:50%;
  background:#B8943E;
  color:#fff;
  font-weight:700;
  font-size:11px;
  margin-top:1px;
}
.v30-autocorrect-note .v30-ac-text{flex:1 1 auto}
.v30-autocorrect-note strong{font-weight:600;color:#4F3D14}
.v30-autocorrect-note code{
  font-family:var(--mono);
  background:rgba(184,148,62,.18);
  padding:1px 5px;
  border-radius:3px;
  font-size:12px;
}
.v30-autocorrect-popup{
  position:absolute;
  top:calc(100% + 6px);
  left:0;
  background:var(--ink);
  color:#fff;
  font-family:var(--sans);
  font-size:12px;
  line-height:1.55;
  padding:10px 14px;
  border-radius:6px;
  max-width:360px;
  z-index:600;
  box-shadow:0 4px 16px rgba(0,0,0,.18);
  display:none;
  pointer-events:none;
}
.v30-autocorrect-popup::before{
  content:"";
  position:absolute;
  top:-6px;
  left:18px;
  border:6px solid transparent;
  border-top:0;
  border-bottom-color:var(--ink);
}
.v30-autocorrect-note:hover .v30-autocorrect-popup,
.v30-autocorrect-note:focus-within .v30-autocorrect-popup,
.v30-autocorrect-note.v30-ac-open .v30-autocorrect-popup{display:block}
</style>
<script data-block="us-009">
/* US-009 — when the clicked analysis cell has no verbatim row, override
   the rendered law article with the best similarity match (pre-computed
   at build time and inlined as JSON). Show a styled custom popup note
   reading 'Article auto-corrected from X to Y'.

   The hook wraps window.updateDrawerContent (after the v29 + v30 (US-008)
   chains have already wrapped it). It mutates dim.cells[juris].reference
   *before* delegating, so the v29 article-render pipeline naturally
   resolves the corrected anchor. The original reference is restored
   afterwards so the override is per-click rather than persistent.
*/
(function(){
  var DATA_ID = "v30-autocorrect-data";
  var NOTE_CLASS = "v30-autocorrect-note";
  var POPUP_CLASS = "v30-autocorrect-popup";
  var FLAG = "__v30_autocorrect_patched";
  var data = null;

  function _loadData(){
    if (data !== null) return data;
    var el = document.getElementById(DATA_ID);
    if (!el){ data = {threshold: 70, lookup: {}}; return data; }
    try {
      data = JSON.parse(el.textContent || "{}");
    } catch (e){
      console.warn("v30 autocorrect: malformed JSON island", e);
      data = {threshold: 70, lookup: {}};
    }
    if (!data.lookup) data.lookup = {};
    return data;
  }

  function _key(cid, sid, dimId, jid){
    return cid + "|" + sid + "|" + dimId + "|" + jid;
  }

  function _lookup(cid, sid, dimId, jid){
    var lk = _loadData().lookup;
    return lk[_key(cid, sid, dimId, jid)] || null;
  }

  function _renderNote(correction){
    // Build the note element — uses styled popup, NOT title attribute.
    var note = document.createElement("div");
    note.className = NOTE_CLASS;
    note.setAttribute("role", "note");
    note.setAttribute("tabindex", "0");
    note.setAttribute(
      "aria-label",
      "Article auto-corrected from " + correction.from_label +
      " to " + correction.to_label
    );

    var icon = document.createElement("span");
    icon.className = "v30-ac-icon";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = "i";
    note.appendChild(icon);

    var msg = document.createElement("span");
    msg.className = "v30-ac-text";
    msg.appendChild(document.createTextNode("Article auto-corrected from "));
    var fromCode = document.createElement("code");
    fromCode.textContent = correction.from_label;
    msg.appendChild(fromCode);
    msg.appendChild(document.createTextNode(" to "));
    var toCode = document.createElement("code");
    toCode.textContent = correction.to_label;
    msg.appendChild(toCode);
    msg.appendChild(document.createTextNode("."));
    note.appendChild(msg);

    var popup = document.createElement("div");
    popup.className = POPUP_CLASS;
    popup.setAttribute("role", "tooltip");
    var pct = (correction.score != null)
      ? (Math.round(correction.score * 10) / 10).toFixed(1) + "%"
      : "n/a";
    popup.textContent =
      "No verbatim entry exists for this term in the linked law. " +
      "A similarity search picked the best-matching article in the " +
      "same law (token-overlap score " + pct + "). The originally " +
      "linked article was \"" + correction.from_label + "\".";
    note.appendChild(popup);

    // Toggle on focus (keyboard) so screen-reader users can dismiss.
    note.addEventListener("click", function(){
      note.classList.toggle("v30-ac-open");
    });
    note.addEventListener("blur", function(){
      note.classList.remove("v30-ac-open");
    });

    return note;
  }

  function _stripExistingNote(container){
    if (!container) return;
    var prev = container.querySelectorAll("." + NOTE_CLASS);
    Array.prototype.forEach.call(prev, function(n){
      if (n.parentNode) n.parentNode.removeChild(n);
    });
  }

  function _registerSyntheticRefs(lookup){
    // The v29 article-render pipeline resolves cell.reference via
    // window.REF_MAP. To swap in our corrected article we register a
    // synthetic REF_MAP entry keyed on the corrected to_label, pointing
    // at the law / anchor we want rendered. Pre-existing keys are
    // never overwritten — if the to_label already resolves to the same
    // (law, anchor), keep the original; if it points elsewhere we
    // generate a uniquified key so we don't break any other cell.
    if (!window.REF_MAP) window.REF_MAP = {};
    Object.keys(lookup).forEach(function(k){
      var c = lookup[k];
      var entry = {
        law: c.law,
        kind: c.kind,
        anchor: c.to_anchor,
        paragraphs: [],
        subparagraphs: []
      };
      var existing = window.REF_MAP[c.to_label];
      if (!existing){
        window.REF_MAP[c.to_label] = entry;
        c.__refkey = c.to_label;
        return;
      }
      if (existing.law === c.law && String(existing.anchor) === String(c.to_anchor)){
        c.__refkey = c.to_label;
        return;
      }
      // Collision — use a uniquified synthetic key. The user-visible
      // citation header will fall back to the synthetic key in that
      // edge case, but the underlying article still renders correctly.
      var syn = c.to_label + " (auto-corrected)";
      window.REF_MAP[syn] = entry;
      c.__refkey = syn;
    });
  }

  function _install(){
    if (typeof window.updateDrawerContent !== "function") return;
    if (window[FLAG]) return;
    // Wait for the v29 article-render and US-008 highlight wrappers to
    // install first — we need to be the OUTERMOST wrapper so that
    // ``cell.reference`` mutations propagate down through both before
    // v29 reads them in ``_renderDrawerArticles``. If either flag is
    // missing we'll get retried via the setTimeout cascade below.
    if (!window.__v29_udc_patched || !window.__v30_highlight_patched){
      return;
    }
    window[FLAG] = true;
    _registerSyntheticRefs(_loadData().lookup || {});
    var orig = window.updateDrawerContent;
    window.updateDrawerContent = function(dim, juris, sc, c){
      var correction = null;
      var savedRef = null;
      var didOverride = false;
      try {
        if (dim && sc && c && juris && dim.cells && dim.cells[juris]){
          var cell = dim.cells[juris];
          // The lookup is the source of truth: it was pre-computed at
          // build time from the verbatim Excel ground truth, so any
          // entry here means "this cell has no verbatim row in the
          // cross-checked data and a higher-similarity article exists
          // in the same law." We override regardless of whether
          // ``cell.verbatim`` happens to carry leftover text from the
          // HTML JSON — the build step already encoded that decision.
          correction = _lookup(c.id, sc.id, dim.id, juris);
          if (correction){
            savedRef = cell.reference;
            cell.reference = correction.__refkey || correction.to_label;
            didOverride = true;
          }
        }
      } catch(e){
        console.warn("v30 autocorrect (pre-render):", e);
      }
      try {
        orig.apply(this, arguments);
      } finally {
        if (didOverride){
          // Restore the original reference so the in-memory CONCEPTS
          // stay clean for downstream features that read raw
          // cell.reference (e.g. citation copy).
          try {
            if (dim && dim.cells && dim.cells[juris]){
              dim.cells[juris].reference = savedRef;
            }
          } catch(e){
            console.warn("v30 autocorrect (restore):", e);
          }
        }
      }
      try {
        var container = document.getElementById("drawer-verbatim");
        if (container){
          // Always strip any leftover note from a prior click so we
          // never leave a stale "auto-corrected" message behind on
          // cells that don't have a correction.
          _stripExistingNote(container);
          if (correction){
            var note = _renderNote(correction);
            // Insert the note ABOVE the article body so it's the
            // first thing the reader sees. Synchronous insertion is
            // important so QA assertions immediately after the click
            // see the note in the DOM.
            container.insertBefore(note, container.firstChild);
          }
        }
      } catch (e){
        console.error("v30 autocorrect (post-render):", e);
      }
    };
  }

  if (document.readyState === "loading"){
    document.addEventListener("DOMContentLoaded", _install);
  } else {
    _install();
  }
  // Defensive re-tries to cover ordering races with v29 / US-008 wrappers.
  setTimeout(_install, 0);
  setTimeout(_install, 100);
  setTimeout(_install, 250);

  // Expose for tests / debugging.
  window.__v30_autocorrect = {
    DATA_ID: DATA_ID,
    NOTE_CLASS: NOTE_CLASS,
    POPUP_CLASS: POPUP_CLASS,
    loadData: _loadData,
    lookup: _lookup,
    renderNote: _renderNote
  };
})();
</script>
"""


def _build_js_block() -> str:
    return _JS_BLOCK.strip("\n")


# --------------------------------------------------------------------------- #
# Orchestration + CLI                                                         #
# --------------------------------------------------------------------------- #

def build_v30_autocorrect(
    threshold: float = DEFAULT_THRESHOLD,
    html_path: Path | str | None = None,
    out_path: Path | str | None = None,
    verbatim_path: Path | str | None = None,
    laws_dir: Path | str | None = None,
    unresolved_md_path: Path | str | None = None,
) -> dict:
    """Compute + inject + log in one call.

    Returns ``{"out_path", "lookup", "unresolved", "unresolved_md_path"}``.
    The unresolved-articles markdown log (US-010) is written to
    ``unresolved_md_path`` (defaults to ``<repo>/outputs/v30_unresolved_articles.md``).
    Pass ``unresolved_md_path=False`` to skip the log.
    """
    lookup = compute_autocorrect_lookup(
        threshold=threshold,
        html_path=html_path,
        verbatim_path=verbatim_path,
        laws_dir=laws_dir,
    )
    out = inject_autocorrect_lookup(
        lookup, html_path=html_path, out_path=out_path, threshold=threshold,
    )
    unresolved = compute_unresolved_articles(
        threshold=threshold,
        html_path=html_path,
        verbatim_path=verbatim_path,
        laws_dir=laws_dir,
    )
    md_path: Path | None
    if unresolved_md_path is False:
        md_path = None
    else:
        md_path = write_unresolved_articles_md(
            unresolved,
            out_path=unresolved_md_path,
            threshold=threshold,
        )
    return {
        "out_path": out,
        "lookup": lookup,
        "unresolved": unresolved,
        "unresolved_md_path": md_path,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--html", default=str(DEFAULT_HTML))
    p.add_argument("--out", default=None,
                   help="Output path; defaults to in-place rewrite of --html.")
    p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    p.add_argument("--laws-dir", default=str(DEFAULT_LAWS_DIR))
    p.add_argument("--verbatim", default=None)
    p.add_argument(
        "--unresolved-md",
        default=str(DEFAULT_UNRESOLVED_MD),
        help="Output path for the US-010 unresolved-articles markdown log.",
    )
    args = p.parse_args(argv)

    result = build_v30_autocorrect(
        threshold=args.threshold,
        html_path=args.html,
        out_path=args.out,
        verbatim_path=args.verbatim,
        laws_dir=args.laws_dir,
        unresolved_md_path=args.unresolved_md,
    )
    print(
        f"US-009 auto-correct: {len(result['lookup'])} cells corrected "
        f"(threshold={args.threshold}) → {result['out_path']}"
    )
    n_unresolved = len(result["unresolved"])
    md_target = result["unresolved_md_path"]
    if n_unresolved == 0:
        print(
            f"US-010 unresolved log: 0 unresolved articles "
            f"→ {md_target}"
        )
    else:
        print(
            f"US-010 unresolved log: {n_unresolved} cell(s) need manual "
            f"review → {md_target}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
