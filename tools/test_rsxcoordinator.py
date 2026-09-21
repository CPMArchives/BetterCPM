#!/usr/bin/env python3
"""Qualify bounded carrier loading and normalization by R3COORD."""
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
WORK_HIGH = 0x7000
CARRIER_SOURCE = 0x9000
CARR_SOURCE = 0x9400
META_SOURCE = 0x9800
FACTS = 0x6400
LIVE_LOW = 0xD600
LIVE_HIGH = 0xEC00


def file_stub(work: Path) -> bytes:
    source = f"""
        ASEG
        ORG     0{LAYOUT['FILE']:04X}H
        JP      OPEN
        JP      NEXT
        JP      OPEN
OPEN:   XOR     A
        LD      ({COUNT:04X}H),A
        LD      A,(HL)
        CP      'R'
        JR      NZ,CARRIER
        INC     HL
        INC     HL
        LD      A,(HL)
        CP      'C'
        JR      Z,CARR
        LD      A,2
        JR      SELECT
CARR:   LD      A,1
        JR      SELECT
CARRIER:
        XOR     A
SELECT: LD      ({SELECT:04X}H),A
        XOR     A
        RET
NEXT:   PUSH    HL
        EX      DE,HL
        LD      A,({SELECT:04X}H)
        OR      A
        LD      BC,{CARRIER_SOURCE:04X}H
        JR      Z,HAVESRC
        DEC     A
        LD      BC,{CARR_SOURCE:04X}H
        JR      Z,HAVESRC
        LD      BC,{META_SOURCE:04X}H
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


def invoke(stub: bytes, carrier: bytes, name: bytes, *, operation: int = 1,
           high: int = WORK_HIGH) -> tuple[Z80, bytes]:
    cpu = Z80(b"")
    coordinator = (ROOT / "build/system/R3COORD.RSX").read_bytes()
    carr = (ROOT / "build/system/R3CARR.RSX").read_bytes()
    meta = (ROOT / "build/system/R3META.RSX").read_bytes()
    cpu.mem[LAYOUT["RSX"]:LAYOUT["RSX"] + len(coordinator)] = coordinator
    cpu.mem[LAYOUT["FILE"]:LAYOUT["FILE"] + len(stub)] = stub
    cpu.mem[CARRIER_SOURCE:CARRIER_SOURCE + 1024] = carrier.ljust(1024, b"\0")
    cpu.mem[CARR_SOURCE:CARR_SOURCE + 1024] = carr.ljust(1024, b"\0")
    cpu.mem[META_SOURCE:META_SOURCE + 1024] = meta.ljust(1024, b"\0")
    cpu.mem[COUNT:SELECT + 1] = b"\xA5\xA5"
    request = bytes((2, operation, 0, 0)) + name + b"\xA5\xA5" + \
        struct.pack("<HH", WORK_LOW, high)
    cpu.mem[REQUEST:REQUEST + len(request)] = request
    cpu.mem[LIVE_LOW:LIVE_HIGH] = b"\x5A" * (LIVE_HIGH - LIVE_LOW)
    before_live = bytes(cpu.mem[LIVE_LOW:LIVE_HIGH])
    cpu.de = REQUEST
    cpu.sp = 0x5700
    cpu.run(LAYOUT["RSX"], limit=100000)
    assert bytes(cpu.mem[LIVE_LOW:LIVE_HIGH]) == before_live
    return cpu, before_live


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="bettercpm-rsx-coordinator-") as temporary:
        stub = file_stub(Path(temporary))
        stateful = (ROOT / "build/rsx/STATEFUL.RSX").read_bytes()
        cpu, _ = invoke(stub, stateful, b"STATEFUL")
        assert cpu.a == 0 and cpu.hl == FACTS
        assert cpu.word(REQUEST + 12) == int.from_bytes(stateful[46:48], "little")
        assert cpu.mem[WORK_LOW:WORK_LOW + len(stateful)] == stateful
        assert cpu.word(FACTS) == WORK_LOW + 512
        assert cpu.mem[FACTS + 20:FACTS + 22] == bytes((1, 2))
        assert cpu.mem[FACTS + 16:FACTS + 18] == b"\x01\x01"

        # The exact worst-case reservation (facts plus two descriptors) is
        # accepted even though this carrier currently publishes only one.
        cpu, _ = invoke(stub, stateful, b"STATEFUL", high=FACTS + 46)
        assert cpu.a == 0 and cpu.hl == FACTS

        hello = (ROOT / "build/rsx/HELLO.RSX").read_bytes()
        cpu, _ = invoke(stub, hello, b"HELLO   ")
        assert cpu.a == 0 and cpu.hl == FACTS
        assert cpu.mem[FACTS + 20:FACTS + 22] == bytes((0, 1))
        assert cpu.mem[FACTS + 16:FACTS + 18] == b"\0\0"

        broken = bytearray(stateful)
        broken[512] ^= 1
        cpu, _ = invoke(stub, bytes(broken), b"STATEFUL")
        assert cpu.a == 0xFF and cpu.word(REQUEST + 12) == 0xA5A5
        cpu, _ = invoke(stub, stateful, b"STATEFUL", high=FACTS + 45)
        assert cpu.a == 0xFF and cpu.word(REQUEST + 12) == 0xA5A5
        cpu, _ = invoke(stub, stateful, b"STATEFUL", operation=2)
        assert cpu.a == 0xFF and cpu.word(REQUEST + 12) == 0xA5A5

    print("R3COORD streams bounded v1/v2 carriers, publishes normalized facts "
          "only after both validation phases, and never mutates the live chain")


if __name__ == "__main__":
    main()
