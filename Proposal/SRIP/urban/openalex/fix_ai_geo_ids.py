#!/usr/bin/env python3
import pathlib

TARGETS = {
    "Roma (Rome) (NA)": "Roma (Rome) (1049)",
    "Nice-Cannes (NA)": "Nice-Cannes (714)",
    "Windhoek (NA)": "Windhoek (1218)",
}
DOMAIN = "Artificial Intelligence"


def update_file(path: pathlib.Path) -> int:
    lines = path.read_text().splitlines(keepends=True)
    changed = 0
    for i, line in enumerate(lines):
        if DOMAIN not in line:
            continue
        for old_geo, new_geo in TARGETS.items():
            needle = f'"{old_geo}","{DOMAIN}",'
            if needle in line:
                lines[i] = line.replace(f'"{old_geo}"', f'"{new_geo}"', 1)
                changed += 1
                break
    if changed:
        path.write_text("".join(lines))
    return changed


def main() -> None:
    root = pathlib.Path("Proposal/SRIP/urban/openalex")
    total = 0
    missing = []
    for year in range(2000, 2026):
        path = root / f"{year}.csv"
        if not path.exists():
            missing.append(str(path.name))
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
