#!/usr/bin/env python3
"""Build the production BRSX transaction entry."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from system_layout import LAYOUT, expand_layout

from build_ccp import assemble

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/system/r3entry.mac"
BUILD = ROOT / "build/system"
BASE = LAYOUT["RSX"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    text = SOURCE.read_text(encoding="ascii").replace(
        "        CSEG\n        .PHASE  ", "        ASEG\n        ORG     ").replace(
        "        .DEPHASE\n", "")
    data = assemble(args.assembler, text, BUILD / "rsxloader.bin",
                    BUILD / "rsxloader.lst", BASE)
    # Raw replacement preserves the final nine stack bytes and gateway.
    if len(data) > 1012:
        raise SystemExit(f"RSX transaction entry exceeds its safe slot: {len(data)} bytes")
    print(f"{hashlib.sha256(data).hexdigest()}  build/system/rsxloader.bin")
    print(f"RSX transaction entry bytes: {len(data)}")


if __name__ == "__main__":
    main()
