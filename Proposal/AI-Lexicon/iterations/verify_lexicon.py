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

def _default_out_path(now: datetime | None = None) -> Path:
    now = now or datetime.now()
    return OUTPUTS / f"lexicon_verification_{now:%Y%m%d_%H%M%S}.csv"


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
             "(default outputs/lexicon_verification_<timestamp>.csv)",
    )
    args = p.parse_args(argv)

    df = verify_lexicon(args.html, args.analysis, args.verbatim)
    out_path = Path(args.out) if args.out else _default_out_path()
    write_verification_csv(df, out_path)

    counts = _summary_counts(df)
    link_counts = _link_summary_counts(df)
    print(f"Verified {len(df)} analysis cells. CSV: {out_path}")
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
