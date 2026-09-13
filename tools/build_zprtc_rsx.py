#!/usr/bin/env python3
"""Build the z80pack RTC TIME provider as a relocatable BRSX carrier."""
from __future__ import annotations

import argparse
import hashlib
import re
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
    listing = (BUILD / "zprtc.lst").read_text(errors="replace")
    service = int(re.search(r"^([0-9a-f]{4}).*\bZP_SERVICE:", listing,
                            re.M | re.I).group(1), 16) - LINK_BASE
    carrier = make_module(name="ZPRTC", version=(0, 2), services=[],
                          linked_base=LINK_BASE, code=code,
                          relocations=relocations, entry_offset=8,
                          format_version=2,
                          callable_services=[(b"TIME", 1, 0, service, 0)])
    allocation = int.from_bytes(carrier[14:16], "little")
    output = BUILD / "ZPRTC.RSX"
    output.write_bytes(carrier)
    print(f"{hashlib.sha256(code).hexdigest()}  build/rsx/zprtc.bin")
    print(f"ZPRTC.RSX bytes: {len(code)}; allocation: {allocation}; "
          f"relocations: {len(relocations)}; carrier: {len(carrier)}")


if __name__ == "__main__":
    main()
