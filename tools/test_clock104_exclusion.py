#!/usr/bin/env python3
"""Test shared clock-profile exclusion, including pre-I/O LOAD rejection."""
from __future__ import annotations

import re
import tempfile
from pathlib import Path

from system_layout import LAYOUT
from test_bios import Z80, require
from test_rsxcoordinator import file_stub, invoke, COUNT, REQUEST

ROOT = Path(__file__).resolve().parents[1]
C3, Z8 = b"T104C3  ", b"T104Z8  "


def symbols() -> dict[str, int]:
    result = {}
    for line in (ROOT / "build/system/r3coord.lst").read_text().splitlines():
        match = re.match(r"^([0-9a-f]{4})\s+.*\s([A-Z][A-Z0-9_]*):", line, re.I)
        if match:
            result[match.group(2).upper()] = int(match.group(1), 16)
    return result


def guard(candidate: bytes, retained: tuple[bytes, ...]) -> int:
    names = symbols()
    code = (ROOT / "build/system/r3coord.bin").read_bytes()
    cpu = Z80(b"")
    cpu.mem[LAYOUT["RSX"]:LAYOUT["RSX"] + len(code)] = code
    cpu.setword(names["RC_REQ"], REQUEST)
    cpu.mem[REQUEST + 4:REQUEST + 12] = candidate
    cpu.mem[LAYOUT["RSX_STATE"]] = len(retained)
    for index, stem in enumerate(retained):
        base = LAYOUT["RSX_STATE"] + 1 + index * 8
        cpu.mem[base:base + 8] = stem
    before = bytes(cpu.mem)
    sp = cpu.sp
    cpu.run(names["RC_CLOCK"], limit=2000)
    require(cpu.sp == sp, "clock guard unbalanced stack")
    # Only the return/call stack scratch may change; live profile and request
    # are immutable during this guard.
    state = LAYOUT["RSX_STATE"]
    require(bytes(cpu.mem[state:state + 41]) == before[state:state + 41],
            "clock guard changed live profile")
    require(bytes(cpu.mem[REQUEST:REQUEST + 18]) == before[REQUEST:REQUEST + 18],
            "clock guard changed public request")
    return cpu.a


def main() -> None:
    count = 0
    ordinary = b"P2DOS   "
    near = (b"T104C3 X", b"T104Z8 X", b"T104C4  ", b"T104Z9  ")
    for candidate, opposite in ((C3, Z8), (Z8, C3)):
        require(guard(candidate, ()) == 0, "empty profile rejected")
        require(guard(candidate, (candidate,)) == 0,
                "clock guard replaced ordinary duplicate validation")
        require(guard(candidate, (ordinary,)) == 0, "P2DOS coexistence rejected")
        count += 3
        for size in range(1, 5):
            for position in range(size):
                retained = [ordinary] * size
                retained[position] = opposite
                require(guard(candidate, tuple(retained)) == 0xFF,
                        "opposite clock profile escaped exclusion")
                count += 1
        for name in near:
            require(guard(candidate, (name,)) == 0, "nonexact stem rejected")
            require(guard(name, (opposite,)) == 0, "nonexact candidate rejected")
            count += 2
    require(guard(ordinary, (C3,)) == 0, "unrelated candidate rejected")
    require(guard(ordinary, (Z8,)) == 0, "unrelated candidate rejected")
    require(guard(C3, (ordinary,) * 5) == 0xFF, "invalid profile count accepted")
    count += 3

    # Execute the real coordinator entry with conflicting candidate requests.
    # File-open count remains poisoned: rejection precedes even opening media.
    with tempfile.TemporaryDirectory(prefix="clock104-exclusion-") as temporary:
        stub = file_stub(Path(temporary))
        for stem, opposite in ((C3, Z8), (Z8, C3)):
            carrier = (ROOT / f"build/rsx/{stem.decode().strip()}.RSX").read_bytes()
            cpu, _ = invoke(stub, carrier, stem, retained=(opposite,))
            require(cpu.a == 0xFF, "coordinator accepted clock conflict")
            require(cpu.mem[COUNT] == 0xA5, "conflict reached file I/O")
            require(cpu.word(REQUEST + 12) == 0xA5A5,
                    "conflict published candidate length")
    print(f"clock exclusion: {count} guard cases and both pre-I/O LOAD orders passed")


if __name__ == "__main__":
    main()
