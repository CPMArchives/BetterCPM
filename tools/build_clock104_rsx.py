#!/usr/bin/env python3
"""Build the optional 104/105 clock frontends as a relocatable BRSX-v2 carrier."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from build_cpx_module import relocation_offsets
from build_ccp import assemble
from build_rsx_module import make_module

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/rsx"
BUILD = ROOT / "build/rsx"
LINK_BASE = 0x8000
ALTERNATE_BASE = 0x8101


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    for stem in ("T104C3", "T104Z8"):
        source = (SOURCE / (stem.lower() + ".mac")).read_text(encoding="ascii")
        source = source.replace("        INCLUDE clock104.inc", (SOURCE / "clock104.inc").read_text(encoding="ascii"))
        text = source.replace("        CSEG\n        .PHASE  ",
                              "        ASEG\n        ORG     ").replace(
                                  "        .DEPHASE\n", "")
        code = assemble(args.assembler, text, BUILD / f"{stem.lower()}.bin",
                        BUILD / f"{stem.lower()}.lst", LINK_BASE)
        alternate = assemble(
            args.assembler,
            text.replace("RSXBASE         EQU     08000H",
                         "RSXBASE         EQU     08101H"),
            BUILD / f"{stem.lower()}-alt.bin", BUILD / f"{stem.lower()}-alt.lst", ALTERNATE_BASE)
        relocations = relocation_offsets(code, alternate,
                                         ALTERNATE_BASE - LINK_BASE)
        carrier = make_module(name=stem, version=(1, 0), services=[104, 105],
                              linked_base=LINK_BASE, code=code,
                              relocations=relocations, entry_offset=8,
                              format_version=2)
        allocation = int.from_bytes(carrier[14:16], "little")
        (BUILD / f"{stem}.RSX").write_bytes(carrier)
        print(f"{hashlib.sha256(code).hexdigest()}  build/rsx/{stem.lower()}.bin")
        print(f"{stem}.RSX bytes: {len(code)}; allocation: {allocation}; "
              f"relocations: {len(relocations)}; carrier: {len(carrier)}")


if __name__ == "__main__":
    main()
