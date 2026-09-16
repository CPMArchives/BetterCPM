#!/usr/bin/env python3
"""Exercise prospective RSX layout planning and reconstruction classes."""
from __future__ import annotations

import struct
from pathlib import Path

from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]
ENTRY = 0x7400
REQUEST = 0x6000
OLD_ALLOC = 0x6100
NEW_ALLOC = 0x6200
CLASSES = 0x6300
OUTPUT = 0x6400
TOP = 0xF000


def invoke(old: tuple[int, ...], new: tuple[int, ...], classes: tuple[int, ...],
           removed: int = 0xFF, minimum: int = 0xE000,
           capacity: int | None = None) -> tuple[Z80, bytes]:
    cpu = Z80(b"")
    code = (ROOT / "build/system/rsxplan.bin").read_bytes()
    cpu.mem[ENTRY:ENTRY + len(code)] = code
    cpu.mem[OLD_ALLOC:OLD_ALLOC + 2 * len(old)] = b"".join(
        value.to_bytes(2, "little") for value in old)
    cpu.mem[NEW_ALLOC:NEW_ALLOC + 2 * len(new)] = b"".join(
        value.to_bytes(2, "little") for value in new)
    cpu.mem[CLASSES:CLASSES + len(classes)] = bytes(classes)
    cpu.mem[OUTPUT:OUTPUT + 64] = bytes((0xA5,)) * 64
    capacity = len(new) if capacity is None else capacity
    request = struct.pack("<HHBBBBHHHHB", TOP, minimum, len(old), len(new),
                          removed, 0, OLD_ALLOC, NEW_ALLOC, CLASSES, OUTPUT,
                          capacity) + b"\xCC"
    cpu.mem[REQUEST:REQUEST + len(request)] = request
    before = bytes(cpu.mem[OUTPUT:OUTPUT + 64])
    cpu.de = REQUEST
    cpu.sp = 0x5F00
    cpu.run(ENTRY, limit=20000)
    return cpu, before


def records(cpu: Z80) -> tuple[tuple[int, int, int, int, int], ...]:
    count = cpu.mem[REQUEST + 17]
    return tuple(struct.unpack_from("<HHHBB", cpu.mem, OUTPUT + 8 * index)
                 for index in range(count))


def rejected(*args, **kwargs) -> None:
    cpu, _before = invoke(*args, **kwargs)
    assert cpu.a == 0xFF
    assert cpu.mem[REQUEST + 17] == 0xCC


def main() -> None:
    # Removing the first module moves the retained STATEFUL module upward;
    # the following STATELESS module is marked for a fresh disk reload.
    cpu, _ = invoke((0x100, 0x200, 0x100), (0x200, 0x100), (1, 0), removed=0)
    assert cpu.a == 0
    assert records(cpu) == (
        (0xED00, 0xEE00, 0x200, 1, 1),
        (0, 0xED00, 0x100, 0, 0xFF),
    )

    # Appending a STATEFUL provider creates a fresh record without an old base.
    cpu, _ = invoke((0x100,), (0x100, 0x200), (0, 1))
    assert cpu.a == 0
    assert records(cpu) == (
        (0, 0xEF00, 0x100, 0, 0xFF),
        (0, 0xED00, 0x200, 1, 0xFF),
    )

    # A retained stateless carrier may change allocation because it is reloaded.
    cpu, _ = invoke((0x100,), (0x200,), (0,))
    assert cpu.a == 0 and records(cpu)[0][2] == 0x200

    rejected((0x100,), (0x100,), (2,))                 # reserved export/import
    rejected((0x100, 0x100), (0x100,), (3,), removed=0)  # COLD_ONLY moved
    rejected((0x100,), (0x200,), (1,))                 # stateful size changed
    rejected((0x100,), (0x100,), (1,), minimum=0xEFFF) # below minimum
    rejected((0x100,), (0x100,), (1,), capacity=0)     # no output capacity
    rejected((0,), (0x100,), (0,), removed=0)          # invalid old allocation
    print("RSX profile planner calculates append/removal layouts, preserves "
          "stateful provenance, reloads stateless entries, and rejects unsafe plans")


if __name__ == "__main__":
    main()
