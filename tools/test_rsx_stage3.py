#!/usr/bin/env python3
"""Qualify prepared Stage 3 load, stateful removal, and publication."""
from __future__ import annotations

import struct
import tempfile
from pathlib import Path

from build_ccp import assemble
from system_layout import LAYOUT
from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]
REQUEST = 0x3800
WORK_LOW = 0x4000
WORK_HIGH = 0x7600
SOURCE_BASE = 0x7800
RSTCOUNT = LAYOUT["RSX_STATE"]
RSTABLE = RSTCOUNT + 1
RSTSERV = RSTCOUNT + 0x21
HEAD = LAYOUT["SYSTEM"] + 0x84
LOW = LAYOUT["SYSTEM"] + 0x88
TPA = LAYOUT["SYSTEM"] + 0x90
GEN = LAYOUT["SYSTEM"] + 0x92

FILES = (
    ("R3MOVE  ", "build/system/R3MOVE.RSX"),
    ("R3COORD ", "build/system/R3COORD.RSX"),
    ("R3CARR  ", "build/system/R3CARR.RSX"),
    ("R3META  ", "build/system/R3META.RSX"),
    ("R3PROF  ", "build/system/R3PROF.RSX"),
    ("R3PLAN  ", "build/system/R3PLAN.RSX"),
    ("R3SNAP  ", "build/system/R3SNAP.RSX"),
    ("R3KCTX  ", "build/system/R3KCTX.RSX"),
    ("R3KEEP  ", "build/system/R3KEEP.RSX"),
    ("R3KPRE  ", "build/system/R3KPRE.RSX"),
    ("R3SLOTS ", "build/system/R3SLOTS.RSX"),
    ("R3FINAL ", "build/system/R3FINAL.RSX"),
    ("R3COMIT ", "build/system/R3COMIT.RSX"),
    ("R3RESOL ", "build/system/R3RESOL.RSX"),
    ("R3DROP  ", "build/system/R3DROP.RSX"),
    ("HELLO   ", "build/rsx/HELLO.RSX"),
    ("STATEFUL", "build/rsx/STATEFUL.RSX"),
)


def file_stub(work: Path, sources: tuple[int, ...]) -> bytes:
    table = "\n".join(
        f"        DW 0{address:04X}H\n        DB '{name}'"
        for (name, _path), address in zip(FILES, sources)
    )
    source = f"""
        ASEG
        ORG     0{LAYOUT['FILE']:04X}H
        JP      OPEN
        JP      NEXT
        JP      RESET
OPEN:   LD      (INPUT),HL
        LD      HL,TABLE
SEARCH: LD      E,(HL)
        INC     HL
        LD      D,(HL)
        INC     HL
        LD      A,D
        OR      E
        JR      Z,FAIL
        PUSH    HL
        PUSH    DE
        LD      DE,(INPUT)
        LD      B,8
MATCH:  LD      A,(DE)
        CP      (HL)
        JR      NZ,NEXTNAME
        INC     DE
        INC     HL
        DJNZ    MATCH
        POP     BC
        POP     HL
        LD      (SOURCE),BC
        XOR     A
        LD      (COUNT),A
        RET
NEXTNAME:
        POP     DE
        POP     HL
        LD      BC,8
        ADD     HL,BC
        JR      SEARCH
FAIL:   LD      A,0FFH
        OR      A
        RET
RESET:  XOR     A
        LD      (COUNT),A
        RET
NEXT:   PUSH    HL
        LD      HL,0{LAYOUT['CONFIG']:04X}H
        LD      DE,0{LAYOUT['CONFIG'] + 1:04X}H
        LD      BC,03FFH
        LD      (HL),055H
        LDIR
        POP     HL
        PUSH    HL
        EX      DE,HL
        LD      A,(COUNT)
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
        LD      BC,(SOURCE)
        ADD     HL,BC
        LD      BC,0200H
        LDIR
        POP     HL
        LD      DE,0200H
        ADD     HL,DE
        LD      A,(COUNT)
        INC     A
        LD      (COUNT),A
        XOR     A
        RET
INPUT:  DW      0
SOURCE: DW      0
COUNT:  DB      0
TABLE:
{table}
        DW      0
        END
"""
    return assemble(Path("/Users/nathanael/bin/z80asm"), source,
                    work / "files.bin", work / "files.lst", LAYOUT["FILE"])


def service_offset(carrier: bytes) -> int:
    metadata = struct.unpack_from("<H", carrier, 30)[0]
    cursor = metadata + 12
    for _ in range(carrier[metadata + 7]):
        kind, length = carrier[cursor:cursor + 2]
        if kind == 2:
            return struct.unpack_from("<H", carrier, cursor + 8)[0]
        cursor += 2 + length
    raise AssertionError("STATEFUL carrier lacks callable service")


def invoke(cpu: Z80, bootstrap: bytes, operation: int, name: bytes,
           high: int = WORK_HIGH) -> None:
    cpu.mem[LAYOUT["RSX"]:LAYOUT["RSX"] + 1024] = bootstrap.ljust(1024, b"\0")
    request = bytes((2, operation, 0, 0)) + name + b"\xA5\xA5" + \
        struct.pack("<HH", WORK_LOW, high)
    cpu.mem[REQUEST:REQUEST + len(request)] = request
    cpu.de = REQUEST
    cpu.sp = 0x3F00
    cpu.run(LAYOUT["RSX"], limit=600000)


def main() -> None:
    sources = tuple(SOURCE_BASE + 0x400 * index for index in range(len(FILES)))
    cpu = Z80(b"")
    for (_name, relative), address in zip(FILES, sources):
        data = (ROOT / relative).read_bytes()
        cpu.mem[address:address + 1024] = data.ljust(1024, b"\0")
    with tempfile.TemporaryDirectory(prefix="bettercpm-stage3-production-") as temporary:
        stub = file_stub(Path(temporary), sources)
    cpu.mem[LAYOUT["FILE"]:LAYOUT["FILE"] + len(stub)] = stub
    cpu.mem[LAYOUT["BIOS"] + 60:LAYOUT["BIOS"] + 64] = b"\xAF\xC9\0\0"
    bootstrap = (ROOT / "build/system/r3entry.bin").read_bytes()
    hello = (ROOT / "build/rsx/HELLO.RSX").read_bytes()
    stateful = (ROOT / "build/rsx/STATEFUL.RSX").read_bytes()
    hello_allocation = struct.unpack_from("<H", hello, 14)[0]
    stateful_allocation = struct.unpack_from("<H", stateful, 14)[0]
    service = service_offset(stateful)

    cpu.setword(HEAD, 0)
    cpu.setword(LOW, LAYOUT["RSX"])
    cpu.setword(TPA, LAYOUT["RSX"] - 3)
    cpu.setword(6, LAYOUT["RSX"] - 3)
    cpu.setword(GEN, 1)
    cpu.mem[RSTCOUNT:RSTCOUNT + 41] = bytes(41)

    invoke(cpu, bootstrap, 1, b"HELLO   ")
    assert cpu.a == 0 and cpu.mem[RSTCOUNT] == 1
    assert cpu.mem[RSTABLE:RSTABLE + 8] == b"HELLO   "
    assert cpu.word(REQUEST + 12) == struct.unpack_from("<H", hello, 46)[0]

    invoke(cpu, bootstrap, 1, b"STATEFUL")
    assert cpu.a == 0 and cpu.mem[RSTCOUNT] == 2
    assert cpu.mem[RSTABLE:RSTABLE + 16] == b"HELLO   STATEFUL"
    old_base = LAYOUT["RSX"] - hello_allocation - stateful_allocation
    assert cpu.word(LOW) == old_base

    def stat(base: int, operation: int) -> tuple[int, bytes]:
        request = 0x3600
        cpu.mem[request:request + 16] = bytes((1, 16, operation)) + bytes(13)
        cpu.de = request
        cpu.sp = 0x3500
        cpu.run(base + service, limit=5000)
        return cpu.a, bytes(cpu.mem[request:request + 16])

    stat(old_base, 0)
    for _ in range(3):
        stat(old_base, 1)
    before_live = bytes(cpu.mem[old_base:LAYOUT["RSX"]])
    before_state = bytes(cpu.mem[RSTCOUNT:RSTCOUNT + 41])
    invoke(cpu, bootstrap, 2, b"HELLO   ", high=cpu.word(6) + 1)
    assert cpu.a == 0xFF
    assert bytes(cpu.mem[old_base:LAYOUT["RSX"]]) == before_live
    assert bytes(cpu.mem[RSTCOUNT:RSTCOUNT + 41]) == before_state
    invoke(cpu, bootstrap, 2, b"HELLO   ", high=WORK_LOW + 32)
    assert cpu.a == 0xFF
    assert bytes(cpu.mem[old_base:LAYOUT["RSX"]]) == before_live
    assert bytes(cpu.mem[RSTCOUNT:RSTCOUNT + 41]) == before_state

    # A missing resolver must fail before any live movement or publication.
    resolver_name = cpu.mem.find(b"R3RESOL ", LAYOUT["FILE"], LAYOUT["FILE"] + len(stub))
    assert resolver_name >= 0
    cpu.mem[resolver_name] = ord("X")
    generation = cpu.word(GEN)
    invoke(cpu, bootstrap, 2, b"HELLO   ")
    assert cpu.a == 0xFF and cpu.word(GEN) == generation
    assert bytes(cpu.mem[old_base:LAYOUT["RSX"]]) == before_live
    assert bytes(cpu.mem[RSTCOUNT:RSTCOUNT + 41]) == before_state
    cpu.mem[resolver_name] = ord("R")

    invoke(cpu, bootstrap, 2, b"HELLO   ")
    assert cpu.a == 0 and cpu.mem[RSTCOUNT] == 1
    assert cpu.mem[RSTABLE:RSTABLE + 8] == b"STATEFUL"
    new_base = LAYOUT["RSX"] - stateful_allocation
    assert cpu.word(HEAD) == cpu.word(LOW) == new_base
    value, report = stat(new_base, 2)
    assert report[4:6] == b"\x03\0"
    runtime = int.from_bytes(report[6:8], "little")
    linked = int.from_bytes(report[8:10], "little")
    assert runtime == linked == new_base + (runtime - new_base)
    assert new_base <= runtime < new_base + stateful_allocation
    assert not old_base <= runtime < old_base + stateful_allocation
    assert report[10:16] == b"\x05\0\0\0\xFF\xFF"
    assert value == 0xA4
    assert cpu.mem[runtime:runtime + 4] == b"\xA4\xB2\xC3\xD4"
    assert cpu.word(REQUEST + 12) == 0
    assert cpu.word(GEN) == 4

    invoke(cpu, bootstrap, 2, b"STATEFUL")
    assert cpu.a == 0 and cpu.mem[RSTCOUNT] == 0
    assert cpu.word(HEAD) == 0
    assert cpu.word(TPA) == cpu.word(6) == LAYOUT["TPA"]

    print("prepared Stage 3 loads and removes a profile transactionally; "
          "forced STATEFUL relocation preserves mutable state and pointers")


if __name__ == "__main__":
    main()
