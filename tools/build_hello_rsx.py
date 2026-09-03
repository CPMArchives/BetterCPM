#!/usr/bin/env python3
"""Build the BRSX version-1 HELLO.RSX carrier."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from build_cpx_module import relocation_offsets
from build_ccp import assemble
from build_rsx_module import make_module

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/rsx/hello.mac"
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
    data = assemble(args.assembler, text, BUILD / "hello.bin",
                    BUILD / "hello.lst", LINK_BASE)
    alternate = assemble(args.assembler,
                         text.replace("RSXBASE         EQU     08000H",
                                      "RSXBASE         EQU     08101H"),
                         BUILD / "hello-alt.bin", BUILD / "hello-alt.lst",
                         ALTERNATE_BASE)
    offsets = relocation_offsets(data, alternate, ALTERNATE_BASE - LINK_BASE)
    # The proof module deliberately claims one KiB.  Besides leaving realistic
    # growth room, this makes the protected-memory cost visible in CP/M's
    # whole-K TPA convention while load/unload is being verified.
    allocation = max(0x400, (len(data) + 0xFF) & ~0xFF)
    carrier = make_module(name="HELLO", version=(0, 1), services=[201],
                          linked_base=LINK_BASE, code=data, relocations=offsets,
                          allocation=allocation)
    output = BUILD / "HELLO.RSX"
    output.write_bytes(carrier)
    print(f"{hashlib.sha256(data).hexdigest()}  build/rsx/hello.bin")
    print(f"HELLO.RSX bytes: {len(data)}; allocation: {allocation}; "
          f"relocations: {len(offsets)}; carrier: {len(carrier)}")


if __name__ == "__main__":
    main()
