#!/usr/bin/env python3
"""Build the protected BRSX manager and ordered-chain loader."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from system_layout import LAYOUT, expand_layout

from build_ccp import assemble

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/system/rsxloader.mac"
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
    # Keep the independently linked loader and extension adapters disjoint.
    if len(data) > LAYOUT["EXTENSIONS"] - BASE:
        raise SystemExit(f"RSX loader exceeds its packed slot: {len(data)} bytes")
    print(f"{hashlib.sha256(data).hexdigest()}  build/system/rsxloader.bin")
    print(f"RSX loader bytes: {len(data)}")


if __name__ == "__main__":
    main()
