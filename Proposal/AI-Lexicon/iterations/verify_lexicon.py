"""verify_lexicon.py — Per-analysis verification of v29 HTML against the Excel.

US-003: outer-join every analysis cell extracted by ``parse_v29`` against the
canonical analysis text loaded by ``load_analyses`` and emit a status per
cell:

* ``match``            both sides have the same analysis text (after
                       whitespace normalisation).
* ``mismatch``         both sides have analysis text, but they differ.
* ``missing_in_html``  Excel has the analysis; HTML cell is empty / missing.
* ``missing_in_excel`` HTML has the analysis; Excel has nothing for that cell.

Public API
----------
- verify_lexicon(html_path: Path | None = None,
                 analysis_path: Path | None = None) -> pandas.DataFrame
- write_verification_csv(df: pandas.DataFrame, out_path: Path) -> None

Comparison key
--------------
The natural unit is one ``(concept_id, sub_concept_id, dim_label, jid)`` cell.
The HTML carries those identifiers directly. The Excel doesn't, so we map
``(sheet, term, jurisdiction_header)`` → ``(concept_id, sub_concept_id, jid)``
using a static table — this is the *one* place the verifier knows about the
cross-source identity of cells, isolated so a future refactor can move it
into the loader.
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

from load_lexicon_sources import load_analyses  # noqa: E402
from parse_v29 import parse_v29  # noqa: E402

REPO = ITER_DIR.parent
OUTPUTS = REPO / "outputs"

VERIFY_COLUMNS = [
    "status",
    "concept_id", "sub_concept_id", "jid", "dim_label",
    "term_html", "term_excel",
    "html_analysis", "excel_analysis",
    "sheet", "addr",
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
) -> pd.DataFrame:
    """Compare every HTML analysis cell to its Excel counterpart.

    The returned frame has one row per ``(concept_id, sub_concept_id,
    dim_label, jid)`` cell that appears in *either* source, with a
    ``status`` column drawn from :data:`ALL_STATUSES`. Mismatched cells
    keep both ``html_analysis`` and ``excel_analysis`` for side-by-side
    review.
    """
    html_df = parse_v29(html_path)
    analyses_df = load_analyses(analysis_path)

    excel_cells = _excel_cells(analyses_df)
    html_cells = _html_cells(html_df)

    join_keys = ["concept_id", "sub_concept_id", "jid", "dim_label"]
    merged = pd.merge(
        excel_cells, html_cells, on=join_keys, how="outer",
        indicator=False,
    )

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
        rows.append({
            "status": _classify(html_text, excel_text),
            "concept_id": getattr(r, "concept_id", None),
            "sub_concept_id": getattr(r, "sub_concept_id", None),
            "jid": getattr(r, "jid", None),
            "dim_label": getattr(r, "dim_label", None),
            "term_html": getattr(r, "term_html", None),
            "term_excel": getattr(r, "term_excel", None),
            "html_analysis": html_text,
            "excel_analysis": excel_text,
            "sheet": getattr(r, "sheet", None),
            "addr": getattr(r, "addr", None),
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
        "--out", default=None,
        help="path to write the per-analysis CSV "
             "(default outputs/lexicon_verification_<timestamp>.csv)",
    )
    args = p.parse_args(argv)

    df = verify_lexicon(args.html, args.analysis)
    out_path = Path(args.out) if args.out else _default_out_path()
    write_verification_csv(df, out_path)

    counts = _summary_counts(df)
    print(f"Verified {len(df)} analysis cells. CSV: {out_path}")
    print("Status counts:")
    for status in ALL_STATUSES:
        print(f"  {status:18s} {counts.get(status, 0):>5d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
