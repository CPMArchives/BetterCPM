#!/usr/bin/env python3
"""Build the z80pack RTC TIME provider as a relocatable BRSX carrier."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from build_cpx_module import relocation_offsets
from build_ccp import assemble
from build_rsx_module import make_module

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/rsx/zprtc.mac"
BUILD = ROOT / "build/rsx"
LINK_BASE = 0x8000
ALTERNATE_BASE = 0x8101


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path.home() / "bin/z80asm")
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    source = SOURCE.read_text(encoding="ascii")
    text = source.replace("        CSEG\n        .PHASE  ",
                          "        ASEG\n        ORG     ").replace(
                              "        .DEPHASE\n", "")
    code = assemble(args.assembler, text, BUILD / "zprtc.bin",
                    BUILD / "zprtc.lst", LINK_BASE)
    alternate = assemble(
        args.assembler,
        text.replace("RSXBASE         EQU     08000H",
                     "RSXBASE         EQU     08101H"),
        BUILD / "zprtc-alt.bin", BUILD / "zprtc-alt.lst",
        ALTERNATE_BASE)
    relocations = relocation_offsets(code, alternate,
                                     ALTERNATE_BASE - LINK_BASE)
    allocation = (len(code) + 0xFF) & ~0xFF
    carrier = make_module(name="ZPRTC", version=(0, 1), services=[208],
                          linked_base=LINK_BASE, code=code,
                          relocations=relocations, allocation=allocation)
    output = BUILD / "ZPRTC.RSX"
    output.write_bytes(carrier)
    print(f"{hashlib.sha256(code).hexdigest()}  build/rsx/zprtc.bin")
    print(f"ZPRTC.RSX bytes: {len(code)}; allocation: {allocation}; "
          f"relocations: {len(relocations)}; carrier: {len(carrier)}")


if __name__ == "__main__":
    main()
