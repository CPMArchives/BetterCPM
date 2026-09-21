#!/usr/bin/env python3
"""Qualify in-memory STATEFUL movement, snapshot reconstruction, and publish."""
from __future__ import annotations

import struct
from pathlib import Path

from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]
MOVER = 0x7000
SCHEDULER = 0x7800
COMMIT = 0x7C00
REQUEST = 0x6000
PLAN = 0x6100
SLOTS_DESC = 0x6200
SNAP_DESC = 0x6240
SLOTS = 0x6300
SCHED_REQ = 0x6400
MOVE_REQ = 0x6420
PUB_DESC = 0x6460
SNAPSHOT = 0x6800
OLD_STATEFUL = 0x8200
NEW_STATEFUL = 0x8300
NEW_STATELESS = 0x8200
ALLOCATION = 0x100
DISPATCH = 0x40
CORE = 0xD6BC
HEAD = 0x6600
LOW = 0x6602
TPA = 0x6604
GEN = 0x6606
PAGEZERO = 0x6608


def setup(bad_snapshot_size: bool = False, overlap_snapshot: bool = False) -> tuple[Z80, bytes]:
    cpu = Z80(b"")
    for address, name in ((MOVER, "rsxmover"), (SCHEDULER, "rsxschedule"),
                          (COMMIT, "rsxcommit")):
        code = (ROOT / f"build/system/{name}.bin").read_bytes()
        cpu.mem[address:address + len(code)] = code

    # Retained STATEFUL image: mutable bytes, one internal pointer, and a fixed word.
    cpu.mem[OLD_STATEFUL:OLD_STATEFUL + ALLOCATION] = b"\x31" * ALLOCATION
    cpu.setword(OLD_STATEFUL + 0x20, OLD_STATEFUL + 0x60)
    cpu.setword(OLD_STATEFUL + 0x22, 0x0005)
    old_image = bytes(cpu.mem[OLD_STATEFUL:OLD_STATEFUL + ALLOCATION])

    source = NEW_STATELESS if overlap_snapshot else SNAPSHOT
    snapshot = bytearray(b"\x52" * ALLOCATION)
    snapshot[0x30:0x34] = b"DATA"
    cpu.mem[source:source + ALLOCATION] = snapshot
    plans = (
        (OLD_STATEFUL, NEW_STATEFUL, ALLOCATION, 1, 1),
        (0, NEW_STATELESS, ALLOCATION, 0, 0xFF),
    )
    cpu.mem[PLAN:PLAN + 16] = b"".join(struct.pack("<HHHBB", *record)
                                       for record in plans)
    cpu.mem[SLOTS:SLOTS + 2] = struct.pack("<H", 0x20)
    cpu.mem[SLOTS_DESC:SLOTS_DESC + 6] = struct.pack(
        "<HBHB", SLOTS, 1, SLOTS + 2, 0)
    snap_size = ALLOCATION - 1 if bad_snapshot_size else ALLOCATION
    cpu.mem[SNAP_DESC:SNAP_DESC + 12] = (
        struct.pack("<HHH", 0, 0, DISPATCH) +
        struct.pack("<HHH", source, snap_size, DISPATCH))
    cpu.mem[PUB_DESC:PUB_DESC + 10] = struct.pack(
        "<HHHHH", HEAD, LOW, TPA, GEN, PAGEZERO)
    cpu.setword(HEAD, OLD_STATEFUL)
    cpu.setword(LOW, 0x8100)
    cpu.setword(TPA, 0x80FD)
    cpu.setword(GEN, 7)
    cpu.setword(PAGEZERO, 0x80FD)
    request = struct.pack(
        "<HHHBBHHHHHHHHB", PLAN, SLOTS_DESC, SNAP_DESC, 2, 0,
        SCHED_REQ, SCHEDULER, MOVE_REQ, 32, MOVER, 0x8400, CORE,
        PUB_DESC, 0xCC)
    cpu.mem[REQUEST:REQUEST + len(request)] = request
    before = bytes(cpu.mem[0x8100:0x8400])
    cpu.de = REQUEST
    cpu.sp = 0x5F00
    cpu.run(COMMIT, limit=50000)
    return cpu, before


def main() -> None:
    cpu, _ = setup()
    assert cpu.a == 0 and cpu.mem[REQUEST + 24] == 2
    assert cpu.word(NEW_STATEFUL + 0x20) == NEW_STATEFUL + 0x60
    assert cpu.word(NEW_STATEFUL + 0x22) == 0x0005
    assert cpu.mem[NEW_STATELESS + 0x30:NEW_STATELESS + 0x34] == b"DATA"
    assert cpu.word(NEW_STATEFUL) == NEW_STATELESS + DISPATCH
    assert cpu.word(NEW_STATEFUL + 2) == NEW_STATEFUL + DISPATCH
    assert cpu.word(NEW_STATELESS) == CORE
    assert cpu.word(NEW_STATELESS + 2) == NEW_STATELESS + DISPATCH
    assert cpu.word(HEAD) == NEW_STATEFUL
    assert cpu.word(LOW) == NEW_STATELESS
    assert cpu.word(TPA) == NEW_STATELESS - 3
    assert cpu.word(PAGEZERO) == NEW_STATELESS - 3
    assert cpu.word(GEN) == 8
    assert cpu.sp == 0x5F00

    # Every validation failure precedes movement and publication.
    for kwargs in ({"bad_snapshot_size": True}, {"overlap_snapshot": True}):
        cpu, before = setup(**kwargs)
        assert cpu.a == 0xFF and cpu.mem[REQUEST + 24] == 0xCC
        assert bytes(cpu.mem[0x8100:0x8400]) == before
        assert cpu.word(HEAD) == OLD_STATEFUL and cpu.word(GEN) == 7

    # Removing the final provider publishes the empty profile and discards it.
    cpu = Z80(b"")
    for address, name in ((MOVER, "rsxmover"), (SCHEDULER, "rsxschedule"),
                          (COMMIT, "rsxcommit")):
        code = (ROOT / f"build/system/{name}.bin").read_bytes()
        cpu.mem[address:address + len(code)] = code
    cpu.mem[PUB_DESC:PUB_DESC + 10] = struct.pack(
        "<HHHHH", HEAD, LOW, TPA, GEN, PAGEZERO)
    cpu.setword(HEAD, OLD_STATEFUL)
    cpu.setword(GEN, 11)
    request = struct.pack(
        "<HHHBBHHHHHHHHB", PLAN, SLOTS_DESC, SNAP_DESC, 0, 0,
        SCHED_REQ, SCHEDULER, MOVE_REQ, 32, MOVER, 0x8400, CORE,
        PUB_DESC, 0xCC)
    cpu.mem[REQUEST:REQUEST + len(request)] = request
    cpu.de = REQUEST
    cpu.sp = 0x5F00
    cpu.run(COMMIT, limit=20000)
    assert cpu.a == 0 and cpu.mem[REQUEST + 24] == 0
    assert cpu.word(HEAD) == 0 and cpu.word(LOW) == 0x8400
    assert cpu.word(TPA) == 0x83FD and cpu.word(PAGEZERO) == 0x83FD
    assert cpu.word(GEN) == 12
    print("RSX commit moves retained STATEFUL images, installs prepared snapshots, "
          "relinks providers, and publishes the new generation only after success")


if __name__ == "__main__":
    main()
