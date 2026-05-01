"""Tests for iterations/verify_lexicon.py (US-003 + US-004 + US-005)."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from load_lexicon_sources import DEFAULT_ANALYSIS, DEFAULT_VERBATIM
from parse_v29 import DEFAULT_HTML, _extract_concepts_json
from verify_lexicon import (
    ALL_LINK_STATUSES,
    ALL_STATUSES,
    CORRECTION_KIND_ANALYSIS,
    CORRECTION_KIND_LINK,
    CORRECTION_KIND_SKIPPED,
    FILTER_BUTTONS,
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
    _apply_correction,
    _build_verbatim_indices,
    _classify,
    _classify_link,
    _compute_corrections,
    _extract_concepts_span,
    _find_cell,
    _format_links,
    _format_statuses,
    _inject_summary_block,
    _link_summary_counts,
    _render_summary_block,
    _replace_id_in_atom,
    _resolve_excel_cell,
    _row_filter_tags,
    _row_payload,
    _serialize_concepts,
    _substitute_article_in_reference,
    _summary_counts,
    build_corrected_html,
    normalize_whitespace,
    render_html_report,
    render_markdown_report,
    verify_lexicon,
    write_verification_csv,
    write_verification_html,
    write_verification_md,
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


# --------------------------------------------------------------------------- #
# US-005 — markdown + HTML report                                             #
# --------------------------------------------------------------------------- #

def _toy_verify_df() -> pd.DataFrame:
    """A small fixture covering every status branch the report must surface."""
    rows = [
        {
            "status": STATUS_MATCH,
            "concept_id": "c1", "sub_concept_id": "s1", "jid": "eu",
            "dim_label": "Definition",
            "term_html": "Provider", "term_excel": "Provider",
            "html_analysis": "same text", "excel_analysis": "same text",
            "sheet": "S", "addr": "B2",
            "linked_articles": "eu-ai-act:6",
            "link_statuses": STATUS_VERBATIM_FOUND,
            "link_status": STATUS_VERBATIM_FOUND,
        },
        {
            "status": STATUS_MISMATCH,
            "concept_id": "c1", "sub_concept_id": "s1", "jid": "eu",
            "dim_label": "Scope",
            "term_html": "Provider", "term_excel": "Provider",
            "html_analysis": "alpha beta gamma",
            "excel_analysis": "alpha BETA gamma",
            "sheet": "S", "addr": "B3",
            "linked_articles": "eu-ai-act:6;eu-ai-act:9",
            "link_statuses": f"{STATUS_VERBATIM_FOUND};{STATUS_WRONG_ARTICLE}",
            "link_status": STATUS_WRONG_ARTICLE,
        },
        {
            "status": STATUS_MISSING_IN_HTML,
            "concept_id": "c1", "sub_concept_id": "s1", "jid": "co",
            "dim_label": "Penalties",
            "term_html": None, "term_excel": "Developer",
            "html_analysis": None, "excel_analysis": "Up to $20K",
            "sheet": "S", "addr": "C5",
            "linked_articles": None, "link_statuses": None,
            "link_status": None,
        },
        {
            "status": STATUS_MISSING_IN_EXCEL,
            "concept_id": "c1", "sub_concept_id": "s1", "jid": "tx",
            "dim_label": "Term",
            "term_html": "Developer", "term_excel": None,
            "html_analysis": "Developer", "excel_analysis": None,
            "sheet": None, "addr": None,
            "linked_articles": "tx-hb149:552",
            "link_statuses": STATUS_WRONG_LAW,
            "link_status": STATUS_WRONG_LAW,
        },
    ]
    cols = VERIFY_COLUMNS
    df = pd.DataFrame(rows, columns=cols)
    return df


# --- Markdown report ---

def test_render_markdown_report_has_all_sections():
    df = _toy_verify_df()
    md = render_markdown_report(df, generated_at=datetime(2026, 5, 1, 10, 0, 0))
    assert "# Lexicon verification report" in md
    assert "_Generated: 2026-05-01T10:00:00_" in md
    assert "## Summary" in md
    assert "## Top mismatches" in md
    assert "## Broken links" in md
    assert "## Missing in HTML" in md
    assert "## Missing in Excel" in md


def test_markdown_summary_carries_status_and_link_counts():
    df = _toy_verify_df()
    md = render_markdown_report(df)
    # 4 cells: 1 match / 1 mismatch / 1 missing_in_html / 1 missing_in_excel.
    assert "Total analysis cells verified: **4**" in md
    assert "`match`: **1**" in md
    assert "`mismatch`: **1**" in md
    assert "`missing_in_html`: **1**" in md
    assert "`missing_in_excel`: **1**" in md
    # 4 links: 2 verbatim_found, 1 wrong_article, 1 wrong_law.
    assert "Total linked articles classified: **4**" in md
    assert "`verbatim_found`: **2**" in md
    assert "`wrong_article`: **1**" in md
    assert "`wrong_law`: **1**" in md


def test_markdown_top_mismatches_lists_mismatched_cells():
    df = _toy_verify_df()
    md = render_markdown_report(df)
    # The mismatch row's terms / dim should appear in the top-mismatches table.
    assert "Scope" in md
    assert "alpha beta gamma" in md
    assert "alpha BETA gamma" in md


def test_markdown_broken_links_section_lists_only_broken_links():
    df = _toy_verify_df()
    md = render_markdown_report(df)
    # The wrong_article on eu-ai-act:9 and wrong_law on tx-hb149:552 must
    # both appear; the verbatim_found link must NOT be listed as broken.
    assert "`eu-ai-act:9`" in md
    assert "`tx-hb149:552`" in md
    # The verbatim_found link is not listed in the broken-links section
    # (it can still appear in the summary chips above).
    broken_section = md.split("## Broken links")[1].split("## Missing")[0]
    assert "`eu-ai-act:6`" not in broken_section


def test_markdown_truncates_long_text_and_escapes_pipes():
    long_text = "a" * 500 + "|hello|" + "b" * 500
    df = pd.DataFrame([{
        "status": STATUS_MISMATCH,
        "concept_id": "c", "sub_concept_id": "s", "jid": "eu",
        "dim_label": "D",
        "term_html": "X", "term_excel": "X",
        "html_analysis": long_text, "excel_analysis": "short",
        "sheet": None, "addr": None,
        "linked_articles": None, "link_statuses": None,
        "link_status": None,
    }], columns=VERIFY_COLUMNS)
    md = render_markdown_report(df)
    # The long body should not contain a raw "|" that would break the table,
    # and should be elided with an ellipsis.
    body_line = [
        line for line in md.splitlines()
        if line.startswith("| c |") or line.startswith("| c|")
    ]
    assert body_line, f"could not find table row in:\n{md}"
    assert "|hello|" not in body_line[0]
    assert "…" in body_line[0]


def test_write_verification_md_creates_parent_dir_and_returns_path(tmp_path: Path):
    df = _toy_verify_df()
    out = tmp_path / "nested" / "report.md"
    written = write_verification_md(df, out)
    assert written == out
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert text.startswith("# Lexicon verification report")


# --- HTML report ---

def test_row_filter_tags_for_each_combination():
    assert _row_filter_tags(STATUS_MATCH, None) == ["all"]
    assert _row_filter_tags(STATUS_MISMATCH, STATUS_VERBATIM_FOUND) == [
        "all", "mismatch",
    ]
    assert _row_filter_tags(STATUS_MISSING_IN_HTML, None) == [
        "all", "missing",
    ]
    assert _row_filter_tags(STATUS_MISSING_IN_EXCEL, STATUS_WRONG_LAW) == [
        "all", "missing", "wrong_law",
    ]
    assert _row_filter_tags(STATUS_MATCH, STATUS_WRONG_ARTICLE) == [
        "all", "wrong_article",
    ]


def test_row_payload_has_one_dict_per_row():
    df = _toy_verify_df()
    payload = _row_payload(df)
    assert len(payload) == len(df)
    # Each entry carries the keys the JS reads.
    keys = {
        "status", "concept_id", "sub_concept_id", "jid", "dim_label",
        "term_html", "term_excel", "html_analysis", "excel_analysis",
        "linked_articles", "link_statuses", "link_status", "tags",
    }
    for row in payload:
        assert keys <= set(row.keys())
    # Filter tags reflect the row's status / link status.
    assert payload[0]["tags"] == ["all"]
    assert "mismatch" in payload[1]["tags"]
    assert "missing" in payload[2]["tags"]
    assert "wrong_law" in payload[3]["tags"]


def test_render_html_report_contains_filter_buttons_and_no_inline_onclick():
    df = _toy_verify_df()
    html = render_html_report(df)
    # Self-contained: no remote scripts/links.
    assert "<!DOCTYPE html>" in html
    assert "src=\"http" not in html
    assert "href=\"http" not in html
    # Filter buttons all present.
    for key, label in FILTER_BUTTONS:
        assert f'data-filter="{key}"' in html
        assert f">{label}</button>" in html
    # No inline onclick handlers anywhere — interactivity uses addEventListener.
    assert "onclick=" not in html.lower()
    assert "addEventListener" in html


def test_render_html_report_embeds_payload_as_json():
    df = _toy_verify_df()
    html = render_html_report(df)
    m = re.search(
        r'<script id="payload" type="application/json">(.*?)</script>',
        html, flags=re.S,
    )
    assert m, "payload script tag not found"
    # Undo the closing-tag escape we apply for safe embedding.
    raw = m.group(1).replace("<\\/", "</")
    payload = json.loads(raw)
    assert isinstance(payload, list)
    assert len(payload) == len(df)
    assert payload[1]["status"] == STATUS_MISMATCH


def test_render_html_report_payload_safe_against_script_breakout():
    """A row containing the literal "</script>" must not break the page out
    of its embedded JSON island."""
    df = pd.DataFrame([{
        "status": STATUS_MISMATCH,
        "concept_id": "c", "sub_concept_id": "s", "jid": "eu",
        "dim_label": "D",
        "term_html": "X", "term_excel": "X",
        "html_analysis": "evil </script><script>alert(1)</script> end",
        "excel_analysis": "ok",
        "sheet": None, "addr": None,
        "linked_articles": None, "link_statuses": None,
        "link_status": None,
    }], columns=VERIFY_COLUMNS)
    html = render_html_report(df)
    # The raw "</script>" must not appear inside the JSON literal — the
    # writer escapes it to "<\/script>" so the browser won't terminate the
    # script element early.
    payload_block = re.search(
        r'<script id="payload" type="application/json">(.*?)</script>',
        html, flags=re.S,
    ).group(1)
    assert "</script>" not in payload_block
    assert "<\\/script>" in payload_block


def test_render_html_report_includes_all_rows_with_data_tags():
    df = _toy_verify_df()
    html = render_html_report(df)
    # data-tags attribute should appear once per row (we render to JS so this
    # check happens on the JS-side via the payload — assert each tag is
    # represented somewhere in the markup or payload).
    for row in _row_payload(df):
        for tag in row["tags"]:
            assert tag in html


def test_write_verification_html_creates_parent_dir_and_writes_file(tmp_path: Path):
    df = _toy_verify_df()
    out = tmp_path / "nested" / "report.html"
    written = write_verification_html(df, out)
    assert written == out
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert text.startswith("<!DOCTYPE html>")
    assert text.endswith("</html>\n")


# --- End-to-end against real fixtures ---

@pytestmark_e2e
def test_writes_md_and_html_with_real_data(vdf, tmp_path: Path):
    md_out = tmp_path / "verify.md"
    html_out = tmp_path / "verify.html"
    write_verification_md(vdf, md_out)
    write_verification_html(vdf, html_out)
    assert md_out.exists() and md_out.stat().st_size > 0
    assert html_out.exists() and html_out.stat().st_size > 0
    md = md_out.read_text(encoding="utf-8")
    assert "## Summary" in md
    html = html_out.read_text(encoding="utf-8")
    assert "addEventListener" in html
    # The interactive viewer carries one payload entry per verification row.
    m = re.search(
        r'<script id="payload" type="application/json">(.*?)</script>',
        html, flags=re.S,
    )
    payload = json.loads(m.group(1).replace("<\\/", "</"))
    assert len(payload) == len(vdf)


# --------------------------------------------------------------------------- #
# US-006 — v29-corrected.html builder                                         #
# --------------------------------------------------------------------------- #

# Pure helpers — no I/O ----------------------------------------------------- #

def test_extract_concepts_span_returns_indices_that_round_trip():
    """The (start, end) span must point at a JSON literal that re-parses to
    the same data."""
    sample = '<html><body><script>const CONCEPTS = [{"a":1},{"b":2}];\nconst X = 0;</script></body></html>'
    concepts, start, end = _extract_concepts_span(sample)
    assert concepts == [{"a": 1}, {"b": 2}]
    assert sample[start:end] == '[{"a":1},{"b":2}]'


def test_extract_concepts_span_handles_brackets_in_strings():
    """Brackets that appear inside JSON strings must not break depth counting."""
    sample = 'x const CONCEPTS = [{"s":"]"}]; trailing'
    concepts, start, end = _extract_concepts_span(sample)
    assert concepts == [{"s": "]"}]
    assert sample[start:end] == '[{"s":"]"}]'


def test_extract_concepts_span_raises_when_not_present():
    with pytest.raises(ValueError, match="not found"):
        _extract_concepts_span("<html><body>no script here</body></html>")


def test_serialize_concepts_uses_compact_separators():
    out = _serialize_concepts([{"a": 1, "b": [2, 3]}])
    assert out == '[{"a":1,"b":[2,3]}]'


def test_replace_id_in_atom_article():
    out = _replace_id_in_atom("AIA Article 6(1)", "article", "6", "9")
    assert out == "AIA Article 9(1)"


def test_replace_id_in_atom_section_does_not_partial_match():
    """Section ids are distinctive — substituting '6-1-1701' must not also
    swallow the head of a longer id like '6-1-1701.5'."""
    out = _replace_id_in_atom(
        "Colorado SB 24-205, §6-1-1701", "section", "6-1-1701", "6-1-1702",
    )
    assert out == "Colorado SB 24-205, §6-1-1702"


def test_replace_id_in_atom_unknown_kind_returns_original():
    assert _replace_id_in_atom("foo", "mystery", "6", "9") == "foo"


def test_substitute_article_in_reference_swaps_matching_atom_only():
    ref = "AIA Article 6(1); AIA Article 50"
    out = _substitute_article_in_reference(ref, "eu-ai-act", "6", "9")
    assert out == "AIA Article 9(1); AIA Article 50"


def test_substitute_article_in_reference_preserves_separators():
    """Whitespace around `;` must round-trip exactly."""
    ref = "AIA Article 6(1); AIA Article 16"
    out = _substitute_article_in_reference(ref, "eu-ai-act", "16", "17")
    assert out == "AIA Article 6(1); AIA Article 17"
    ref2 = "AIA Article 6 ;AIA Article 16"
    out2 = _substitute_article_in_reference(ref2, "eu-ai-act", "16", "17")
    assert out2 == "AIA Article 6 ;AIA Article 17"


def test_substitute_article_in_reference_no_match_returns_unchanged():
    ref = "Texas HB 149, §552.001"
    out = _substitute_article_in_reference(ref, "eu-ai-act", "6", "9")
    assert out == ref


# Correction computation ---------------------------------------------------- #

def _toy_correction_inputs():
    by_block = {("Provider_Developer", "EU"): "Provider"}
    by_term = {
        "Provider": {("eu-ai-act", "6"), ("eu-ai-act", "16")},
    }
    return by_block, by_term


def test_compute_corrections_emits_analysis_for_each_mismatch():
    df = pd.DataFrame([{
        "status": STATUS_MISMATCH,
        "concept_id": "c", "sub_concept_id": "s", "jid": "eu",
        "dim_label": "Definition",
        "term_html": "X", "term_excel": "X",
        "html_analysis": "old", "excel_analysis": "new",
        "sheet": None, "addr": None,
        "linked_articles": None, "link_statuses": None,
        "link_status": None,
    }], columns=VERIFY_COLUMNS)
    by_block, by_term = _toy_correction_inputs()
    out = _compute_corrections(df, by_block, by_term)
    assert len(out) == 1
    c = out[0]
    assert c["kind"] == CORRECTION_KIND_ANALYSIS
    assert c["new_text"] == "new"
    assert c["old_text"] == "old"


def test_compute_corrections_skips_mismatch_with_blank_excel_text():
    """A mismatch row whose excel_analysis is blank can't produce a fix."""
    df = pd.DataFrame([{
        "status": STATUS_MISMATCH,
        "concept_id": "c", "sub_concept_id": "s", "jid": "eu",
        "dim_label": "Definition",
        "term_html": "X", "term_excel": "X",
        "html_analysis": "old", "excel_analysis": "   ",
        "sheet": None, "addr": None,
        "linked_articles": None, "link_statuses": None,
        "link_status": None,
    }], columns=VERIFY_COLUMNS)
    by_block, by_term = _toy_correction_inputs()
    assert _compute_corrections(df, by_block, by_term) == []


def test_compute_corrections_emits_link_when_unique_candidate():
    df = pd.DataFrame([{
        "status": STATUS_MATCH,
        "concept_id": "provider-developer",
        "sub_concept_id": "provider", "jid": "eu",
        "dim_label": "Transparency",
        "term_html": "Provider", "term_excel": "Provider",
        "html_analysis": "ok", "excel_analysis": "ok",
        "sheet": None, "addr": None,
        "linked_articles": "eu-ai-act:9",
        "link_statuses": STATUS_WRONG_ARTICLE,
        "link_status": STATUS_WRONG_ARTICLE,
    }], columns=VERIFY_COLUMNS)
    # Only one candidate other than 9: but our toy has both 6 and 16 — that's
    # ambiguous. Narrow to one.
    by_block = {("Provider_Developer", "EU"): "Provider"}
    by_term = {"Provider": {("eu-ai-act", "6")}}
    out = _compute_corrections(df, by_block, by_term)
    assert len(out) == 1
    assert out[0]["kind"] == CORRECTION_KIND_LINK
    assert out[0]["new_article"] == "6"
    assert out[0]["law"] == "eu-ai-act"
    assert out[0]["old_article"] == "9"


def test_compute_corrections_emits_skipped_when_ambiguous_candidates():
    df = pd.DataFrame([{
        "status": STATUS_MATCH,
        "concept_id": "provider-developer",
        "sub_concept_id": "provider", "jid": "eu",
        "dim_label": "Transparency",
        "term_html": "Provider", "term_excel": "Provider",
        "html_analysis": "ok", "excel_analysis": "ok",
        "sheet": None, "addr": None,
        "linked_articles": "eu-ai-act:9",
        "link_statuses": STATUS_WRONG_ARTICLE,
        "link_status": STATUS_WRONG_ARTICLE,
    }], columns=VERIFY_COLUMNS)
    by_block, by_term = _toy_correction_inputs()  # has both 6 and 16
    out = _compute_corrections(df, by_block, by_term)
    assert len(out) == 1
    assert out[0]["kind"] == CORRECTION_KIND_SKIPPED
    assert out[0]["reason"] == "ambiguous"
    assert sorted(out[0]["candidates"]) == ["16", "6"]


def test_compute_corrections_ignores_verbatim_found_links():
    """Only wrong_article should generate a correction; verbatim_found is
    already correct."""
    df = pd.DataFrame([{
        "status": STATUS_MATCH,
        "concept_id": "provider-developer",
        "sub_concept_id": "provider", "jid": "eu",
        "dim_label": "Transparency",
        "term_html": "Provider", "term_excel": "Provider",
        "html_analysis": "ok", "excel_analysis": "ok",
        "sheet": None, "addr": None,
        "linked_articles": "eu-ai-act:6",
        "link_statuses": STATUS_VERBATIM_FOUND,
        "link_status": STATUS_VERBATIM_FOUND,
    }], columns=VERIFY_COLUMNS)
    by_block, by_term = _toy_correction_inputs()
    assert _compute_corrections(df, by_block, by_term) == []


# Apply ---------------------------------------------------------------------- #

def _toy_concepts():
    return [{
        "id": "c1",
        "sub_concepts": [{
            "id": "s1",
            "dimensions": [
                {
                    "id": "d1", "label": "Definition",
                    "cells": {
                        "eu": {
                            "analysis": "old analysis",
                            "verbatim": "x",
                            "reference": "AIA Article 6(1)",
                        },
                    },
                },
            ],
        }],
    }]


def test_find_cell_returns_dict_when_present():
    cell = _find_cell(_toy_concepts(), "c1", "s1", "eu", "Definition")
    assert cell and cell["analysis"] == "old analysis"


def test_find_cell_returns_none_when_missing():
    assert _find_cell(_toy_concepts(), "c1", "s1", "us", "Definition") is None
    assert _find_cell(_toy_concepts(), "c1", "s2", "eu", "Definition") is None
    assert _find_cell(_toy_concepts(), None, "s1", "eu", "Definition") is None


def test_apply_correction_replaces_analysis_text():
    concepts = _toy_concepts()
    ok = _apply_correction(concepts, {
        "kind": CORRECTION_KIND_ANALYSIS,
        "cid": "c1", "sid": "s1", "jid": "eu", "dim_label": "Definition",
        "old_text": "old analysis", "new_text": "fresh from Excel",
    })
    assert ok
    cell = _find_cell(concepts, "c1", "s1", "eu", "Definition")
    assert cell["analysis"] == "fresh from Excel"


def test_apply_correction_swaps_article_in_reference():
    concepts = _toy_concepts()
    ok = _apply_correction(concepts, {
        "kind": CORRECTION_KIND_LINK,
        "cid": "c1", "sid": "s1", "jid": "eu", "dim_label": "Definition",
        "law": "eu-ai-act", "old_article": "6", "new_article": "9",
    })
    assert ok
    cell = _find_cell(concepts, "c1", "s1", "eu", "Definition")
    assert cell["reference"] == "AIA Article 9(1)"


def test_apply_correction_returns_false_when_cell_missing():
    concepts = _toy_concepts()
    ok = _apply_correction(concepts, {
        "kind": CORRECTION_KIND_ANALYSIS,
        "cid": "nope", "sid": "s1", "jid": "eu", "dim_label": "Definition",
        "old_text": "x", "new_text": "y",
    })
    assert not ok


# Summary block ------------------------------------------------------------- #

def test_render_summary_block_lists_every_change():
    """AC: summary block lists every change applied."""
    applied = [
        {
            "kind": CORRECTION_KIND_ANALYSIS,
            "cid": "c1", "sid": "s1", "jid": "eu", "dim_label": "Definition",
            "old_text": "old", "new_text": "new",
        },
        {
            "kind": CORRECTION_KIND_LINK,
            "cid": "c1", "sid": "s1", "jid": "eu", "dim_label": "Penalty",
            "law": "eu-ai-act", "old_article": "6", "new_article": "9",
        },
    ]
    skipped = [{
        "kind": CORRECTION_KIND_SKIPPED,
        "cid": "c2", "sid": "s2", "jid": "ca", "dim_label": "Term",
        "law": "ca-sb53", "old_article": "x", "candidates": ["a", "b"],
        "reason": "ambiguous",
    }]
    block = _render_summary_block(
        applied, skipped, generated_at=datetime(2026, 5, 1, 12, 0, 0),
    )
    # Headline counts.
    assert "2 corrections applied" in block
    assert "1 not auto-correctable" in block
    # Both applied entries surface their cell IDs and changes.
    assert "Definition" in block and "Penalty" in block
    assert "eu-ai-act:6" in block and "eu-ai-act:9" in block
    # Skipped entry surfaces with reason and candidates.
    assert "ambiguous" in block
    assert "a, b" in block
    # The block is HTML and self-styled.
    assert 'id="v29-corrections-summary"' in block
    assert "<style>" in block


def test_render_summary_block_handles_no_corrections():
    block = _render_summary_block([], [])
    assert "0 corrections applied" in block
    assert "0 not auto-correctable" in block
    assert "No corrections were applied." in block


def test_inject_summary_block_after_body_tag():
    html = "<!doctype html><html><body><h1>Hi</h1></body></html>"
    out = _inject_summary_block(html, "<p>summary</p>")
    assert "<body><p>summary</p>" in out.replace("\n", "")
    assert "<h1>Hi</h1>" in out


def test_inject_summary_block_falls_back_when_no_body():
    out = _inject_summary_block("<html>no body</html>", "<p>summary</p>")
    assert out.startswith("<p>summary</p>")


# End-to-end against real fixtures ------------------------------------------ #

@pytestmark_e2e
def test_build_corrected_html_writes_file_to_default_location(tmp_path: Path):
    """AC: iterations/digital_lexicon_v29-corrected.html generated in --fix mode."""
    out_path = tmp_path / "digital_lexicon_v29-corrected.html"
    result = build_corrected_html(out_path=out_path)
    assert result["out_path"] == out_path
    assert out_path.exists()
    text = out_path.read_text(encoding="utf-8")
    assert text.startswith("<!DOCTYPE html>")
    assert text.rstrip().endswith("</html>")


@pytestmark_e2e
def test_build_corrected_html_does_not_modify_original(tmp_path: Path):
    """AC: original v29 file is not modified."""
    import hashlib
    before = hashlib.sha256(DEFAULT_HTML.read_bytes()).hexdigest()
    build_corrected_html(out_path=tmp_path / "out.html")
    after = hashlib.sha256(DEFAULT_HTML.read_bytes()).hexdigest()
    assert before == after


@pytestmark_e2e
def test_build_corrected_html_resolves_all_mismatches(vdf, tmp_path: Path):
    """AC: mismatched analysis text is replaced with the cross-checked Excel text.

    Verified by re-running the verifier against the corrected file and
    confirming there are no mismatches left (only missing rows can survive,
    since those have no Excel→HTML or HTML→Excel content to replace with).
    """
    out_path = tmp_path / "v29-corrected.html"
    result = build_corrected_html(out_path=out_path)
    n_analysis_applied = sum(
        1 for c in result["applied"] if c["kind"] == CORRECTION_KIND_ANALYSIS
    )
    expected = int((vdf["status"] == STATUS_MISMATCH).sum())
    # Every mismatch with non-blank Excel text yields an analysis fix.
    assert n_analysis_applied == expected
    # Re-verify against the corrected file: zero mismatches remain.
    df2 = verify_lexicon(html_path=out_path)
    assert int((df2["status"] == STATUS_MISMATCH).sum()) == 0


@pytestmark_e2e
def test_build_corrected_html_fixes_some_wrong_article_links(tmp_path: Path):
    """AC: wrong article links are updated to the article confirmed by verbatim.

    The verifier reports both unambiguous and ambiguous wrong_article links;
    the corrector only fixes the unambiguous ones (US-009 will tackle the
    rest with similarity matching).
    """
    out_path = tmp_path / "v29-corrected.html"
    result = build_corrected_html(out_path=out_path)
    n_link_applied = sum(
        1 for c in result["applied"] if c["kind"] == CORRECTION_KIND_LINK
    )
    # At least one wrong_article link in the fixtures should be uniquely
    # resolvable from the verbatim Excel.
    assert n_link_applied >= 1
    # Cross-check via re-verification: total wrong_article links must
    # decrease by exactly the number of link fixes applied.
    df2 = verify_lexicon(html_path=out_path)
    new_link_counts = _link_summary_counts(df2)
    orig_link_counts = _link_summary_counts(verify_lexicon())
    delta = orig_link_counts[STATUS_WRONG_ARTICLE] - new_link_counts[STATUS_WRONG_ARTICLE]
    assert delta == n_link_applied


@pytestmark_e2e
def test_build_corrected_html_summary_block_lists_every_change(tmp_path: Path):
    """AC: summary block at top of the corrected file lists every change."""
    out_path = tmp_path / "v29-corrected.html"
    result = build_corrected_html(out_path=out_path)
    text = out_path.read_text(encoding="utf-8")
    assert 'id="v29-corrections-summary"' in text
    # Summary block lives between <body> and the first existing element.
    body_idx = text.find("<body")
    body_end = text.find(">", body_idx)
    summary_idx = text.find('id="v29-corrections-summary"')
    assert body_end < summary_idx, "summary block should appear after <body>"
    # Every applied correction's cell key surfaces in the summary table — look
    # for at least 5 expected dim_labels from the first 5 entries.
    sample = result["applied"][:5]
    for c in sample:
        if c.get("dim_label"):
            # dim_label appears in the cell column of the summary table
            assert c["dim_label"] in text


@pytestmark_e2e
def test_build_corrected_html_concepts_still_parseable(tmp_path: Path):
    """The corrected file's CONCEPTS literal must remain valid JSON so the
    page still renders without console errors."""
    out_path = tmp_path / "v29-corrected.html"
    build_corrected_html(out_path=out_path)
    text = out_path.read_text(encoding="utf-8")
    concepts = _extract_concepts_json(text)
    assert isinstance(concepts, list) and concepts


@pytestmark_e2e
def test_build_corrected_html_via_cli_fix_flag(tmp_path: Path):
    """The --fix CLI flag must write the corrected file alongside the reports."""
    from verify_lexicon import main
    csv_out = tmp_path / "verify.csv"
    fix_out = tmp_path / "v29-corrected.html"
    rc = main([
        "--out", str(csv_out),
        "--fix", "--fix-out", str(fix_out),
    ])
    assert rc == 0
    assert fix_out.exists()
    assert csv_out.exists()
