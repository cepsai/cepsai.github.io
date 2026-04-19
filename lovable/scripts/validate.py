#!/usr/bin/env python3
"""Schema validator for founders.*.json. Run before serving the dashboard."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

REQUIRED_TOP = [
    "id", "name", "founders", "hq_country", "is_european", "problem_category",
    "traction_tier", "built_with_lovable_confidence", "narrative_short",
    "sources", "last_verified", "status", "dataset",
]

TRACTION_TIERS = {"T0", "T1", "T2", "T3", "T4", "T5", "TX"}
STATUS_VALUES = {"active", "pivoted", "dead", "unknown"}
DATASET_VALUES = {"balanced", "breadth", "both"}
CONFIDENCE_VALUES = {"confirmed", "likely", "partial"}
SOURCE_QUALITY_VALUES = {"disclosed_by_founder", "press_reported", "self_reported_social", "estimated", "unknown"}


def load_taxonomy() -> tuple[set[str], set[str]]:
    tax = json.loads((DATA / "taxonomy.json").read_text())
    cats = {c["id"] for c in tax["categories"]}
    subs = {s["id"] for c in tax["categories"] for s in c.get("subcategories", [])}
    return cats, subs


def validate_record(rec: dict, idx: int, cats: set[str], subs: set[str]) -> list[str]:
    errs: list[str] = []
    tag = f"[{idx}:{rec.get('id', '?')}]"

    for field in REQUIRED_TOP:
        if field not in rec:
            errs.append(f"{tag} missing required field '{field}'")

    if rec.get("traction_tier") not in TRACTION_TIERS:
        errs.append(f"{tag} invalid traction_tier {rec.get('traction_tier')!r}")
    if rec.get("status") not in STATUS_VALUES:
        errs.append(f"{tag} invalid status {rec.get('status')!r}")
    if rec.get("dataset") not in DATASET_VALUES:
        errs.append(f"{tag} invalid dataset {rec.get('dataset')!r}")
    if rec.get("built_with_lovable_confidence") not in CONFIDENCE_VALUES:
        errs.append(f"{tag} invalid built_with_lovable_confidence {rec.get('built_with_lovable_confidence')!r}")

    if rec.get("problem_category") not in cats:
        errs.append(f"{tag} problem_category {rec.get('problem_category')!r} not in taxonomy")
    psub = rec.get("problem_subcategory")
    if psub is not None and psub not in subs:
        errs.append(f"{tag} problem_subcategory {psub!r} not in taxonomy")

    hq = rec.get("hq_country")
    if hq is not None and (not isinstance(hq, str) or len(hq) != 2):
        errs.append(f"{tag} hq_country must be ISO-2 or null, got {hq!r}")

    founders = rec.get("founders") or []
    if not founders:
        errs.append(f"{tag} founders[] must have at least 1 entry")
    for i, f in enumerate(founders):
        if not f.get("name"):
            errs.append(f"{tag} founders[{i}].name is required")
        rc = f.get("residence_country")
        if rc is not None and (not isinstance(rc, str) or len(rc) != 2):
            errs.append(f"{tag} founders[{i}].residence_country must be ISO-2 or null, got {rc!r}")

    sources = rec.get("sources") or []
    if not sources:
        errs.append(f"{tag} sources[] must have at least 1 entry")
    for i, s in enumerate(sources):
        if not s.get("url"):
            errs.append(f"{tag} sources[{i}].url is required")

    tm = rec.get("traction_metric")
    if tm is not None and tm.get("source_quality") is not None:
        if tm["source_quality"] not in SOURCE_QUALITY_VALUES:
            errs.append(f"{tag} traction_metric.source_quality invalid: {tm['source_quality']!r}")

    # T3+ requires a dated source excerpt
    if rec.get("traction_tier") in {"T3", "T4", "T5"}:
        has_dated_excerpt = any(s.get("date") and s.get("excerpt") for s in sources)
        if not has_dated_excerpt:
            errs.append(f"{tag} T3+ tier requires at least one source with date AND excerpt")

    return errs


def main() -> int:
    cats, subs = load_taxonomy()
    total_errs = 0
    for fname in ["founders.balanced.json", "founders.breadth.json"]:
        path = DATA / fname
        records = json.loads(path.read_text())
        print(f"== {fname}: {len(records)} records ==")
        file_errs = 0
        seen_ids: dict[str, int] = {}
        for i, rec in enumerate(records):
            rid = rec.get("id")
            if rid in seen_ids:
                print(f"  [{i}:{rid}] duplicate id (first seen at index {seen_ids[rid]})")
                file_errs += 1
            else:
                seen_ids[rid] = i
            for err in validate_record(rec, i, cats, subs):
                print(f"  {err}")
                file_errs += 1
        print(f"  -> {file_errs} error(s)")
        total_errs += file_errs
    print(f"\nTotal errors across both files: {total_errs}")
    return 0 if total_errs == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
