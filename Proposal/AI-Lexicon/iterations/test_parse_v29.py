"""Tests for iterations/parse_v29.py (US-002)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from parse_v29 import (
    DEFAULT_HTML,
    PARSE_V29_COLUMNS,
    _explode_reference,
    _extract_concepts_json,
    parse_v29,
)


pytestmark = pytest.mark.skipif(
    not DEFAULT_HTML.exists(),
    reason=f"v29 HTML not found at {DEFAULT_HTML}",
)


# --------------------------------------------------------------------------- #
# Pure helpers                                                                #
# --------------------------------------------------------------------------- #

def test_explode_reference_handles_empty():
    assert _explode_reference("") == []
    assert _explode_reference(None) == []


def test_explode_reference_single_eu_article():
    out = _explode_reference("AIA Article 6(1), (2)")
    # Article 6 with two paragraphs collapses to a single (law, anchor) row.
    assert len(out) == 1
    assert out[0]["law_id"] == "eu-ai-act"
    assert out[0]["article_id"] == "6"


def test_explode_reference_multiple_atomic_via_semicolon():
    """Semicolon-joined atomic citations explode into separate rows."""
    out = _explode_reference(
        "AIA Article 6(1); EU AI Act, Annex III"
    )
    assert len(out) == 2
    laws = {r["law_id"] for r in out}
    assert laws == {"eu-ai-act"}
    anchors = {r["article_id"] for r in out}
    # Article 6 → "6"; Annex III → "III"
    assert anchors == {"6", "III"}


def test_explode_reference_state_section():
    out = _explode_reference("Colorado SB24-205, 6-1-1701. (9)")
    assert len(out) == 1
    assert out[0]["law_id"] == "co-sb24205"
    assert out[0]["article_id"] == "6-1-1701"


# --------------------------------------------------------------------------- #
# CONCEPTS extraction                                                         #
# --------------------------------------------------------------------------- #

def test_extract_concepts_uses_beautifulsoup_to_locate_script():
    """We rely on bs4 to find the right <script> — verify a tiny synthetic
    HTML round-trips through the extractor."""
    html = (
        "<html><head><title>x</title></head><body>"
        "<script>const SOMETHING_ELSE = 1;</script>"
        "<script>const CONCEPTS = "
        "[{\"id\": \"a\", \"sub_concepts\": []},"
        " {\"id\": \"b\", \"sub_concepts\": []}];"
        "\nconst foo = 'bar';</script>"
        "</body></html>"
    )
    out = _extract_concepts_json(html)
    assert isinstance(out, list)
    assert [c["id"] for c in out] == ["a", "b"]


def test_extract_concepts_handles_brackets_inside_strings():
    """A '[' or ']' inside a JSON string must not break the depth scan."""
    html = (
        "<script>const CONCEPTS = "
        "[{\"id\": \"q\", \"note\": \"text with ] and [ inside\","
        " \"sub_concepts\": []}];</script>"
    )
    out = _extract_concepts_json(html)
    assert out[0]["note"] == "text with ] and [ inside"


# --------------------------------------------------------------------------- #
# Schema and shape                                                            #
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    return parse_v29()


def test_returns_dataframe_with_expected_columns(df):
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == PARSE_V29_COLUMNS
    assert len(df) > 0


def test_required_pdr_columns_present(df):
    """AC: columns must include term, analysis_text, law_id, article_id."""
    for col in ("term", "analysis_text", "law_id", "article_id"):
        assert col in df.columns


def test_no_nan_strings_in_object_columns(df):
    """Empty cells must come through as Python None, never the string 'nan'."""
    for col in df.columns:
        if df[col].dtype != object:
            continue
        bad = df[col].apply(
            lambda v: isinstance(v, str) and v.strip().lower() == "nan"
        )
        assert not bad.any(), f"column {col} contains the string 'nan'"


# --------------------------------------------------------------------------- #
# Round-tripping the analysis text                                            #
# --------------------------------------------------------------------------- #

def test_analysis_text_preserves_exact_source_string(df):
    """AC: round-trips analysis text without whitespace/punctuation drift.

    Re-extract the JSON directly and assert that for at least one cell the
    DataFrame's analysis_text matches the JSON's ``analysis`` field byte-for-
    byte (including newlines, parentheses, and inline citations).
    """
    raw = _extract_concepts_json(DEFAULT_HTML.read_text(encoding="utf-8"))
    # Find one EU "Definition" cell — they typically span paragraphs and
    # contain inline parenthesised citations, so any normalisation would
    # show up here.
    sample = None
    for c in raw:
        for sc in c.get("sub_concepts", []):
            for dim in sc.get("dimensions", []):
                cell = (dim.get("cells") or {}).get("eu")
                if cell and cell.get("analysis") and "(" in cell["analysis"]:
                    sample = (
                        c["id"], sc["id"], dim["id"], cell["analysis"],
                    )
                    break
            if sample:
                break
        if sample:
            break
    assert sample is not None, "no EU analysis cell with inline parens found"

    cid, sid, dim_id, expected = sample
    matched = df[
        (df["concept_id"] == cid)
        & (df["sub_concept_id"] == sid)
        & (df["dim_id"] == dim_id)
        & (df["jurisdiction"] == "eu")
    ]
    assert not matched.empty
    # Every row for this (cell) carries the same analysis_text — pick the
    # first and compare verbatim.
    assert matched["analysis_text"].iloc[0] == expected


def test_analysis_text_is_constant_across_exploded_rows(df):
    """When a reference fans out into multiple atomic citations the analysis
    text is duplicated — verify that's the case."""
    grouped = df.groupby(
        ["concept_id", "sub_concept_id", "jurisdiction", "dim_id"],
        dropna=False,
    )
    # Assert that within each cell-grouping, analysis_text has one unique value.
    for _, sub in grouped:
        unique_texts = sub["analysis_text"].dropna().unique()
        assert len(unique_texts) <= 1


# --------------------------------------------------------------------------- #
# Multi-article handling                                                      #
# --------------------------------------------------------------------------- #

def test_handles_cells_with_multiple_atomic_articles(df):
    """AC: handles entries that have multiple linked articles.

    A cell whose ``reference`` carries semicolon-joined atomic citations is
    expected to expand into multiple rows in the output frame.
    """
    grouped = (
        df.dropna(subset=["law_id", "article_id"])
        .groupby(
            ["concept_id", "sub_concept_id", "jurisdiction", "dim_id"],
            dropna=False,
        )
        .size()
    )
    multi = grouped[grouped > 1]
    assert not multi.empty, (
        "expected at least one cell to fan out into multiple (law, article) "
        "rows — none found"
    )


# --------------------------------------------------------------------------- #
# Spot checks against the known v29 data                                      #
# --------------------------------------------------------------------------- #

def test_high_risk_ai_system_eu_resolves_to_article_6(df):
    rows = df[
        (df["sub_concept_id"] == "high-risk-ai-system")
        & (df["jurisdiction"] == "eu")
    ]
    assert not rows.empty
    laws = set(rows["law_id"].dropna())
    arts = set(rows["article_id"].dropna())
    assert "eu-ai-act" in laws
    assert "6" in arts


def test_unique_terms_and_laws_are_nontrivial(df):
    """Sanity check: should be more than a handful of unique laws/terms."""
    assert df["term"].dropna().nunique() >= 10
    assert df["law_id"].dropna().nunique() >= 3


def test_law_ids_are_canonical_slugs(df):
    expected = {
        "eu-ai-act", "eu-guidelines-gpai-scope",
        "eu-gpai-cop-copyright", "eu-gpai-cop-transparency",
        "eu-gpai-cop-safety",
        "co-sb24205", "ut-sb226", "tx-hb149",
        "ca-sb53", "ca-sb942", "ca-ab2013",
        "ny-s8828", "ny-a6453",
    }
    seen = set(df["law_id"].dropna().unique())
    unknown = seen - expected
    assert not unknown, f"unexpected law_ids: {sorted(unknown)}"
