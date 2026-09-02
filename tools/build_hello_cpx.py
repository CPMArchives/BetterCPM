#!/usr/bin/env python3
"""Build the relocatable HELLO.CPX module."""
from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

from build_basic_cpx import relocation_offsets
from build_ccp import assemble

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/cpx/hello.mac"
BUILD = ROOT / "build/cpx"
LINK_BASE = 0x8000
ALTERNATE_BASE = 0x8101


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    source = SOURCE.read_text(encoding="ascii")
    text = source.replace("        CSEG\n        .PHASE  ",
                          "        ASEG\n        ORG     ").replace(
                              "        .DEPHASE\n", "")
    data = assemble(args.assembler, text, BUILD / "hello.bin",
                    BUILD / "hello.lst", LINK_BASE)
    alternate_text = text.replace("CPXBASE         EQU     08000H",
                                  "CPXBASE         EQU     08101H")
    alternate = assemble(args.assembler, alternate_text,
                         BUILD / "hello-alt.bin", BUILD / "hello-alt.lst",
                         ALTERNATE_BASE)
    offsets = relocation_offsets(data, alternate)
    allocation = (len(data) + 0xFF) & ~0xFF
    if 512 + len(data) > 3 * 512:
        raise SystemExit(f"HELLO.CPX exceeds three module slots: {len(data)}")
    header = bytearray(512)
    struct.pack_into("<4sBBHHHHH", header, 0, b"BCX1", 1, 1, LINK_BASE,
                     len(data), allocation, 0, len(offsets))
    for index, offset in enumerate(offsets):
        struct.pack_into("<H", header, 16 + index * 2, offset)
    module = BUILD / "HELLO.CPX"
    module.write_bytes(header + data)
    print(f"{hashlib.sha256(data).hexdigest()}  {BUILD.relative_to(ROOT)}/hello.bin")
    print(f"HELLO.CPX bytes: {len(data)}; allocation: {allocation}; "
          f"relocations: {len(offsets)}; module: {len(module.read_bytes())}")


if __name__ == "__main__":
    main()
