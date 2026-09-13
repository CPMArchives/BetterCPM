#!/usr/bin/env python3
"""Build the BRSX-v2 pre-publication validator overlay."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from build_ccp import assemble
from system_layout import LAYOUT

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/system/rsxvalidator.mac"
BUILD = ROOT / "build/system"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    text = SOURCE.read_text(encoding="ascii").replace(
        "        CSEG\n        .PHASE  ", "        ASEG\n        ORG     ").replace(
        "        .DEPHASE\n", "")
    data = assemble(args.assembler, text, BUILD / "rsxvalidator.bin",
                    BUILD / "rsxvalidator.lst", LAYOUT["RSX"])
    if not data or len(data) > 935:
        raise SystemExit(f"RSX validator exceeds its packed slot: {len(data)} bytes")
    print(f"{hashlib.sha256(data).hexdigest()}  build/system/rsxvalidator.bin")
    print(f"RSX validator bytes: {len(data)}")


if __name__ == "__main__":
    main()
