#!/usr/bin/env python3
import pathlib

OLD_GEO = "Herat (NA) (NA)"
NEW_GEO = "Herat (1)"


def update_file(path: pathlib.Path) -> int:
    lines = path.read_text().splitlines(keepends=True)
    changed = 0
    for i, line in enumerate(lines):
        if line.startswith(OLD_GEO + ","):
            lines[i] = line.replace(OLD_GEO, NEW_GEO, 1)
            changed += 1
    if changed:
        path.write_text("".join(lines))
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
