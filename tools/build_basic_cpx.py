#!/usr/bin/env python3
"""Build the relocatable proof-of-concept BASIC.CPX module."""
from __future__ import annotations

import argparse
import hashlib
import struct
import subprocess
import tempfile
from pathlib import Path

from build_ccp import assemble

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/cpx/basic.mac"
BUILD = ROOT / "build/cpx"
LINK_BASE = 0x8000
ALTERNATE_BASE = 0x8101


def relocation_offsets(linked: bytes, alternate: bytes) -> list[int]:
    if len(linked) != len(alternate):
        raise SystemExit("BASIC.CPX alternate-origin size changed")
    delta = ALTERNATE_BASE - LINK_BASE
    changed = {index for index, pair in enumerate(zip(linked, alternate))
               if pair[0] != pair[1]}
    candidates = []
    for offset in range(len(linked) - 1):
        old = int.from_bytes(linked[offset:offset + 2], "little")
        new = int.from_bytes(alternate[offset:offset + 2], "little")
        covered = changed.intersection((offset, offset + 1))
        if covered and (old + delta) & 0xFFFF == new:
            candidates.append((offset, covered))
    selected, uncovered = [], set(changed)
    while uncovered:
        useful = [(len(covered & uncovered), offset, covered)
                  for offset, covered in candidates if covered & uncovered]
        if not useful:
            raise SystemExit(f"unexplained BASIC.CPX relocation bytes: {sorted(uncovered)}")
        _score, offset, covered = max(useful)
        selected.append(offset)
        uncovered -= covered
    selected.sort()
    relocated = bytearray(linked)
    for offset in selected:
        value = int.from_bytes(relocated[offset:offset + 2], "little")
        relocated[offset:offset + 2] = ((value + delta) & 0xFFFF).to_bytes(2, "little")
    if bytes(relocated) != alternate:
        raise SystemExit("BASIC.CPX relocation table does not reproduce alternate image")
    return selected


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
    data = assemble(args.assembler, text, BUILD / "basic.bin",
                    BUILD / "basic.lst", LINK_BASE)
    alternate_text = text.replace("CPXBASE         EQU     08000H",
                                  "CPXBASE         EQU     08101H")
    alternate = assemble(args.assembler, alternate_text,
                         BUILD / "basic-alt.bin", BUILD / "basic-alt.lst",
                         ALTERNATE_BASE)
    offsets = relocation_offsets(data, alternate)
    allocation = (len(data) + 0xFF) & ~0xFF
    if 512 + len(data) > 6 * 512:
        raise SystemExit(f"BASIC.CPX exceeds six available module slots: {len(data)}")
    if len(offsets) > 248:
        raise SystemExit("BASIC.CPX relocation table exceeds its header")
    header = bytearray(512)
    struct.pack_into("<4sBBHHHHH", header, 0, b"BCX1", 1, 1, LINK_BASE,
                     len(data), allocation, 0, len(offsets))
    for index, offset in enumerate(offsets):
        struct.pack_into("<H", header, 16 + index * 2, offset)
    module = BUILD / "BASIC.CPX"
    module.write_bytes(header + data)
    print(f"{hashlib.sha256(data).hexdigest()}  {BUILD.relative_to(ROOT)}/basic.bin")
    print(f"BASIC.CPX bytes: {len(data)}; allocation: {allocation}; "
          f"relocations: {len(offsets)}; module: {len(module.read_bytes())}")


if __name__ == "__main__":
    main()
