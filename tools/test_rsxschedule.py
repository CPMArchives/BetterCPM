#!/usr/bin/env python3
"""Prove safe ordering of multiple planned STATEFUL live moves."""
from __future__ import annotations

import struct
from pathlib import Path

from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]
MOVER = 0x7000
SCHEDULER = 0x7800
REQUEST = 0x6000
PLAN = 0x6100
DESCRIPTORS = 0x6200
SLOTS = 0x6300
SCRATCH = 0x6400
SIZE = 0x100


def fixture(cpu: Z80, base: int, marker: int) -> bytes:
    cpu.mem[base:base + SIZE] = bytes((marker,)) * SIZE
    cpu.setword(base + 0x20, base + 0x40)
    return bytes(cpu.mem[base:base + SIZE])


def run(old_bases: tuple[int, int], new_bases: tuple[int, int]) -> None:
    cpu = Z80((ROOT / "build/bios/bios.bin").read_bytes())
    mover = (ROOT / "build/system/rsxmover.bin").read_bytes()
    scheduler = (ROOT / "build/system/rsxschedule.bin").read_bytes()
    cpu.mem[MOVER:MOVER + len(mover)] = mover
    cpu.mem[SCHEDULER:SCHEDULER + len(scheduler)] = scheduler
    expected = [fixture(cpu, base, 0x31 + index * 0x22)
                for index, base in enumerate(old_bases)]
    records = b"".join(struct.pack("<HHHBB", old, new, SIZE, 1, index)
                       for index, (old, new) in enumerate(zip(old_bases, new_bases)))
    cpu.mem[PLAN:PLAN + len(records)] = records
    cpu.mem[SLOTS:SLOTS + 4] = struct.pack("<HH", 0x20, 0x22)
    cpu.mem[DESCRIPTORS:DESCRIPTORS + 6] = \
        struct.pack("<HBHB", SLOTS, 2, SLOTS, 2)
    cpu.mem[REQUEST:REQUEST + 13] = struct.pack(
        "<HHBBHHH", PLAN, DESCRIPTORS, 2, 0, SCRATCH, 32, MOVER) + b"\xCC"
    cpu.de = REQUEST
    cpu.sp = 0x5F00
    cpu.run(SCHEDULER, limit=30000)
    assert cpu.a == 0 and cpu.mem[REQUEST + 12] == 2
    for index, base in enumerate(new_bases):
        moved = bytearray(expected[index])
        moved[0x20:0x22] = (base + 0x40).to_bytes(2, "little")
        actual = cpu.mem[base:base + SIZE]
        assert actual == moved, (index, hex(base), bytes(actual[:8]), bytes(moved[:8]), next(
            (offset for offset, pair in enumerate(zip(actual, moved))
             if pair[0] != pair[1]), None))
        assert cpu.word(base + 0x20) == base + 0x40
        assert cpu.word(base + 0x22) == 0x3131 + index * 0x2222
    assert cpu.sp == 0x5F00


def rejected_mixed_direction() -> None:
    cpu = Z80((ROOT / "build/bios/bios.bin").read_bytes())
    mover = (ROOT / "build/system/rsxmover.bin").read_bytes()
    scheduler = (ROOT / "build/system/rsxschedule.bin").read_bytes()
    cpu.mem[MOVER:MOVER + len(mover)] = mover
    cpu.mem[SCHEDULER:SCHEDULER + len(scheduler)] = scheduler
    records = (struct.pack("<HHHBB", 0x8000, 0x8100, SIZE, 1, 0) +
               struct.pack("<HHHBB", 0x8300, 0x8200, SIZE, 1, 1))
    cpu.mem[PLAN:PLAN + len(records)] = records
    cpu.mem[SLOTS:SLOTS + 2] = struct.pack("<H", 0x20)
    cpu.mem[DESCRIPTORS:DESCRIPTORS + 6] = struct.pack("<HBHB", SLOTS, 1, SLOTS, 1)
    cpu.mem[REQUEST:REQUEST + 13] = struct.pack(
        "<HHBBHHH", PLAN, DESCRIPTORS, 2, 0, SCRATCH, 16, MOVER) + b"\xCC"
    before = bytes(cpu.mem[0x8000:0x8400])
    cpu.de = REQUEST
    cpu.sp = 0x5F00
    cpu.run(SCHEDULER, limit=10000)
    assert cpu.a == 0xFF and cpu.mem[REQUEST + 12] == 0xCC
    assert cpu.mem[0x8000:0x8400] == before


def repair_count_boundaries() -> None:
    # Exercise the actual scheduler/mover together. Both byte-length conversion
    # and copying must retain the carry across 127 -> 128 words.
    for count in (0, 1, 127, 128, 144, 255):
        for short in (False, True):
            cpu = Z80((ROOT/'build/bios/bios.bin').read_bytes())
            for address, name in [(MOVER, 'rsxmover.bin'), (SCHEDULER, 'rsxschedule.bin')]:
                image = (ROOT/'build/system'/name).read_bytes()
                cpu.mem[address:address+len(image)] = image
            old, new, size = 0x8000, 0x8400, 0x400
            original = bytearray(b'Z'*size)
            for i in range(count):original[i*2:i*2+2] = (old+0x300).to_bytes(2, 'little')
            cpu.mem[old:old+size] = original
            slots = b''.join((i*2).to_bytes(2, 'little') for i in range(count))
            slot_base = 0x6800
            cpu.mem[slot_base:slot_base+len(slots)] = slots
            cpu.mem[PLAN:PLAN+8] = struct.pack('<HHHBB', old, new, size, 1, 0)
            cpu.mem[DESCRIPTORS:DESCRIPTORS+3] = struct.pack('<HB', slot_base, count)
            capacity = 8+2*count-int(short)
            cpu.mem[REQUEST:REQUEST+13] = struct.pack('<HHBBHHH', PLAN, DESCRIPTORS, 1, 0, SCRATCH, capacity, MOVER)+b'\xcc'
            cpu.mem[SCRATCH+capacity:SCRATCH+capacity+8] = b'G'*8
            before = bytes(cpu.mem[old:new+size])
            cpu.de=REQUEST;cpu.sp=0x5F00;cpu.run(SCHEDULER, limit=100000)
            assert cpu.sp==0x5F00,(count,short,hex(cpu.sp))
            if short:
                assert cpu.a==255 and bytes(cpu.mem[old:new+size])==before, count
                assert cpu.mem[REQUEST+12]==0xCC
            else:
                expected=bytearray(original)
                for i in range(count):expected[i*2:i*2+2]=(new+0x300).to_bytes(2, 'little')
                assert cpu.a==0 and cpu.mem[REQUEST+12]==1, count
                assert bytes(cpu.mem[new:new+size])==expected, count
            assert bytes(cpu.mem[SCRATCH+capacity:SCRATCH+capacity+8])==b'G'*8, count


def main() -> None:
    # Upward compaction must run in profile order or the lower image overwrites
    # the source of the higher image before it can be preserved.
    run((0x8000, 0x7F00), (0x8100, 0x8000))
    # Downward movement uses reverse profile order for the symmetric reason.
    run((0x8100, 0x8000), (0x8000, 0x7F00))
    rejected_mixed_direction()
    repair_count_boundaries()
    print("RSX scheduler orders multiple upward/downward STATEFUL moves safely "
          "and rejects mixed-direction plans before mutation; repair counts 0/1/127/128/144/255 pass with guarded capacity checks")


if __name__ == "__main__":
    main()
