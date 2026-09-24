#!/usr/bin/env python3
"""Qualify the file-backed Stage-3 overlay handoff and packed addresses."""
from __future__ import annotations

import struct
import tempfile
from pathlib import Path

from build_ccp import assemble
from system_layout import LAYOUT
from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]
STREAM = 0x6000
COUNT = 0x5FFF
REQUEST = 0x6600
NAME = 0x6620
NEXT = 0x6543
SCRATCH = 0x6800
MARK = 0x5FFE
ENTRY = LAYOUT["CONFIG"] + 0x310


def file_stub(work: Path) -> bytes:
    source = f"""
        ASEG
        ORG     0{LAYOUT['FILE']:04X}H
        JP      OPEN
        JP      NEXTREC
        JP      RESET
OPEN:   XOR     A
        LD      ({COUNT:04X}H),A
        RET
RESET:  XOR     A
        LD      ({COUNT:04X}H),A
        RET
NEXTREC:
        PUSH    HL
        EX      DE,HL
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
        LD      BC,{STREAM:04X}H
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


def target(work: Path) -> bytes:
    source = f"""
        ASEG
        ORG     0{LAYOUT['RSX']:04X}H
        LD      ({MARK:04X}H),DE
        XOR     A
        RET
        END
"""
    return assemble(Path("/Users/nathanael/bin/z80asm"), source,
                    work / "target.bin", work / "target.lst", LAYOUT["RSX"])


def main() -> None:
    snapshot = (ROOT / "build/system/R3SNAP.RSX").read_bytes()
    carrier = (ROOT / "build/system/R3CARR.RSX").read_bytes()
    metadata = (ROOT / "build/system/R3META.RSX").read_bytes()
    coordinator = (ROOT / "build/system/R3COORD.RSX").read_bytes()
    profile = (ROOT / "build/system/R3PROF.RSX").read_bytes()
    retained_context = (ROOT / "build/system/R3KCTX.RSX").read_bytes()
    retained_loader = (ROOT / "build/system/R3KEEP.RSX").read_bytes()
    retained_prepare = (ROOT / "build/system/R3KPRE.RSX").read_bytes()
    finalizer = (ROOT / "build/system/R3FINAL.RSX").read_bytes()
    remover = (ROOT / "build/system/R3DROP.RSX").read_bytes()
    move = (ROOT / "build/system/R3MOVE.RSX").read_bytes()
    commit = (ROOT / "build/system/R3COMIT.RSX").read_bytes()
    resolver = (ROOT / "build/system/R3RESOL.RSX").read_bytes()
    assert 0 < len(snapshot) <= 1024
    assert 0 < len(carrier) <= 1024
    assert 0 < len(metadata) <= 1024
    assert len(coordinator) == 1024
    assert coordinator[-3:] == bytes((0xC3, LAYOUT["BDOS"] & 0xFF,
                                      LAYOUT["BDOS"] >> 8))
    assert len(profile) == 1024
    assert profile[-3:] == bytes((0xC3, LAYOUT["BDOS"] & 0xFF,
                                  LAYOUT["BDOS"] >> 8))
    for overlay in (retained_context, retained_loader, retained_prepare,
                    finalizer, remover):
        assert len(overlay) == 1024
        assert overlay[-3:] == bytes((0xC3, LAYOUT["BDOS"] & 0xFF,
                                      LAYOUT["BDOS"] >> 8))
    assert len(move) == len(commit) == len(resolver) == 1024
    assert (move[0] != 0 and move[0x120] != 0 and move[0x310] != 0 and
            move[0x38F] != 0 and move[0x3DF] != 0)
    for overlay in (commit, resolver):
        assert overlay[-3:] == bytes((0xC3, LAYOUT["BDOS"] & 0xFF,
                                      LAYOUT["BDOS"] >> 8))
    with tempfile.TemporaryDirectory(prefix="bettercpm-rsx-overlay-") as temporary:
        work = Path(temporary)
        cpu = Z80(b"")
        io = (ROOT / "build/system/rsxio.bin").read_bytes()
        io_base = SCRATCH + 0x400
        cpu.mem[io_base:io_base + len(io)] = io
        stub = file_stub(work)
        payload = target(work).ljust(1024, b"\0")
        cpu.mem[LAYOUT["FILE"]:LAYOUT["FILE"] + len(stub)] = stub
        cpu.mem[LAYOUT["CONFIG"]:LAYOUT["CONFIG"] + len(move)] = move
        cpu.mem[STREAM:STREAM + 1024] = payload
        preserved = bytes(range(12))
        cpu.mem[LAYOUT["RSX"] + 1012:LAYOUT["RSX"] + 1024] = preserved
        cpu.mem[NAME:NAME + 8] = b"R3COMIT "
        cpu.mem[REQUEST:REQUEST + 6] = struct.pack(
            "<HHH", NAME, SCRATCH, NEXT)
        cpu.de = REQUEST
        cpu.sp = 0x5F00
        cpu.run(ENTRY, limit=20000)
        assert cpu.a == 0 and cpu.word(MARK) == NEXT
        assert cpu.mem[LAYOUT["RSX"]:LAYOUT["RSX"] + 1012] == payload[:1012]
        assert cpu.mem[LAYOUT["RSX"] + 1012:LAYOUT["RSX"] + 1024] == preserved
        assert cpu.sp == 0x5F00
    print("file-backed RSX handoff replaces the safe 1,012-byte prefix, preserves "
          "the live manager frame, and transfers control safely")


if __name__ == "__main__":
    main()
