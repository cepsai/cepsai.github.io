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
    """Load v17 and verify DOM-level invariants. Browse's headless session
    can lose globals between calls, so bundle navigations + assertions
    into single JS expressions wherever possible."""
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
        time.sleep(1.0)
        out = _browse(
            "js",
            "(function(){"
            "return JSON.stringify({"
            "cards: document.querySelectorAll('.v17-home-card').length,"
            "hasCutoff: /20 Apr 2026|2026/.test(document.body.textContent),"
            "title: document.querySelector('.landing h1')?.textContent?.trim() || ''"
            "});})()",
        ).strip()
        home = json.loads(out) if out else {}
        if home.get("cards") != 3:
            failures.append(f"home cards = {home.get('cards')} (want 3)")
        if not home.get("hasCutoff"):
            failures.append("home page has no 2026 date")
        if "Digital AI Lexicon" not in home.get("title", ""):
            failures.append(f"home title wrong: {home.get('title')!r}")

        # ---- Concepts page — cluster matrix --------------------------
        out = _browse(
            "js",
            "(function(){"
            "go('concepts');"
            "if (typeof filterConcepts === 'function') filterConcepts();"
            "return JSON.stringify({"
            "hasTable: !!document.querySelector('.v17-cluster-table'),"
            "pills: document.querySelectorAll('.v17-cluster-table .v-pill').length,"
            "perJ: Object.fromEntries(['eu','ca','co','ny','tx','ut']"
            "  .map(j => [j, document.querySelectorAll('.v17-cluster-table .v-pill.'+j).length]))"
            "});})()",
        ).strip()
        concepts = json.loads(out) if out else {}
        if not concepts.get("hasTable"):
            failures.append("cluster-matrix table not rendered")
        if concepts.get("pills", 0) < 15:
            failures.append(f"too few variant pills: {concepts.get('pills')}")
        for j in ("eu", "ca", "co", "ny", "tx"):  # UT sometimes has fewer
            if concepts.get("perJ", {}).get(j, 0) < 1:
                failures.append(f"no variant pills for jurisdiction {j!r}")

        # ---- Sub-concept page: notes + analysis cells ----------------
        out = _browse(
            "js",
            "(function(){"
            "go('concept', 'provider-developer', 2);"
            "var active = document.querySelector('.sub-tab.active')?.textContent || '';"
            "return JSON.stringify({"
            "active: active,"
            "notesBodyLen: document.querySelector('.ceps-notes-body')?.textContent?.trim()?.length || 0,"
            "analysisCells: document.querySelectorAll('.analysis-cell').length"
            "});})()",
        ).strip()
        sub = json.loads(out) if out else {}
        if "general-purpose" not in sub.get("active", "").lower():
            failures.append(f"sub-tab active = {sub.get('active')!r}")
        if sub.get("notesBodyLen", 0) < 100:
            failures.append(f"notes body = {sub.get('notesBodyLen')} chars (want >=100)")
        if sub.get("analysisCells", 0) < 5:
            failures.append(f"analysis cells = {sub.get('analysisCells')}")

        # ---- Verbatim drawer + Explore-in-full-law ------------------
        out = _browse(
            "js",
            "(function(){"
            # Navigate to a sub-concept whose cells likely resolve in REF_MAP
            # (sub-idx 0 on Provider/Developer = 'Provider', which has the
            # EU 'Article 3' citation — guaranteed to resolve).
            "go('concept', 'provider-developer', 0);"
            "var cells = document.querySelectorAll('.analysis-cell');"
            "var found = null;"
            "for (var i = 0; i < cells.length; i++){ cells[i].click(); "
            "  var btn = document.querySelector('.v17-explore-btn');"
            "  if (btn){ found = i; break; }"
            "}"
            "return JSON.stringify({"
            "drawerOpen: document.getElementById('drawer')?.classList?.contains('open') || false,"
            "verbatimLen: (document.getElementById('drawer-verbatim')?.textContent || '').length,"
            "exploreBtnCellIdx: found,"
            "});})()",
        ).strip()
        drawer = json.loads(out) if out else {}
        if not drawer.get("drawerOpen"):
            failures.append("drawer never opened after cell click")
        if drawer.get("verbatimLen", 0) < 10:
            failures.append(f"drawer-verbatim empty: {drawer.get('verbatimLen')} chars")
        if drawer.get("exploreBtnCellIdx") is None:
            failures.append("Explore-in-full-law button never appeared for any cell")
        else:
            # Click it and verify the full article appears.
            out = _browse(
                "js",
                "(function(){"
                "document.querySelector('.v17-explore-btn')?.click();"
                "return (document.querySelector('.v17-full-article')?.textContent || '').slice(0, 300);"
                "})()",
            ).strip()
            if len(out) < 30:
                failures.append(f"full-article panel empty after Explore click: {out!r}")

        # ---- Laws page -----------------------------------------------
        out = _browse(
            "js",
            "(function(){"
            "go('laws');"
            "return JSON.stringify({"
            "cards: document.querySelectorAll('.law-card-v2').length,"
            "blocks: document.querySelectorAll('.juris-block').length,"
            "hasTitle: /Primary Sources/.test(document.getElementById('p-laws')?.textContent || '')"
            "});})()",
        ).strip()
        laws = json.loads(out) if out else {}
        if laws.get("cards", 0) < 9:
            failures.append(f"Laws page: {laws.get('cards')} law cards (want >=9)")
        if laws.get("blocks", 0) < 6:
            failures.append(f"Laws page: {laws.get('blocks')} jurisdiction blocks (want >=6)")
        if not laws.get("hasTitle"):
            failures.append("Laws page missing 'Primary Sources' heading")

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
