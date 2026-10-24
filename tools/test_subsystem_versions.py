#!/usr/bin/env python3
"""Check the authoritative subsystem-version matrix and exposed banners."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from version_metadata import (CPX_INCLUDE, INCLUDE, RSX_INCLUDE, render,
                              render_manager)

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "metadata/subsystem-versions.tsv"
EXPECTED = {
    "BetterCP/M": ("-", "1.0", "completed baseline"),
    "CCP": ("1.0", "1.4", "completed"),
    "CPX": ("1.0", "1.3", "completed"),
    "BDOS": ("1.2", "1.9", "completed"),
    "RSX": ("1.0", "1.5", "completed"),
    "BIOS": ("1.7", "1.13", "completed"),
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
    require(CPX_INCLUDE.read_text(encoding="ascii") == render_manager("CPX", "CX_VERSION"),
            "src/utilities/cpxvers.inc is stale")
    require(RSX_INCLUDE.read_text(encoding="ascii") == render_manager("RSX", "RS_VERSION"),
            "src/utilities/rsxvers.inc is stale")
    package = json.loads((ROOT / 'metadata/release-package.json').read_text())
    require(package['version'] == '1.0' and package['status'] == 'in-progress',
            'release-package target/completion must remain distinct from core OS version')
    banner = f"BetterCP/M {rows['BetterCP/M']['implementation_version']}"
    # The visible system banner is owned by the resident command package; the
    # compact core CCP contains no user-facing sign-on text.
    for relative in ("src/cpx/rcp.mac",):
        text = (ROOT / relative).read_text(encoding="ascii")
        require(banner in text, f"{relative} does not expose {banner}")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    require(banner in readme, f"README does not identify {banner}")
    print(banner + "; " + "; ".join(
        f"{name} impl {rows[name]['implementation_version']}/API {rows[name]['interface_version']}"
        for name in ("CCP", "BDOS", "CPX", "RSX", "BIOS")))



if __name__ == "__main__":
    main()
