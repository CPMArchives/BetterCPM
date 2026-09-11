#!/usr/bin/env python3
"""Build the second BRSX v1 proof carrier, FDF.RSX."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from build_cpx_module import relocation_offsets
from build_ccp import assemble
from build_rsx_module import make_module

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/rsx/fdf.mac"
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
    code = assemble(args.assembler, text, BUILD / "fdf.bin",
                    BUILD / "fdf.lst", LINK_BASE)
    alternate = assemble(
        args.assembler,
        text.replace("RSXBASE         EQU     08000H",
                     "RSXBASE         EQU     08101H"),
        BUILD / "fdf-alt.bin", BUILD / "fdf-alt.lst", ALTERNATE_BASE)
    offsets = relocation_offsets(code, alternate, ALTERNATE_BASE - LINK_BASE)
    carrier = make_module(name="FDF", version=(0, 1), services=[209],
                          linked_base=LINK_BASE, code=code,
                          relocations=offsets)
    (BUILD / "FDF.RSX").write_bytes(carrier)
    print(f"{hashlib.sha256(code).hexdigest()}  build/rsx/fdf.bin")
    print(f"FDF.RSX bytes: {len(code)}; relocations: {len(offsets)}; "
          f"carrier: {len(carrier)}")


if __name__ == "__main__":
    main()
