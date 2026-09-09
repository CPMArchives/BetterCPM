#!/usr/bin/env python3
"""Build the relocatable RCP.CPX module."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path

from build_ccp import assemble
from build_cpx_module import make_module, relocation_offsets

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/cpx/rcp.mac"
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
    data = assemble(args.assembler, text, BUILD / "rcp.bin",
                    BUILD / "rcp.lst", LINK_BASE)
    alternate_text = text.replace("CPXBASE         EQU     08000H",
                                  "CPXBASE         EQU     08101H")
    alternate = assemble(args.assembler, alternate_text,
                         BUILD / "rcp-alt.bin", BUILD / "rcp-alt.lst",
                         ALTERNATE_BASE)
    offsets = relocation_offsets(data, alternate, ALTERNATE_BASE - LINK_BASE)
    module_data = make_module(
        name="RCP", version=(0, 2),
        commands=["DIR", "ERA", "TYPE", "REN", "USER", "CLS", "VER",
                  "COPY", "MOVE"],
        linked_base=LINK_BASE, code=data, relocations=offsets)
    module = BUILD / "RCP.CPX"
    module.write_bytes(module_data)
    allocation = (len(data) + 0xFF) & ~0xFF
    print(f"{hashlib.sha256(data).hexdigest()}  {BUILD.relative_to(ROOT)}/rcp.bin")
    print(f"RCP.CPX bytes: {len(data)}; allocation: {allocation}; "
          f"relocations: {len(offsets)}; module: {len(module.read_bytes())}")


if __name__ == "__main__":
    main()
