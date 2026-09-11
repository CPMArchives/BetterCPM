#!/usr/bin/env python3
"""Build the BRSX-v2 TEST callable-service qualification provider."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from build_cpx_module import relocation_offsets
from build_ccp import assemble
from build_rsx_module import make_module

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/rsx/testsvc.mac"
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
    code = assemble(args.assembler, text, BUILD / "testsvc.bin",
                    BUILD / "testsvc.lst", LINK_BASE)
    alternate = assemble(
        args.assembler,
        text.replace("RSXBASE         EQU     08000H",
                     "RSXBASE         EQU     08101H"),
        BUILD / "testsvc-alt.bin", BUILD / "testsvc-alt.lst", ALTERNATE_BASE)
    relocations = relocation_offsets(code, alternate, ALTERNATE_BASE - LINK_BASE)
    service_offset = code.index(bytes((0x21, 0x53, 0x52, 0x7D, 0xC9)))
    carrier = make_module(
        name="TEST", version=(0, 1), services=[], linked_base=LINK_BASE,
        code=code, relocations=relocations, entry_offset=8, format_version=2,
        callable_services=[(b"TEST", 1, 0, service_offset, 1)])
    (BUILD / "TEST.RSX").write_bytes(carrier)
    print(f"{hashlib.sha256(code).hexdigest()}  build/rsx/testsvc.bin")
    print(f"TEST.RSX bytes: {len(code)}; relocations: {len(relocations)}; "
          f"carrier: {len(carrier)}")


if __name__ == "__main__":
    main()
