#!/usr/bin/env python3
"""Require complete public-function coverage in the unified-BDOS inventory."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "metadata/bdos-service-inventory.tsv"
SERVICES = {f"U{number:02d}" for number in range(1, 11)}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    with MATRIX.open(encoding="ascii", newline="") as source:
        rows = list(csv.DictReader(source, delimiter="\t"))
    require(rows, "empty BDOS service inventory")
    functions = [int(row["function"]) for row in rows]
    require(functions == list(range(13, 41)),
            f"expected exactly functions 13..40, got {functions}")
    used: set[str] = set()
    for row in rows:
        assigned = set(row["universal_services"].split(","))
        unknown = assigned - SERVICES
        require(not unknown,
                f"function {row['function']} names unknown services {unknown}")
        require(row["operation"] and row["current_entry"] and
                row["replacement_rule"],
                f"function {row['function']} has an incomplete inventory row")
        used.update(assigned)
    require(used == SERVICES,
            f"unreferenced universal services: {sorted(SERVICES - used)}")
    print("BDOS inventory covers functions 13..40 and universal services U01..U10")


if __name__ == "__main__":
    main()
