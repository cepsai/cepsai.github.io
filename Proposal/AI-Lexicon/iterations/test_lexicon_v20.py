"""test_lexicon_v20.py — smoke test for digital_lexicon_v20.html.

v20 reshape of v19's Verbatim feature:
    * Top nav is back to "Concepts" (no Verbatim nav, no home card).
    * Inside each concept page, two mode tabs appear above the
      sub-concept sub-tabs: Analysis (default) and Verbatim.
    * URL encodes the mode as ?view=verbatim on #/concept/<id>.
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
HTML = HERE / "digital_lexicon_v20.html"

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


# --------------------------------------------------------------------------- #
# Static HTML checks                                                          #
# --------------------------------------------------------------------------- #

def test_static_nav_reverted():
    html = HTML.read_text(encoding="utf-8")
    # Top nav back to "Concepts" (no Analysis/Verbatim top-level).
    assert 'id="nav-concepts"' in html, "missing nav-concepts button id"
    assert ">Concepts<" in html, "nav label should read 'Concepts'"
    assert 'id="nav-verbatim"' not in html, "v19's Verbatim nav button should be removed"
    assert 'onclick="go(\'analysis\')"' not in html, \
        "v19's analysis-route onclick should be gone"
    # Home cards: back to v17's "Browse concepts" (no Browse verbatim).
    assert "Browse concepts" in html, "home card 'Browse concepts' missing"
    assert "Browse verbatim" not in html, "v19's home verbatim card should be removed"


def test_static_dim_parents_blob_present():
    html = HTML.read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" id="__v20_dim_parents__">(.*?)</script>', html, re.S)
    assert m, "V20 dim-parents blob not found"
    blob = json.loads(m.group(1))
    for cid in ("provider-developer", "deployer-supplier", "incident"):
        assert cid in blob, f"V20_DIM_PARENTS missing {cid}"
    pp = {k.lower(): v for k, v in blob["provider-developer"].items()}
    assert pp.get("transparency", "").lower() == "obligations"


# --------------------------------------------------------------------------- #
# Browser tests                                                               #
# --------------------------------------------------------------------------- #

def test_browser_v20_features():
    if BROWSE is None:
        print("  skip (browse binary not found)", file=sys.stderr)
        return
    server, port = _start_http_server()
    failures: list[str] = []
    try:
        url = f"http://127.0.0.1:{port}/digital_lexicon_v20.html"
        _browse("goto", url)
        _browse("wait", "--load")
        time.sleep(1.0)
        _browse("js", "localStorage.clear(); 'ok'")
        _browse("goto", url)
        _browse("wait", "--load")
        time.sleep(1.0)

        # ---- 1. Top nav + home cards unchanged from v18 -------------------
        out = _browse(
            "js",
            "JSON.stringify({"
            "nav: Array.from(document.querySelectorAll('.nav-link')).map(e=>e.textContent.trim()),"
            "cards: Array.from(document.querySelectorAll('.v17-home-card-title')).map(e=>e.textContent.replace(/\\s+/g,' ').trim())"
            "})",
        ).strip()
        home = json.loads(out)
        if "Concepts" not in home["nav"]:
            failures.append(f"top nav missing 'Concepts': {home['nav']}")
        if "Verbatim" in home["nav"]:
            failures.append(f"top nav should not have 'Verbatim': {home['nav']}")
        if "Analysis" in home["nav"]:
            failures.append(f"top nav should not have 'Analysis': {home['nav']}")
        if not any("Browse concepts" in t for t in home["cards"]):
            failures.append(f"home should have 'Browse concepts' card: {home['cards']}")
        if any("Browse verbatim" in t for t in home["cards"]):
            failures.append(f"home should NOT have 'Browse verbatim' card: {home['cards']}")

        # ---- 2. Open a concept; mode bar exists below sub-tabs ----------
        out = _browse(
            "js",
            "(function(){"
            "go('concept','provider-developer',0);"
            "var bar = document.getElementById('v20-mode-bar');"
            "var tabs = bar ? Array.from(bar.querySelectorAll('.v20-mode-tab')).map(b => ({"
            "  mode: b.getAttribute('data-mode'),"
            "  active: b.classList.contains('active'),"
            "  label: b.textContent.trim()"
            "})) : [];"
            "var subTabs = document.getElementById('sub-tabs');"
            # compareDocumentPosition: 4 = following — we want bar to FOLLOW subTabs.
            "return JSON.stringify({"
            "barPresent: !!bar,"
            "barFollowsSubtabs: (bar && subTabs) ? ((subTabs.compareDocumentPosition(bar) & 4) === 4) : false,"
            "tabs: tabs,"
            "stateMode: state.mode,"
            "hash: location.hash"
            "});})()",
        ).strip()
        cp = json.loads(out)
        if not cp["barPresent"]:
            failures.append("mode bar not rendered in concept page")
        if cp["barPresent"] and not cp["barFollowsSubtabs"]:
            failures.append("mode bar must appear AFTER the sub-concept sub-tabs")
        tab_modes = {t["mode"]: t for t in cp.get("tabs", [])}
        if "analysis" not in tab_modes or "verbatim" not in tab_modes:
            failures.append(f"mode bar should have analysis+verbatim tabs, got: {tab_modes}")
        if tab_modes.get("verbatim", {}).get("label") != "Legal text":
            failures.append(
                f"Verbatim tab should be labelled 'Legal text', got: "
                f"{tab_modes.get('verbatim', {}).get('label')!r}"
            )
        if tab_modes.get("analysis", {}).get("label") != "Analysis":
            failures.append(
                f"Analysis tab should be labelled 'Analysis', got: "
                f"{tab_modes.get('analysis', {}).get('label')!r}"
            )
        if tab_modes.get("analysis", {}).get("active") is not True:
            failures.append(f"Analysis tab should be active by default: {tab_modes}")
        if cp["stateMode"] != "analysis":
            failures.append(f"default state.mode should be 'analysis', got: {cp['stateMode']}")

        # ---- 3. Click Verbatim tab → verbatim table ---------------------
        out = _browse(
            "js",
            "(function(){"
            "document.querySelector('.v20-mode-tab[data-mode=\"verbatim\"]').click();"
            "var tbody = document.getElementById('analysis-tbody');"
            "var rowsDims = Array.from(tbody.querySelectorAll('tr')).map(tr => {"
            "  var dimTd = tr.querySelector('td.v20-dim-cell');"
            "  var subTd = tr.querySelector('td.v20-subdim-cell');"
            "  return {dim: dimTd ? dimTd.textContent.trim() : '(covered)', rs: dimTd ? dimTd.rowSpan : 0, sub: subTd ? subTd.textContent.trim() : ''};"
            "});"
            "return JSON.stringify({"
            "mode: state.mode,"
            "hash: location.hash,"
            "hasSubDim: !!document.querySelector('#analysis-thead .v20-subdim-cell'),"
            "hasVerbatimCell: !!document.querySelector('.v20-verbatim-cell'),"
            "rowsDims: rowsDims.slice(0, 10)"
            "});})()",
        ).strip()
        vb = json.loads(out)
        if vb["mode"] != "verbatim":
            failures.append(f"state.mode should be 'verbatim' after click, got: {vb['mode']}")
        if "?view=verbatim" not in vb["hash"]:
            failures.append(f"hash should include ?view=verbatim, got: {vb['hash']}")
        if not vb["hasSubDim"]:
            failures.append("Verbatim view should have a Sub-dimension column header")
        if not vb["hasVerbatimCell"]:
            failures.append("Verbatim view should have at least one .v20-verbatim-cell")
        # Expect "Obligations" dim cell with rowspan>1 (Provider has 4 Obligations sub-dims).
        obl = [r for r in vb.get("rowsDims", []) if r.get("dim") == "Obligations"]
        if not obl or obl[0]["rs"] < 2:
            failures.append(
                f"Provider verbatim: expected 'Obligations' rowspan >= 2, got rows: {vb['rowsDims']}"
            )

        # ---- 4. Click Analysis tab → single-column layout comes back ---
        out = _browse(
            "js",
            "(function(){"
            "document.querySelector('.v20-mode-tab[data-mode=\"analysis\"]').click();"
            "return JSON.stringify({"
            "mode: state.mode,"
            "hash: location.hash,"
            "hasSubDim: !!document.querySelector('#analysis-thead .v20-subdim-cell'),"
            "ths: Array.from(document.querySelectorAll('#analysis-thead th')).map(e=>e.textContent.replace(/\\s+/g,' ').trim().slice(0, 30))"
            "});})()",
        ).strip()
        an = json.loads(out)
        if an["mode"] != "analysis":
            failures.append(f"state.mode should be 'analysis', got: {an['mode']}")
        if "view=verbatim" in an["hash"]:
            failures.append(f"hash should NOT contain view=verbatim, got: {an['hash']}")
        if an["hasSubDim"]:
            failures.append("Analysis view for Provider should NOT have Sub-dimension col")

        # ---- 5. Verbatim cell click opens full-law drawer ---------------
        _browse(
            "js",
            "document.querySelector('.v20-mode-tab[data-mode=\"verbatim\"]').click(); 'switched'",
        )
        time.sleep(0.3)
        _browse(
            "js",
            "(function(){"
            "var cells = document.querySelectorAll('.v20-verbatim-cell');"
            "if (cells.length) cells[0].click();"
            "return 'clicked ' + (cells.length ? 1 : 0);"
            "})()",
        )
        time.sleep(0.5)
        out = _browse(
            "js",
            "JSON.stringify({"
            "drawerOpen: !!document.querySelector('.drawer.open'),"
            "hasFullArticle: !!document.querySelector('.v17-full-article'),"
            "articlePreview: (document.querySelector('.v17-full-article')?.textContent || '').slice(0, 80)"
            "})",
        ).strip()
        cl = json.loads(out)
        if not (cl["drawerOpen"] and cl["hasFullArticle"]):
            failures.append(
                f"cell click should open drawer + full-article panel; got {cl}"
            )

        # ---- 6. Deep link with ?view=verbatim opens in Verbatim mode ---
        _browse("js", "window.location.hash = '#/concept/deployer-supplier?view=verbatim'; 'set'")
        time.sleep(0.5)
        out = _browse(
            "js",
            "JSON.stringify({mode: state.mode, hasSubDim: !!document.querySelector('#analysis-thead .v20-subdim-cell')})",
        ).strip()
        dp = json.loads(out)
        if dp["mode"] != "verbatim":
            failures.append(f"deep link ?view=verbatim should set mode=verbatim; got {dp}")
        if not dp["hasSubDim"]:
            failures.append("deep link ?view=verbatim should show Sub-dimension column")

        assert not failures, "\n".join(failures)
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    tests = [
        ("static: nav + home reverted",   test_static_nav_reverted),
        ("static: dim parents blob",      test_static_dim_parents_blob_present),
        ("browser: v20 features",         test_browser_v20_features),
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
