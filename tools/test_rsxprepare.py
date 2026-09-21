#!/usr/bin/env python3
"""Qualify the combined prospective layout and pointer-union preparation."""
from __future__ import annotations

import struct
from pathlib import Path

from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]
SLOTS = 0x7200
PLANNER = 0x7400
PREPARER = 0x7A00
REQUEST = 0x6000
PLAN_REQUEST = 0x6020
OLD_ALLOC = 0x6100
NEW_ALLOC = 0x6120
CLASSES = 0x6140
PLAN = 0x6200
INPUTS = 0x6300
STATIC0 = 0x6400
RUNTIME0 = 0x6440
STATIC1 = 0x6480
RUNTIME1 = 0x64C0
UNIONS = 0x6500
DESCRIPTORS = 0x6600
LIVE = 0x8000


def invoke(second_runtime: tuple[int, ...] = (0x24,), minimum: int = 0xE000,
           union_capacity: int = 8) -> tuple[Z80, bytes]:
    cpu = Z80(b"")
    for address, name in ((SLOTS, "rsxslots"), (PLANNER, "rsxplan"),
                          (PREPARER, "rsxprepare")):
        code = (ROOT / f"build/system/{name}.bin").read_bytes()
        cpu.mem[address:address + len(code)] = code

    old = (0x100, 0x100, 0x100)
    new = (0x100, 0x100)
    classes = (1, 1)
    cpu.mem[OLD_ALLOC:OLD_ALLOC + 6] = struct.pack("<HHH", *old)
    cpu.mem[NEW_ALLOC:NEW_ALLOC + 4] = struct.pack("<HH", *new)
    cpu.mem[CLASSES:CLASSES + 2] = bytes(classes)
    cpu.mem[PLAN:PLAN + 32] = b"\xA5" * 32
    planner_request = struct.pack(
        "<HHBBBBHHHHB", 0xF000, minimum, 3, 2, 0, 0,
        OLD_ALLOC, NEW_ALLOC, CLASSES, PLAN, 2) + b"\xCC"
    cpu.mem[PLAN_REQUEST:PLAN_REQUEST + len(planner_request)] = planner_request

    lists = (((0x20, 0x28), (0x24, 0x28)),
             ((0x22,), second_runtime))
    addresses = ((STATIC0, RUNTIME0), (STATIC1, RUNTIME1))
    records = bytearray()
    for (static, runtime), (static_address, runtime_address) in zip(lists, addresses):
        cpu.mem[static_address:static_address + 2 * len(static)] = struct.pack(
            "<" + "H" * len(static), *static)
        cpu.mem[runtime_address:runtime_address + 2 * len(runtime)] = struct.pack(
            "<" + "H" * len(runtime), *runtime)
        records += struct.pack("<HBHB", static_address, len(static),
                               runtime_address, len(runtime))
    cpu.mem[INPUTS:INPUTS + len(records)] = records
    cpu.mem[UNIONS:UNIONS + 32] = b"\xA5" * 32
    cpu.mem[DESCRIPTORS:DESCRIPTORS + 16] = b"\xA5" * 16
    cpu.mem[LIVE:LIVE + 0x400] = bytes(range(256)) * 4
    before_live = bytes(cpu.mem[LIVE:LIVE + 0x400])
    request = struct.pack("<HHHBBHHHBB", PLAN_REQUEST, INPUTS, UNIONS,
                          union_capacity, 0, PLANNER, SLOTS, DESCRIPTORS,
                          2, 0xCC)
    cpu.mem[REQUEST:REQUEST + len(request)] = request
    cpu.de = REQUEST
    cpu.sp = 0x5F00
    cpu.run(PREPARER, limit=40000)
    assert bytes(cpu.mem[LIVE:LIVE + 0x400]) == before_live
    return cpu, before_live


def main() -> None:
    cpu, _ = invoke()
    assert cpu.a == 0 and cpu.mem[REQUEST + 15] == 2
    assert tuple(struct.unpack_from("<HHHBB", cpu.mem, PLAN + 8 * index)
                 for index in range(2)) == (
        (0xEE00, 0xEF00, 0x100, 1, 1),
        (0xED00, 0xEE00, 0x100, 1, 2),
    )
    first_address, first_count = struct.unpack_from("<HB", cpu.mem, DESCRIPTORS)
    second_address, second_count = struct.unpack_from("<HB", cpu.mem, DESCRIPTORS + 3)
    assert first_address == UNIONS and first_count == 3
    assert tuple(cpu.word(first_address + 2 * i) for i in range(first_count)) == \
        (0x20, 0x24, 0x28)
    assert second_address == UNIONS + 6 and second_count == 2
    assert tuple(cpu.word(second_address + 2 * i) for i in range(second_count)) == \
        (0x22, 0x24)
    assert cpu.sp == 0x5F00

    # A malformed later provider may alter scratch, but cannot publish a
    # prepared count or touch the live profile.
    cpu, _ = invoke(second_runtime=(0x24, 0x20))
    assert cpu.a == 0xFF and cpu.mem[REQUEST + 15] == 0xCC

    # Capacity and prospective-layout failures are rejected before commit.
    cpu, _ = invoke(union_capacity=4)
    assert cpu.a == 0xFF and cpu.mem[REQUEST + 15] == 0xCC
    cpu, _ = invoke(minimum=0xEF80)
    assert cpu.a == 0xFF and cpu.mem[REQUEST + 15] == 0xCC
    print("RSX transaction preparation combines prospective layout and per-provider "
          "pointer unions, publishes only a complete plan, and never touches live images")


if __name__ == "__main__":
    main()
