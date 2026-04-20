"""test_lexicon_v18.py — smoke test for digital_lexicon_v18.html.

Checks the final-pass features on top of v17:
    1. Home landing copy uses About-sheet prose.
    2. Nav + home card renamed "Laws" → "Regulations".
    3. Incident sub-concept renders the 2-column Dimension hierarchy
       (Scope / High-risk AI systems, Scope / GPAI models with systemic
       risks).
    4. Clicking a cited cell + Explore-in-full-law highlights the
       referenced sub-paragraph via the <mark class="v18-cited-para">
       wrapper.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
HTML = HERE / "digital_lexicon_v18.html"

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


def test_v18_dom_features():
    """Headless-browser checks for all four v18 features."""
    if BROWSE is None:
        print("  skip (browse binary not found)", file=sys.stderr)
        return
    server, port = _start_http_server()
    failures: list[str] = []
    try:
        url = f"http://127.0.0.1:{port}/digital_lexicon_v18.html"

        # ---- 1. Home-page About copy --------------------------------------
        _browse("goto", url)
        _browse("wait", "--load")
        time.sleep(1.0)
        out = _browse(
            "js",
            "(function(){"
            "var nav = Array.from(document.querySelectorAll('.nav-link')).map(e=>e.textContent);"
            "var cards = Array.from(document.querySelectorAll('.v17-home-card-title')).map(e=>e.textContent);"
            "return JSON.stringify({"
            "tagline: document.querySelector('.landing-tagline')?.textContent || '',"
            "sub: document.querySelector('.landing-sub')?.textContent?.slice(0,120) || '',"
            "nav: nav, cards: cards"
            "});})()",
        ).strip()
        home = json.loads(out)
        if "searchable digital database" not in home.get("tagline", "").lower():
            failures.append(f"tagline wrong: {home.get('tagline')[:80]!r}")
        if "AI Act as a benchmark" not in home.get("sub", ""):
            failures.append(f"landing-sub doesn't match About: {home.get('sub')!r}")
        if "Regulations" not in home.get("nav", []):
            failures.append(f"nav missing Regulations: {home.get('nav')}")
        if "Laws" in home.get("nav", []):
            failures.append(f"nav still has 'Laws': {home.get('nav')}")
        if "Regulations" not in home.get("cards", []):
            failures.append(f"home cards missing Regulations: {home.get('cards')}")

        # ---- 2. Incident sub-concept: 2-col dim --------------------------
        out = _browse(
            "js",
            "(function(){"
            "go('concept', 'incident', 0);"
            "var ths = Array.from(document.querySelectorAll('#analysis-thead th'));"
            "var firstRowCells = document.querySelectorAll('#analysis-tbody tr:first-child td').length;"
            "var hasSubDim = ths.some(t => /sub.?dim/i.test(t.textContent));"
            "var rows = Array.from(document.querySelectorAll('#analysis-tbody tr')).map(r => "
            "  Array.from(r.querySelectorAll('td')).slice(0, 2).map(c => c.textContent.trim()).join(' / '));"
            "return JSON.stringify({"
            "hasSubDim: hasSubDim,"
            "rowSample: rows.slice(0, 10),"
            "scopeRows: rows.filter(r => r.toLowerCase().startsWith('scope')).length,"
            "});})()",
        ).strip()
        inc = json.loads(out)
        if not inc.get("hasSubDim"):
            failures.append("Incident sub-concept has no 'Sub-dimension' column header")
        if inc.get("scopeRows", 0) < 2:
            failures.append(
                f"expected Incident to split Scope into 2 sub-rows, got: "
                f"{inc.get('rowSample')}"
            )

        # ---- 3. Highlight cited sub-paragraph ----------------------------
        out = _browse(
            "js",
            "(function(){"
            "go('concept', 'provider-developer', 0);"
            "var cells = document.querySelectorAll('.analysis-cell');"
            "var ref = '';"
            "for (var i = 0; i < cells.length; i++){"
            "  cells[i].click();"
            "  ref = document.getElementById('drawer-ref')?.textContent || '';"
            "  if (/\\(\\d+\\)/.test(ref) || /\\([a-z]\\)/.test(ref)) break;"
            "}"
            "var btn = document.querySelector('.v17-explore-btn');"
            "if (btn) btn.click();"
            "return JSON.stringify({ref: ref, hasBtn: !!btn});})()",
        ).strip()
        step = json.loads(out)
        if not step.get("hasBtn"):
            failures.append("no Explore button found for a cell with a parenthesised ref")
        else:
            time.sleep(0.6)
            hl = _browse(
                "js",
                "JSON.stringify({"
                "highlighted: !!document.querySelector('.v18-cited-para'),"
                "text: (document.querySelector('.v18-cited-para')?.textContent || '').slice(0, 100)"
                "})",
            ).strip()
            hl = json.loads(hl)
            if not hl.get("highlighted"):
                failures.append(
                    f"no <mark.v18-cited-para> appeared for ref {step.get('ref')!r}"
                )

        assert not failures, "\n".join(failures)
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    tests = [("v18 DOM features", test_v18_dom_features)]
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
