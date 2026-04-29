"""audit_us_state_compare.py — US-008 mismatch finder.

For every US-state cell extracted in `us008_state_cells.json`:
  1. Parse article/section references from the analysis text
     (e.g. "(§6-1-1704)", "(22757.13.)", "§ 1422", "§13-75-103").
  2. Compare against the cell's `reference` field.
  3. Flag mismatches, missing citations, and reference-only-without-analysis
     situations. Emit a per-jurisdiction summary report.

This is a heuristic checker — final adjudication still requires reading
the Excel inventory's per-attribute reference (see
`v28_excel_inventory.md` §4–§6).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
CELLS = HERE / "outputs" / "us008_state_cells.json"
OUT = HERE / "outputs" / "us008_compare.md"


# ---- Reference patterns ---------------------------------------------------- #
# Citations as they appear in the v28 analysis text (NOT in reference field).
# Note: many cells use no `§` prefix (e.g. "(22757.11.)" or "(§ 1422)"
# depending on jurisdiction).
RE_CO_ANALYSIS = re.compile(r"§\s*6-1-170[1-7](?:\s*\(\d+\)(?:\([a-z]\))?)?")
RE_CA_ANALYSIS = re.compile(
    r"§?\s*22757\.\d+(?:\.\s*\([a-z0-9]+\))?(?:\.|\b)"
    r"|§?\s*(?:3110|3111|1107\.1)(?:\.\s*\([a-z]\))?(?:\.|\b)"
)
RE_NY_ANALYSIS = re.compile(
    r"§\s*14[2-3]\d(?:\s*\((\d+)\)(?:\([a-z]\))?)?",
)
RE_TX_ANALYSIS = re.compile(
    r"§?\s*552\.\d{3}(?:\.\s*\([a-z]\))?(?:\.|\b)"
)
RE_UT_ANALYSIS = re.compile(
    r"§\s*13-75-10[1-5](?:\s*\(\d+\))?"
)


def jur_prefix(jid: str) -> str:
    return jid.split("-")[0]


PATTERN_BY_PREFIX = {
    "ca": RE_CA_ANALYSIS,
    "co": RE_CO_ANALYSIS,
    "ny": RE_NY_ANALYSIS,
    "tx": RE_TX_ANALYSIS,
    "ut": RE_UT_ANALYSIS,
}


def _normalise_cite(s: str) -> str:
    """Normalise a citation string: strip whitespace, leading §,
    trailing dots, and any internal whitespace runs. After normalisation
    `(22757.1.)`, `§22757.1`, `22757.1.` all collapse to `22757.1`."""
    s = s.strip().lstrip("§").strip()
    s = re.sub(r"\s+", "", s)
    s = s.rstrip(".")
    return s


def cite_in_analysis(analysis: str, jid: str) -> set[str]:
    """Return the set of distinct article-style citations in the analysis,
    normalised so that `§22757.1`, `(22757.1.)`, `22757.1` all match.

    Also includes parent-paragraph forms so that a sub-paragraph cite
    like `1420(9)(a)` is considered satisfied by a reference that names
    `1420(9)` or `1420`."""
    pat = PATTERN_BY_PREFIX[jur_prefix(jid)]
    raw = {_normalise_cite(m.group(0)) for m in pat.finditer(analysis or "")}
    expanded: set[str] = set()
    for s in raw:
        expanded.add(s)
        # Strip trailing `(letter)` then trailing `(number)` to surface
        # the section-only prefix.
        for tail_re in (r"\([a-z]\)$", r"\(\d+\)$"):
            t = re.sub(tail_re, "", s)
            if t and t != s:
                expanded.add(t)
                s = t
    return expanded


def cite_in_reference(ref: str, jid: str) -> set[str]:
    pat = PATTERN_BY_PREFIX[jur_prefix(jid)]
    out = {_normalise_cite(m.group(0)) for m in pat.finditer(ref or "")}
    # Allow a sub-paragraph reference (e.g. `1420(3)(a)`) to satisfy a
    # less-specific analysis cite like `1420` — the more-specific ref is
    # *more* informative, not less. Treat the section-only prefix as also
    # present.
    extra = set()
    for s in out:
        m = re.match(r"([0-9]+(?:-[0-9]+){0,2}|[0-9]+\.\d+)", s)
        if m:
            extra.add(m.group(1))
    return out | extra


def main() -> None:
    rows = json.loads(CELLS.read_text(encoding="utf-8"))
    findings: list[dict] = []

    for r in rows:
        analysis = r["analysis"] or ""
        ref = r["reference"] or ""
        verbatim = r["verbatim"] or ""
        jid = r["jid"]

        a_cites = cite_in_analysis(analysis, jid)
        r_cites = cite_in_reference(ref, jid)

        # Skip cells whose analysis is just "-" or short non-citation text.
        if analysis.strip() == "-":
            continue

        # Treat an analysis cite as satisfied if any prefix of it is in
        # the reference set (e.g. analysis `1420(9)(a)` is covered by ref
        # `1420(9)` or `1420`).
        def _covered(cite: str, ref_set: set[str]) -> bool:
            if cite in ref_set:
                return True
            cur = cite
            for tail_re in (r"\([a-z]\)$", r"\(\d+\)$"):
                cur2 = re.sub(tail_re, "", cur)
                if cur2 != cur and cur2 in ref_set:
                    return True
                cur = cur2
            return False

        unsatisfied = {c for c in a_cites if not _covered(c, r_cites)}

        flags = []
        if a_cites and not ref.strip():
            flags.append(("MISSING_REF", sorted(a_cites)))
        elif a_cites and r_cites and not (a_cites & r_cites) and unsatisfied:
            flags.append(("REF_MISMATCH", {
                "analysis_cites": sorted(a_cites),
                "ref_cites":      sorted(r_cites),
            }))
        elif unsatisfied and a_cites and r_cites:
            flags.append(("EXTRA_IN_ANALYSIS", sorted(unsatisfied)))

        if flags:
            findings.append({
                "concept": r["concept"],
                "sub_concept": r["sub_concept"],
                "dim_id": r["dim_id"],
                "dim_title": r["dim_title"],
                "jid": jid,
                "analysis_short": (analysis[:200].replace("\n", " ") + ("…" if len(analysis) > 200 else "")),
                "reference": ref,
                "flags": flags,
            })

    # Group findings by jurisdiction for the report.
    by_jur: dict[str, list] = {}
    for f in findings:
        p = jur_prefix(f["jid"])
        by_jur.setdefault(p, []).append(f)

    lines = ["# US-008 audit — state article-link findings\n"]
    lines.append(f"Total findings: {len(findings)}\n")
    for jp in sorted(by_jur):
        lines.append(f"\n## {jp.upper()} ({len(by_jur[jp])} findings)\n")
        for f in by_jur[jp]:
            lines.append(
                f"- `{f['concept']}/{f['sub_concept']}/{f['dim_id']}` "
                f"({f['jid']})"
            )
            for tag, payload in f["flags"]:
                lines.append(f"  - **{tag}**: `{payload}`")
            lines.append(f"  - ref: `{f['reference'] or '(empty)'}`")
            lines.append(f"  - analysis: {f['analysis_short']}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"total findings: {len(findings)}")


if __name__ == "__main__":
    main()
