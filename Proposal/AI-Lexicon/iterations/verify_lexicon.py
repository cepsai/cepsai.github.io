"""verify_lexicon.py — Per-analysis verification of v29 HTML against the Excel.

US-003: outer-join every analysis cell extracted by ``parse_v29`` against the
canonical analysis text loaded by ``load_analyses`` and emit a ``status`` per
cell:

* ``match``            both sides have the same analysis text (after
                       whitespace normalisation).
* ``mismatch``         both sides have analysis text, but they differ.
* ``missing_in_html``  Excel has the analysis; HTML cell is empty / missing.
* ``missing_in_excel`` HTML has the analysis; Excel has nothing for that cell.

US-004: for every ``(law_id, article_id)`` link parsed from the HTML cell, look
that pair up in the verbatim Excel and emit a ``link_status`` per cell:

* ``verbatim_found``   the verbatim Excel has the term in the linked law and
                       the linked article.
* ``wrong_article``    the verbatim Excel has the term in the linked law but a
                       different article.
* ``wrong_law``        the term has no entry in the linked law but exists in
                       another law.
* ``no_verbatim``      the term has no entries in the verbatim Excel at all.

Per-link details (one entry per linked article) are kept in the
``linked_articles`` / ``link_statuses`` columns; ``link_status`` carries the
worst-case aggregate so reviewers can sort by severity.

Public API
----------
- verify_lexicon(html_path: Path | None = None,
                 analysis_path: Path | None = None,
                 verbatim_path: Path | None = None) -> pandas.DataFrame
- write_verification_csv(df: pandas.DataFrame, out_path: Path) -> None

Comparison key
--------------
The natural unit is one ``(concept_id, sub_concept_id, dim_label, jid)`` cell.
The HTML carries those identifiers directly. The Excel doesn't, so we map
``(sheet, term, jurisdiction_header)`` → ``(concept_id, sub_concept_id, jid)``
using a static table — this is the *one* place the verifier knows about the
cross-source identity of cells, isolated so a future refactor can move it
into the loader.

For verbatim, the ``Provider_Developer`` and ``Deployer_Supplier`` sheets
collapse all sub-concepts under a single jurisdiction-keyed term (e.g. EU's
"Provider" covers limited-risk / high-risk / GPAI / GPAISR providers). The
``VERBATIM_CELLS`` map below therefore points each HTML ``(cid, sid, jid)``
cell at the verbatim block whose term it should be looked up under.
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ITER_DIR = Path(__file__).resolve().parent
if str(ITER_DIR) not in sys.path:
    sys.path.insert(0, str(ITER_DIR))

from load_lexicon_sources import load_analyses, load_verbatim  # noqa: E402
from parse_v29 import parse_v29  # noqa: E402

REPO = ITER_DIR.parent
OUTPUTS = REPO / "outputs"

VERIFY_COLUMNS = [
    "status",
    "concept_id", "sub_concept_id", "jid", "dim_label",
    "term_html", "term_excel",
    "html_analysis", "excel_analysis",
    "sheet", "addr",
    "linked_articles", "link_statuses", "link_status",
]

STATUS_MATCH = "match"
STATUS_MISMATCH = "mismatch"
STATUS_MISSING_IN_HTML = "missing_in_html"
STATUS_MISSING_IN_EXCEL = "missing_in_excel"

ALL_STATUSES = (
    STATUS_MATCH,
    STATUS_MISMATCH,
    STATUS_MISSING_IN_HTML,
    STATUS_MISSING_IN_EXCEL,
)

# US-004 link statuses
STATUS_VERBATIM_FOUND = "verbatim_found"
STATUS_WRONG_ARTICLE = "wrong_article"
STATUS_WRONG_LAW = "wrong_law"
STATUS_NO_VERBATIM = "no_verbatim"

ALL_LINK_STATUSES = (
    STATUS_VERBATIM_FOUND,
    STATUS_WRONG_ARTICLE,
    STATUS_WRONG_LAW,
    STATUS_NO_VERBATIM,
)

# Severity ranking used to aggregate per-cell ``link_status`` from a list of
# per-link statuses — the worst result wins.
_LINK_STATUS_SEVERITY = {
    STATUS_VERBATIM_FOUND: 0,
    STATUS_NO_VERBATIM: 1,
    STATUS_WRONG_ARTICLE: 2,
    STATUS_WRONG_LAW: 3,
}


# --------------------------------------------------------------------------- #
# Cell-key mapping: Excel (sheet, term, juris) → HTML (cid, sid, jid)         #
# --------------------------------------------------------------------------- #
#
# For SINGLE_SUB sheets the sub-concept id is sheet-scoped, so any term in a
# given (sheet, juris_header) maps to the same HTML cell.
#
# For MULTI_SUB sheets each section has its own (term per juris column), so
# disambiguation requires the per-row term value. Section terms are taken
# from the actual loader output (not synthesised) so a heterogeneous spelling
# in the Excel ("Utah (SB 226)" vs "Utah (SB226)") flows through cleanly.

SINGLE_SUB_SHEETS: dict[str, tuple[str, str, dict[str, str]]] = {
    " High-risk AI system_ANALYSIS": (
        "model-system", "high-risk-ai-system",
        {
            "EU (AIA)": "eu",
            "Colorado (SB 24-205)": "co",
            "Utah (SB 226)": "ut",
            "Utah (SB226)": "ut",
        },
    ),
    "GPAI_Frontier_Foundation_Analys": (
        "model-system", "general-purpose-ai-model",
        {
            "EU (AIA)": "eu",
            "California (SB 53)": "ca",
            "New York (S8828)": "ny",
        },
    ),
    "GPAI system_Generative AI_ANALY": (
        "model-system", "general-purpose-ai-system",
        {
            "EU (AIA)": "eu",
            "California (SB 942, AB 2013)": "ca",
            "Utah (SB 226)": "ut",
            "Utah (SB226)": "ut",
        },
    ),
    "Risk_ANALYSIS": (
        "risk", "systemic-risk",
        {
            "EU (AIA)": "eu",
            "California (SB 53)": "ca",
            "New York (S8828)": "ny",
        },
    ),
    "Modification_ANALYSIS": (
        "modification", "substantial-modification",
        {
            "EU (AIA)": "eu",
            "California (SB 53)":
                "ca-0-substantially-modified-version-of-a-frontier-model-no-standalone-defined-term",
            "California (AB 2013)": "ca-1-substantial-modification",
            # NY is present in the Excel but not in the v29 HTML — the
            # corresponding row will surface as ``missing_in_html``.
            "New York (S8828)": "ny",
            "Colorado (SB 24-205)": "co",
        },
    ),
    "Incident_ANALYSIS": (
        "incident", "serious-incident",
        {
            "EU (AIA)": "eu",
            "California (SB 53)": "ca",
            "New York (S8828)": "ny",
        },
    ),
}

# Multi-sub sheets keyed by (sheet, term, juris_header) → (cid, sid, jid).
# The term is jurisdiction-specific (the value of the section's Term row at
# the column of that jurisdiction).
MULTI_SUB_CELLS: dict[tuple[str, str, str], tuple[str, str, str]] = {
    # ---- Provider_Developer_Analysis ----
    # Section: Provider of limited-risk AI systems
    (
        "Provider_Developer_Analysis",
        "Provider of limited-risk AI systems", "EU (AIA)",
    ): ("provider-developer", "provider", "eu"),
    (
        "Provider_Developer_Analysis", "Developer", "Colorado (SB 24-205)",
    ): ("provider-developer", "provider", "co"),
    (
        "Provider_Developer_Analysis", "Developer", "Texas (HB 149)",
    ): ("provider-developer", "provider", "tx"),

    # Section: Provider of high-risk AI systems
    (
        "Provider_Developer_Analysis",
        "Provider of high-risk AI systems", "EU (AIA)",
    ): ("provider-developer", "provider-of-high-risk-ai-systems", "eu"),
    (
        "Provider_Developer_Analysis",
        "Developer of high-risk AI systems", "Colorado (SB 24-205)",
    ): ("provider-developer", "provider-of-high-risk-ai-systems", "co"),

    # Section: Provider of GPAI
    (
        "Provider_Developer_Analysis",
        "Provider of GPAI models", "EU (AIA)",
    ): (
        "provider-developer",
        "provider-of-general-purpose-ai-models", "eu",
    ),
    (
        "Provider_Developer_Analysis",
        "Covered provider", "California (SB 942)",
    ): (
        "provider-developer",
        "provider-of-general-purpose-ai-models", "ca-0-covered-provider",
    ),
    (
        "Provider_Developer_Analysis", "Developer", "California (AB 2013)",
    ): (
        "provider-developer",
        "provider-of-general-purpose-ai-models", "ca-1-developer",
    ),

    # Section: Provider of GPAI models with systemic risk
    (
        "Provider_Developer_Analysis",
        "Provider of GPAI models with systemic risk", "EU (AIA)",
    ): (
        "provider-developer",
        "provider-of-general-purpose-ai-models-with-systemic-risk", "eu",
    ),
    (
        "Provider_Developer_Analysis",
        "Frontier developer", "California (SB 53)",
    ): (
        "provider-developer",
        "provider-of-general-purpose-ai-models-with-systemic-risk",
        "ca-0-frontier-developer",
    ),
    (
        "Provider_Developer_Analysis",
        "Large frontier developer", "California (SB 53)",
    ): (
        "provider-developer",
        "provider-of-general-purpose-ai-models-with-systemic-risk",
        "ca-1-large-frontier-developer",
    ),
    (
        "Provider_Developer_Analysis",
        "Frontier developer", "New York (S8828)",
    ): (
        "provider-developer",
        "provider-of-general-purpose-ai-models-with-systemic-risk",
        "ny-0-frontier-developer",
    ),
    (
        "Provider_Developer_Analysis",
        "Large frontier developer", "New York (S8828)",
    ): (
        "provider-developer",
        "provider-of-general-purpose-ai-models-with-systemic-risk",
        "ny-1-large-frontier-developer",
    ),
    (
        "Provider_Developer_Analysis",
        "Large developer", "New York (A6453B)",
    ): (
        "provider-developer",
        "provider-of-general-purpose-ai-models-with-systemic-risk",
        "ny-2-large-developer",
    ),

    # ---- Deployer_Supplier_Analysis ----
    # Section: Deployer of limited-risk AI systems
    (
        "Deployer_Supplier_Analysis",
        "Deployer of limited-risk AI systems", "EU (AIA)",
    ): ("deployer-supplier", "deployer", "eu"),
    (
        "Deployer_Supplier_Analysis", "Deployer", "Colorado (SB 24-205)",
    ): ("deployer-supplier", "deployer", "co"),
    (
        "Deployer_Supplier_Analysis", "Deployer", "Texas (HB 149)",
    ): ("deployer-supplier", "deployer", "tx"),

    # Section: Deployer / supplier of high-risk
    (
        "Deployer_Supplier_Analysis",
        "Deployer of high-risk AI systems", "EU (AIA)",
    ): ("deployer-supplier", "deployer-of-high-risk-ai-systems", "eu"),
    (
        "Deployer_Supplier_Analysis",
        "Deployer of high-risk AI systems", "Colorado (SB 24-205)",
    ): ("deployer-supplier", "deployer-of-high-risk-ai-systems", "co"),
    (
        "Deployer_Supplier_Analysis",
        "Supplier of high-risk generative AI systems", "Utah (SB 226)",
    ): ("deployer-supplier", "deployer-of-high-risk-ai-systems", "ut"),

    # Section: Deployers of GPAI systems
    (
        "Deployer_Supplier_Analysis",
        "Deployer of GPAI systems", "EU (AIA)",
    ): ("deployer-supplier", "deployer-of-general-purpose-ai-systems", "eu"),
    (
        "Deployer_Supplier_Analysis",
        "Supplier of generative AI systems", "Utah (SB226)",
    ): ("deployer-supplier", "deployer-of-general-purpose-ai-systems", "ut"),
}


# --------------------------------------------------------------------------- #
# Verbatim cell-key mapping: HTML (cid, sid, jid) → verbatim (sheet, juris)   #
# --------------------------------------------------------------------------- #
#
# The verbatim Excel collapses sub-concepts that the HTML keeps separate:
# every "Provider of …" sub-concept (limited-risk, high-risk, GPAI, GPAISR)
# routes through the same EU "Provider" verbatim block. The mapping below
# encodes that collapse so a single (cid, sid, jid) cell knows where to look
# up its verbatim entries.
#
# Cells that have no verbatim block at all (e.g. California / New York rows
# in Provider_Developer — those columns simply don't exist in the verbatim
# Excel) are left out of the map. Their ``link_status`` will default to
# ``no_verbatim`` regardless of the linked article, since the verbatim Excel
# carries nothing for the term.

VERBATIM_CELLS: dict[tuple[str, str, str], tuple[str, str]] = {
    # ----- High-risk AI system -----
    ("model-system", "high-risk-ai-system", "eu"):
        (" High-risk AI system", "EU"),
    ("model-system", "high-risk-ai-system", "co"):
        (" High-risk AI system", "U.S. - Colorado"),
    ("model-system", "high-risk-ai-system", "ut"):
        (" High-risk AI system", "U.S. - Utah"),

    # ----- GPAI model / Foundation model -----
    ("model-system", "general-purpose-ai-model", "eu"):
        ("GPAI_Frontier_Foundation model", "EU"),
    ("model-system", "general-purpose-ai-model", "ca"):
        ("GPAI_Frontier_Foundation model", "U.S. - California"),
    ("model-system", "general-purpose-ai-model", "ny"):
        ("GPAI_Frontier_Foundation model", "U.S. - New York"),

    # ----- GPAI system / Generative AI -----
    ("model-system", "general-purpose-ai-system", "eu"):
        ("GPAI system_Generative AI", "EU"),
    ("model-system", "general-purpose-ai-system", "ca"):
        ("GPAI system_Generative AI", "U.S. - California"),
    ("model-system", "general-purpose-ai-system", "ut"):
        ("GPAI system_Generative AI", "U.S. - Utah"),

    # ----- Risk -----
    ("risk", "systemic-risk", "eu"): ("Risk", "EU"),
    ("risk", "systemic-risk", "ca"): ("Risk", "U.S. - California"),
    ("risk", "systemic-risk", "ny"): ("Risk", "U.S. - New York"),

    # ----- Substantial modification -----
    # The verbatim sheet has only one California column, so both ca-0 and
    # ca-1 jids in the HTML route to the same block.
    ("modification", "substantial-modification", "eu"):
        ("Substantial modification", "EU"),
    ("modification", "substantial-modification", "co"):
        ("Substantial modification", "Colorado"),
    (
        "modification", "substantial-modification",
        "ca-0-substantially-modified-version-of-a-frontier-model-no-standalone-defined-term",
    ): ("Substantial modification", "California"),
    (
        "modification", "substantial-modification",
        "ca-1-substantial-modification",
    ): ("Substantial modification", "California"),
    # NB: NY has no verbatim column on Substantial modification.

    # ----- Serious incident -----
    ("incident", "serious-incident", "eu"): ("Incident", "EU"),
    ("incident", "serious-incident", "ny"):
        ("Incident", "U.S. - New York"),
    # NB: California has no verbatim column on Incident.

    # ----- Provider_Developer (one block per juris, shared across sub-concepts) -----
    # provider (limited-risk)
    ("provider-developer", "provider", "eu"): ("Provider_Developer", "EU"),
    ("provider-developer", "provider", "co"):
        ("Provider_Developer", "Colorado"),
    ("provider-developer", "provider", "tx"):
        ("Provider_Developer", "Texas"),
    # provider-of-high-risk-ai-systems
    ("provider-developer", "provider-of-high-risk-ai-systems", "eu"):
        ("Provider_Developer", "EU"),
    ("provider-developer", "provider-of-high-risk-ai-systems", "co"):
        ("Provider_Developer", "Colorado"),
    # provider-of-general-purpose-ai-models — only EU has a verbatim column
    ("provider-developer", "provider-of-general-purpose-ai-models", "eu"):
        ("Provider_Developer", "EU"),
    # provider-of-general-purpose-ai-models-with-systemic-risk — only EU
    (
        "provider-developer",
        "provider-of-general-purpose-ai-models-with-systemic-risk", "eu",
    ): ("Provider_Developer", "EU"),

    # ----- Deployer_Supplier -----
    ("deployer-supplier", "deployer", "eu"): ("Deployer_Supplier", "EU"),
    ("deployer-supplier", "deployer", "co"):
        ("Deployer_Supplier", "Colorado"),
    ("deployer-supplier", "deployer", "tx"):
        ("Deployer_Supplier", "Texas"),
    ("deployer-supplier", "deployer-of-high-risk-ai-systems", "eu"):
        ("Deployer_Supplier", "EU"),
    ("deployer-supplier", "deployer-of-high-risk-ai-systems", "co"):
        ("Deployer_Supplier", "Colorado"),
    # NB: Utah Supplier of high-risk generative AI systems has no verbatim
    # column on Deployer_Supplier (the sheet covers EU/Colorado/Texas only).
    ("deployer-supplier", "deployer-of-general-purpose-ai-systems", "eu"):
        ("Deployer_Supplier", "EU"),
    # NB: Utah Supplier of generative AI systems has no verbatim column.
}


def _resolve_excel_cell(
    sheet: str | None, term: str | None, juris_header: str | None,
) -> tuple[str, str, str] | None:
    """Map an Excel row's identity to ``(concept_id, sub_concept_id, jid)``.

    Returns ``None`` for rows we cannot place in the HTML schema (e.g.
    footnote-only rows whose ``term`` is a paragraph of interpretative
    notes). Such rows are intentionally dropped from the comparison.
    """
    if not sheet:
        return None
    if (sheet, term, juris_header) in MULTI_SUB_CELLS:
        return MULTI_SUB_CELLS[(sheet, term, juris_header)]
    if sheet in SINGLE_SUB_SHEETS:
        cid, sid, juris_to_jid = SINGLE_SUB_SHEETS[sheet]
        if juris_header in juris_to_jid:
            return cid, sid, juris_to_jid[juris_header]
    return None


# --------------------------------------------------------------------------- #
# Comparison helpers                                                          #
# --------------------------------------------------------------------------- #

_WS_RE = re.compile(r"\s+")


def normalize_whitespace(text: str | None) -> str:
    """Collapse runs of whitespace and trim the result.

    ``None`` and empty/blank strings both normalise to ``""`` so they compare
    equal — that's what we want when treating "no analysis" as a single
    canonical state.
    """
    if text is None:
        return ""
    return _WS_RE.sub(" ", str(text).replace("\xa0", " ")).strip()


def _classify(html_text: str | None, excel_text: str | None) -> str:
    n_html = normalize_whitespace(html_text)
    n_excel = normalize_whitespace(excel_text)
    if n_html and n_excel:
        return STATUS_MATCH if n_html == n_excel else STATUS_MISMATCH
    if n_html and not n_excel:
        return STATUS_MISSING_IN_EXCEL
    if not n_html and n_excel:
        return STATUS_MISSING_IN_HTML
    # Both empty — these never reach the report (we only emit rows where at
    # least one side has content). Returning match is the natural fallback.
    return STATUS_MATCH


# --------------------------------------------------------------------------- #
# Link verification helpers (US-004)                                          #
# --------------------------------------------------------------------------- #

def _build_verbatim_indices(
    verbatim_df: pd.DataFrame,
) -> tuple[dict[tuple[str, str], str], dict[str, set[tuple[str, str | None]]]]:
    """Build the two indices the link classifier needs.

    * ``by_block``: ``(sheet, jurisdiction_header)`` → verbatim term.
    * ``by_term``: verbatim term → set of ``(law_id, article_id)`` pairs that
      appear under that term anywhere in the verbatim Excel.
    """
    by_block: dict[tuple[str, str], str] = {}
    by_term: dict[str, set[tuple[str, str | None]]] = {}
    for r in verbatim_df.itertuples(index=False):
        term = getattr(r, "term", None)
        sheet = getattr(r, "sheet", None)
        juris_header = getattr(r, "jurisdiction_header", None)
        law_id = getattr(r, "law_id", None)
        article_id = getattr(r, "article_id", None)
        if not term:
            continue
        if sheet and juris_header:
            by_block.setdefault((sheet, juris_header), term)
        if law_id:
            by_term.setdefault(term, set()).add((law_id, article_id))
    return by_block, by_term


def _resolve_verbatim_term(
    cid: str | None, sid: str | None, jid: str | None,
    by_block: dict[tuple[str, str], str],
) -> str | None:
    """Return the verbatim term used to look up cell ``(cid, sid, jid)``.

    Returns ``None`` when the cell has no corresponding verbatim block —
    those cells can never produce a ``verbatim_found`` and default to
    ``no_verbatim``.
    """
    if cid is None or sid is None or jid is None:
        return None
    block = VERBATIM_CELLS.get((cid, sid, jid))
    if block is None:
        return None
    return by_block.get(block)


def _classify_link(
    verbatim_term: str | None,
    law_id: str | None,
    article_id: str | None,
    by_term: dict[str, set[tuple[str, str | None]]],
) -> str:
    """Classify a single ``(law_id, article_id)`` link against verbatim.

    The four statuses are documented at the top of this module. ``None``
    inputs propagate to ``no_verbatim`` so the caller never has to special-
    case missing data.
    """
    if not verbatim_term or not law_id:
        return STATUS_NO_VERBATIM
    entries = by_term.get(verbatim_term)
    if not entries:
        return STATUS_NO_VERBATIM
    if (law_id, article_id) in entries:
        return STATUS_VERBATIM_FOUND
    same_law = any(law == law_id for law, _ in entries)
    if same_law:
        return STATUS_WRONG_ARTICLE
    return STATUS_WRONG_LAW


def _aggregate_link_status(statuses: list[str]) -> str | None:
    """Reduce a list of per-link statuses to one cell-level status.

    Worst severity wins so reviewers can spot the most-broken cells first.
    Returns ``None`` when no link statuses are provided.
    """
    if not statuses:
        return None
    return max(statuses, key=lambda s: _LINK_STATUS_SEVERITY.get(s, -1))


def _html_links_per_cell(
    html_df: pd.DataFrame,
) -> dict[tuple[str | None, str | None, str | None, str | None], list[tuple[str, str | None]]]:
    """Group parse_v29 rows into per-cell ordered lists of unique links.

    Cells without any parseable reference produce an empty list. Order is
    insertion order (parse_v29's ``_explode_reference`` preserves the order
    of citations as they appear in the HTML).
    """
    links: dict[
        tuple[str | None, str | None, str | None, str | None],
        list[tuple[str, str | None]],
    ] = {}
    for r in html_df.itertuples(index=False):
        cid = getattr(r, "concept_id", None)
        sid = getattr(r, "sub_concept_id", None)
        jid = getattr(r, "jurisdiction", None)
        dim_label = getattr(r, "dim_label", None)
        law_id = getattr(r, "law_id", None)
        article_id = getattr(r, "article_id", None)
        key = (cid, sid, jid, dim_label)
        bucket = links.setdefault(key, [])
        if law_id is None:
            continue
        pair = (law_id, article_id)
        if pair not in bucket:
            bucket.append(pair)
    return links


def _format_links(pairs: list[tuple[str, str | None]]) -> str | None:
    """Render link list as ``law_id:article_id;law_id:article_id`` string.

    Returns ``None`` when there are no links so the CSV stays empty rather
    than carrying an empty string for cells without references.
    """
    if not pairs:
        return None
    parts = []
    for law, art in pairs:
        if art is None:
            parts.append(f"{law}:")
        else:
            parts.append(f"{law}:{art}")
    return ";".join(parts)


def _format_statuses(statuses: list[str]) -> str | None:
    if not statuses:
        return None
    return ";".join(statuses)


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #

def _excel_cells(analyses_df: pd.DataFrame) -> pd.DataFrame:
    """Reduce the loader's exploded rows to one row per analysis cell.

    The loader emits one row per (term, dim_label, law_id, article_id);
    several rows may share the same (sheet, term, dim_label, juris_header)
    when a cell cites multiple inline references. For verification we want
    one row per cell — pick the first ``analysis_text`` seen and resolve
    the HTML identity columns at the same time.
    """
    rows = []
    seen: set[tuple[str, str, str, str]] = set()
    for r in analyses_df.itertuples(index=False):
        sheet = getattr(r, "sheet", None)
        term = getattr(r, "term", None)
        dim_label = getattr(r, "dim_label", None)
        juris_header = getattr(r, "jurisdiction_header", None)
        analysis_text = getattr(r, "analysis_text", None)
        addr = getattr(r, "addr", None)
        key = (sheet, term, dim_label, juris_header)
        if key in seen:
            continue
        seen.add(key)
        resolved = _resolve_excel_cell(sheet, term, juris_header)
        if resolved is None:
            continue
        cid, sid, jid = resolved
        rows.append({
            "concept_id": cid,
            "sub_concept_id": sid,
            "jid": jid,
            "dim_label": dim_label,
            "term_excel": term,
            "excel_analysis": analysis_text,
            "sheet": sheet,
            "addr": addr,
        })
    return pd.DataFrame(rows)


def _html_cells(html_df: pd.DataFrame) -> pd.DataFrame:
    """Reduce parse_v29's exploded rows to one row per analysis cell."""
    cols = [
        "concept_id", "sub_concept_id", "jurisdiction",
        "dim_label", "term", "analysis_text",
    ]
    sub = (
        html_df[cols]
        .drop_duplicates(
            subset=[
                "concept_id", "sub_concept_id", "jurisdiction", "dim_label",
            ],
            keep="first",
        )
        .rename(columns={
            "jurisdiction": "jid",
            "term": "term_html",
            "analysis_text": "html_analysis",
        })
    )
    return sub.reset_index(drop=True)


def verify_lexicon(
    html_path: Path | str | None = None,
    analysis_path: Path | str | None = None,
    verbatim_path: Path | str | None = None,
) -> pd.DataFrame:
    """Compare every HTML analysis cell to its Excel counterpart.

    The returned frame has one row per ``(concept_id, sub_concept_id,
    dim_label, jid)`` cell that appears in *either* source, with a
    ``status`` column drawn from :data:`ALL_STATUSES`. Mismatched cells
    keep both ``html_analysis`` and ``excel_analysis`` for side-by-side
    review.

    Each cell row also carries link-verification columns from US-004:
    ``linked_articles`` (the per-cell list of ``law_id:article_id`` pairs
    parsed from the HTML), ``link_statuses`` (one status per link, drawn
    from :data:`ALL_LINK_STATUSES`) and ``link_status`` (worst severity).
    Cells with no parseable links leave all three columns empty.
    """
    html_df = parse_v29(html_path)
    analyses_df = load_analyses(analysis_path)
    verbatim_df = load_verbatim(verbatim_path)

    excel_cells = _excel_cells(analyses_df)
    html_cells = _html_cells(html_df)

    join_keys = ["concept_id", "sub_concept_id", "jid", "dim_label"]
    merged = pd.merge(
        excel_cells, html_cells, on=join_keys, how="outer",
        indicator=False,
    )

    by_block, by_term = _build_verbatim_indices(verbatim_df)
    html_links = _html_links_per_cell(html_df)

    rows = []
    for r in merged.itertuples(index=False):
        html_text = getattr(r, "html_analysis", None)
        excel_text = getattr(r, "excel_analysis", None)
        # pandas merges leave missing values as NaN — turn those into None.
        if isinstance(html_text, float) and pd.isna(html_text):
            html_text = None
        if isinstance(excel_text, float) and pd.isna(excel_text):
            excel_text = None
        # Skip cells that are empty in both sources (nothing to verify).
        if (
            normalize_whitespace(html_text) == ""
            and normalize_whitespace(excel_text) == ""
        ):
            continue
        cid = getattr(r, "concept_id", None)
        sid = getattr(r, "sub_concept_id", None)
        jid = getattr(r, "jid", None)
        dim_label = getattr(r, "dim_label", None)

        verbatim_term = _resolve_verbatim_term(cid, sid, jid, by_block)
        pairs = html_links.get((cid, sid, jid, dim_label), [])
        link_statuses = [
            _classify_link(verbatim_term, law, art, by_term)
            for (law, art) in pairs
        ]

        rows.append({
            "status": _classify(html_text, excel_text),
            "concept_id": cid,
            "sub_concept_id": sid,
            "jid": jid,
            "dim_label": dim_label,
            "term_html": getattr(r, "term_html", None),
            "term_excel": getattr(r, "term_excel", None),
            "html_analysis": html_text,
            "excel_analysis": excel_text,
            "sheet": getattr(r, "sheet", None),
            "addr": getattr(r, "addr", None),
            "linked_articles": _format_links(pairs),
            "link_statuses": _format_statuses(link_statuses),
            "link_status": _aggregate_link_status(link_statuses),
        })
    df = pd.DataFrame(rows, columns=VERIFY_COLUMNS)
    return df.astype(object).where(df.notna(), None)


# --------------------------------------------------------------------------- #
# CSV writer                                                                  #
# --------------------------------------------------------------------------- #

def write_verification_csv(df: pd.DataFrame, out_path: Path | str) -> Path:
    """Write the verification frame as CSV. Ensures parent dir exists.

    Long analysis bodies are written verbatim (csv.QUOTE_ALL) so newlines and
    commas inside the text don't break the row structure.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, quoting=1)  # 1 == csv.QUOTE_ALL
    return out_path


# --------------------------------------------------------------------------- #
# Markdown report (US-005)                                                    #
# --------------------------------------------------------------------------- #

def _truncate(text: str | None, limit: int = 200) -> str:
    if text is None:
        return ""
    s = str(text).replace("\n", " \\n ").replace("|", "\\|")
    if len(s) > limit:
        return s[: limit - 1] + "…"
    return s


def _md_table(rows: list[list[str]], headers: list[str]) -> str:
    if not rows:
        return "_(none)_\n"
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("|" + "|".join("---" for _ in headers) + "|")
    for r in rows:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines) + "\n"


def _broken_link_rows(df: pd.DataFrame) -> list[dict]:
    """Yield one entry per broken link (status wrong_article / wrong_law)."""
    out = []
    for r in df.itertuples(index=False):
        statuses = getattr(r, "link_statuses", None)
        articles = getattr(r, "linked_articles", None)
        if not statuses or not articles:
            continue
        per_status = str(statuses).split(";")
        per_article = str(articles).split(";")
        if len(per_status) != len(per_article):
            continue
        for art, st in zip(per_article, per_status):
            if st in (STATUS_WRONG_ARTICLE, STATUS_WRONG_LAW):
                out.append({
                    "concept_id": getattr(r, "concept_id", None),
                    "sub_concept_id": getattr(r, "sub_concept_id", None),
                    "jid": getattr(r, "jid", None),
                    "dim_label": getattr(r, "dim_label", None),
                    "term_html": getattr(r, "term_html", None),
                    "link": art,
                    "link_status": st,
                })
    return out


def render_markdown_report(
    df: pd.DataFrame, generated_at: datetime | None = None,
) -> str:
    """Render the verification frame as a human-readable markdown report.

    Sections:
    1. Summary totals (status + link status).
    2. Top mismatches (analysis-text mismatch).
    3. Broken links (per-link wrong_article / wrong_law).
    4. Missing-in-HTML and missing-in-Excel cells.
    """
    generated_at = generated_at or datetime.now()
    counts = _summary_counts(df)
    link_counts = _link_summary_counts(df)
    total_cells = len(df)
    total_links = sum(link_counts.values())

    lines: list[str] = []
    lines.append("# Lexicon verification report")
    lines.append("")
    lines.append(f"_Generated: {generated_at:%Y-%m-%dT%H:%M:%S}_")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total analysis cells verified: **{total_cells}**")
    for status in ALL_STATUSES:
        lines.append(f"  - `{status}`: **{counts.get(status, 0)}**")
    lines.append(f"- Total linked articles classified: **{total_links}**")
    for status in ALL_LINK_STATUSES:
        lines.append(f"  - `{status}`: **{link_counts.get(status, 0)}**")
    lines.append("")

    # ------- Top mismatches -------
    mm = df[df["status"] == STATUS_MISMATCH]
    lines.append(f"## Top mismatches ({len(mm)})")
    lines.append("")
    headers = [
        "Concept", "Sub-concept", "Juris", "Dim",
        "HTML text", "Excel text",
    ]
    rows: list[list[str]] = []
    for r in mm.head(20).itertuples(index=False):
        rows.append([
            str(getattr(r, "concept_id", "") or ""),
            str(getattr(r, "sub_concept_id", "") or ""),
            str(getattr(r, "jid", "") or ""),
            str(getattr(r, "dim_label", "") or ""),
            _truncate(getattr(r, "html_analysis", None)),
            _truncate(getattr(r, "excel_analysis", None)),
        ])
    lines.append(_md_table(rows, headers))
    if len(mm) > 20:
        lines.append(f"_…and {len(mm) - 20} more in the CSV._")
        lines.append("")

    # ------- Broken links -------
    broken = _broken_link_rows(df)
    lines.append(f"## Broken links ({len(broken)})")
    lines.append("")
    headers = [
        "Concept", "Sub-concept", "Juris", "Dim", "Link", "Status",
    ]
    rows = []
    for b in broken[:50]:
        rows.append([
            str(b["concept_id"] or ""),
            str(b["sub_concept_id"] or ""),
            str(b["jid"] or ""),
            str(b["dim_label"] or ""),
            f"`{b['link']}`",
            f"`{b['link_status']}`",
        ])
    lines.append(_md_table(rows, headers))
    if len(broken) > 50:
        lines.append(f"_…and {len(broken) - 50} more in the CSV._")
        lines.append("")

    # ------- Missing in HTML -------
    mh = df[df["status"] == STATUS_MISSING_IN_HTML]
    lines.append(f"## Missing in HTML ({len(mh)})")
    lines.append("")
    headers = [
        "Concept", "Sub-concept", "Juris", "Dim", "Excel text",
    ]
    rows = []
    for r in mh.head(25).itertuples(index=False):
        rows.append([
            str(getattr(r, "concept_id", "") or ""),
            str(getattr(r, "sub_concept_id", "") or ""),
            str(getattr(r, "jid", "") or ""),
            str(getattr(r, "dim_label", "") or ""),
            _truncate(getattr(r, "excel_analysis", None)),
        ])
    lines.append(_md_table(rows, headers))
    if len(mh) > 25:
        lines.append(f"_…and {len(mh) - 25} more in the CSV._")
        lines.append("")

    # ------- Missing in Excel -------
    me = df[df["status"] == STATUS_MISSING_IN_EXCEL]
    lines.append(f"## Missing in Excel ({len(me)})")
    lines.append("")
    headers = [
        "Concept", "Sub-concept", "Juris", "Dim", "HTML text",
    ]
    rows = []
    for r in me.head(25).itertuples(index=False):
        rows.append([
            str(getattr(r, "concept_id", "") or ""),
            str(getattr(r, "sub_concept_id", "") or ""),
            str(getattr(r, "jid", "") or ""),
            str(getattr(r, "dim_label", "") or ""),
            _truncate(getattr(r, "html_analysis", None)),
        ])
    lines.append(_md_table(rows, headers))
    if len(me) > 25:
        lines.append(f"_…and {len(me) - 25} more in the CSV._")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_verification_md(
    df: pd.DataFrame,
    out_path: Path | str,
    generated_at: datetime | None = None,
) -> Path:
    """Write the markdown report. Ensures parent dir exists."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        render_markdown_report(df, generated_at), encoding="utf-8",
    )
    return out_path


# --------------------------------------------------------------------------- #
# Interactive HTML diff viewer (US-005)                                       #
# --------------------------------------------------------------------------- #

# Filter labels exposed in the UI; data attributes on rows match these keys.
FILTER_BUTTONS = [
    ("all", "All"),
    ("mismatch", "Mismatch"),
    ("missing", "Missing"),
    ("wrong_article", "Wrong Article"),
    ("wrong_law", "Wrong Law"),
]


def _row_filter_tags(row_status: str | None, link_status: str | None) -> list[str]:
    """Compute the data-filter tags that apply to this row.

    A row with status ``mismatch`` matches ``mismatch``; either ``missing_*``
    matches ``missing``; ``wrong_article`` / ``wrong_law`` link statuses each
    match their own filter. Every row matches ``all``.
    """
    tags = ["all"]
    if row_status == STATUS_MISMATCH:
        tags.append("mismatch")
    elif row_status in (STATUS_MISSING_IN_HTML, STATUS_MISSING_IN_EXCEL):
        tags.append("missing")
    if link_status == STATUS_WRONG_ARTICLE:
        tags.append("wrong_article")
    elif link_status == STATUS_WRONG_LAW:
        tags.append("wrong_law")
    return tags


def _row_payload(df: pd.DataFrame) -> list[dict]:
    """Reduce the verification frame to the dict shape consumed by the JS."""
    out = []
    for r in df.itertuples(index=False):
        status = getattr(r, "status", None)
        link_status = getattr(r, "link_status", None) or None
        tags = _row_filter_tags(status, link_status)
        out.append({
            "status": status,
            "concept_id": getattr(r, "concept_id", None),
            "sub_concept_id": getattr(r, "sub_concept_id", None),
            "jid": getattr(r, "jid", None),
            "dim_label": getattr(r, "dim_label", None),
            "term_html": getattr(r, "term_html", None),
            "term_excel": getattr(r, "term_excel", None),
            "html_analysis": getattr(r, "html_analysis", None),
            "excel_analysis": getattr(r, "excel_analysis", None),
            "linked_articles": getattr(r, "linked_articles", None),
            "link_statuses": getattr(r, "link_statuses", None),
            "link_status": link_status,
            "tags": tags,
        })
    return out


def render_html_report(
    df: pd.DataFrame, generated_at: datetime | None = None,
) -> str:
    """Render a self-contained interactive verification report.

    Each row carries a status badge and (where applicable) a link-status
    badge. Clicking a row expands it to show the HTML and Excel text side
    by side with a character-level diff. Filter buttons restrict the
    visible rows by status. Every interaction uses ``addEventListener``;
    no inline ``onclick`` handlers.
    """
    generated_at = generated_at or datetime.now()
    counts = _summary_counts(df)
    link_counts = _link_summary_counts(df)
    payload = _row_payload(df)

    summary_chips = "".join(
        f'<span class="chip chip-status chip-{s}">{s}: '
        f'<b>{counts.get(s, 0)}</b></span>'
        for s in ALL_STATUSES
    )
    link_chips = "".join(
        f'<span class="chip chip-link chip-{s}">{s}: '
        f'<b>{link_counts.get(s, 0)}</b></span>'
        for s in ALL_LINK_STATUSES
    )
    filter_buttons = "".join(
        f'<button type="button" class="filter-btn" '
        f'data-filter="{key}">{label}</button>'
        for key, label in FILTER_BUTTONS
    )

    # JSON-encode safely for embedding in <script>: escape closing tags so
    # the browser cannot break out of the script element on a string like
    # "</script>".
    payload_json = (
        json.dumps(payload, ensure_ascii=False)
        .replace("</", "<\\/")
    )

    css = _HTML_REPORT_CSS
    js = _HTML_REPORT_JS

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Lexicon verification report</title>
<style>{css}</style>
</head>
<body>
<header>
  <h1>Lexicon verification report</h1>
  <p class="meta">Generated {html_lib.escape(generated_at.strftime('%Y-%m-%dT%H:%M:%S'))} — {len(df)} cells, {sum(link_counts.values())} linked articles</p>
  <div class="chips">{summary_chips}</div>
  <div class="chips">{link_chips}</div>
  <nav class="filters">{filter_buttons}</nav>
  <p class="hint">Click a row to expand and view the HTML ↔ Excel character-level diff.</p>
</header>
<main>
  <table class="rows">
    <thead>
      <tr>
        <th>Status</th>
        <th>Concept</th>
        <th>Sub-concept</th>
        <th>Juris</th>
        <th>Dim</th>
        <th>Link</th>
      </tr>
    </thead>
    <tbody id="rows"></tbody>
  </table>
</main>
<script id="payload" type="application/json">{payload_json}</script>
<script>{js}</script>
</body>
</html>
"""


def write_verification_html(
    df: pd.DataFrame,
    out_path: Path | str,
    generated_at: datetime | None = None,
) -> Path:
    """Write the self-contained interactive HTML report."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        render_html_report(df, generated_at), encoding="utf-8",
    )
    return out_path


_HTML_REPORT_CSS = """
:root {
  --bg: #ffffff; --fg: #1a1a1a; --muted: #6b7280;
  --border: #e5e7eb; --row-hover: #f3f4f6;
  --match: #16a34a; --mismatch: #dc2626;
  --missing: #d97706; --info: #2563eb;
  --wrong-article: #dc2626; --wrong-law: #b91c1c;
  --verbatim-found: #16a34a; --no-verbatim: #6b7280;
  --add: #dcfce7; --add-fg: #166534;
  --del: #fee2e2; --del-fg: #991b1b;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: var(--fg); background: var(--bg); font-size: 14px; line-height: 1.45;
}
header {
  position: sticky; top: 0; background: var(--bg); border-bottom: 1px solid var(--border);
  padding: 16px 24px; z-index: 10;
}
header h1 { margin: 0 0 6px; font-size: 1.4rem; }
.meta { color: var(--muted); margin: 0 0 10px; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 6px 0; }
.chip {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 8px; border-radius: 999px;
  font-size: 12px; background: #f3f4f6; color: #374151;
  border: 1px solid var(--border);
}
.chip b { font-weight: 600; }
.chip-match { background: #dcfce7; color: #166534; border-color: #bbf7d0; }
.chip-mismatch { background: #fee2e2; color: #991b1b; border-color: #fecaca; }
.chip-missing_in_html, .chip-missing_in_excel {
  background: #fef3c7; color: #92400e; border-color: #fde68a;
}
.chip-verbatim_found { background: #dcfce7; color: #166534; border-color: #bbf7d0; }
.chip-no_verbatim { background: #f3f4f6; color: #4b5563; }
.chip-wrong_article, .chip-wrong_law {
  background: #fee2e2; color: #991b1b; border-color: #fecaca;
}
.filters { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0 4px; }
.filter-btn {
  padding: 6px 12px; border: 1px solid var(--border);
  background: #f9fafb; border-radius: 6px; cursor: pointer;
  font-size: 13px; color: var(--fg);
}
.filter-btn:hover { background: var(--row-hover); }
.filter-btn[aria-pressed="true"] {
  background: #1f2937; color: #f9fafb; border-color: #1f2937;
}
.hint { color: var(--muted); margin: 8px 0 0; font-size: 12px; }
main { padding: 0 24px 48px; }
table.rows {
  width: 100%; border-collapse: collapse; margin-top: 16px;
  font-size: 13px;
}
.rows thead th {
  position: sticky; top: 184px; background: var(--bg);
  text-align: left; padding: 8px; font-weight: 600;
  border-bottom: 2px solid var(--border);
}
.rows tbody tr.row { cursor: pointer; }
.rows tbody tr.row:hover td { background: var(--row-hover); }
.rows tbody tr.row td {
  padding: 6px 8px; border-bottom: 1px solid var(--border);
  vertical-align: top;
}
.rows tbody tr.detail td { padding: 0; }
.rows tbody tr.detail .detail-inner {
  padding: 14px 16px 18px; background: #fafafa;
  border-bottom: 1px solid var(--border);
}
.rows tbody tr.hidden { display: none; }
.badge {
  display: inline-block; padding: 1px 8px; border-radius: 4px;
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.04em;
}
.badge.b-match { background: #dcfce7; color: #166534; }
.badge.b-mismatch { background: #fee2e2; color: #991b1b; }
.badge.b-missing_in_html { background: #fef3c7; color: #92400e; }
.badge.b-missing_in_excel { background: #fde68a; color: #78350f; }
.badge.b-verbatim_found { background: #dcfce7; color: #166534; }
.badge.b-no_verbatim { background: #e5e7eb; color: #374151; }
.badge.b-wrong_article { background: #fee2e2; color: #991b1b; }
.badge.b-wrong_law { background: #fecaca; color: #7f1d1d; }
.diff {
  display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
}
.diff-pane h4 {
  margin: 0 0 6px; font-size: 12px; color: var(--muted);
  text-transform: uppercase; letter-spacing: 0.06em;
}
.diff-pane pre {
  margin: 0; padding: 10px 12px; border: 1px solid var(--border);
  background: #ffffff; border-radius: 6px;
  white-space: pre-wrap; word-break: break-word;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12.5px; line-height: 1.5;
  max-height: 360px; overflow: auto;
}
.diff-pane ins { background: var(--add); color: var(--add-fg); text-decoration: none; }
.diff-pane del { background: var(--del); color: var(--del-fg); text-decoration: none; }
.detail-meta {
  display: flex; flex-wrap: wrap; gap: 12px;
  margin-bottom: 10px; font-size: 12px; color: var(--muted);
}
.detail-meta span { display: inline-flex; gap: 4px; }
.detail-meta b { color: var(--fg); font-weight: 500; }
.empty {
  padding: 30px 12px; text-align: center; color: var(--muted);
}
@media (max-width: 720px) { .diff { grid-template-columns: 1fr; } }
"""

_HTML_REPORT_JS = r"""
(function() {
  const payloadEl = document.getElementById("payload");
  const data = JSON.parse(payloadEl.textContent || "[]");
  const tbody = document.getElementById("rows");

  // ------- Render table rows -------
  function fmtCell(v) {
    if (v === null || v === undefined || v === "") return "";
    return String(v);
  }
  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  data.forEach((row, idx) => {
    const tr = document.createElement("tr");
    tr.className = "row";
    tr.dataset.idx = idx;
    tr.dataset.tags = (row.tags || []).join(" ");
    const linkBadge = row.link_status
      ? `<span class="badge b-${row.link_status}">${escapeHtml(row.link_status)}</span>`
      : "";
    tr.innerHTML = `
      <td><span class="badge b-${row.status}">${escapeHtml(row.status || "")}</span></td>
      <td>${escapeHtml(fmtCell(row.concept_id))}</td>
      <td>${escapeHtml(fmtCell(row.sub_concept_id))}</td>
      <td>${escapeHtml(fmtCell(row.jid))}</td>
      <td>${escapeHtml(fmtCell(row.dim_label))}</td>
      <td>${linkBadge}</td>`;
    const det = document.createElement("tr");
    det.className = "detail hidden";
    det.dataset.idx = idx;
    det.innerHTML = `<td colspan="6"><div class="detail-inner"></div></td>`;
    tbody.appendChild(tr);
    tbody.appendChild(det);
  });

  // ------- Filter handling (event delegation) -------
  const filtersEl = document.querySelector(".filters");
  let activeFilter = "all";
  function applyFilter(name) {
    activeFilter = name;
    document.querySelectorAll(".filter-btn").forEach(b => {
      b.setAttribute("aria-pressed", b.dataset.filter === name ? "true" : "false");
    });
    let visible = 0;
    document.querySelectorAll("tr.row").forEach(tr => {
      const tags = (tr.dataset.tags || "").split(" ");
      const show = name === "all" || tags.includes(name);
      tr.classList.toggle("hidden", !show);
      if (!show) {
        const det = tr.nextElementSibling;
        if (det && det.classList.contains("detail")) {
          det.classList.add("hidden");
        }
      } else {
        visible++;
      }
    });
    let empty = document.getElementById("empty-msg");
    if (!visible) {
      if (!empty) {
        empty = document.createElement("tr");
        empty.id = "empty-msg";
        empty.innerHTML = '<td colspan="6" class="empty">No rows match this filter.</td>';
        tbody.appendChild(empty);
      }
    } else if (empty) {
      empty.remove();
    }
  }
  filtersEl.addEventListener("click", e => {
    const btn = e.target.closest(".filter-btn");
    if (!btn) return;
    applyFilter(btn.dataset.filter);
  });
  applyFilter("all");

  // ------- Char-level diff (LCS) -------
  function diffChars(a, b) {
    a = a || ""; b = b || "";
    const n = a.length, m = b.length;
    // Bound the DP to keep huge cells fast — fall back to plain blocks for
    // anything exceptional. 4000x4000 = 16M ops which is plenty for these
    // analyses.
    if (n * m > 4_000_000 || n + m > 8000) {
      return [
        { op: "del", text: a },
        { op: "ins", text: b },
      ];
    }
    // dp[i][j] = LCS length of a[..i] vs b[..j]
    const dp = new Int32Array((n + 1) * (m + 1));
    const W = m + 1;
    for (let i = 1; i <= n; i++) {
      for (let j = 1; j <= m; j++) {
        if (a[i - 1] === b[j - 1]) {
          dp[i * W + j] = dp[(i - 1) * W + (j - 1)] + 1;
        } else {
          const u = dp[(i - 1) * W + j];
          const l = dp[i * W + (j - 1)];
          dp[i * W + j] = u > l ? u : l;
        }
      }
    }
    // Walk back, batching consecutive ops.
    const out = [];
    let i = n, j = m;
    function push(op, ch) {
      const last = out[out.length - 1];
      if (last && last.op === op) last.text += ch;
      else out.push({ op, text: ch });
    }
    while (i > 0 && j > 0) {
      if (a[i - 1] === b[j - 1]) {
        push("eq", a[i - 1]); i--; j--;
      } else if (dp[(i - 1) * W + j] >= dp[i * W + (j - 1)]) {
        push("del", a[i - 1]); i--;
      } else {
        push("ins", b[j - 1]); j--;
      }
    }
    while (i > 0) { push("del", a[i - 1]); i--; }
    while (j > 0) { push("ins", b[j - 1]); j--; }
    out.reverse();
    return out;
  }

  function renderDiffSide(ops, side) {
    // side: "html" -> hide ins (only del+eq), "excel" -> hide del.
    let s = "";
    for (const o of ops) {
      const t = escapeHtml(o.text);
      if (o.op === "eq") s += t;
      else if (o.op === "del" && side === "html") s += `<del>${t}</del>`;
      else if (o.op === "ins" && side === "excel") s += `<ins>${t}</ins>`;
    }
    return s;
  }

  // ------- Row click expansion (event delegation) -------
  tbody.addEventListener("click", e => {
    const tr = e.target.closest("tr.row");
    if (!tr) return;
    const idx = +tr.dataset.idx;
    const det = tr.nextElementSibling;
    if (!det || !det.classList.contains("detail")) return;
    const isHidden = det.classList.contains("hidden");
    if (!isHidden) {
      det.classList.add("hidden");
      return;
    }
    if (!det.dataset.rendered) {
      const row = data[idx];
      const inner = det.querySelector(".detail-inner");
      const ops = diffChars(row.html_analysis || "", row.excel_analysis || "");
      const links = row.linked_articles
        ? `<span><b>Links:</b> ${escapeHtml(row.linked_articles)}</span>`
        : "";
      const linkStatuses = row.link_statuses
        ? `<span><b>Link statuses:</b> ${escapeHtml(row.link_statuses)}</span>`
        : "";
      const termHtml = row.term_html
        ? `<span><b>HTML term:</b> ${escapeHtml(row.term_html)}</span>` : "";
      const termExcel = row.term_excel
        ? `<span><b>Excel term:</b> ${escapeHtml(row.term_excel)}</span>` : "";
      inner.innerHTML = `
        <div class="detail-meta">${termHtml}${termExcel}${links}${linkStatuses}</div>
        <div class="diff">
          <div class="diff-pane">
            <h4>HTML</h4>
            <pre>${renderDiffSide(ops, "html")}</pre>
          </div>
          <div class="diff-pane">
            <h4>Excel</h4>
            <pre>${renderDiffSide(ops, "excel")}</pre>
          </div>
        </div>`;
      det.dataset.rendered = "1";
    }
    det.classList.remove("hidden");
  });
})();
"""


def _summary_counts(df: pd.DataFrame) -> dict[str, int]:
    counts = {s: 0 for s in ALL_STATUSES}
    for s in df["status"]:
        counts[s] = counts.get(s, 0) + 1
    return counts


def _link_summary_counts(df: pd.DataFrame) -> dict[str, int]:
    """Count per-link statuses across every cell.

    Cells contribute one count per link they have, so a cell with three
    linked articles contributes three to the totals. Cells with no links
    are skipped entirely.
    """
    counts = {s: 0 for s in ALL_LINK_STATUSES}
    for raw in df["link_statuses"]:
        if not raw:
            continue
        for s in str(raw).split(";"):
            if s in counts:
                counts[s] += 1
            else:
                counts[s] = counts.get(s, 0) + 1
    return counts


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #

def _default_out_paths(now: datetime | None = None) -> tuple[Path, Path, Path]:
    """Return (csv, md, html) default output paths sharing one timestamp."""
    now = now or datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    base = OUTPUTS / f"lexicon_verification_{stamp}"
    return (
        base.with_suffix(".csv"),
        base.with_suffix(".md"),
        base.with_suffix(".html"),
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--html", default=None, help="path to digital_lexicon_v29.html")
    p.add_argument(
        "--analysis", default=None,
        help="path to the cross-checked analysis Excel",
    )
    p.add_argument(
        "--verbatim", default=None,
        help="path to the verbatim Excel",
    )
    p.add_argument(
        "--out", default=None,
        help="path to write the per-analysis CSV "
             "(default outputs/lexicon_verification_<timestamp>.csv); "
             ".md and .html siblings are written alongside the CSV",
    )
    p.add_argument(
        "--md-out", default=None,
        help="explicit path for the markdown report (overrides --out sibling)",
    )
    p.add_argument(
        "--html-out", default=None,
        help="explicit path for the interactive HTML report",
    )
    args = p.parse_args(argv)

    df = verify_lexicon(args.html, args.analysis, args.verbatim)

    now = datetime.now()
    csv_default, md_default, html_default = _default_out_paths(now)
    if args.out:
        csv_path = Path(args.out)
        sibling_base = csv_path.with_suffix("")
        md_path = Path(args.md_out) if args.md_out else sibling_base.with_suffix(".md")
        html_path = (
            Path(args.html_out) if args.html_out
            else sibling_base.with_suffix(".html")
        )
    else:
        csv_path = csv_default
        md_path = Path(args.md_out) if args.md_out else md_default
        html_path = Path(args.html_out) if args.html_out else html_default

    write_verification_csv(df, csv_path)
    write_verification_md(df, md_path, generated_at=now)
    write_verification_html(df, html_path, generated_at=now)

    counts = _summary_counts(df)
    link_counts = _link_summary_counts(df)
    print(f"Verified {len(df)} analysis cells.")
    print(f"  CSV : {csv_path}")
    print(f"  MD  : {md_path}")
    print(f"  HTML: {html_path}")
    print("Status counts:")
    for status in ALL_STATUSES:
        print(f"  {status:18s} {counts.get(status, 0):>5d}")
    total_links = sum(link_counts.values())
    print(f"\nLink status counts ({total_links} linked articles):")
    for status in ALL_LINK_STATUSES:
        print(f"  {status:18s} {link_counts.get(status, 0):>5d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
