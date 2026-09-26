#!/usr/bin/env python3
"""Build the P2DOS clock frontend as a relocatable BRSX-v2 carrier."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from build_cpx_module import relocation_offsets
from build_ccp import assemble
from build_rsx_module import make_module

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/rsx/p2dos.mac"
BUILD = ROOT / "build/rsx"
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
    code = assemble(args.assembler, text, BUILD / "p2dos.bin",
                    BUILD / "p2dos.lst", LINK_BASE)
    alternate = assemble(
        args.assembler,
        text.replace("RSXBASE         EQU     08000H",
                     "RSXBASE         EQU     08101H"),
        BUILD / "p2dos-alt.bin", BUILD / "p2dos-alt.lst", ALTERNATE_BASE)
    relocations = relocation_offsets(code, alternate,
                                     ALTERNATE_BASE - LINK_BASE)
    carrier = make_module(name="P2DOS", version=(1, 0), services=[200, 201],
                          linked_base=LINK_BASE, code=code,
                          relocations=relocations, entry_offset=8,
                          format_version=2)
    allocation = int.from_bytes(carrier[14:16], "little")
    (BUILD / "P2DOS.RSX").write_bytes(carrier)
    print(f"{hashlib.sha256(code).hexdigest()}  build/rsx/p2dos.bin")
    print(f"P2DOS.RSX bytes: {len(code)}; allocation: {allocation}; "
          f"relocations: {len(relocations)}; carrier: {len(carrier)}")


if __name__ == "__main__":
    main()
