"""test_lexicon_v30_autocorrect.py — acceptance tests for US-009.

US-009 auto-corrects the displayed article when an analysis cell has no
verbatim row in the cross-checked Excel. The corrector lives in
``build_v30_autocorrect.py`` and produces:

  1. A JSON island ``<script type="application/json"
     id="v30-autocorrect-data">{...}</script>`` containing
     ``{threshold: float, lookup: {key: correction, ...}}``.
  2. An inline ``<script data-block="us-009">…</script>`` that wraps
     ``window.updateDrawerContent`` and renders a styled popup note
     reading "Article auto-corrected from X to Y" whenever a correction
     applies.

These tests exercise both the build-time logic (similarity, lookup
shape, idempotency, threshold) and the embedded artefact (correct JSON
island, JS hook present, no inline onclick added).
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
HTML = HERE / "digital_lexicon_v30.html"
V29_CORRECTED = HERE / "digital_lexicon_v29-corrected.html"

if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from build_v30_autocorrect import (  # noqa: E402
    DATA_SCRIPT_ID,
    DEFAULT_THRESHOLD,
    DEFAULT_UNRESOLVED_MD,
    LAW_LABEL_PREFIX,
    _blob_articles,
    _format_unresolved_md,
    _key_for_cell,
    _make_label,
    _serialise_lookup,
    best_article_match,
    build_v30_autocorrect,
    compute_autocorrect_lookup,
    compute_unresolved_articles,
    inject_autocorrect_lookup,
    top_n_article_matches,
    write_unresolved_articles_md,
)


def _html() -> str:
    return HTML.read_text(encoding="utf-8")


def _extract_json_island(html: str) -> dict:
    pat = re.compile(
        r'<script type="application/json" id="v30-autocorrect-data">'
        r"(.*?)</script>",
        re.DOTALL,
    )
    m = pat.search(html)
    assert m, "v30-autocorrect-data JSON island not found in HTML"
    body = m.group(1).replace(r"<\/", "</")
    return json.loads(body)


# --------------------------------------------------------------------------- #
# T1.  Pure helpers                                                           #
# --------------------------------------------------------------------------- #

def test_make_label_eu_article():
    assert _make_label("eu-ai-act", "article", "6") == "EU AI Act, Article 6"


def test_make_label_state_section():
    assert _make_label("ca-sb53", "section", "22757.11") == "CA SB 53 §22757.11"
    assert _make_label("co-sb24205", "section", "6-1-1701") == "CO SB 24-205 §6-1-1701"
    assert _make_label("ny-s8828", "section", "1420") == "NY S8828 §1420"


def test_make_label_annex():
    assert _make_label("eu-ai-act", "annex", "III") == "EU AI Act, Annex III"


def test_make_label_unknown_law_falls_back():
    # An unknown law id still produces a sensible label.
    out = _make_label("xx-unknown", "article", "1")
    assert "xx-unknown" in out


def test_key_for_cell_round_trip():
    k = _key_for_cell("incident", "serious-incident", "term-0-0", "ca")
    assert k == "incident|serious-incident|term-0-0|ca"


def test_law_label_prefix_covers_known_laws():
    for law in (
        "eu-ai-act", "ca-sb53", "ca-sb942", "ca-ab2013",
        "co-sb24205", "ny-s8828", "ny-a6453",
        "tx-hb149", "ut-sb226",
    ):
        assert law in LAW_LABEL_PREFIX, f"missing prefix for {law}"


# --------------------------------------------------------------------------- #
# T2.  Similarity scoring                                                     #
# --------------------------------------------------------------------------- #

def test_best_article_match_picks_best_above_threshold():
    articles = [
        {"id": "1", "title": "Subject matter",
         "text": "This regulation lays down rules on AI systems."},
        {"id": "2", "title": "Definitions",
         "text": "Provider means any natural or legal person that "
                 "develops an AI system."},
        {"id": "3", "title": "Penalties",
         "text": "Fines up to thirty-five million euro."},
    ]
    query = "Provider develops or has developed an AI system natural legal person"
    best, score = best_article_match(query, articles, threshold=70.0)
    assert best is not None
    assert best["id"] == "2"
    assert score >= 70.0


def test_best_article_match_returns_none_below_threshold():
    articles = [
        {"id": "1", "title": "Misc",
         "text": "Nothing in common with the query whatsoever."},
    ]
    best, score = best_article_match(
        "AI definitions transparency obligations", articles, threshold=70.0,
    )
    assert best is None


def test_best_article_match_empty_query():
    articles = [{"id": "1", "title": "x", "text": "y"}]
    best, score = best_article_match("", articles, threshold=70.0)
    assert best is None
    assert score == 0.0


def test_best_article_match_empty_articles():
    best, score = best_article_match("query", [], threshold=70.0)
    assert best is None


# --------------------------------------------------------------------------- #
# T3.  Blob article extraction                                                #
# --------------------------------------------------------------------------- #

def test_blob_articles_extracts_articles_sections_annexes():
    blob = {
        "articles": [{"id": "1", "title": "A", "text": "T1"}],
        "sections": [{"id": "100", "title": "B", "text": "T2"}],
        "annexes": [{"id": "I", "title": "C", "text": "T3"}],
    }
    out = _blob_articles(blob)
    kinds = [a["kind"] for a in out]
    ids = [a["id"] for a in out]
    assert kinds == ["article", "section", "annex"]
    assert ids == ["1", "100", "I"]


def test_blob_articles_skips_invalid_entries():
    blob = {
        "articles": [
            {"id": "1", "text": "x"},
            {"title": "no-id"},
            "junk",
            None,
        ],
    }
    out = _blob_articles(blob)
    assert len(out) == 1
    assert out[0]["id"] == "1"


# --------------------------------------------------------------------------- #
# T4.  End-to-end lookup against the real fixtures                            #
# --------------------------------------------------------------------------- #

def test_compute_lookup_returns_at_least_five_corrections():
    """The acceptance test verifies >=5 cells with auto-correct notes — so
    the build step must surface at least that many cells where a better
    article scores above threshold."""
    lookup = compute_autocorrect_lookup(threshold=DEFAULT_THRESHOLD)
    assert len(lookup) >= 5, (
        f"only {len(lookup)} corrections produced; acceptance requires >=5"
    )


def test_lookup_entries_have_required_fields():
    lookup = compute_autocorrect_lookup(threshold=DEFAULT_THRESHOLD)
    assert lookup, "empty lookup — nothing to validate"
    for k, v in lookup.items():
        # Composite key shape: cid|sid|dim_id|jid
        assert k.count("|") == 3, f"bad key shape: {k}"
        for field in (
            "from_anchor", "from_label",
            "to_anchor", "to_label",
            "law", "kind", "score",
        ):
            assert field in v, f"correction {k} missing {field}"
        # to != from (corrections only).
        assert v["from_anchor"] != v["to_anchor"], (
            f"correction {k} is a no-op (from == to)"
        )
        # Score above threshold.
        assert v["score"] >= DEFAULT_THRESHOLD


def test_higher_threshold_prunes_lookup():
    """Bumping the threshold should monotonically reduce (or equal) the
    number of corrections — never increase it."""
    base = compute_autocorrect_lookup(threshold=DEFAULT_THRESHOLD)
    strict = compute_autocorrect_lookup(threshold=95.0)
    assert len(strict) <= len(base)
    # Every strict correction is also in base (with the same to_anchor).
    for k, v in strict.items():
        assert k in base
        assert base[k]["to_anchor"] == v["to_anchor"]


# --------------------------------------------------------------------------- #
# T5.  HTML injection                                                         #
# --------------------------------------------------------------------------- #

def test_v30_html_has_autocorrect_data_island():
    payload = _extract_json_island(_html())
    assert "threshold" in payload
    assert "lookup" in payload
    assert isinstance(payload["lookup"], dict)
    assert payload["threshold"] == DEFAULT_THRESHOLD


def test_v30_html_has_at_least_five_corrections_inlined():
    payload = _extract_json_island(_html())
    assert len(payload["lookup"]) >= 5


def test_v30_html_contains_us009_js_block():
    html = _html()
    assert '<script data-block="us-009">' in html
    assert "__v30_autocorrect_patched" in html
    assert "v30-autocorrect-note" in html


def test_v30_html_us009_does_not_use_title_attribute_for_popup():
    """Acceptance: the inline note uses a styled custom popup, NOT the
    native title attribute."""
    html = _html()
    # The note element must not carry a title="…" attribute for its
    # "auto-corrected" message — instead the popup is built with a
    # dedicated `.v30-autocorrect-popup` element.
    pat = re.compile(
        r'class="v30-autocorrect-note"[^>]*\stitle=', re.IGNORECASE,
    )
    assert not pat.search(html), (
        "US-009 inline note uses a native title attribute — should be "
        "a styled custom popup instead."
    )
    # And the styled popup class must exist and be CSS-styled.
    assert "v30-autocorrect-popup" in html


def test_v30_html_us009_does_not_add_new_inline_onclick():
    """US-009 must not add new inline onclick handlers — event delegation
    or addEventListener only. Compare against v29-corrected baseline."""
    base = V29_CORRECTED.read_text(encoding="utf-8")
    v30 = _html()
    assert v30.count("onclick=") == base.count("onclick="), (
        "US-009 added new inline onclick handlers — use addEventListener."
    )


def test_v30_html_us009_styled_note_has_custom_styling():
    html = _html()
    # The note's CSS rule must define a background colour.
    m = re.search(
        r"\.v30-autocorrect-note\s*\{([^}]*)\}",
        html,
        re.DOTALL,
    )
    assert m, ".v30-autocorrect-note CSS rule missing"
    body = m.group(1).lower()
    assert "background" in body
    assert "border" in body


def test_v30_html_lookup_key_round_trips_via_js_keys():
    """The JS uses ``cid|sid|dim_id|jid`` keys — make sure the inlined
    JSON uses the same shape."""
    payload = _extract_json_island(_html())
    for key in payload["lookup"].keys():
        parts = key.split("|")
        assert len(parts) == 4, f"unexpected key shape: {key!r}"


# --------------------------------------------------------------------------- #
# T6.  Idempotency                                                            #
# --------------------------------------------------------------------------- #

def test_inject_is_idempotent(tmp_path):
    """Running the build twice produces the same final HTML — the
    injection strips any prior block before re-inserting."""
    src = HTML.read_text(encoding="utf-8")
    target = tmp_path / "v30.html"
    target.write_text(src, encoding="utf-8")
    lookup = {
        "x|y|z|eu": {
            "from_anchor": "1", "from_label": "EU AI Act, Article 1",
            "to_anchor": "2", "to_label": "EU AI Act, Article 2",
            "law": "eu-ai-act", "kind": "article", "score": 90.0,
        },
    }
    inject_autocorrect_lookup(lookup, html_path=target, out_path=target)
    after_first = target.read_text(encoding="utf-8")
    inject_autocorrect_lookup(lookup, html_path=target, out_path=target)
    after_second = target.read_text(encoding="utf-8")
    assert after_first == after_second, (
        "re-running the injection changes the file — the strip-and-replace "
        "step is not idempotent."
    )
    # Only one JSON island.
    assert after_second.count('id="v30-autocorrect-data"') == 1
    # Only one US-009 JS block.
    assert after_second.count('<script data-block="us-009">') == 1


# --------------------------------------------------------------------------- #
# T7.  Build CLI orchestration                                                #
# --------------------------------------------------------------------------- #

def test_build_v30_autocorrect_writes_to_target(tmp_path):
    """build_v30_autocorrect computes + injects in one call, returning
    both the lookup and the written path."""
    src = HTML.read_text(encoding="utf-8")
    target = tmp_path / "out.html"
    # Strip any existing US-009 block to test from a clean baseline.
    src_clean = re.sub(
        r'<script type="application/json" id="v30-autocorrect-data">'
        r".*?</script>\n?",
        "",
        src,
        flags=re.DOTALL,
    )
    src_clean = re.sub(
        r'<style data-block="us-009">.*?</style>\s*'
        r'<script data-block="us-009">.*?</script>\n?',
        "",
        src_clean,
        flags=re.DOTALL,
    )
    baseline = tmp_path / "v30_baseline.html"
    baseline.write_text(src_clean, encoding="utf-8")
    result = build_v30_autocorrect(
        threshold=DEFAULT_THRESHOLD,
        html_path=baseline,
        out_path=target,
    )
    assert result["out_path"] == target
    assert target.exists()
    written = target.read_text(encoding="utf-8")
    assert 'id="v30-autocorrect-data"' in written
    assert '<script data-block="us-009">' in written
    # Lookup is non-empty against real fixtures.
    assert len(result["lookup"]) >= 5


# --------------------------------------------------------------------------- #
# T8.  JSON serialisation script-breakout safety                              #
# --------------------------------------------------------------------------- #

def test_serialise_escapes_closing_script_tags():
    """A label or analysis containing a literal ``</script>`` must be
    escaped so the browser HTML tokenizer cannot terminate the script
    element early."""
    payload_lookup = {
        "k|k|k|eu": {
            "from_anchor": "1",
            "from_label": "Article 1 with </script> nasty tag",
            "to_anchor": "2",
            "to_label": "Article 2",
            "law": "eu-ai-act", "kind": "article", "score": 90.0,
        }
    }
    body = _serialise_lookup(payload_lookup, threshold=70.0)
    # The literal sequence "</" must not appear unescaped.
    assert "</" not in body
    assert "<\\/script>" in body
    # And the JSON still parses (after un-escaping).
    parsed = json.loads(body.replace(r"<\/", "</"))
    assert parsed["threshold"] == 70.0
    assert "k|k|k|eu" in parsed["lookup"]


# --------------------------------------------------------------------------- #
# T9.  v29-corrected baseline still untouched up to its </body>               #
# --------------------------------------------------------------------------- #

def test_v30_prefix_matches_v29_corrected_through_body():
    """Append-only contract: every byte of v29-corrected up to its final
    ``</body>`` is still present in v30. US-009 (and US-008) only added
    content, never modified the baseline."""
    v30_bytes = HTML.read_bytes()
    base_bytes = V29_CORRECTED.read_bytes()
    end_body = base_bytes.rfind(b"</body>")
    assert end_body != -1
    assert v30_bytes[:end_body] == base_bytes[:end_body], (
        "v30 prefix diverges from v29-corrected — US-008/US-009 must be "
        "append-only."
    )


# --------------------------------------------------------------------------- #
# T10. JS hook installs as a wrapper, not a replacement                       #
# --------------------------------------------------------------------------- #

def test_us009_js_wraps_update_drawer_content():
    html = _html()
    # The wrapper captures the prior updateDrawerContent and reinstalls
    # itself — we MUST chain after v29 (article render) and US-008
    # (verbatim highlight), not replace them.
    assert (
        "var orig = window.updateDrawerContent;" in html
    ), "US-009 wrapper does not capture prior updateDrawerContent"
    # The flag prevents double-installation across the defensive
    # setTimeout retries.
    assert "window[FLAG] = true;" in html or "__v30_autocorrect_patched" in html


def test_us009_register_synthetic_refs():
    html = _html()
    # We register synthetic REF_MAP entries so the corrected to_label
    # resolves through the existing v29 article-render pipeline.
    assert "_registerSyntheticRefs" in html
    assert "window.REF_MAP" in html


# --------------------------------------------------------------------------- #
# US-010 — unresolved-articles markdown log                                   #
# --------------------------------------------------------------------------- #

def test_top_n_article_matches_returns_ranked_top_n():
    articles = [
        {"id": "1", "title": "Subject matter",
         "text": "Lays down rules on AI systems."},
        {"id": "2", "title": "Definitions",
         "text": "Provider develops AI systems for natural and legal persons."},
        {"id": "3", "title": "Penalties",
         "text": "Fines up to thirty-five million euro."},
        {"id": "4", "title": "Misc",
         "text": "Unrelated topic."},
    ]
    top = top_n_article_matches(
        "provider develops AI systems natural legal persons",
        articles,
        n=3,
    )
    assert len(top) == 3
    # Sorted descending by score.
    scores = [s for (_, s) in top]
    assert scores == sorted(scores, reverse=True)
    # The most relevant article ranks first.
    assert top[0][0]["id"] == "2"


def test_top_n_article_matches_handles_empty():
    assert top_n_article_matches("", [{"id": "1", "title": "a", "text": "b"}], n=3) == []
    assert top_n_article_matches("query", [], n=3) == []
    assert top_n_article_matches("query", [{"id": "1", "title": "a", "text": "b"}], n=0) == []


def test_compute_unresolved_articles_yields_entries_at_higher_threshold():
    """At a strict threshold, cells that previously auto-corrected fall
    through to the unresolved log."""
    base = compute_autocorrect_lookup(threshold=DEFAULT_THRESHOLD)
    assert len(base) >= 5
    strict_unresolved = compute_unresolved_articles(threshold=99.0)
    # Strict threshold turns most no_verbatim cells into unresolved entries.
    assert len(strict_unresolved) >= 1


def test_compute_unresolved_articles_excludes_corrected_cells():
    """Cells the lookup *did* correct must not also appear in the
    unresolved list — they were resolved, not unresolved."""
    threshold = DEFAULT_THRESHOLD
    lookup = compute_autocorrect_lookup(threshold=threshold)
    unresolved = compute_unresolved_articles(threshold=threshold)
    lookup_keys = set(lookup.keys())
    unresolved_keys = {
        f"{r['cid']}|{r['sid']}|{r['dim_id']}|{r['jid']}"
        for r in unresolved
    }
    assert not (lookup_keys & unresolved_keys), (
        "a cell appears in BOTH the auto-correct lookup and the "
        "unresolved log — they must be disjoint sets."
    )


def test_compute_unresolved_articles_entries_have_required_fields():
    unresolved = compute_unresolved_articles(threshold=DEFAULT_THRESHOLD)
    if not unresolved:
        pytest.skip("no unresolved cells in current snapshot")
    for rec in unresolved:
        for field in ("cid", "sid", "dim_id", "jid", "term", "law_id",
                      "from_label", "best_score", "candidates"):
            assert field in rec, f"missing {field} in {rec}"
        # Up to top 3 candidates, each with the right shape.
        assert 1 <= len(rec["candidates"]) <= 3
        for c in rec["candidates"]:
            for field in ("to_label", "to_anchor", "kind", "score"):
                assert field in c
        # best_score < threshold (otherwise it'd have been auto-corrected
        # or phantom-skipped — neither belongs here).
        assert rec["best_score"] < DEFAULT_THRESHOLD


def test_compute_unresolved_articles_empty_at_zero_threshold():
    """At threshold=0 every match is confident, so nothing is unresolved."""
    unresolved = compute_unresolved_articles(threshold=0.0)
    assert unresolved == []


def test_format_unresolved_md_empty_says_no_unresolved():
    body = _format_unresolved_md(
        [], threshold=70.0,
        generated_at=datetime(2026, 5, 1, 12, 0, 0),
    )
    assert "No unresolved articles." in body
    assert "# v30 Unresolved Articles" in body
    # File must NOT be empty even when there are no entries.
    assert body.strip() != ""


def test_format_unresolved_md_includes_required_fields_per_entry():
    rec = {
        "cid": "incident",
        "sid": "serious-incident",
        "dim_id": "term-0-0",
        "jid": "ca",
        "term": "Critical safety incident",
        "dim_label": "Term",
        "law_id": "ca-sb53",
        "from_label": "CA SB 53 §22757.11(d)",
        "best_score": 60.5,
        "candidates": [
            {"to_label": "CA SB 53 §22757.13", "to_anchor": "22757.13",
             "kind": "section", "score": 60.5},
            {"to_label": "CA SB 53 §22757.12", "to_anchor": "22757.12",
             "kind": "section", "score": 55.0},
            {"to_label": "CA SB 53 §22757.11", "to_anchor": "22757.11",
             "kind": "section", "score": 40.1},
        ],
    }
    body = _format_unresolved_md(
        [rec], threshold=70.0,
        generated_at=datetime(2026, 5, 1, 12, 0, 0),
    )
    # AC: term, linked law, originally selected article, top 3 candidates.
    assert "Critical safety incident" in body
    assert "ca-sb53" in body
    assert "CA SB 53 §22757.11(d)" in body
    assert "CA SB 53 §22757.13" in body
    assert "CA SB 53 §22757.12" in body
    assert "CA SB 53 §22757.11" in body
    # Scores rendered.
    assert "60.5" in body
    # Timestamp header present.
    assert "Generated 2026-05-01 12:00:00 UTC" in body


def test_format_unresolved_md_truncates_to_top_3():
    """Even if more than 3 candidates are passed in, the rendered list
    shows only the top 3 (the build helper requests top_n=3 anyway, but
    the formatter must enforce the cap defensively)."""
    rec = {
        "cid": "x", "sid": "y", "dim_id": "z", "jid": "eu",
        "term": "T", "dim_label": "", "law_id": "eu-ai-act",
        "from_label": "Article 1",
        "best_score": 50.0,
        "candidates": [
            {"to_label": f"Article {i}", "to_anchor": str(i),
             "kind": "article", "score": 50.0 - i}
            for i in range(1, 8)
        ],
    }
    body = _format_unresolved_md(
        [rec], threshold=70.0,
        generated_at=datetime(2026, 5, 1, 12, 0, 0),
    )
    # First three candidates rendered.
    for i in range(1, 4):
        assert f"Article {i}" in body
    # Fourth and beyond NOT rendered.
    assert "Article 5" not in body
    assert "Article 6" not in body
    assert "Article 7" not in body


def test_write_unresolved_articles_md_empty_writes_non_empty_file(tmp_path):
    target = tmp_path / "v30_unresolved_articles.md"
    out = write_unresolved_articles_md([], out_path=target, threshold=65.0)
    assert out == target
    assert target.exists()
    body = target.read_text(encoding="utf-8")
    assert body.strip() != "", "empty file produced when there are no entries"
    assert "No unresolved articles." in body
    assert "# v30 Unresolved Articles" in body
    # Header is timestamped.
    assert "Generated " in body and "UTC" in body


def test_write_unresolved_articles_md_overwrites(tmp_path):
    target = tmp_path / "v30_unresolved_articles.md"
    target.write_text("STALE OLD CONTENT", encoding="utf-8")
    write_unresolved_articles_md([], out_path=target, threshold=65.0)
    assert "STALE OLD CONTENT" not in target.read_text(encoding="utf-8")


def test_write_unresolved_articles_md_creates_parent(tmp_path):
    target = tmp_path / "nested" / "dir" / "v30_unresolved_articles.md"
    write_unresolved_articles_md([], out_path=target, threshold=65.0)
    assert target.exists()


def test_write_unresolved_articles_md_uses_provided_timestamp(tmp_path):
    target = tmp_path / "log.md"
    write_unresolved_articles_md(
        [], out_path=target, threshold=65.0,
        generated_at=datetime(2030, 1, 2, 3, 4, 5),
    )
    body = target.read_text(encoding="utf-8")
    assert "2030-01-02 03:04:05 UTC" in body


def test_default_unresolved_md_path_under_outputs():
    """The default output path is ``outputs/v30_unresolved_articles.md``
    under the project root — that's the path the AC pins."""
    assert DEFAULT_UNRESOLVED_MD.name == "v30_unresolved_articles.md"
    assert DEFAULT_UNRESOLVED_MD.parent.name == "outputs"


def test_build_v30_autocorrect_writes_unresolved_md(tmp_path):
    src = HTML.read_text(encoding="utf-8")
    target = tmp_path / "out.html"
    src_clean = re.sub(
        r'<script type="application/json" id="v30-autocorrect-data">'
        r".*?</script>\n?",
        "",
        src,
        flags=re.DOTALL,
    )
    src_clean = re.sub(
        r'<style data-block="us-009">.*?</style>\s*'
        r'<script data-block="us-009">.*?</script>\n?',
        "",
        src_clean,
        flags=re.DOTALL,
    )
    baseline = tmp_path / "v30_baseline.html"
    baseline.write_text(src_clean, encoding="utf-8")
    md_target = tmp_path / "v30_unresolved_articles.md"
    result = build_v30_autocorrect(
        threshold=DEFAULT_THRESHOLD,
        html_path=baseline,
        out_path=target,
        unresolved_md_path=md_target,
    )
    assert result["unresolved_md_path"] == md_target
    assert md_target.exists()
    assert "unresolved" in result
    assert isinstance(result["unresolved"], list)
    body = md_target.read_text(encoding="utf-8")
    # Either no entries (and the safety message), or at least one heading.
    assert body.strip() != ""
    if result["unresolved"]:
        assert "## 1." in body
    else:
        assert "No unresolved articles." in body


def test_build_v30_autocorrect_skips_md_when_path_is_false(tmp_path):
    src = HTML.read_text(encoding="utf-8")
    target = tmp_path / "out.html"
    baseline = tmp_path / "v30_baseline.html"
    baseline.write_text(src, encoding="utf-8")
    result = build_v30_autocorrect(
        threshold=DEFAULT_THRESHOLD,
        html_path=baseline,
        out_path=target,
        unresolved_md_path=False,
    )
    assert result["unresolved_md_path"] is None
    # No new file was written under tmp_path beyond `target`.
    assert not (tmp_path / "v30_unresolved_articles.md").exists()


def test_build_main_cli_writes_unresolved_md(tmp_path, monkeypatch):
    """End-to-end CLI: --unresolved-md writes the log file."""
    from build_v30_autocorrect import main as build_main

    src = HTML.read_text(encoding="utf-8")
    baseline = tmp_path / "v30_baseline.html"
    baseline.write_text(src, encoding="utf-8")
    target = tmp_path / "out.html"
    md_target = tmp_path / "log.md"
    rc = build_main([
        "--html", str(baseline),
        "--out", str(target),
        "--unresolved-md", str(md_target),
        "--threshold", str(DEFAULT_THRESHOLD),
    ])
    assert rc == 0
    assert md_target.exists()
    assert md_target.stat().st_size > 0
    body = md_target.read_text(encoding="utf-8")
    assert "# v30 Unresolved Articles" in body


# --------------------------------------------------------------------------- #
# Standalone runner                                                           #
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
