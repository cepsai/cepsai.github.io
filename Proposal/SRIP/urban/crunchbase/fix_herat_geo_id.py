#!/usr/bin/env python3
import pathlib

REMOVE_GEO = "Herat (1)"


def update_file(path: pathlib.Path) -> int:
    lines = path.read_text().splitlines(keepends=True)
    changed = 0
    kept = []
    for line in lines:
        if line.startswith(REMOVE_GEO + ","):
            changed += 1
            continue
        kept.append(line)
    if changed:
        path.write_text("".join(kept))
    return changed


def main() -> None:
    root = pathlib.Path("Proposal/SRIP/urban/crunchbase")
    total = 0
    missing = []
    for year in range(2000, 2026):
        path = root / f"{year}.csv"
        if not path.exists():
            missing.append(path.name)
            continue
        updated = update_file(path)
        if updated:
            print(f"{path.name}: updated {updated} row(s)")
        total += updated
    print(f"Total updates: {total}")
    if missing:
        print(f"Missing files (skipped): {', '.join(missing)}")


if __name__ == "__main__":
    main()
