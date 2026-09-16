#!/usr/bin/env python3
"""Qualify overlap-safe RSX movement and guarded internal-pointer repair."""
from pathlib import Path

from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]
MOVER = ROOT / "build/system/rsxmover.bin"
ENTRY = 0x7000
REQUEST = 0x6000
SIZE = 0x300
SLOTS = (0x20, 0x22, 0x24, 0x26)


def request(cpu: Z80, old: int, new: int, slots: tuple[int, ...] = SLOTS) -> None:
    data = (old.to_bytes(2, "little") + new.to_bytes(2, "little") +
            SIZE.to_bytes(2, "little") + bytes((len(slots), 0)) +
            b"".join(slot.to_bytes(2, "little") for slot in slots))
    cpu.mem[REQUEST:REQUEST + len(data)] = data
    cpu.de = REQUEST
    cpu.run(ENTRY, limit=10000)


def image(cpu: Z80, base: int) -> None:
    cpu.mem[base:base + SIZE] = bytes((index * 37 + 11) & 0xFF
                                      for index in range(SIZE))
    cpu.setword(base + 0x20, base + 0x180)
    cpu.setword(base + 0x22, 5)
    cpu.setword(base + 0x24, 0)
    cpu.setword(base + 0x26, 0xFFFF)


def qualify(old: int, new: int) -> None:
    cpu = Z80(b"")
    mover = MOVER.read_bytes()
    cpu.mem[ENTRY:ENTRY + len(mover)] = mover
    cpu.sp = 0x5F00
    image(cpu, old)
    expected = bytes(cpu.mem[old:old + SIZE])
    request(cpu, old, new)
    assert cpu.a == 0
    moved = bytearray(expected)
    moved[0x20:0x22] = (new + 0x180).to_bytes(2, "little")
    assert cpu.mem[new:new + SIZE] == moved
    assert tuple(cpu.word(new + offset) for offset in SLOTS) == (
        new + 0x180, 5, 0, 0xFFFF)
    assert cpu.sp == 0x5F00


def invalid_is_atomic() -> None:
    cpu = Z80(b"")
    mover = MOVER.read_bytes()
    cpu.mem[ENTRY:ENTRY + len(mover)] = mover
    cpu.sp = 0x5F00
    old, new = 0x8000, 0x8400
    image(cpu, old)
    before_old = bytes(cpu.mem[old:old + SIZE])
    before_new = bytes(cpu.mem[new:new + SIZE])
    request(cpu, old, new, (0x20, SIZE - 1))
    assert cpu.a == 0xFF
    assert cpu.mem[old:old + SIZE] == before_old
    assert cpu.mem[new:new + SIZE] == before_new


def main() -> None:
    qualify(0x8000, 0x8100)  # overlapping upward movement
    qualify(0x8100, 0x8000)  # overlapping downward movement
    invalid_is_atomic()
    print("RSX mover preserves overlapping images, repairs only internal "
          "pointers, and rejects invalid slots before mutation")


if __name__ == "__main__":
    main()
