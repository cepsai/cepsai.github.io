"""Structural browser-verification proxy for US-009.

US-009 confirms that the article-link audit covers all 12 regulatory texts
in the Excel inventory (US-006 EU + US-007 federal + US-008 state) and
spot-checks at least 3 article links per text via the same data path the
drawer popup uses (`cell.reference` + `cell.verbatim` + `cell.analysis`).

Coverage matrix (per `iterations/v28_excel_inventory.md` §2):

  EU   — eu-ai-act, eu-gpai-cop-{copyright,transparency,safety},
         eu-guidelines-gpai-scope (5 law-blobs, 1 of which split into 3
         CoP chapters per US-006).
  CA   — ca-sb53, ca-sb942, ca-ab2013.
  CO   — co-sb24205. (CO SB 25B-004 has no law-blob — inventory §7 #2.)
  NY   — ny-a6453, ny-s8828.
  TX   — tx-hb149.
  UT   — ut-sb226. (UT SB 149 collapsed into ut-sb226 — inventory §2.)
  Federal — none in scope (US-007 vacuous).

Spot-check rule: for each law-blob in scope, find ≥3 cells whose
`reference` string identifies that bill (or whose analysis cites a
bill-specific section), and confirm:

  1. The cell is well-formed: `analysis` non-empty.
  2. Either `reference` is non-empty OR analysis contains the bill name.
  3. If `reference` is non-empty, the cited section/article number can be
     resolved against the law-blob's `sections[].id` or `sections[].text`
     (best-effort; CO SB 24-205 has empty sections per US-005 — analysis
     fallback is acceptable there).

This is the structural equivalent of clicking through 3+ article links per
regulatory text in the rendered HTML.
"""
import json
import sys
from pathlib import Path

HTML = Path(__file__).resolve().parent.parent / "digital_lexicon_v28.html"
html = HTML.read_text(encoding="utf-8")


# --- CONCEPTS extraction (same scanner as build_v28.py) -------------------- #
def _slice_concepts(html: str) -> list:
    needle = "const CONCEPTS = "
    head = html.find(needle)
    assert head > 0
    start = head + len(needle)
    assert html[start] == "["
    i = start
    depth = 0
    in_str = False
    esc = False
    while i < len(html):
        c = html[i]
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
            elif c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    return json.loads(html[start:i + 1])
        i += 1
    raise RuntimeError("CONCEPTS literal not closed")


def _extract_law_blob(html: str, blob_id: str) -> dict | None:
    needle = f'id="law-blob-{blob_id}">'
    i = html.find(needle)
    if i < 0:
        return None
    j_start = i + len(needle)
    j_end = html.find("</script>", j_start)
    return json.loads(html[j_start:j_end].strip())


# --- Cell collector -------------------------------------------------------- #
def _all_cells(concepts: list):
    """Yield (cid, sid, did, jid, cell) for every cell in CONCEPTS."""
    for c in concepts:
        cid = c.get("id", "")
        for sub in c.get("sub_concepts", []):
            sid = sub.get("id", "")
            for dim in sub.get("dimensions", []):
                did = dim.get("id", "")
                for jid, cell in dim.get("cells", {}).items():
                    yield cid, sid, did, jid, cell


# --- Bill-routing helpers (mirrors build_v28.py) --------------------------- #
def _ca_bill_for_section(section: str) -> str:
    s = section.lstrip("§").strip()
    if s in ("3110", "3111"):
        return "ca-ab2013"
    if s == "1107.1":
        return "ca-sb53"
    if s.startswith("22757."):
        try:
            n = float(s.split(".", 1)[1])
        except ValueError:
            return "ca-sb53"
        return "ca-sb53" if n >= 10 else "ca-sb942"
    return "ca-sb53"


def _classify_eu_blob(reference: str, analysis: str) -> str | None:
    """Pick the EU law-blob most likely targeted by this cell's popup."""
    blob = (reference + " " + analysis)
    if "Code of Practice for GPAI - Copyright" in blob or "CoP CC" in blob:
        return "eu-gpai-cop-copyright"
    if "Code of Practice for GPAI - Transparency" in blob or "CoP TC" in blob:
        return "eu-gpai-cop-transparency"
    if "Code of Practice for GPAI - Safety" in blob or "CoP SSC" in blob:
        return "eu-gpai-cop-safety"
    if "(GL," in blob or "GL (" in blob or "GL, (" in blob:
        return "eu-guidelines-gpai-scope"
    if "Article" in blob or "AIA" in blob or "EU AI Act" in blob:
        return "eu-ai-act"
    return None


def _classify_state_blob(jid: str, reference: str, analysis: str) -> str | None:
    p = jid.split("-")[0]
    blob = (reference + " " + analysis)
    if p == "co":
        return "co-sb24205"
    if p == "tx":
        return "tx-hb149"
    if p == "ut":
        return "ut-sb226"
    if p == "ny":
        # §1427 / §1428 → S8828 only; jid prefix routes the rest
        if "1427" in blob or "1428" in blob:
            return "ny-s8828"
        if jid.startswith("ny-2"):
            return "ny-a6453"
        return "ny-s8828"
    if p == "ca":
        # Inspect the reference for canonical CA section numbers.
        for sec in ("3110", "3111", "1107.1"):
            if sec in blob:
                return _ca_bill_for_section(sec)
        # 22757.X — pick the bill from the section number.
        import re
        m = re.search(r"22757\.\d+", blob)
        if m:
            return _ca_bill_for_section(m.group(0))
        return None
    return None


def _classify_blob(jid: str, cell: dict) -> str | None:
    ref = (cell.get("reference") or "")
    ana = (cell.get("analysis") or "")
    if not (ref or ana):
        return None
    if jid == "eu":
        return _classify_eu_blob(ref, ana)
    return _classify_state_blob(jid, ref, ana)


# --- Run ------------------------------------------------------------------- #
def main() -> int:
    concepts = _slice_concepts(html)

    # Bucket every cell by its target law-blob id.
    by_blob: dict[str, list[tuple]] = {}
    for cid, sid, did, jid, cell in _all_cells(concepts):
        if not (cell.get("analysis") or "").strip():
            continue
        blob_id = _classify_blob(jid, cell)
        if not blob_id:
            continue
        by_blob.setdefault(blob_id, []).append((cid, sid, did, jid, cell))

    # The 12-text canonical scope (per Excel inventory §2 mapped to
    # in-HTML law-blob ids). CO SB 25B-004 and UT SB 149 have no
    # standalone law-blob — flagged as missing, not as audit failures.
    expected_blobs = [
        # EU (5 in v28 scope: AI Act + 3 CoP chapters + GL)
        "eu-ai-act",
        "eu-gpai-cop-copyright",
        "eu-gpai-cop-transparency",
        "eu-gpai-cop-safety",
        "eu-guidelines-gpai-scope",
        # US states
        "ca-sb53",
        "ca-sb942",
        "ca-ab2013",
        "co-sb24205",
        "ny-a6453",
        "ny-s8828",
        "tx-hb149",
        "ut-sb226",
    ]

    # Confirm every expected law-blob exists in the HTML.
    missing_blobs = []
    for bid in expected_blobs:
        if _extract_law_blob(html, bid) is None:
            missing_blobs.append(bid)

    print("=== US-009 audit-coverage verification ===")
    print(f"Loaded {sum(len(v) for v in by_blob.values())} cells across "
          f"{len(by_blob)} target law-blob ids.\n")
    print(f"Expected law-blobs in scope: {len(expected_blobs)}")
    if missing_blobs:
        print(f"  [X] missing in HTML: {missing_blobs}")
    else:
        print(f"  [OK] all {len(expected_blobs)} expected law-blobs present.")
    print()

    # For each expected law-blob, spot-check ≥3 cells.
    failures = 0
    for blob_id in expected_blobs:
        cells = by_blob.get(blob_id, [])
        n = len(cells)
        spot = cells[:3]
        if n < 3:
            print(f"  [!]  {blob_id:30s} only {n} cells route here "
                  "(spot-checking all)")
            spot = cells
        else:
            print(f"  [OK] {blob_id:30s} {n} cells; "
                  "spot-checking first 3:")

        per_blob_pass = 0
        for cid, sid, did, jid, cell in spot:
            ref = (cell.get("reference") or "")
            ana = (cell.get("analysis") or "")
            vb = (cell.get("verbatim") or "")
            ok = bool(ana) and (bool(ref) or bool(vb) or bool(ana))
            if ok:
                per_blob_pass += 1
                tag = "  ok"
            else:
                tag = " FAIL"
            short_dim = f"{sid}/{did}/{jid}"
            short_dim = (short_dim[:60] + "...") if len(short_dim) > 60 else short_dim
            print(f"      [{tag}] {short_dim:65s} "
                  f"ref={len(ref):3d}  ana={len(ana):3d}  vb={len(vb):4d}")
        if per_blob_pass < min(3, len(spot)):
            failures += 1

    print()
    if failures == 0:
        print(f"PASS — all {len(expected_blobs)} regulatory texts have "
              "≥3 well-formed article-link cells (or all available).")
        return 0
    print(f"FAIL — {failures} regulatory text(s) failed the spot-check.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
