#!/usr/bin/env python3
"""Check the authoritative subsystem-version matrix and exposed banners."""
from __future__ import annotations

import csv
from pathlib import Path

from version_metadata import INCLUDE, render

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "metadata/subsystem-versions.tsv"
EXPECTED = {
    "BetterCP/M": ("-", "0.3", "completed baseline"),
    "CCP": ("1.0", "1.1", "completed"),
    "CPX": ("1.0", "1.0", "completed"),
    "BDOS": ("1.1", "1.1", "completed"),
    "RSX": ("1.0", "1.0", "completed"),
    "BIOS": ("1.0", "1.0", "completed"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    with MATRIX.open(newline="", encoding="utf-8") as source:
        rows = {row["component"]: row for row in csv.DictReader(source,
                                                                  delimiter="\t")}
    for component, expected in EXPECTED.items():
        require(component in rows, f"version matrix lacks {component}")
        row = rows[component]
        observed = (row["interface_version"], row["implementation_version"],
                    row["status"])
        require(observed == expected,
                f"{component} version is {observed!r}, expected {expected!r}")
    require(INCLUDE.read_text(encoding="ascii") == render(),
            "src/bdos/versions.inc is stale; run tools/version_metadata.py")
    banner = f"BetterCP/M {rows['BetterCP/M']['implementation_version']}"
    for relative in ("src/ccp/ccp.mac", "src/cpx/basic.mac"):
        text = (ROOT / relative).read_text(encoding="ascii")
        require(banner in text, f"{relative} does not expose {banner}")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    require(banner in readme, f"README does not identify {banner}")
    print(f"{banner}; CCP impl 1.1/API 1.0; BDOS impl 1.1/API 1.1; "
          "CPX, RSX, BIOS impl 1.0/API 1.0")


if __name__ == "__main__":
    main()
