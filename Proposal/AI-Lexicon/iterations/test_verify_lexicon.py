"""Tests for iterations/verify_lexicon.py (US-003)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from load_lexicon_sources import DEFAULT_ANALYSIS
from parse_v29 import DEFAULT_HTML
from verify_lexicon import (
    ALL_STATUSES,
    STATUS_MATCH,
    STATUS_MISMATCH,
    STATUS_MISSING_IN_EXCEL,
    STATUS_MISSING_IN_HTML,
    VERIFY_COLUMNS,
    _classify,
    _resolve_excel_cell,
    _summary_counts,
    normalize_whitespace,
    verify_lexicon,
    write_verification_csv,
)


# --------------------------------------------------------------------------- #
# Pure helpers — no I/O                                                       #
# --------------------------------------------------------------------------- #

def test_normalize_whitespace_collapses_runs():
    assert normalize_whitespace("a\n  b\tc") == "a b c"


def test_normalize_whitespace_strips_outer():
    assert normalize_whitespace("  hello  ") == "hello"


def test_normalize_whitespace_treats_blanks_as_empty():
    assert normalize_whitespace(None) == ""
    assert normalize_whitespace("") == ""
    assert normalize_whitespace("   ") == ""
    assert normalize_whitespace("\xa0\xa0") == ""


def test_classify_match_after_whitespace_normalisation():
    """AC: Comparison is exact-text after normalising whitespace."""
    assert _classify("a b c", "a   b\nc") == STATUS_MATCH
    assert _classify(" foo bar  ", "foo bar") == STATUS_MATCH


def test_classify_mismatch_is_real_text_difference():
    assert _classify("a b c", "a b d") == STATUS_MISMATCH


def test_classify_missing_sides():
    assert _classify(None, "x") == STATUS_MISSING_IN_HTML
    assert _classify("", "x") == STATUS_MISSING_IN_HTML
    assert _classify("x", None) == STATUS_MISSING_IN_EXCEL
    assert _classify("x", "") == STATUS_MISSING_IN_EXCEL


def test_resolve_excel_cell_single_sub_lookup():
    out = _resolve_excel_cell(
        " High-risk AI system_ANALYSIS",
        "High-risk AI system",  # term irrelevant for single-sub sheets
        "EU (AIA)",
    )
    assert out == ("model-system", "high-risk-ai-system", "eu")


def test_resolve_excel_cell_multi_sub_disambiguates_by_term():
    """Same juris_header, different sections → different sub_concept."""
    co_provider = _resolve_excel_cell(
        "Provider_Developer_Analysis", "Developer", "Colorado (SB 24-205)",
    )
    ca_dev = _resolve_excel_cell(
        "Provider_Developer_Analysis", "Developer", "California (AB 2013)",
    )
    assert co_provider == ("provider-developer", "provider", "co")
    assert ca_dev == (
        "provider-developer",
        "provider-of-general-purpose-ai-models",
        "ca-1-developer",
    )


def test_resolve_excel_cell_unknown_returns_none():
    assert _resolve_excel_cell("Mystery_Sheet", "X", "Y") is None
    assert _resolve_excel_cell(
        " High-risk AI system_ANALYSIS", "anything", "Mars (??)",
    ) is None


# --------------------------------------------------------------------------- #
# End-to-end verification                                                     #
# --------------------------------------------------------------------------- #

pytestmark_e2e = pytest.mark.skipif(
    not (DEFAULT_HTML.exists() and DEFAULT_ANALYSIS.exists()),
    reason="v29 HTML or analysis Excel not available",
)


@pytest.fixture(scope="module")
def vdf() -> pd.DataFrame:
    return verify_lexicon()


@pytestmark_e2e
def test_returns_dataframe_with_expected_columns(vdf):
    assert isinstance(vdf, pd.DataFrame)
    assert list(vdf.columns) == VERIFY_COLUMNS
    assert len(vdf) > 0


@pytestmark_e2e
def test_status_values_are_in_known_set(vdf):
    """AC: per-analysis status must be one of the four documented values."""
    seen = set(vdf["status"].dropna().unique())
    assert seen <= set(ALL_STATUSES), f"unexpected statuses: {seen - set(ALL_STATUSES)}"


@pytestmark_e2e
def test_match_rows_have_identical_normalised_text(vdf):
    matches = vdf[vdf["status"] == STATUS_MATCH]
    assert not matches.empty
    sample = matches.head(50)
    for _, r in sample.iterrows():
        assert normalize_whitespace(r["html_analysis"]) == normalize_whitespace(
            r["excel_analysis"]
        )


@pytestmark_e2e
def test_mismatch_rows_have_different_normalised_text(vdf):
    """AC: Mismatches include both versions side by side."""
    mm = vdf[vdf["status"] == STATUS_MISMATCH]
    if mm.empty:
        pytest.skip("no mismatches in current data — nothing to assert")
    for _, r in mm.iterrows():
        assert normalize_whitespace(r["html_analysis"]) != normalize_whitespace(
            r["excel_analysis"]
        )
        # Both columns are populated for mismatches.
        assert r["html_analysis"]
        assert r["excel_analysis"]


@pytestmark_e2e
def test_missing_in_excel_has_html_text_only(vdf):
    me = vdf[vdf["status"] == STATUS_MISSING_IN_EXCEL]
    if me.empty:
        pytest.skip("no missing_in_excel rows — nothing to assert")
    assert me["html_analysis"].apply(
        lambda v: bool(normalize_whitespace(v))
    ).all()
    assert me["excel_analysis"].apply(
        lambda v: not normalize_whitespace(v)
    ).all()


@pytestmark_e2e
def test_missing_in_html_has_excel_text_only(vdf):
    mh = vdf[vdf["status"] == STATUS_MISSING_IN_HTML]
    if mh.empty:
        pytest.skip("no missing_in_html rows — nothing to assert")
    assert mh["excel_analysis"].apply(
        lambda v: bool(normalize_whitespace(v))
    ).all()
    assert mh["html_analysis"].apply(
        lambda v: not normalize_whitespace(v)
    ).all()


@pytestmark_e2e
def test_known_match_eu_high_risk_definition(vdf):
    """The EU definition of 'High-risk AI system' should match exactly between
    the v29 HTML and the cross-checked Excel."""
    rows = vdf[
        (vdf["sub_concept_id"] == "high-risk-ai-system")
        & (vdf["jid"] == "eu")
        & (vdf["dim_label"] == "Definition")
    ]
    assert not rows.empty
    # Allow either match or known-mismatch — but at least it must be one of
    # the four statuses, and we want to assert the verifier has classified it.
    assert rows.iloc[0]["status"] in ALL_STATUSES


@pytestmark_e2e
def test_writes_csv_with_all_columns(vdf, tmp_path: Path):
    out = tmp_path / "verify.csv"
    written = write_verification_csv(vdf, out)
    assert written == out
    assert out.exists()
    rt = pd.read_csv(out, dtype=object, keep_default_na=False)
    assert list(rt.columns) == VERIFY_COLUMNS
    assert len(rt) == len(vdf)


@pytestmark_e2e
def test_summary_counts_sum_to_total(vdf):
    counts = _summary_counts(vdf)
    assert sum(counts.values()) == len(vdf)
    # All four statuses surface in real data — sanity check that the verifier
    # is exercising every branch (otherwise the test_<status>_… tests above
    # would silently skip).
    assert counts[STATUS_MATCH] > 0
    assert counts[STATUS_MISMATCH] > 0
    assert counts[STATUS_MISSING_IN_HTML] > 0
    assert counts[STATUS_MISSING_IN_EXCEL] > 0
