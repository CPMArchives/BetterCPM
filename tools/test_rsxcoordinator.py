#!/usr/bin/env python3
"""Qualify candidate normalization and prospective-profile planning."""
from __future__ import annotations

import struct
import tempfile
from pathlib import Path

from build_ccp import assemble
from system_layout import LAYOUT
from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]
REQUEST = 0x5800
COUNT = 0x5FF0
SELECT = 0x5FF1
WORK_LOW = 0x6000
WORK_HIGH = 0x8800
CARRIER_SOURCE = 0x9000
CARR_SOURCE = 0x9400
META_SOURCE = 0x9800
PLAN_SOURCE = 0x9C00
MOVE_SOURCE = 0xA000
PROF_SOURCE = 0xA400
HELLO_SOURCE = 0xA800
SNAP_SOURCE = 0xAC00
KCTX_SOURCE = 0xB000
KEEP_SOURCE = 0xB400
KPRE_SOURCE = 0xB800
SLOTS_SOURCE = 0xBC00
STATEFUL_SOURCE = 0xC000
FINAL_SOURCE = 0xC400
FACTS = 0x6400
LIVE_LOW = 0xD600
LIVE_HIGH = 0xEC00
FINAL_IMAGE = b""


def file_stub(work: Path) -> bytes:
    source = f"""
        ASEG
        ORG     0{LAYOUT['FILE']:04X}H
        JP      OPEN
        JP      NEXT
        JP      RESET
OPEN:   XOR     A
        LD      ({COUNT:04X}H),A
        LD      A,(HL)
        CP      'R'
        JP      NZ,CARRIER
        INC     HL
        LD      A,(HL)
        CP      '3'
        JP      NZ,CARRIER
        INC     HL
        LD      A,(HL)
        CP      'C'
        JR      Z,CARR
        CP      'P'
        JR      Z,PSELECT
        CP      'M'
        JR      Z,MSELECT
        CP      'S'
        JR      Z,SSELECT
        CP      'K'
        JR      Z,KSELECT
        CP      'F'
        JR      Z,FSELECT
        JP      CARRIER
PSELECT:
        INC     HL
        LD      A,(HL)
        CP      'R'
        JP      Z,PROF
        JP      PLAN
MSELECT:
        INC     HL
        LD      A,(HL)
        CP      'O'
        JR      Z,MOVE
        LD      A,2
        JR      SELECTED
CARR:   LD      A,1
        JR      SELECTED
PLAN:   LD      A,3
        JR      SELECTED
MOVE:   LD      A,4
        JR      SELECTED
PROF:   LD      A,5
        JR      SELECTED
SNAP:   LD      A,7
        JR      SELECTED
SSELECT:
        INC     HL
        LD      A,(HL)
        CP      'L'
        JR      Z,SLOTS
        JP      SNAP
KSELECT:
        INC     HL
        LD      A,(HL)
        CP      'C'
        JR      Z,KCTX
        CP      'E'
        JR      Z,KEEP
        LD      A,10
        JR      SELECTED
KCTX:   LD      A,8
        JR      SELECTED
KEEP:   LD      A,9
        JR      SELECTED
SLOTS:  LD      A,11
        JR      SELECTED
FSELECT:
        LD      A,13
        JR      SELECTED
CARRIER:
        LD      A,(HL)
        CP      'H'
        JR      Z,HELLO
        CP      'S'
        JR      Z,STATEFUL
        LD      A,0
        JR      SELECTED
HELLO:
        LD      A,6
        JR      SELECTED
STATEFUL:
        LD      A,12
SELECTED:
        LD      ({SELECT:04X}H),A
        XOR     A
        RET
RESET:  XOR     A
        LD      ({COUNT:04X}H),A
        RET
NEXT:   PUSH    HL
        EX      DE,HL
        LD      A,({SELECT:04X}H)
        OR      A
        LD      BC,0{CARRIER_SOURCE:04X}H
        JP      Z,HAVESRC
        DEC     A
        LD      BC,0{CARR_SOURCE:04X}H
        JP      Z,HAVESRC
        DEC     A
        LD      BC,0{META_SOURCE:04X}H
        JP      Z,HAVESRC
        DEC     A
        LD      BC,0{PLAN_SOURCE:04X}H
        JP      Z,HAVESRC
        DEC     A
        LD      BC,0{MOVE_SOURCE:04X}H
        JP      Z,HAVESRC
        DEC     A
        LD      BC,0{PROF_SOURCE:04X}H
        JP      Z,HAVESRC
        DEC     A
        LD      BC,0{HELLO_SOURCE:04X}H
        JP      Z,HAVESRC
        DEC     A
        LD      BC,0{SNAP_SOURCE:04X}H
        JP      Z,HAVESRC
        DEC     A
        LD      BC,0{KCTX_SOURCE:04X}H
        JP      Z,HAVESRC
        DEC     A
        LD      BC,0{KEEP_SOURCE:04X}H
        JP      Z,HAVESRC
        DEC     A
        LD      BC,0{KPRE_SOURCE:04X}H
        JP      Z,HAVESRC
        DEC     A
        LD      BC,0{SLOTS_SOURCE:04X}H
        JP      Z,HAVESRC
        DEC     A
        LD      BC,0{STATEFUL_SOURCE:04X}H
        JP      Z,HAVESRC
        LD      BC,0{FINAL_SOURCE:04X}H
HAVESRC:
        LD      A,({COUNT:04X}H)
        LD      L,A
        LD      H,0
        ADD     HL,HL
        ADD     HL,HL
        ADD     HL,HL
        ADD     HL,HL
        ADD     HL,HL
        ADD     HL,HL
        ADD     HL,HL
        ADD     HL,HL
        ADD     HL,HL
        ADD     HL,BC
        LD      BC,0200H
        LDIR
        POP     HL
        LD      DE,0200H
        ADD     HL,DE
        LD      A,({COUNT:04X}H)
        INC     A
        LD      ({COUNT:04X}H),A
        XOR     A
        RET
        END
"""
    return assemble(Path("/Users/nathanael/bin/z80asm"), source,
                    work / "stub.bin", work / "stub.lst", LAYOUT["FILE"])


def final_stub(work: Path) -> bytes:
    source = f"""
        ASEG
        ORG     0{LAYOUT['RSX']:04X}H
        LD      (CTX),DE
        EX      DE,HL
        LD      E,(HL)
        INC     HL
        LD      D,(HL)
        LD      (PUB),DE
        INC     HL
        LD      E,(HL)
        INC     HL
        LD      D,(HL)
        LD      (FACT),DE
        LD      HL,(CTX)
        LD      DE,12
        ADD     HL,DE
        LD      E,(HL)
        INC     HL
        LD      D,(HL)
        LD      HL,(FACT)
        LD      BC,24
        ADD     HL,BC
        LD      (HL),E
        INC     HL
        LD      (HL),D
        LD      HL,(FACT)
        LD      BC,22
        ADD     HL,BC
        LD      E,(HL)
        INC     HL
        LD      D,(HL)
        LD      HL,(PUB)
        LD      BC,12
        ADD     HL,BC
        LD      (HL),E
        INC     HL
        LD      (HL),D
        LD      HL,(FACT)
        XOR     A
        RET
CTX:    DW      0
PUB:    DW      0
FACT:   DW      0
        END
"""
    return assemble(Path("/Users/nathanael/bin/z80asm"), source,
                    work / "final.bin", work / "final.lst", LAYOUT["RSX"])


def invoke(stub: bytes, carrier: bytes, name: bytes, *, operation: int = 1,
           high: int = WORK_HIGH,
           retained: tuple[bytes, ...] = (), final: bytes = b"") -> tuple[Z80, bytes]:
    cpu = Z80(b"")
    io = (ROOT / "build/system/rsxio.bin").read_bytes()
    io_base = high - 0xE00 + 0x400
    cpu.mem[io_base:io_base + len(io)] = io
    coordinator = (ROOT / "build/system/R3COORD.RSX").read_bytes()
    carr = (ROOT / "build/system/R3CARR.RSX").read_bytes()
    meta = (ROOT / "build/system/R3META.RSX").read_bytes()
    plan = (ROOT / "build/system/R3PLAN.RSX").read_bytes()
    move = (ROOT / "build/system/R3MOVE.RSX").read_bytes()
    profile = (ROOT / "build/system/R3PROF.RSX").read_bytes()
    snapshot = (ROOT / "build/system/R3SNAP.RSX").read_bytes()
    context = (ROOT / "build/system/R3KCTX.RSX").read_bytes()
    retained_loader = (ROOT / "build/system/R3KEEP.RSX").read_bytes()
    retained_prepare = (ROOT / "build/system/R3KPRE.RSX").read_bytes()
    slots = (ROOT / "build/system/R3SLOTS.RSX").read_bytes()
    hello = (ROOT / "build/rsx/HELLO.RSX").read_bytes()
    stateful = (ROOT / "build/rsx/STATEFUL.RSX").read_bytes()
    cpu.mem[LAYOUT["RSX"]:LAYOUT["RSX"] + len(coordinator)] = coordinator
    cpu.mem[LAYOUT["FILE"]:LAYOUT["FILE"] + len(stub)] = stub
    cpu.mem[CARRIER_SOURCE:CARRIER_SOURCE + 1024] = carrier.ljust(1024, b"\0")
    cpu.mem[CARR_SOURCE:CARR_SOURCE + 1024] = carr.ljust(1024, b"\0")
    cpu.mem[META_SOURCE:META_SOURCE + 1024] = meta.ljust(1024, b"\0")
    cpu.mem[PLAN_SOURCE:PLAN_SOURCE + 1024] = plan.ljust(1024, b"\0")
    cpu.mem[MOVE_SOURCE:MOVE_SOURCE + 1024] = move.ljust(1024, b"\0")
    cpu.mem[PROF_SOURCE:PROF_SOURCE + 1024] = profile.ljust(1024, b"\0")
    cpu.mem[HELLO_SOURCE:HELLO_SOURCE + 1024] = hello.ljust(1024, b"\0")
    selected_stateful = carrier if name == b"STATEFUL" else stateful
    cpu.mem[STATEFUL_SOURCE:STATEFUL_SOURCE + 1024] = \
        selected_stateful.ljust(1024, b"\0")
    final = final or FINAL_IMAGE
    cpu.mem[FINAL_SOURCE:FINAL_SOURCE + 1024] = final.ljust(1024, b"\0")
    cpu.mem[SNAP_SOURCE:SNAP_SOURCE + 1024] = snapshot.ljust(1024, b"\0")
    cpu.mem[KCTX_SOURCE:KCTX_SOURCE + 1024] = context.ljust(1024, b"\0")
    cpu.mem[KEEP_SOURCE:KEEP_SOURCE + 1024] = retained_loader.ljust(1024, b"\0")
    cpu.mem[KPRE_SOURCE:KPRE_SOURCE + 1024] = retained_prepare.ljust(1024, b"\0")
    cpu.mem[SLOTS_SOURCE:SLOTS_SOURCE + 1024] = slots.ljust(1024, b"\0")
    cpu.mem[COUNT:SELECT + 1] = b"\xA5\xA5"
    cpu.mem[LAYOUT["RSX_STATE"]] = len(retained)
    for index, stem in enumerate(retained):
        start = LAYOUT["RSX_STATE"] + 1 + index * 8
        cpu.mem[start:start + 8] = stem
    before_state = bytes(cpu.mem[LAYOUT["RSX_STATE"]:
                                 LAYOUT["RSX_STATE"] + 41])
    request = bytes((2, operation, 0, 0)) + name + b"\xA5\xA5" + \
        struct.pack("<HH", WORK_LOW, high)
    cpu.mem[REQUEST:REQUEST + len(request)] = request
    cpu.mem[LIVE_LOW:LIVE_HIGH] = b"\x5A" * (LIVE_HIGH - LIVE_LOW)
    before_live = bytes(cpu.mem[LIVE_LOW:LIVE_HIGH])
    cpu.de = REQUEST
    cpu.sp = 0x5700
    cpu.run(LAYOUT["RSX"], limit=200000)
    assert bytes(cpu.mem[LIVE_LOW:LIVE_HIGH]) == before_live
    assert bytes(cpu.mem[LAYOUT["RSX_STATE"]:
                         LAYOUT["RSX_STATE"] + 41]) == before_state
    return cpu, before_live


def main() -> None:
    global FINAL_IMAGE
    with tempfile.TemporaryDirectory(prefix="bettercpm-rsx-coordinator-") as temporary:
        stub = file_stub(Path(temporary))
        final = final_stub(Path(temporary))
        FINAL_IMAGE = final
        stateful = (ROOT / "build/rsx/STATEFUL.RSX").read_bytes()
        hello = (ROOT / "build/rsx/HELLO.RSX").read_bytes()
        cpu, _ = invoke(stub, stateful, b"STATEFUL", final=final)
        assert cpu.a == 0 and cpu.hl == FACTS
        assert cpu.word(REQUEST + 12) == int.from_bytes(stateful[46:48], "little")
        assert cpu.mem[WORK_LOW:WORK_LOW + len(stateful)] == stateful
        assert cpu.word(FACTS) == WORK_LOW + 512
        assert cpu.mem[FACTS + 20:FACTS + 22] == bytes((1, 2))
        assert cpu.mem[FACTS + 16:FACTS + 18] == b"\x01\x01"
        plan_record = FACTS + 46
        allocation = cpu.word(FACTS + 4)
        assert cpu.word(plan_record) == 0
        assert cpu.word(plan_record + 2) == LAYOUT["RSX"] - allocation
        assert cpu.word(plan_record + 4) == allocation
        assert cpu.mem[plan_record + 6:plan_record + 8] == b"\x01\xFF"
        snap_descriptor = FACTS + 75
        snapshot = FACTS + 107
        assert cpu.word(snap_descriptor) == snapshot
        assert cpu.word(snap_descriptor + 2) == allocation
        assert cpu.word(snap_descriptor + 4) == cpu.word(FACTS + 8)
        assert cpu.word(FACTS + 24) == snapshot + allocation + 23
        assert cpu.mem[snapshot:snapshot + 4] == b"\0\0\0\0"
        assert cpu.mem[snapshot + 4:snapshot + 6] == b"\x01\0"
        assert cpu.word(snapshot + 6) == allocation - 10
        relocations = [int.from_bytes(stateful[48 + 2 * index:
                                               50 + 2 * index], "little")
                       for index in range(
                           int.from_bytes(stateful[22:24], "little"))]
        relocation = next(offset for offset in relocations if offset >= 8)
        linked_value = int.from_bytes(
            stateful[512 + relocation:514 + relocation], "little")
        assert cpu.word(snapshot + relocation) == \
            (linked_value + cpu.word(plan_record + 2) -
             cpu.word(FACTS + 6)) & 0xFFFF

        cpu, _ = invoke(stub, stateful, b"STATEFUL",
                        high=FACTS + 386 + 0xE00)
        assert cpu.a == 0 and cpu.hl == FACTS
        cpu, _ = invoke(stub, stateful, b"STATEFUL",
                        high=FACTS + 385 + 0xE00)
        assert cpu.a == 0xFF and cpu.word(REQUEST + 12) == 0xA5A5

        cpu, _ = invoke(stub, hello, b"HELLO   ")
        assert cpu.a == 0 and cpu.hl == FACTS
        assert cpu.mem[FACTS + 20:FACTS + 22] == bytes((0, 1))
        assert cpu.mem[FACTS + 16:FACTS + 18] == b"\0\0"

        cpu, _ = invoke(stub, stateful, b"STATEFUL",
                        retained=(b"HELLO   ",))
        assert cpu.a == 0 and cpu.hl == FACTS
        old_allocation = int.from_bytes(hello[14:16], "little")
        new_allocation = cpu.word(FACTS + 4)
        first = FACTS + 46
        second = first + 8
        assert cpu.word(first) == 0
        assert cpu.word(first + 2) == LAYOUT["RSX"] - old_allocation
        assert cpu.word(first + 4) == old_allocation
        assert cpu.mem[first + 6:first + 8] == b"\x00\xFF"
        assert cpu.word(second) == 0
        assert cpu.word(second + 2) == \
            LAYOUT["RSX"] - old_allocation - new_allocation
        assert cpu.word(second + 4) == new_allocation
        assert cpu.mem[second + 6:second + 8] == b"\x01\xFF"
        snap_descriptors = FACTS + 88
        snapshot = snap_descriptors + 12 + 6 + 23
        retained_snapshot = snapshot + new_allocation + 23
        assert cpu.word(snap_descriptors) == retained_snapshot
        assert cpu.word(snap_descriptors + 2) == old_allocation
        assert cpu.word(snap_descriptors + 4) == int.from_bytes(
            hello[16:18], "little")
        assert cpu.word(snap_descriptors + 6) == snapshot
        assert cpu.word(snap_descriptors + 8) == new_allocation
        assert cpu.word(snap_descriptors + 10) == cpu.word(FACTS + 8)
        assert cpu.word(FACTS + 24) == retained_snapshot + old_allocation

        cpu, _ = invoke(stub, hello, b"HELLO   ",
                        retained=(b"STATEFUL",))
        assert cpu.a == 0 and cpu.hl == FACTS
        stateful_allocation = int.from_bytes(stateful[14:16], "little")
        candidate_allocation = cpu.word(FACTS + 4)
        snapshots = FACTS + 88
        unions = snapshots + 12
        candidate_snapshot = unions + 6 + 23
        durable_union = candidate_snapshot + candidate_allocation + 23
        assert cpu.mem[snapshots:snapshots + 4] == b"\0" * 4
        assert cpu.word(snapshots + 4) == int.from_bytes(
            stateful[16:18], "little")
        assert cpu.word(snapshots + 6) == candidate_snapshot
        assert cpu.word(snapshots + 8) == candidate_allocation
        union_address = cpu.word(unions)
        union_count = cpu.mem[unions + 2]
        static_count = int.from_bytes(stateful[22:24], "little")
        static = tuple(int.from_bytes(stateful[48 + 2 * index:
                                                 50 + 2 * index], "little")
                       for index in range(static_count))
        metadata = int.from_bytes(stateful[30:32], "little")
        record = metadata + 12
        runtime: tuple[int, ...] = ()
        for _ in range(stateful[metadata + 7]):
            kind, length = stateful[record:record + 2]
            data = record + 2
            if kind == 3:
                runtime = tuple(int.from_bytes(stateful[offset:offset + 2],
                                               "little")
                                for offset in range(data, data + length, 2))
            record = data + length
        expected_union = tuple(sorted(set(static) | set(runtime)))
        assert union_address == durable_union
        assert union_count == len(expected_union)
        assert tuple(cpu.word(union_address + 2 * index)
                     for index in range(union_count)) == expected_union
        assert cpu.mem[unions + 3:unions + 6] == b"\0" * 3
        assert cpu.word(FACTS + 24) == durable_union + 2 * union_count
        assert stateful_allocation == cpu.word(FACTS + 46 + 4)

        cpu, _ = invoke(stub, stateful, b"STATEFUL",
                        high=FACTS + 2502 + 0xE00,
                        retained=(b"HELLO   ",))
        assert cpu.a == 0
        cpu, _ = invoke(stub, stateful, b"STATEFUL",
                        high=FACTS + 2501 + 0xE00,
                        retained=(b"HELLO   ",))
        assert cpu.a == 0xFF and cpu.word(REQUEST + 12) == 0xA5A5
        cpu, _ = invoke(stub, stateful, b"STATEFUL",
                        retained=(b"STATEFUL",))
        assert cpu.a == 0xFF and cpu.word(REQUEST + 12) == 0xA5A5
        cpu, _ = invoke(stub, stateful, b"STATEFUL",
                        retained=(b"MISSING ",))
        assert cpu.a == 0xFF and cpu.word(REQUEST + 12) == 0xA5A5

        broken = bytearray(stateful)
        broken[512] ^= 1
        cpu, _ = invoke(stub, bytes(broken), b"STATEFUL")
        assert cpu.a == 0xFF and cpu.word(REQUEST + 12) == 0xA5A5
        cpu, _ = invoke(stub, stateful, b"STATEFUL", high=FACTS + 74)
        assert cpu.a == 0xFF and cpu.word(REQUEST + 12) == 0xA5A5
        cpu, _ = invoke(stub, stateful, b"STATEFUL", operation=2)
        assert cpu.a == 0xFF and cpu.word(REQUEST + 12) == 0xA5A5

    print("Stage 3 normalizes and plans bounded appends, prepares the fresh "
          "candidate, and constructs retained STATELESS snapshots and "
          "STATEFUL pointer unions without changing live state")


if __name__ == "__main__":
    main()
