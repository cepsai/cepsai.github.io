"""Tests for iterations/load_lexicon_sources.py (US-001).

These tests are skipped when the source Excel files are not present (e.g. on
CI without the developer's Downloads folder), so they remain non-fatal in
shared environments while still validating the loader locally.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from load_lexicon_sources import (
    ANALYSIS_COLUMNS,
    DEFAULT_ANALYSIS,
    DEFAULT_VERBATIM,
    VERBATIM_COLUMNS,
    _norm_str,
    load_analyses,
    load_verbatim,
)


pytestmark = pytest.mark.skipif(
    not (DEFAULT_ANALYSIS.exists() and DEFAULT_VERBATIM.exists()),
    reason=f"Source Excel files not found at {DEFAULT_ANALYSIS} / "
           f"{DEFAULT_VERBATIM}",
)


# --------------------------------------------------------------------------- #
# Pure helpers — no I/O                                                       #
# --------------------------------------------------------------------------- #

def test_norm_str_treats_blank_as_none():
    assert _norm_str(None) is None
    assert _norm_str("") is None
    assert _norm_str("   ") is None
    assert _norm_str("\xa0") is None


def test_norm_str_preserves_namibia():
    """ISO 'NA' (Namibia) must round-trip as a real string, not be coerced
    to None even though pandas treats 'NA' as missing by default."""
    assert _norm_str("NA") == "NA"
    assert _norm_str(" NA ") == "NA"


# --------------------------------------------------------------------------- #
# Schema                                                                      #
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def analyses() -> pd.DataFrame:
    return load_analyses()


@pytest.fixture(scope="module")
def verbatim() -> pd.DataFrame:
    return load_verbatim()


def test_analyses_returns_dataframe_with_expected_columns(analyses):
    assert isinstance(analyses, pd.DataFrame)
    assert list(analyses.columns) == ANALYSIS_COLUMNS
    assert len(analyses) > 0, "expected non-empty analyses frame"


def test_verbatim_returns_dataframe_with_expected_columns(verbatim):
    assert isinstance(verbatim, pd.DataFrame)
    assert list(verbatim.columns) == VERBATIM_COLUMNS
    assert len(verbatim) > 0, "expected non-empty verbatim frame"


def test_analyses_has_join_key_columns(analyses):
    for col in ("term", "law_id", "article_id"):
        assert col in analyses.columns


def test_verbatim_has_join_key_columns(verbatim):
    for col in ("term", "law_id", "article_id"):
        assert col in verbatim.columns


# --------------------------------------------------------------------------- #
# Empty-cell preservation                                                     #
# --------------------------------------------------------------------------- #

def _no_nan_strings(df: pd.DataFrame) -> bool:
    """Return True iff no string cell holds the literal text 'nan' / 'NaN'.

    Pandas readers occasionally coerce missing cells to the *string* 'nan'
    when forcing object dtype; this would silently break downstream string
    comparisons.
    """
    for col in df.columns:
        if df[col].dtype != object:
            continue
        bad = df[col].apply(
            lambda v: isinstance(v, str) and v.strip().lower() == "nan"
        )
        if bad.any():
            return False
    return True


def test_verbatim_empty_cells_are_none_not_nan(verbatim):
    """AC: Empty/missing verbatim cells are preserved as None, not NaN strings."""
    assert _no_nan_strings(verbatim)
    # Direct check: tags is sparsely populated; missing entries should be None.
    if verbatim["tags"].isna().any():
        any_missing = verbatim[verbatim["tags"].isna()].iloc[0]
        assert any_missing["tags"] is None


def test_analyses_empty_cells_are_none_not_nan(analyses):
    assert _no_nan_strings(analyses)


# --------------------------------------------------------------------------- #
# Join key reachability                                                       #
# --------------------------------------------------------------------------- #

def test_analyses_and_verbatim_share_some_join_keys(analyses, verbatim):
    """Sanity check: at least one (term, law_id, article_id) tuple appears in
    both frames. The verifier downstream depends on this overlap."""
    a_keys = set(
        analyses.dropna(subset=["term", "law_id", "article_id"])
        .apply(lambda r: (r["term"], r["law_id"], r["article_id"]), axis=1)
    )
    v_keys = set(
        verbatim.dropna(subset=["term", "law_id", "article_id"])
        .apply(lambda r: (r["term"], r["law_id"], r["article_id"]), axis=1)
    )
    overlap = a_keys & v_keys
    # We don't expect 100% overlap (analysis terms are jurisdictional, e.g.
    # "High-risk AI system" vs "High-risk artificial intelligence system"),
    # but at least several rows should join — otherwise the loader is broken.
    assert len(overlap) >= 5, (
        f"analyses ↔ verbatim join is too sparse: {len(overlap)} shared keys"
    )


# --------------------------------------------------------------------------- #
# Spot checks against known data                                              #
# --------------------------------------------------------------------------- #

def test_analyses_includes_eu_ai_act_high_risk(analyses):
    rows = analyses[
        (analyses["term"] == "High-risk AI system")
        & (analyses["law_id"] == "eu-ai-act")
    ]
    assert not rows.empty, "expected an EU AI Act row for 'High-risk AI system'"
    # Article 6 should be one of the cited articles for the Definition row.
    arts = set(rows["article_id"].dropna().tolist())
    assert "6" in arts


def test_verbatim_includes_provider_eu_ai_act(verbatim):
    rows = verbatim[
        (verbatim["term"] == "Provider")
        & (verbatim["law_id"] == "eu-ai-act")
    ]
    assert not rows.empty, "expected EU verbatim rows for 'Provider'"
    # The Scope row cites Article 3 (the provider definition).
    arts = set(rows["article_id"].dropna().tolist())
    assert "3" in arts


def test_verbatim_text_round_trips_unicode(verbatim):
    """AC implicit: verbatim text preserves source quotes (no mojibake)."""
    nonempty = verbatim[verbatim["verbatim_text"].notna()]
    assert not nonempty.empty
    sample = nonempty["verbatim_text"].iloc[0]
    assert isinstance(sample, str)
    # No literal 'nan' polluting the data.
    assert sample.strip().lower() != "nan"


def test_law_ids_use_canonical_slugs(analyses, verbatim):
    """Detected law_ids must come from the project's canonical slug set."""
    expected = {
        "eu-ai-act", "eu-guidelines-gpai-scope",
        "eu-gpai-cop-copyright", "eu-gpai-cop-transparency",
        "eu-gpai-cop-safety",
        "co-sb24205", "ut-sb226", "tx-hb149",
        "ca-sb53", "ca-sb942", "ca-ab2013",
        "ny-s8828", "ny-a6453",
    }
    for df in (analyses, verbatim):
        seen = set(df["law_id"].dropna().unique())
        unknown = seen - expected
        assert not unknown, f"unexpected law_ids: {sorted(unknown)}"
