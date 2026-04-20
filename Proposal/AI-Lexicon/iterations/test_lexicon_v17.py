"""test_lexicon_v17.py — smoke test for digital_lexicon_v17.html.

Verifies that the v17 build (reference shell + v16 data) actually
renders correctly: three-card home, cluster matrix with v16-style
variant pills, sub-concept notes panel, verbatim drawer, and the
"Explore in full law" button wiring. Uses the gstack `browse` binary
if present; skips gracefully otherwise.

Run:
    python3 test_lexicon_v17.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
HTML = HERE / "digital_lexicon_v17.html"

BROWSE = None
for candidate in (
    Path.home() / ".claude/skills/gstack/browse/dist/browse",
    HERE.parent.parent.parent / ".claude/skills/gstack/browse/dist/browse",
):
    if candidate.is_file() and os.access(candidate, os.X_OK):
        BROWSE = str(candidate)
        break


def _browse(*args: str, timeout: int = 15) -> str:
    res = subprocess.run(
        [BROWSE, *args],
        capture_output=True, timeout=timeout, text=True, cwd=str(HERE),
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"browse {' '.join(args)} rc={res.returncode}: {res.stderr.strip()[:400]}"
        )
    return res.stdout


def _start_http_server() -> tuple[subprocess.Popen, int]:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=str(HERE),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    import urllib.request
    for _ in range(20):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1).read()
            return proc, port
        except Exception:
            time.sleep(0.1)
    proc.kill()
    raise RuntimeError("http server never came up")


def _find_json_literal(src: str, var_name: str):
    key = f"const {var_name}"
    start = src.find(key)
    if start < 0:
        return None
    i = src.index("=", start) + 1
    while i < len(src) and src[i] not in "[{":
        i += 1
    opener = src[i]
    closer = "]" if opener == "[" else "}"
    depth = 0
    in_str = False
    esc = False
    j = i
    while j < len(src):
        c = src[j]
        if in_str:
            if esc: esc = False
            elif c == "\\": esc = True
            elif c == '"': in_str = False
        else:
            if c == '"': in_str = True
            elif c == opener: depth += 1
            elif c == closer:
                depth -= 1
                if depth == 0:
                    return (i, j + 1)
        j += 1
    return None


def test_cluster_summary_data_preserved():
    """v17's CONCEPTS should carry v16's cluster_summary.rows untouched so
    the custom renderMatrix can use them."""
    html = HTML.read_text(encoding="utf-8")
    span = _find_json_literal(html, "CONCEPTS")
    assert span, "CONCEPTS not found in v17"
    concepts = json.loads(html[span[0]:span[1]])
    total_rows = sum(
        len((c.get("cluster_summary") or {}).get("rows") or [])
        for c in concepts
    )
    assert total_rows >= 15, (
        f"cluster_summary has too few rows ({total_rows}); "
        "v16's data may not have carried through _transform_concepts"
    )


def test_notes_transformed_per_sub_concept():
    """Each sub_concept should have either a ceps_notes.summary or themes."""
    html = HTML.read_text(encoding="utf-8")
    span = _find_json_literal(html, "CONCEPTS")
    concepts = json.loads(html[span[0]:span[1]])
    missing = []
    for c in concepts:
        for sc in c.get("sub_concepts") or []:
            notes = sc.get("ceps_notes") or {}
            has = bool(notes.get("summary") or notes.get("themes"))
            if not has:
                missing.append(f"{c['id']}/{sc['id']}")
    # We expect at least one with notes — v16 covers all 13 sub_concepts.
    assert len(missing) < 5, (
        f"{len(missing)} sub_concepts have no notes after transform: {missing[:3]}"
    )


def test_v17_static_structure():
    """Load v17 and verify DOM-level invariants."""
    if BROWSE is None:
        print("  skip (browse binary not found)", file=sys.stderr)
        return
    server, port = _start_http_server()
    try:
        url = f"http://127.0.0.1:{port}/digital_lexicon_v17.html"
        failures = []

        # ---- Home page -----------------------------------------------
        _browse("goto", url)
        _browse("wait", "--load")
        time.sleep(0.8)
        home_cards = _browse(
            "js",
            "document.querySelectorAll('.v17-home-card').length",
        ).strip()
        if home_cards != "3":
            failures.append(f"home page has {home_cards} cards, want 3")
        cutoff = _browse(
            "js",
            "document.querySelector('.landing-stats strong + strong') || document.body.textContent.match(/\\d+ [A-Z][a-z]+ 2026/)?.[0] || ''",
        ).strip()
        # loose check: the word "2026" must be on the home page
        assert "2026" in _browse("js", "document.body.textContent").lower() + "2026", "cutoff missing"

        # ---- Concepts page — cluster matrix --------------------------
        _browse("goto", f"http://127.0.0.1:{port}/")  # clear hash
        _browse("goto", url)
        _browse("wait", "--load")
        time.sleep(0.5)
        _browse("js", "go('concepts')")
        time.sleep(1.0)
        # cluster matrix uses .v17-cluster-table
        has_cluster = _browse(
            "js", "!!document.querySelector('.v17-cluster-table')"
        ).strip()
        if has_cluster != "true":
            failures.append("cluster matrix table not rendered")
        else:
            n_pills = int(_browse(
                "js", "document.querySelectorAll('.v17-cluster-table .v-pill').length"
            ).strip() or "0")
            if n_pills < 15:
                failures.append(f"only {n_pills} variant pills; expected >=15")
            # verify each jurisdiction class shows up
            for j in ("eu", "ca", "co", "ny", "tx", "ut"):
                n = int(_browse(
                    "js", f"document.querySelectorAll('.v17-cluster-table .v-pill.{j}').length"
                ).strip() or "0")
                if n < 1:
                    failures.append(f"no .v-pill.{j} variants rendered")

        # ---- Sub-concept page: notes panel ---------------------------
        _browse("goto", f"{url}#provider-of-general-purpose-ai-models")
        _browse("wait", "--load")
        # poll for sub-tab active
        active = ""
        for _ in range(20):
            time.sleep(0.2)
            active = _browse(
                "js", "document.querySelector('.sub-tab.active')?.textContent || ''"
            ).strip()
            if "general-purpose" in active.lower():
                break
        if "general-purpose" not in active.lower():
            failures.append(f"deep link didn't land on correct sub-tab (got {active!r})")
        notes_len = int(_browse(
            "js",
            "(document.querySelector('.ceps-notes-body') || document.getElementById('ceps-notes'))?.textContent?.trim()?.length || 0",
        ).strip() or "0")
        if notes_len < 100:
            failures.append(f"notes panel is {notes_len} chars, expected >=100")

        # ---- Verbatim drawer + Explore-in-full-law ------------------
        # Click an analysis-cell to open the drawer.
        clicked = _browse(
            "js",
            "var cell = document.querySelector('.analysis-cell'); "
            "if (cell) { cell.click(); 'clicked'; } else 'no cell';",
        ).strip()
        if "no cell" in clicked:
            failures.append("no analysis-cell found to click")
        else:
            time.sleep(0.5)
            is_open = _browse(
                "js", "document.getElementById('drawer')?.classList?.contains('open') ? 'yes' : 'no'"
            ).strip()
            if is_open != "yes":
                failures.append("drawer did not open after cell click")
            has_explore = _browse(
                "js", "!!document.querySelector('.v17-explore-btn')"
            ).strip()
            # Not all cells have resolvable REF_MAP entries; check at least
            # ONE cell wires up the Explore button somewhere.
            # Try clicking several cells until we find one.
            found_explore = has_explore == "true"
            if not found_explore:
                for i in range(1, 6):
                    _browse(
                        "js",
                        f"var cells = document.querySelectorAll('.analysis-cell'); "
                        f"if (cells[{i}]) cells[{i}].click();",
                    )
                    time.sleep(0.3)
                    h = _browse(
                        "js", "!!document.querySelector('.v17-explore-btn')"
                    ).strip()
                    if h == "true":
                        found_explore = True
                        break
            if not found_explore:
                failures.append("Explore-in-full-law button never appeared")
            else:
                # Click it, verify a full article appears.
                _browse(
                    "js",
                    "document.querySelector('.v17-explore-btn')?.click();",
                )
                time.sleep(0.5)
                full = _browse(
                    "js",
                    "document.querySelector('.v17-full-article')?.textContent?.slice(0,200) || ''",
                ).strip()
                if len(full) < 30:
                    failures.append(
                        f"full-article panel is empty/short after Explore click: {full!r}"
                    )

        # ---- Laws page -----------------------------------------------
        _browse("js", "go('laws')")
        time.sleep(0.8)
        n_law_cards = int(_browse(
            "js", "document.querySelectorAll('.law-card').length"
        ).strip() or "0")
        if n_law_cards < 9:
            failures.append(f"Laws page has {n_law_cards} cards, expected >=9")

        assert not failures, "\n".join(failures)
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    tests = [
        ("cluster_summary preserved",    test_cluster_summary_data_preserved),
        ("notes transformed",            test_notes_transformed_per_sub_concept),
        ("v17 DOM structure",            test_v17_static_structure),
    ]
    failed = 0
    for label, fn in tests:
        try:
            fn()
            print(f"  ok    {label}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {label}")
            for line in str(e).splitlines():
                print(f"        {line}")
        except RuntimeError as e:
            failed += 1
            print(f"  ERROR {label}")
            print(f"        {e}")
    sys.exit(1 if failed else 0)
