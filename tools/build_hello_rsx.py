#!/usr/bin/env python3
"""Build the compact one-sector HELLO.RSX proof carrier."""
from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

from build_basic_cpx import relocation_offsets
from build_ccp import assemble

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/rsx/hello.mac"
BUILD = ROOT / "build/rsx"
LINK_BASE = 0x8000
ALTERNATE_BASE = 0x8101
PAYLOAD_OFFSET = 64


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
    offsets = relocation_offsets(data, alternate)
    # The proof module deliberately claims one KiB.  Besides leaving realistic
    # growth room, this makes the protected-memory cost visible in CP/M's
    # whole-K TPA convention while load/unload is being verified.
    allocation = max(0x400, (len(data) + 0xFF) & ~0xFF)
    if PAYLOAD_OFFSET + len(data) > 512 or len(offsets) > 24:
        raise SystemExit("HELLO.RSX exceeds compact one-sector carrier")
    carrier = bytearray(512)
    struct.pack_into("<4sHHHHH", carrier, 0, b"BRX1", LINK_BASE, len(data),
                     allocation, len(offsets), PAYLOAD_OFFSET)
    for index, offset in enumerate(offsets):
        struct.pack_into("<H", carrier, 16 + index * 2, offset)
    carrier[PAYLOAD_OFFSET:PAYLOAD_OFFSET + len(data)] = data
    output = BUILD / "HELLO.RSX"
    output.write_bytes(carrier)
    print(f"{hashlib.sha256(data).hexdigest()}  build/rsx/hello.bin")
    print(f"HELLO.RSX bytes: {len(data)}; allocation: {allocation}; "
          f"relocations: {len(offsets)}; carrier: 512")


if __name__ == "__main__":
    main()
