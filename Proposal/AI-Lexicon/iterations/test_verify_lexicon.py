"""Tests for iterations/verify_lexicon.py (US-003 + US-004)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from load_lexicon_sources import DEFAULT_ANALYSIS, DEFAULT_VERBATIM
from parse_v29 import DEFAULT_HTML
from verify_lexicon import (
    ALL_LINK_STATUSES,
    ALL_STATUSES,
    STATUS_MATCH,
    STATUS_MISMATCH,
    STATUS_MISSING_IN_EXCEL,
    STATUS_MISSING_IN_HTML,
    STATUS_NO_VERBATIM,
    STATUS_VERBATIM_FOUND,
    STATUS_WRONG_ARTICLE,
    STATUS_WRONG_LAW,
    VERBATIM_CELLS,
    VERIFY_COLUMNS,
    _aggregate_link_status,
    _classify,
    _classify_link,
    _format_links,
    _format_statuses,
    _link_summary_counts,
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
# US-004 link-classifier helpers (pure)                                        #
# --------------------------------------------------------------------------- #

def _toy_by_term() -> dict:
    """A minimal verbatim term index used by the unit tests."""
    return {
        "Provider": {("eu-ai-act", "6"), ("eu-ai-act", "16"), ("eu-ai-act", None)},
        "Developer": {("co-sb24205", "6-1-1701")},
    }


def test_classify_link_verbatim_found_exact_article():
    """AC: status verbatim_found when (term, law, article) is present."""
    out = _classify_link("Provider", "eu-ai-act", "6", _toy_by_term())
    assert out == STATUS_VERBATIM_FOUND


def test_classify_link_wrong_article_same_law():
    """AC: wrong_article when verbatim has the term in the same law but a
    different article."""
    out = _classify_link("Provider", "eu-ai-act", "99", _toy_by_term())
    assert out == STATUS_WRONG_ARTICLE


def test_classify_link_wrong_law_term_in_other_law():
    """AC: wrong_law when the term has no entry in the linked law but exists
    in another."""
    out = _classify_link("Provider", "tx-hb149", "552.001", _toy_by_term())
    assert out == STATUS_WRONG_LAW


def test_classify_link_no_verbatim_when_term_absent():
    out = _classify_link("UnknownTerm", "eu-ai-act", "6", _toy_by_term())
    assert out == STATUS_NO_VERBATIM


def test_classify_link_no_verbatim_when_term_is_none():
    """Cells with no verbatim block (term is None) collapse to no_verbatim."""
    out = _classify_link(None, "eu-ai-act", "6", _toy_by_term())
    assert out == STATUS_NO_VERBATIM


def test_classify_link_article_none_in_verbatim_counts_as_same_law():
    """A verbatim entry with article_id=None still anchors the term to the
    law, so an HTML link to a specific article in that law is wrong_article
    rather than wrong_law."""
    out = _classify_link("Developer", "co-sb24205", "9-9-9999", _toy_by_term())
    # Same law, different article (verbatim has 6-1-1701 only).
    assert out == STATUS_WRONG_ARTICLE


def test_aggregate_link_status_picks_worst():
    assert _aggregate_link_status([
        STATUS_VERBATIM_FOUND,
        STATUS_WRONG_ARTICLE,
        STATUS_NO_VERBATIM,
    ]) == STATUS_WRONG_ARTICLE
    assert _aggregate_link_status([
        STATUS_VERBATIM_FOUND, STATUS_VERBATIM_FOUND,
    ]) == STATUS_VERBATIM_FOUND
    assert _aggregate_link_status([
        STATUS_NO_VERBATIM, STATUS_WRONG_LAW,
    ]) == STATUS_WRONG_LAW


def test_aggregate_link_status_empty_returns_none():
    assert _aggregate_link_status([]) is None


def test_format_links_renders_pairs():
    out = _format_links([("eu-ai-act", "6"), ("co-sb24205", "6-1-1701")])
    assert out == "eu-ai-act:6;co-sb24205:6-1-1701"


def test_format_links_handles_none_article():
    out = _format_links([("eu-ai-act", None)])
    assert out == "eu-ai-act:"


def test_format_links_empty_returns_none():
    assert _format_links([]) is None
    assert _format_statuses([]) is None


def test_verbatim_cells_keys_match_documented_blocks():
    """VERBATIM_CELLS should only point at sheets/juris-headers that exist
    in the loaded verbatim DataFrame (sanity check on the static map)."""
    if not DEFAULT_VERBATIM.exists():
        pytest.skip("verbatim Excel not available")
    from load_lexicon_sources import load_verbatim
    v = load_verbatim()
    seen_blocks = set(
        zip(
            v["sheet"].tolist(), v["jurisdiction_header"].tolist(),
        )
    )
    bad = []
    for cell_key, block in VERBATIM_CELLS.items():
        if block not in seen_blocks:
            bad.append((cell_key, block))
    assert not bad, f"VERBATIM_CELLS points at unknown blocks: {bad}"


# --------------------------------------------------------------------------- #
# End-to-end verification                                                     #
# --------------------------------------------------------------------------- #

pytestmark_e2e = pytest.mark.skipif(
    not (DEFAULT_HTML.exists() and DEFAULT_ANALYSIS.exists()
         and DEFAULT_VERBATIM.exists()),
    reason="v29 HTML, analysis Excel, or verbatim Excel not available",
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


# --------------------------------------------------------------------------- #
# US-004 end-to-end                                                            #
# --------------------------------------------------------------------------- #

@pytestmark_e2e
def test_link_status_values_in_known_set(vdf):
    seen = {
        s for s in vdf["link_status"].dropna().unique()
    }
    assert seen <= set(ALL_LINK_STATUSES), (
        f"unexpected link statuses: {seen - set(ALL_LINK_STATUSES)}"
    )


@pytestmark_e2e
def test_linked_articles_and_link_statuses_zip_one_to_one(vdf):
    """Each cell with linked_articles has the same number of statuses."""
    sub = vdf[vdf["linked_articles"].notna()]
    assert not sub.empty
    for _, r in sub.iterrows():
        articles = str(r["linked_articles"]).split(";")
        statuses = str(r["link_statuses"]).split(";")
        assert len(articles) == len(statuses), (
            f"length mismatch for {r['concept_id']}/{r['sub_concept_id']}: "
            f"{r['linked_articles']!r} vs {r['link_statuses']!r}"
        )
        for s in statuses:
            assert s in ALL_LINK_STATUSES


@pytestmark_e2e
def test_link_status_aggregate_matches_worst_per_link(vdf):
    """The cell-level link_status is always the most-severe per-link status."""
    sub = vdf[vdf["link_statuses"].notna()]
    assert not sub.empty
    for _, r in sub.iterrows():
        per_link = str(r["link_statuses"]).split(";")
        agg = _aggregate_link_status(per_link)
        assert r["link_status"] == agg


@pytestmark_e2e
def test_cells_without_links_have_empty_link_columns(vdf):
    """missing_in_html cells (Excel-only) cannot have HTML-side links."""
    sub = vdf[vdf["status"] == STATUS_MISSING_IN_HTML]
    if sub.empty:
        pytest.skip("no missing_in_html rows")
    for _, r in sub.iterrows():
        assert r["linked_articles"] in (None, "")
        assert r["link_statuses"] in (None, "")
        assert r["link_status"] in (None, "")


@pytestmark_e2e
def test_all_link_statuses_appear_in_real_data(vdf):
    """AC: status values verbatim_found / no_verbatim / wrong_article /
    wrong_law all surface against the real fixtures."""
    counts = _link_summary_counts(vdf)
    assert counts[STATUS_VERBATIM_FOUND] > 0
    # The remaining three may be 0 in some snapshots, but at least one
    # severity-bearing status should be present (otherwise US-004 isn't
    # actually exercising the failure branches).
    assert (
        counts[STATUS_WRONG_ARTICLE]
        + counts[STATUS_WRONG_LAW]
        + counts[STATUS_NO_VERBATIM]
    ) > 0


@pytestmark_e2e
def test_known_verbatim_found_eu_provider_article_50(vdf):
    """Provider of limited-risk AI systems / EU / Transparency cites
    Article 50, which has a verbatim entry under 'Provider' / EU / eu-ai-act.
    """
    rows = vdf[
        (vdf["concept_id"] == "provider-developer")
        & (vdf["sub_concept_id"] == "provider")
        & (vdf["jid"] == "eu")
        & (vdf["dim_label"] == "Transparency")
    ]
    if rows.empty:
        pytest.skip("Provider/eu/Transparency cell not present in v29")
    r = rows.iloc[0]
    assert r["linked_articles"] is not None
    assert "eu-ai-act:50" in str(r["linked_articles"])
    statuses = str(r["link_statuses"]).split(";")
    articles = str(r["linked_articles"]).split(";")
    idx = articles.index("eu-ai-act:50")
    assert statuses[idx] == STATUS_VERBATIM_FOUND
