"""audit_us_state_links.py — US-008 audit helper.

Walks the CONCEPTS literal in digital_lexicon_v28.html and dumps every
US-state cell (jurisdictions: ca, co, ny, tx, ut — plus the per-row
bill-suffixed variants like ca-1-developer or ny-2-large-developer) to
TSV/JSON for cross-checking against the Excel inventory.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
HTML = HERE / "digital_lexicon_v28.html"

US_PREFIXES = ("ca", "co", "ny", "tx", "ut")


def extract_concepts(html: str) -> list:
    start = html.find("const CONCEPTS = [")
    if start < 0:
        raise SystemExit("CONCEPTS literal not found")
    i = start + len("const CONCEPTS = ")
    depth = 0
    in_str = False
    esc = False
    end = -1
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
                    end = i + 1
                    break
        i += 1
    if end < 0:
        raise SystemExit("CONCEPTS literal closing bracket not found")
    return json.loads(html[start + len("const CONCEPTS = "):end])


def is_us(jid: str) -> bool:
    if jid in US_PREFIXES:
        return True
    for p in US_PREFIXES:
        if jid.startswith(p + "-"):
            return True
    return False


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
                    if not is_us(jid):
                        continue
                    rows.append({
                        "concept": cid,
                        "concept_title": ctitle,
                        "sub_concept": sid,
                        "sub_title": stitle,
                        "dim_id": did,
                        "dim_title": dtitle,
                        "jid": jid,
                        "analysis": (cell.get("analysis") or "").strip(),
                        "verbatim": (cell.get("verbatim") or "").strip(),
                        "reference": (cell.get("reference") or "").strip(),
                    })

    print(f"Found {len(rows)} US-state cells across {len(concepts)} concepts")
    out = HERE / "outputs" / "us008_state_cells.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        f.write(
            "concept\tsub_concept\tdim_id\tdim_title\tjid\treference\t"
            "analysis_short\n"
        )
        for r in rows:
            short = r["analysis"][:240].replace("\n", " ").replace("\t", " ")
            ref = r["reference"].replace("\n", " ").replace("\t", " ")
            f.write(
                f"{r['concept']}\t{r['sub_concept']}\t{r['dim_id']}\t"
                f"{r['dim_title']}\t{r['jid']}\t{ref}\t{short}\n"
            )
    print(f"wrote {out}")
    out_json = HERE / "outputs" / "us008_state_cells.json"
    out_json.write_text(
        json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8",
    )
    print(f"wrote {out_json}")

    # Bucket by jurisdiction prefix for a quick overview.
    counts: dict[str, int] = {}
    for r in rows:
        j = r["jid"].split("-")[0]
        counts[j] = counts.get(j, 0) + 1
    print("By jurisdiction prefix:")
    for k in sorted(counts):
        print(f"  {k}: {counts[k]}")


if __name__ == "__main__":
    main()
