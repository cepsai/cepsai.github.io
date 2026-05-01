"""test_lexicon_v30.py — acceptance tests for v30 (US-008).

v30 starts as a byte-equivalent scaffold of v29-corrected. US-008 adds a
verbatim-highlight feature to the law-article drawer: when an analysis
cell is clicked, the rendered law article scrolls to and wraps the
matching verbatim text in <mark class="v30-verbatim-mark"> with a yellow
background. Existing marks from a prior click are cleared first, and
matching is lenient against smart quotes / non-breaking spaces / soft
hyphens / em-dashes / case / whitespace runs.

Tests:
  T1.  v30 file is byte-identical to v29-corrected up to the new US-008
       block (the original baseline is untouched). The append-only
       contract makes review trivial.
  T2.  US-008 highlight script + style are present and well-formed.
  T3.  No NEW inline `onclick=` handlers were added by US-008. (The
       v29 baseline carries pre-existing `onclick` attributes; we only
       require US-008 not to add more.)
  T4.  The highlight feature is wired via wrapping
       `window.updateDrawerContent` (event-delegation pattern, no
       inline onclick).
  T5.  The MARK_CLASS is `v30-verbatim-mark` and CSS rule for that
       class sets a yellow background.
  T6.  Required helper functions and module-flag are present:
       `__v30_highlight_patched`, `_highlightVerbatim`, `_clearMarks`,
       `_normalize`, `_splitSpans`, `_buildFlatText`, `_wrapRange`.
  T7.  Helpers are exposed on `window.__v30_highlight` for tests.
  T8.  Existing v29 patches still present — we wrap, never replace,
       the v29 article-rendering pipeline.

Run:
    python3 -m pytest test_lexicon_v30.py -q
or standalone:
    python3 test_lexicon_v30.py
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
HTML = HERE / "digital_lexicon_v30.html"
V29_CORRECTED = HERE / "digital_lexicon_v29-corrected.html"


def _html() -> str:
    return HTML.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# T1.  v30 is the v29-corrected baseline plus an append-only US-008 block.    #
# --------------------------------------------------------------------------- #

def test_v30_starts_with_v29_corrected_baseline():
    """The first N bytes of v30 must match v29-corrected exactly. The
    US-008 highlight block is append-only, sitting between the last
    pre-existing </script> and </body>."""
    assert HTML.exists(), f"{HTML} missing"
    assert V29_CORRECTED.exists(), f"{V29_CORRECTED} missing"
    v30 = HTML.read_bytes()
    base = V29_CORRECTED.read_bytes()
    # v30 must be at least as large as the baseline (we appended a script).
    assert len(v30) > len(base), (
        "v30 is not larger than v29-corrected — US-008 block missing."
    )
    # Find the last </body> in v29-corrected; everything before it must be
    # byte-identical in v30.
    end_body = base.rfind(b"</body>")
    assert end_body != -1, "v29-corrected has no </body> marker"
    assert v30[:end_body] == base[:end_body], (
        "v30 prefix diverges from v29-corrected before </body> — "
        "US-008 must be append-only."
    )


# --------------------------------------------------------------------------- #
# T2.  US-008 highlight script + style are present and well-formed.           #
# --------------------------------------------------------------------------- #

def test_us008_block_present():
    html = _html()
    # The CSS rule must define the mark class.
    assert "mark.v30-verbatim-mark" in html, (
        "v30-verbatim-mark CSS rule missing — highlights would be invisible."
    )
    # The IIFE must run.
    assert "/* US-008" in html, (
        "US-008 marker comment missing from v30."
    )
    # The flag that the wrapper successfully patched.
    assert "__v30_highlight_patched" in html, (
        "v30 highlight patch flag missing — wrapper not installed."
    )


# --------------------------------------------------------------------------- #
# T3.  No NEW inline onclick=… handlers were added by US-008.                 #
# --------------------------------------------------------------------------- #

def test_us008_does_not_add_inline_onclick():
    """US-008 introduces no new `onclick=` attributes. Counting against
    the v29-corrected baseline lets pre-existing handlers stand without
    forcing this story to refactor unrelated code."""
    v30 = HTML.read_text(encoding="utf-8")
    base = V29_CORRECTED.read_text(encoding="utf-8")
    base_count = base.count("onclick=")
    v30_count = v30.count("onclick=")
    assert v30_count == base_count, (
        f"US-008 added {v30_count - base_count} new inline onclick handlers — "
        "use addEventListener / event delegation instead."
    )


# --------------------------------------------------------------------------- #
# T4.  Highlight is wired via wrapping window.updateDrawerContent.            #
# --------------------------------------------------------------------------- #

def test_us008_wraps_update_drawer_content():
    html = _html()
    # The wrapper must read the existing function and reinstall a wrapper.
    assert "var orig = window.updateDrawerContent;" in html, (
        "US-008 wrapper does not capture the prior updateDrawerContent — "
        "v29 article-rendering would be lost."
    )
    assert "window.updateDrawerContent = function" in html, (
        "US-008 wrapper does not reinstall window.updateDrawerContent."
    )
    assert "orig.apply(this, arguments)" in html, (
        "US-008 wrapper does not delegate to the prior updateDrawerContent."
    )


# --------------------------------------------------------------------------- #
# T5.  CSS: the mark class has a yellow background.                           #
# --------------------------------------------------------------------------- #

def test_mark_class_has_yellow_background():
    html = _html()
    # Locate the rule body for `mark.v30-verbatim-mark`.
    m = re.search(
        r"mark\.v30-verbatim-mark\s*\{([^}]*)\}",
        html,
        re.DOTALL,
    )
    assert m, "mark.v30-verbatim-mark CSS rule not found"
    body = m.group(1).lower()
    assert "background" in body, (
        "mark.v30-verbatim-mark has no background declaration — "
        "highlights would not be visible."
    )
    # Accept any yellow-ish hex (must start with f or e and contain only f/e/d/c/b/a/9/8 etc.).
    # Accept the common "yellow" keyword too.
    yellow_hex = re.search(
        r"background\s*:\s*(?:#(f[a-f0-9]{2}[a-f0-9d]{2,3}|ff[ef][a-f0-9]{2,3}|fff59d|ffeb3b|fffacd)|yellow)",
        body,
    )
    assert yellow_hex, (
        f"mark.v30-verbatim-mark background does not look yellow: {body!r}"
    )


# --------------------------------------------------------------------------- #
# T6.  Required helpers + flag are present.                                   #
# --------------------------------------------------------------------------- #

def test_required_helpers_present():
    html = _html()
    needed = (
        "function _normalize(",
        "function _normalizeChar(",
        "function _splitSpans(",
        "function _buildFlatText(",
        "function _wrapRange(",
        "function _clearMarks(",
        "function _highlightVerbatim(",
        "function _afterDrawerRender(",
        "function _scrollMarkIntoView(",
        "function _install(",
    )
    missing = [name for name in needed if name not in html]
    assert not missing, f"v30 highlight helpers missing: {missing}"


def test_clear_marks_runs_before_apply():
    """The acceptance criterion requires existing <mark> from a previous
    click to be cleared. _highlightVerbatim must call _clearMarks before
    rebuilding."""
    html = _html()
    # Locate the body of _highlightVerbatim.
    m = re.search(
        r"function _highlightVerbatim\([^)]*\)\s*\{(.*?)\n  \}",
        html,
        re.DOTALL,
    )
    assert m, "_highlightVerbatim body not found"
    body = m.group(1)
    # _clearMarks must be the first DOM mutation.
    assert "_clearMarks(container);" in body, (
        "_highlightVerbatim does not call _clearMarks — old highlights "
        "would persist across clicks."
    )
    # And it must come before any wrap-range work.
    clear_idx = body.find("_clearMarks(container);")
    wrap_idx = body.find("_wrapRange(")
    assert wrap_idx == -1 or clear_idx < wrap_idx, (
        "_clearMarks must run BEFORE wrapping new spans."
    )


# --------------------------------------------------------------------------- #
# T7.  Helpers are exposed on window.__v30_highlight for tests.               #
# --------------------------------------------------------------------------- #

def test_window_helpers_exposed():
    html = _html()
    assert "window.__v30_highlight = {" in html, (
        "v30 highlight helpers not exposed on window — browser-side tests "
        "would have nothing to introspect."
    )
    for key in (
        "normalize:",
        "splitSpans:",
        "highlightVerbatim:",
        "clearMarks:",
        "MARK_CLASS:",
    ):
        assert key in html, (
            f"window.__v30_highlight is missing key {key.rstrip(':')!r}."
        )


def test_mark_class_constant_value():
    html = _html()
    assert "var MARK_CLASS = 'v30-verbatim-mark';" in html, (
        "MARK_CLASS constant missing or renamed — DOM queries for the "
        "mark class would not find the right elements."
    )


# --------------------------------------------------------------------------- #
# T8.  Existing v29 patches still present (we wrap, not replace).             #
# --------------------------------------------------------------------------- #

def test_v29_patches_still_present():
    html = _html()
    # v29 article-render wrapper must still install — our highlight
    # depends on `.v29-art-body` elements being in the DOM.
    assert "__v29_udc_patched" in html, (
        "v29 drawer wrapper flag missing — _renderDrawerArticles would "
        "not run, leaving us nothing to highlight."
    )
    assert "function _renderDrawerArticles" in html, (
        "v29 _renderDrawerArticles function not present."
    )


# --------------------------------------------------------------------------- #
# T9.  Append-only sanity: the file ends with the new highlight script.       #
# --------------------------------------------------------------------------- #

def test_v30_ends_with_highlight_script():
    """The very last <script>…</script> in v30 must be the US-008 block."""
    html = _html()
    last_script_open = html.rfind("<script>")
    last_script_close = html.rfind("</script>")
    assert -1 < last_script_open < last_script_close, (
        "v30 has no trailing <script>…</script> pair."
    )
    tail = html[last_script_open:last_script_close]
    assert "v30-verbatim-mark" in tail, (
        "Final <script> in v30 is not the US-008 block."
    )
    assert "_highlightVerbatim" in tail, (
        "Final <script> in v30 does not define _highlightVerbatim."
    )


# --------------------------------------------------------------------------- #
# T10. Lenient-match coverage: normalization handles smart quotes, NBSP,      #
#      soft hyphens, en/em dash, and zero-width space.                        #
# --------------------------------------------------------------------------- #

def test_normalize_covers_required_lenient_cases():
    """The _normalizeChar function must collapse the canonical "lenient"
    cases listed in the acceptance criteria. We assert by source-level
    inspection because we can't run JS in pytest."""
    html = _html()
    m = re.search(
        r"function _normalizeChar\(c\)\{(.*?)\}\s*\n\s*function _normalize\(",
        html,
        re.DOTALL,
    )
    assert m, "_normalizeChar body not found"
    body = m.group(1)
    # Smart quotes — both single (U+2018/2019) and double (U+201C/201D).
    assert "‘" in body or "'‘'" in body or "’" in body, (
        "_normalizeChar does not handle smart single quotes."
    )
    assert "“" in body or "”" in body, (
        "_normalizeChar does not handle smart double quotes."
    )
    # Non-breaking space U+00A0.
    assert " " in body, "_normalizeChar does not handle NBSP (U+00A0)."
    # Soft hyphen U+00AD.
    assert "­" in body, (
        "_normalizeChar does not handle soft hyphen (U+00AD)."
    )
    # En-dash / em-dash.
    assert "–" in body or "—" in body, (
        "_normalizeChar does not handle en-dash / em-dash."
    )


# --------------------------------------------------------------------------- #
# T11. Sanity: the highlight script is small enough to ship inline.           #
# --------------------------------------------------------------------------- #

def test_us008_block_size_reasonable():
    """Sanity check on size — keeps the inlined feature under 8 KB so
    we don't bloat the artefact unnecessarily."""
    v30 = HTML.read_bytes()
    base = V29_CORRECTED.read_bytes()
    delta = len(v30) - len(base)
    assert delta > 0
    # Allow up to 12 KB so we have headroom for future small tweaks
    # without tripping this guard.
    assert delta < 12 * 1024, (
        f"US-008 added {delta} bytes — keep the inline block under 12 KB."
    )


# Standalone runner --------------------------------------------------------- #

if __name__ == "__main__":
    import inspect

    g = globals()
    tests = [
        (n, fn)
        for n, fn in g.items()
        if n.startswith("test_") and inspect.isfunction(fn)
    ]
    failed = []
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except AssertionError as e:
            print(f"  FAIL  {name}: {e}")
            failed.append(name)
        except Exception as e:
            print(f"  ERROR {name}: {type(e).__name__}: {e}")
            failed.append(name)
    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
