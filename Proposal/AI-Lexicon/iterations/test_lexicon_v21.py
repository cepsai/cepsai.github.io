"""test_lexicon_v21.py — smoke test for digital_lexicon_v21.html.

v21 features on the Legal-text (verbatim) view:
    * A filter bar above the table with a Dimension select, a
      Sub-dimension select, and Prev/Next navigation buttons.
    * Table body has only ONE row at a time; cells show the full
      verbatim text (no line-clamp).
    * Changing the Dimension dropdown updates the Sub-dimension list
      and jumps to the first sub of that dim.
    * Prev/Next walks the full ordered list of (dim, sub) tuples.
    * Analysis-mode is unchanged.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
HTML = HERE / "digital_lexicon_v21.html"

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


def _start_http_server():
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


def test_browser_v21_features():
    if BROWSE is None:
        print("  skip (browse binary not found)", file=sys.stderr)
        return
    server, port = _start_http_server()
    failures: list[str] = []
    try:
        url = f"http://127.0.0.1:{port}/digital_lexicon_v21.html"
        _browse("goto", url)
        _browse("wait", "--load")
        # Poll until `go` is installed (shell's IIFE finished). This
        # avoids the flaky "go is not defined" error when /browse
        # evaluates before the page's script tags executed.
        for _ in range(30):
            out = _browse("js", "typeof go").strip()
            if "function" in out:
                break
            time.sleep(0.1)
        time.sleep(0.3)

        # ---- 1. Open a concept in Legal-text mode ------------------------
        _browse(
            "js",
            "go('concept','provider-developer',0);"
            "document.querySelector('.v20-mode-tab[data-mode=\"verbatim\"]').click();"
            "'switched'",
        )
        time.sleep(0.5)

        out = _browse(
            "js",
            "(function(){"
            "var bar = document.getElementById('v21-filter-bar');"
            "var dimSel = document.getElementById('v21-dim-select');"
            "var subSel = document.getElementById('v21-sub-select');"
            "var prev = document.getElementById('v21-prev-btn');"
            "var next = document.getElementById('v21-next-btn');"
            "var count = document.getElementById('v21-row-count');"
            "var tbody = document.getElementById('analysis-tbody');"
            "return JSON.stringify({"
            "barPresent: !!bar,"
            "dimOptions: dimSel ? Array.from(dimSel.options).map(o => o.value) : [],"
            "selectedDim: dimSel ? dimSel.value : null,"
            "subOptions: subSel ? Array.from(subSel.options).map(o => o.textContent) : [],"
            "countText: count ? count.textContent : '',"
            "prevDisabled: prev ? prev.disabled : null,"
            "nextDisabled: next ? next.disabled : null,"
            "rowCount: tbody ? tbody.querySelectorAll('tr').length : 0,"
            "verbatimCells: document.querySelectorAll('.v21-verbatim-cell').length,"
            "firstCellTextLen: (document.querySelector('.v21-verbatim-cell')?.textContent || '').length"
            "});})()",
        ).strip()
        cp = json.loads(out)
        if not cp["barPresent"]:
            failures.append("filter bar not rendered in Legal-text mode")
        if cp["rowCount"] != 1:
            failures.append(f"expected exactly 1 row rendered, got: {cp['rowCount']}")
        if cp["verbatimCells"] == 0:
            failures.append("no .v21-verbatim-cell rendered in single-row view")
        if cp["firstCellTextLen"] < 80:
            failures.append(
                f"verbatim cell looks truncated — length={cp['firstCellTextLen']}, "
                "expected full unclamped text (>= 80 chars for a typical AI Act definition)"
            )
        if "1 of" not in cp["countText"]:
            failures.append(f"row count label malformed: {cp['countText']!r}")
        if cp["prevDisabled"] is not True:
            failures.append(f"Prev button should be disabled on first row: {cp['prevDisabled']}")
        if cp["nextDisabled"] is True:
            failures.append("Next button should NOT be disabled when more rows exist")
        dims_expected = {"Term", "Scope", "Obligations", "Rebuttal", "Penalties"}
        dims_got = set(cp["dimOptions"])
        if not dims_expected.issubset(dims_got):
            failures.append(
                f"Dimension options missing expected entries; got: {sorted(dims_got)}"
            )

        # ---- 2. Change Dimension dropdown to 'Obligations' --------------
        _browse(
            "js",
            "(function(){"
            "var s = document.getElementById('v21-dim-select');"
            "s.value = 'Obligations';"
            "s.dispatchEvent(new Event('change'));"
            "return 'changed';"
            "})()",
        )
        time.sleep(0.3)
        out = _browse(
            "js",
            "(function(){"
            "var subSel = document.getElementById('v21-sub-select');"
            "var rows = document.querySelectorAll('#analysis-tbody tr');"
            "var r0 = rows[0];"
            "var cells = r0 ? Array.from(r0.querySelectorAll('td')).slice(0, 2).map(c => c.textContent.trim()) : [];"
            "return JSON.stringify({"
            "selectedDim: document.getElementById('v21-dim-select').value,"
            "selectedSub: subSel ? JSON.parse(subSel.value).sub : null,"
            "subOptions: subSel ? Array.from(subSel.options).map(o => o.textContent) : [],"
            "firstCells: cells"
            "});})()",
        ).strip()
        od = json.loads(out)
        if od["selectedDim"] != "Obligations":
            failures.append(f"dim select should be 'Obligations', got: {od['selectedDim']}")
        if not od["subOptions"]:
            failures.append("sub-dim options should populate for Obligations")
        if od["firstCells"] and od["firstCells"][0] != "Obligations":
            failures.append(
                f"row's first cell should be 'Obligations', got: {od['firstCells']}"
            )

        # ---- 3. Change Sub-dimension to 'AI literacy' -------------------
        out = _browse(
            "js",
            "(function(){"
            "var sel = document.getElementById('v21-sub-select');"
            "var target = null;"
            "for (var i = 0; i < sel.options.length; i++){"
            "  if (sel.options[i].textContent === 'AI literacy') { target = sel.options[i].value; break; }"
            "}"
            "if (target) { sel.value = target; sel.dispatchEvent(new Event('change')); }"
            "var cells = Array.from(document.querySelectorAll('#analysis-tbody tr td')).slice(0, 2).map(c => c.textContent.trim());"
            "return JSON.stringify({"
            "found: !!target,"
            "cells: cells,"
            "storedSub: state.verbatimSub"
            "});})()",
        ).strip()
        ol = json.loads(out)
        if ol.get("found") and ol.get("cells", ["", ""])[1] != "AI literacy":
            failures.append(
                f"After selecting 'AI literacy', the sub-cell should match; got: {ol['cells']}"
            )

        # ---- 4. Next/Prev navigation ------------------------------------
        out = _browse(
            "js",
            "(function(){"
            "document.getElementById('v21-next-btn').click();"
            "var c1 = Array.from(document.querySelectorAll('#analysis-tbody tr td')).slice(0, 2).map(c => c.textContent.trim());"
            "document.getElementById('v21-prev-btn').click();"
            "var c2 = Array.from(document.querySelectorAll('#analysis-tbody tr td')).slice(0, 2).map(c => c.textContent.trim());"
            "return JSON.stringify({afterNext: c1, afterPrev: c2});"
            "})()",
        ).strip()
        nv = json.loads(out)
        if nv["afterNext"] == nv["afterPrev"]:
            failures.append(
                f"Next/Prev didn't move the row: afterNext={nv['afterNext']}, "
                f"afterPrev={nv['afterPrev']}"
            )

        # ---- 5. Analysis mode: filter bar is hidden --------------------
        _browse(
            "js",
            "document.querySelector('.v20-mode-tab[data-mode=\"analysis\"]').click(); 'ok'",
        )
        time.sleep(0.3)
        out = _browse(
            "js",
            "JSON.stringify({"
            "barVisible: (function(){var b=document.getElementById('v21-filter-bar'); return !!(b && b.offsetParent);})(),"
            "rowCount: document.querySelectorAll('#analysis-tbody tr').length"
            "})",
        ).strip()
        am = json.loads(out)
        if am["barVisible"]:
            failures.append("filter bar should be hidden on Analysis mode")
        if am["rowCount"] < 3:
            failures.append(
                f"Analysis mode should render multiple rows, got: {am['rowCount']}"
            )

        # ---- 6. Verbatim cell click still opens full-law drawer ---------
        _browse(
            "js",
            "document.querySelector('.v20-mode-tab[data-mode=\"verbatim\"]').click();",
        )
        time.sleep(0.3)
        _browse(
            "js",
            "(function(){"
            "var c = document.querySelector('.v21-verbatim-cell');"
            "if (c) c.click();"
            "return 'clicked';"
            "})()",
        )
        time.sleep(0.5)
        out = _browse(
            "js",
            "JSON.stringify({"
            "drawerOpen: !!document.querySelector('.drawer.open'),"
            "hasFullArticle: !!document.querySelector('.v17-full-article')"
            "})",
        ).strip()
        cl = json.loads(out)
        if not (cl["drawerOpen"] and cl["hasFullArticle"]):
            failures.append(
                f"cell click should open drawer + full-article panel; got {cl}"
            )

        assert not failures, "\n".join(failures)
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    tests = [
        ("browser: v21 features", test_browser_v21_features),
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
