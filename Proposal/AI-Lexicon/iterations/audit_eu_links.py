"""audit_eu_links.py — US-006 audit helper.

Walks the CONCEPTS literal in digital_lexicon_v28.html and emits a CSV-like
listing of every (concept, sub-concept, dimension, jid='eu', analysis,
verbatim, reference) cell. Used to compare what the v28 popups actually say
against the Excel inventory in v28_excel_inventory.md.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
HTML = HERE / "digital_lexicon_v28.html"


def extract_concepts(html: str) -> list:
    m = re.search(r"const CONCEPTS = (\[.*?\]);\s*\n", html, re.DOTALL)
    if not m:
        m = re.search(r"const CONCEPTS = (\[.*?\]);\n", html, re.DOTALL)
    if not m:
        # Just find from `const CONCEPTS = [` to the matching `];` at end of line
        start = html.find("const CONCEPTS = [")
        if start < 0:
            raise SystemExit("CONCEPTS literal not found")
        # Find the closing `];` at end of a line
        depth = 0
        i = start + len("const CONCEPTS = ")
        in_str = False
        esc = False
        end = -1
        while i < len(html):
            c = html[i]
            if in_str:
                if esc:
                    esc = False
                elif c == '\\':
                    esc = True
                elif c == '"':
                    in_str = False
            else:
                if c == '"':
                    in_str = True
                elif c == '[':
                    depth += 1
                elif c == ']':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            i += 1
        if end < 0:
            raise SystemExit("CONCEPTS literal closing bracket not found")
        return json.loads(html[start + len("const CONCEPTS = "):end])
    return json.loads(m.group(1))


def main() -> None:
    html = HTML.read_text(encoding="utf-8")
    concepts = extract_concepts(html)
    rows = []
    for c in concepts:
        cid = c.get("id")
        ctitle = c.get("title")
        for sub in c.get("sub_concepts", []):
            sid = sub.get("id")
            stitle = sub.get("title", "")
            for dim in sub.get("dimensions", []):
                did = dim.get("id")
                dtitle = dim.get("title", "")
                cells = dim.get("cells", {})
                for jid, cell in cells.items():
                    if jid != "eu":
                        continue
                    rows.append({
                        "concept": cid,
                        "concept_title": ctitle,
                        "sub_concept": sid,
                        "sub_title": stitle,
                        "dim_id": did,
                        "dim_title": dtitle,
                        "analysis": (cell.get("analysis") or "").strip(),
                        "verbatim": (cell.get("verbatim") or "").strip(),
                        "reference": (cell.get("reference") or "").strip(),
                    })
    print(f"Found {len(rows)} EU cells across {len(concepts)} concepts")
    out = HERE / "outputs" / "us006_eu_cells.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        f.write("concept\tsub_concept\tdim_title\treference\tanalysis_short\n")
        for r in rows:
            short = r["analysis"][:200].replace("\n", " ").replace("\t", " ")
            ref = r["reference"].replace("\n", " ").replace("\t", " ")
            f.write(
                f"{r['concept']}\t{r['sub_concept']}\t{r['dim_title']}\t{ref}\t{short}\n"
            )
    print(f"wrote {out}")
    # Also dump full json for any tool to consume
    out_json = HERE / "outputs" / "us006_eu_cells.json"
    out_json.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {out_json}")


if __name__ == "__main__":
    main()
