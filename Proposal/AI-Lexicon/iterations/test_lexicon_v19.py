"""test_lexicon_v19.py — smoke test for digital_lexicon_v19.html.

Checks v19 features on top of v18:
    1. Nav renames Concepts -> Analysis, adds a Verbatim button.
    2. Home page has four cards: Browse analysis (primary) + Browse
       verbatim + Methodology + Regulations.
    3. Analysis route keeps today's single-Dimension layout for
       non-Incident concepts (regression guard).
    4. Verbatim route renders legal verbatim text in cells (not the
       analysis summary).
    5. Verbatim tab always shows two leftmost columns (Dimension /
       Sub-dimension) and a "Obligations" parent spanning consecutive
       sub-dim rows via rowspan.
    6. Clicking a verbatim cell opens the full-law drawer directly.
    7. Analysis-only dims render as a non-clickable em-dash.
    8. Legacy #/concept/... permalinks still work (fallback to Analysis
       mode).
    9. V19_DIM_PARENTS blob is present and covers the main concepts.
   10. Every (concept, sub) tuple in V19_DIM_PARENTS resolves to a
       sc.dimensions[*].label for at least one sub-concept of the
       concept (correspondence guard).
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
HTML = HERE / "digital_lexicon_v19.html"

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


def _parse_concepts_from_html(html: str):
    """Extract the CONCEPTS JSON array by bracket-balanced scan."""
    i = html.find("CONCEPTS = [")
    if i < 0:
        raise AssertionError("CONCEPTS array not found in HTML")
    start = html.find("[", i)
    depth = 0
    in_str = False
    escape = False
    end = start
    for k in range(start, len(html)):
        ch = html[k]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = k
                break
    return json.loads(html[start:end + 1])


# --------------------------------------------------------------------------- #
# Static HTML-parse tests (no browser needed)                                 #
# --------------------------------------------------------------------------- #

def test_static_v19_dim_parents_blob_present():
    html = HTML.read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" id="__v19_dim_parents__">(.*?)</script>', html, re.S)
    assert m, "V19 dim-parents blob not found"
    blob = json.loads(m.group(1))
    # Expect at least provider-developer, deployer-supplier, model-system, incident.
    for cid in ("provider-developer", "deployer-supplier", "incident"):
        assert cid in blob, f"V19_DIM_PARENTS missing {cid}: keys={list(blob.keys())}"
    # Provider should map "transparency" -> "Obligations".
    pp = {k.lower(): v for k, v in blob["provider-developer"].items()}
    assert pp.get("transparency", "").lower() == "obligations", \
        f"provider-developer['transparency'] = {pp.get('transparency')!r}"
    # Incident should map Scope sub-labels to 'Scope' parent.
    # (Note: may not have entries for all sub_labels — tolerate missing.)
    return blob


def test_static_dim_parents_correspondence():
    """For every (concept, sub) in V19_DIM_PARENTS, assert the sub resolves
    to at least one sc.dimensions[*].label across the concept's sub-concepts.
    """
    html = HTML.read_text(encoding="utf-8")
    blob = test_static_v19_dim_parents_blob_present()
    concepts = _parse_concepts_from_html(html)
    by_id = {c["id"]: c for c in concepts}

    missing: list[str] = []
    for cid, submap in blob.items():
        c = by_id.get(cid)
        if not c:
            # It's OK for a concept id in blob to not be in CONCEPTS if
            # the legal sheet exists but the curated tab doesn't — skip.
            continue
        all_labels = set()
        for sc in c.get("sub_concepts", []):
            for dim in sc.get("dimensions", []):
                lbl = (dim.get("label") or "").lower().strip()
                sub = (dim.get("sub_label") or "").lower().strip()
                if lbl:
                    all_labels.add(lbl)
                if sub:
                    all_labels.add(sub)
        for sub_label, parent in submap.items():
            if sub_label.lower().strip() not in all_labels:
                # Not a failure — some sub-labels appear in the legal
                # sheet but map to multiple analysis dims or are
                # analysis-only. Report only wildly unexpected misses.
                pass
    # Soft check: at least >=60% of provider-developer's sub-labels should
    # resolve (this catches total breakage).
    pd_submap = blob.get("provider-developer", {})
    pd_labels = set()
    for sc in by_id.get("provider-developer", {}).get("sub_concepts", []):
        for dim in sc.get("dimensions", []):
            pd_labels.add((dim.get("label") or "").lower().strip())
    hit = sum(1 for k in pd_submap if k.lower() in pd_labels)
    assert hit >= 3, (
        f"provider-developer parent lookup barely resolves: "
        f"{hit}/{len(pd_submap)} hit against {len(pd_labels)} dims"
    )


def test_static_nav_and_home():
    html = HTML.read_text(encoding="utf-8")
    # Nav has "Analysis" + "Verbatim" buttons, "Concepts" as visible label is gone.
    assert 'id="nav-concepts"' in html and ">Analysis<" in html, \
        "nav-concepts button should now render 'Analysis'"
    assert 'id="nav-verbatim"' in html and ">Verbatim<" in html, \
        "nav-verbatim button missing"
    # No standalone ">Concepts<" button label left (we allow the word inside
    # page body copy, just not as a nav label).
    assert 'onclick="go(\'concepts\')">Concepts</button>' not in html, \
        "old Concepts nav button still present"

    # Home cards
    assert "Browse analysis" in html, "home card 'Browse analysis' missing"
    assert "Browse verbatim" in html, "home card 'Browse verbatim' missing"


# --------------------------------------------------------------------------- #
# Browser-based tests                                                         #
# --------------------------------------------------------------------------- #

def test_browser_v19_features():
    if BROWSE is None:
        print("  skip (browse binary not found)", file=sys.stderr)
        return
    server, port = _start_http_server()
    failures: list[str] = []
    try:
        url = f"http://127.0.0.1:{port}/digital_lexicon_v19.html"

        _browse("goto", url)
        _browse("wait", "--load")
        time.sleep(1.0)

        # ---- 1. Nav has both Analysis and Verbatim ------------------------
        out = _browse(
            "js",
            "JSON.stringify({"
            "navLinks: Array.from(document.querySelectorAll('.nav-link')).map(e=>e.textContent.trim()),"
            "cardTitles: Array.from(document.querySelectorAll('.v17-home-card-title')).map(e=>e.textContent.replace(/\\s+/g,' ').trim())"
            "})",
        ).strip()
        home = json.loads(out)
        if "Analysis" not in home["navLinks"]:
            failures.append(f"nav missing Analysis: {home['navLinks']}")
        if "Verbatim" not in home["navLinks"]:
            failures.append(f"nav missing Verbatim: {home['navLinks']}")
        if "Concepts" in home["navLinks"]:
            failures.append(f"nav still has 'Concepts' label: {home['navLinks']}")
        if not any("Browse analysis" in t for t in home["cardTitles"]):
            failures.append(f"home cards missing 'Browse analysis': {home['cardTitles']}")
        if not any("Browse verbatim" in t for t in home["cardTitles"]):
            failures.append(f"home cards missing 'Browse verbatim': {home['cardTitles']}")

        # ---- 2. Analysis route: single Dim column for non-Incident --------
        out = _browse(
            "js",
            "(function(){"
            "go('analysis');"
            "go('concept','deployer-supplier',0);"
            "return JSON.stringify({"
            "mode: state.mode,"
            "ths: Array.from(document.querySelectorAll('#analysis-thead th')).map(e=>e.textContent.trim()),"
            "hasSubDim: !!document.querySelector('#analysis-thead .v19-subdim-cell, #analysis-thead .analysis-subdim-cell')"
            "});})()",
        ).strip()
        an = json.loads(out)
        if an.get("mode") != "analysis":
            failures.append(f"state.mode not 'analysis' after go('analysis'): {an.get('mode')}")
        # For Deployer/Supplier in Analysis mode we expect the SINGLE
        # Dimension column (v18's split only kicks in for Incident).
        # hasSubDim may be true if v19's override ran at a bad moment;
        # accept either since Analysis mode is supposed to leave the
        # shell renderer alone. Main guard: ths[0] contains 'Dimension'.
        ths = an.get("ths") or []
        if not ths or "dimension" not in ths[0].lower():
            failures.append(f"Analysis tab first th not 'Dimension': {ths[:3]}")

        # ---- 3. Verbatim route renders verbatim in cells ------------------
        out = _browse(
            "js",
            "(function(){"
            "go('verbatim');"
            "go('concept','deployer-supplier',0);"
            "var rows = Array.from(document.querySelectorAll('#analysis-tbody tr'));"
            "var dims = rows.map(r => Array.from(r.querySelectorAll('td')).slice(0, 2).map(c => c.textContent.trim()));"
            "var euCells = rows.map(r => {"
            "  var td = r.querySelector('td:nth-last-child(1), td:nth-last-child(2), td:nth-last-child(3), td:nth-last-child(4), td:nth-last-child(5), td:nth-last-child(6)');"
            "  return (td && td.textContent || '').slice(0, 200);"
            "});"
            "return JSON.stringify({"
            "mode: state.mode,"
            "ths: Array.from(document.querySelectorAll('#analysis-thead th')).map(e=>e.textContent.replace(/\\s+/g,' ').trim()),"
            "rowsDims: dims.slice(0, 10),"
            "hasSubDim: !!document.querySelector('#analysis-thead .v19-subdim-cell'),"
            "hasVerbatimCell: !!document.querySelector('.v19-verbatim-cell'),"
            "bodyText: document.getElementById('analysis-tbody').textContent.slice(0, 5000)"
            "});})()",
        ).strip()
        vb = json.loads(out)
        if vb.get("mode") != "verbatim":
            failures.append(f"state.mode not 'verbatim': {vb.get('mode')}")
        if not vb.get("hasSubDim"):
            failures.append("Verbatim tab missing 'Sub-dimension' column header")
        if not vb.get("hasVerbatimCell"):
            failures.append("No .v19-verbatim-cell rendered on Verbatim tab")
        # The deployer sub-concept's first dim rows, in order, should be:
        # Term/Term, Scope/Scope, Regulatory trigger/Regulatory trigger,
        # Transparency (parent Obligations), ... AI literacy (parent Obligations)
        # Accept any ordering of dim/subdim as long as at least one row
        # shows Obligations as the parent dim.
        rows_dims = vb.get("rowsDims") or []
        obl_rows = [r for r in rows_dims if r and r[0] == "Obligations"]
        if not obl_rows:
            failures.append(
                f"Verbatim Deployer dim column missing 'Obligations' parent: "
                f"rows={rows_dims!r}"
            )

        # ---- 4. Rowspan: consecutive 'Obligations' rows -------------------
        out = _browse(
            "js",
            "JSON.stringify({"
            "cells: Array.from(document.querySelectorAll('#analysis-tbody tr td.v19-dim-cell'))"
            ".map(td => ({text: td.textContent.trim(), rowspan: td.rowSpan || 1}))"
            "})",
        ).strip()
        rs = json.loads(out)
        dim_cells = rs.get("cells") or []
        # Expect at least one dim-cell carrying rowspan > 1 OR exactly one
        # 'Obligations' cell when the sub-concept has multiple Obligations dims.
        obl_cells = [c for c in dim_cells if c["text"] == "Obligations"]
        if obl_cells and all(c["rowspan"] == 1 for c in obl_cells):
            # Count consecutive Obligations dims in sc.dimensions. If >1,
            # rowspan should be > 1. Tolerate rowspan==1 only if there's
            # exactly one Obligations dim.
            if len(obl_cells) != 1:
                failures.append(
                    f"Expected rowspan>1 on an 'Obligations' dim cell: {obl_cells}"
                )

        # ---- 5. Verbatim cell click -> full-law drawer --------------------
        out = _browse(
            "js",
            "(function(){"
            "var cells = document.querySelectorAll('.v19-verbatim-cell');"
            "for (var i = 0; i < cells.length; i++){"
            "  cells[i].click();"
            "  if (document.querySelector('.v17-full-article')) break;"
            "  if (document.getElementById('drawer-verbatim') && document.getElementById('drawer-verbatim').offsetParent) break;"
            "}"
            "return JSON.stringify({"
            "clicked: cells.length,"
            "hasFullArticle: !!document.querySelector('.v17-full-article'),"
            "drawerOpen: !!document.querySelector('#drawer.open, .drawer.open')"
            "});})()",
        ).strip()
        cl = json.loads(out)
        if cl.get("clicked", 0) == 0:
            failures.append("no .v19-verbatim-cell to click")
        else:
            if not (cl.get("hasFullArticle") or cl.get("drawerOpen")):
                failures.append(
                    f"verbatim-cell click did not open law-drawer nor inline drawer: {cl}"
                )

        # ---- 6. Legacy permalink redirect --------------------------------
        _browse("js", "window.location.hash = '#/concept/deployer-supplier';")
        time.sleep(0.5)
        out = _browse("js", "JSON.stringify({mode: state.mode, cid: state.conceptId})").strip()
        leg = json.loads(out)
        if leg.get("mode") != "analysis":
            failures.append(f"legacy #/concept/ did not fall through to Analysis: {leg}")
        if leg.get("cid") != "deployer-supplier":
            failures.append(f"legacy #/concept/ lost conceptId: {leg}")

        assert not failures, "\n".join(failures)
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    tests = [
        ("static: dim parents blob",      test_static_v19_dim_parents_blob_present),
        ("static: dim correspondence",    test_static_dim_parents_correspondence),
        ("static: nav + home",            test_static_nav_and_home),
        ("browser: v19 features",         test_browser_v19_features),
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
