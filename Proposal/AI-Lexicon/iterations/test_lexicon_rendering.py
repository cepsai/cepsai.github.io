"""test_lexicon_rendering.py — headless-browser smoke test.

Complements `test_lexicon_correspondence.py` (which checks the JSON data).
This test loads the built HTML in a real browser and asserts the rendered
DOM matches what we expect. Catches class of regressions the data-only
tests miss: IIFE scope bugs, init-order bugs, CSS display: none, broken
event handlers, etc.

Uses the gstack `browse` binary if present (no extra dependencies).
Skips gracefully if the binary isn't installed.

Run:
    python3 test_lexicon_rendering.py
    python3 -m pytest test_lexicon_rendering.py -q
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
HTML = HERE / "digital_lexicon_v16.html"

BROWSE = None
for candidate in (
    Path.home() / ".claude/skills/gstack/browse/dist/browse",
    HERE.parent.parent.parent / ".claude/skills/gstack/browse/dist/browse",
):
    if candidate.is_file() and os.access(candidate, os.X_OK):
        BROWSE = str(candidate)
        break


# ------------------------- helpers -------------------------------------- #

def _browse(*args: str, timeout: int = 15) -> str:
    res = subprocess.run(
        [BROWSE, *args],
        capture_output=True,
        timeout=timeout,
        text=True,
        cwd=str(HERE),
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"browse {' '.join(args)} failed (rc={res.returncode}): "
            f"{res.stderr.strip()[:400]}"
        )
    return res.stdout


def _start_http_server() -> tuple[subprocess.Popen, int]:
    """browse blocks file:// URLs, so serve the iterations folder locally."""
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=str(HERE),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # wait for it to start
    import urllib.request

    for _ in range(20):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1).read()
            return proc, port
        except Exception:
            time.sleep(0.1)
    proc.kill()
    raise RuntimeError("local http server never came up")


def _read_concepts() -> list[dict]:
    """Pull CONCEPTS from the built HTML so we know which sub-tabs to test."""
    html = HTML.read_text(encoding="utf-8")
    i = html.index("const CONCEPTS")
    i = html.index("=", i) + 1
    while html[i] not in "[{":
        i += 1
    opener = html[i]
    closer = "]" if opener == "[" else "}"
    depth = 0
    in_str = False
    esc = False
    j = i
    while j < len(html):
        c = html[j]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == opener:
                depth += 1
            elif c == closer:
                depth -= 1
                if depth == 0:
                    return json.loads(html[i : j + 1])
        j += 1
    return []


# ------------------------- tests ---------------------------------------- #

def test_deep_link_renders_notes():
    """For every sub_concept that has interpretative notes in its JSON,
    deep-link into it via `#<sub_id>` and assert the #ceps-notes panel
    renders non-empty text that includes a substring of the JSON note.

    Regression for: v16 IIFE scope bug (notes attached in JSON but panel
    stayed blank because renderRichNotes wasn't on window)."""
    if BROWSE is None:
        print("  skip (gstack browse binary not found)", file=sys.stderr)
        return

    concepts = _read_concepts()
    expected: list[tuple[str, str, str]] = []  # (sub_id, title, note_excerpt)
    for c in concepts:
        for sc in c.get("sub_concepts") or []:
            notes = sc.get("ceps_notes_rich") or []
            if not notes:
                continue
            plain = "".join(r.get("t", "") for r in notes[0].get("body_runs") or [])
            excerpt = plain.strip()[:40]
            if len(excerpt) >= 10:
                expected.append((sc["id"], sc["title"], excerpt))

    if not expected:
        raise AssertionError("no sub_concepts with notes found in CONCEPTS")

    server, port = _start_http_server()
    failures: list[str] = []
    try:
        # Warm up the browse server once.
        _browse("goto", f"http://127.0.0.1:{port}/digital_lexicon_v16.html")
        _browse("wait", "--load")
        base = f"http://127.0.0.1:{port}/digital_lexicon_v16.html"
        for sub_id, title, excerpt in expected:
            # Bounce through the server root so the fragment change causes a
            # full document reload (same-document #hash changes don't fire
            # the page-load handlers under browse's headless session).
            _browse("goto", f"http://127.0.0.1:{port}/")
            _browse("goto", f"{base}#{sub_id}")
            _browse("wait", "--load")
            # Poll up to 3s for the hash router + renderConceptPage to run.
            active = ""
            notes_text = ""
            for _ in range(15):
                time.sleep(0.2)
                active = _browse(
                    "js",
                    "document.querySelector('.sub-tab.active')?.textContent || ''",
                ).strip()
                if active == title:
                    break
            notes_text = _browse(
                "js",
                "document.getElementById('ceps-notes')?.textContent || ''",
            ).strip()
            if active != title:
                failures.append(
                    f"{sub_id}: wrong active sub-tab. got={active!r} want={title!r}"
                )
            elif excerpt.lower() not in notes_text.lower():
                failures.append(
                    f"{sub_id}: notes panel did not include {excerpt!r}. "
                    f"got={notes_text[:120]!r}"
                )
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()

    assert not failures, (
        f"{len(failures)}/{len(expected)} sub-concepts failed to render notes.\n"
        + "\n".join(failures[:5])
    )


def test_pill_click_opens_drawer_with_content():
    """Clicking an analysis-cell pill should open the drawer with the
    verbatim text for that jurisdiction + dimension. Regression for: a
    change that moves openDrawer out of scope or disconnects the click
    handlers from the cell spans."""
    if BROWSE is None:
        print("  skip (gstack browse binary not found)", file=sys.stderr)
        return
    server, port = _start_http_server()
    try:
        _browse("goto", f"http://127.0.0.1:{port}/digital_lexicon_v16.html")
        _browse("wait", "--load")
        time.sleep(1.0)
        # Navigate to Provider/Developer → Provider sub-tab (first sub).
        _browse("js", "go('concept', 'provider-developer', 0)")
        time.sleep(1.0)
        # Click the first analysis-cell in the rendered table.
        out = _browse(
            "js",
            "var cell = document.querySelector('.analysis-table .analysis-cell'); "
            "if (!cell) 'no cell'; "
            "else { cell.click(); cell.textContent }",
        ).strip()
        assert "no cell" not in out.lower(), f"no analysis-cell found to click"
        time.sleep(0.5)
        # Assert drawer opened and rendered content.
        is_open = _browse(
            "js",
            "document.getElementById('drawer')?.classList?.contains('open') ? 'yes' : 'no'",
        ).strip()
        assert is_open == "yes", f"drawer did not open after pill click (got {is_open!r})"
        verbatim = _browse(
            "js",
            "document.getElementById('drawer-verbatim')?.textContent?.trim() || ''",
        ).strip()
        assert len(verbatim) > 20, (
            f"drawer opened but verbatim text is empty/short: {verbatim[:100]!r}"
        )
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


def test_missing_anchor_banner():
    """When openLawDrawerById is called with a section id that doesn't
    exist in the law blob, a warning banner should be rendered. Regression
    for: silent fallback to items[0] (which was the TX HB 149 bug)."""
    if BROWSE is None:
        print("  skip (gstack browse binary not found)", file=sys.stderr)
        return
    server, port = _start_http_server()
    try:
        _browse("goto", f"http://127.0.0.1:{port}/digital_lexicon_v16.html")
        _browse("wait", "--load")
        time.sleep(1.0)
        # 1. Good anchor: banner should NOT appear.
        _browse("js", "window.openLawDrawerById('tx-hb149', '552.001')")
        time.sleep(0.4)
        good_banner = _browse(
            "js",
            "document.querySelector('.v16-missing-anchor') ? 'yes' : 'no'",
        ).strip()
        assert good_banner == "no", (
            f"banner appeared for a valid TX section 552.001 (false positive)"
        )
        # 2. Bad anchor: banner SHOULD appear.
        _browse("js", "window.openLawDrawerById('tx-hb149', '999.999')")
        time.sleep(0.4)
        banner_text = _browse(
            "js",
            "document.querySelector('.v16-missing-anchor')?.textContent || ''",
        ).strip()
        assert "999.999" in banner_text, (
            f"missing-anchor banner not shown for bogus anchor. Got: {banner_text!r}"
        )
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


def test_overview_hides_notes_panel():
    """On the concept Overview tab the notes panel should be empty/hidden.
    Regression for: family-pool notes leaking into Overview view."""
    if BROWSE is None:
        print("  skip (gstack browse binary not found)", file=sys.stderr)
        return
    concepts = _read_concepts()
    first = next((c for c in concepts if c.get("sub_concepts")), None)
    if not first:
        raise AssertionError("no concepts with sub_concepts found")
    server, port = _start_http_server()
    try:
        url = f"http://127.0.0.1:{port}/digital_lexicon_v16.html"
        _browse("goto", url)
        _browse("wait", "--load")
        # navigate to the concept page (Overview) by clicking the matrix row
        _browse("js", f"go('concept', {json.dumps(first['id'])})")
        time.sleep(0.4)
        notes_text = _browse(
            "js", "document.getElementById('ceps-notes')?.textContent || ''"
        ).strip()
        assert not notes_text, (
            f"Overview tab shows notes text it shouldn't: {notes_text[:200]!r}"
        )
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


# ------------------------- runner --------------------------------------- #

if __name__ == "__main__":
    tests = [
        ("deep-link renders notes",     test_deep_link_renders_notes),
        ("pill click opens drawer",     test_pill_click_opens_drawer_with_content),
        ("missing-anchor banner",       test_missing_anchor_banner),
        ("overview hides notes panel",  test_overview_hides_notes_panel),
    ]
    failed = 0
    for label, fn in tests:
        try:
            fn()
            print(f"  ok    {label}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {label}")
            print(f"        {e}")
        except RuntimeError as e:
            failed += 1
            print(f"  ERROR {label}")
            print(f"        {e}")
    sys.exit(1 if failed else 0)
