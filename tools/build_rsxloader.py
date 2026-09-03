#!/usr/bin/env python3
"""Build the protected BRSX manager and ordered-chain loader."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from build_ccp import assemble

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/system/rsxloader.mac"
BUILD = ROOT / "build/system"
BASE = 0xD100


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
    # D470h..D4EFh is the downward-growing command-reloader stack; keep the
    # two independently built protected components from silently colliding.
    if len(data) > 0x370:
        raise SystemExit(f"RSX loader exceeds D100h..D46Fh: {len(data)} bytes")
    print(f"{hashlib.sha256(data).hexdigest()}  build/system/rsxloader.bin")
    print(f"RSX loader bytes: {len(data)}")


if __name__ == "__main__":
    main()
