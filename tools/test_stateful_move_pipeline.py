#!/usr/bin/env python3
"""Compose carrier slot preparation, live movement, and relocated service use."""
from __future__ import annotations

import struct
from pathlib import Path

from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]
SLOTS_ENTRY = 0x7200
MOVER_ENTRY = 0x7000
SLOTS_REQUEST = 0x6000
STATIC = 0x6100
RUNTIME = 0x6200
UNION = 0x6300
MOVE_REQUEST = 0x6400
SERVICE_REQUEST = 0x6500
OLD = 0x8000
NEW = 0x8080


def main() -> None:
    carrier = (ROOT / "build/rsx/STATEFUL.RSX").read_bytes()
    linked = struct.unpack_from("<H", carrier, 10)[0]
    size = struct.unpack_from("<H", carrier, 12)[0]
    allocation = struct.unpack_from("<H", carrier, 14)[0]
    relocation_count = struct.unpack_from("<H", carrier, 22)[0]
    table = struct.unpack_from("<H", carrier, 28)[0]
    static = tuple(struct.unpack_from("<H", carrier, table + 2 * index)[0]
                   for index in range(relocation_count))
    metadata = struct.unpack_from("<H", carrier, 30)[0]
    cursor = metadata + 12
    runtime: tuple[int, ...] = ()
    service = 0
    for _ in range(carrier[metadata + 7]):
        record_type, length = carrier[cursor:cursor + 2]
        payload = carrier[cursor + 2:cursor + 2 + length]
        if record_type == 2:
            service = struct.unpack_from("<H", payload, 6)[0]
        elif record_type == 3:
            runtime = tuple(struct.unpack_from("<H", payload, offset)[0]
                            for offset in range(0, length, 2))
        cursor += 2 + length

    cpu = Z80(b"")
    slots_code = (ROOT / "build/system/rsxslots.bin").read_bytes()
    mover_code = (ROOT / "build/system/rsxmover.bin").read_bytes()
    cpu.mem[SLOTS_ENTRY:SLOTS_ENTRY + len(slots_code)] = slots_code
    cpu.mem[MOVER_ENTRY:MOVER_ENTRY + len(mover_code)] = mover_code
    cpu.mem[STATIC:STATIC + 2 * len(static)] = b"".join(
        value.to_bytes(2, "little") for value in static)
    cpu.mem[RUNTIME:RUNTIME + 2 * len(runtime)] = b"".join(
        value.to_bytes(2, "little") for value in runtime)
    cpu.mem[SLOTS_REQUEST:SLOTS_REQUEST + 13] = struct.pack(
        "<HBBHHHBB", allocation, len(static), len(runtime), STATIC, RUNTIME,
        UNION, len(static) + len(runtime), 0) + b"\0"
    cpu.de = SLOTS_REQUEST
    cpu.sp = 0x5F00
    cpu.run(SLOTS_ENTRY, limit=10000)
    assert cpu.a == 0
    union_count = cpu.mem[SLOTS_REQUEST + 12]

    cpu.mem[OLD:OLD + allocation] = bytes(allocation)
    cpu.mem[OLD:OLD + size] = carrier[512:512 + size]
    for offset in static:
        cpu.setword(OLD + offset,
                    (cpu.word(OLD + offset) + OLD - linked) & 0xFFFF)

    def service_call(base: int, operation: int) -> None:
        cpu.mem[SERVICE_REQUEST:SERVICE_REQUEST + 16] = \
            bytes((1, 16, operation)) + bytes(13)
        cpu.de = SERVICE_REQUEST
        cpu.run(base + service, limit=3000)

    service_call(OLD, 0)
    for _ in range(3):
        service_call(OLD, 1)

    union = bytes(cpu.mem[UNION:UNION + 2 * union_count])
    move = (OLD.to_bytes(2, "little") + NEW.to_bytes(2, "little") +
            allocation.to_bytes(2, "little") + bytes((union_count, 0)) + union)
    cpu.mem[MOVE_REQUEST:MOVE_REQUEST + len(move)] = move
    cpu.de = MOVE_REQUEST
    cpu.run(MOVER_ENTRY, limit=10000)
    assert cpu.a == 0

    service_call(NEW, 2)
    counter = cpu.word(SERVICE_REQUEST + 4)
    runtime_pointer = cpu.word(SERVICE_REQUEST + 6)
    linked_pointer = cpu.word(SERVICE_REQUEST + 8)
    assert counter == 3
    assert runtime_pointer == linked_pointer == cpu.hl
    assert not OLD <= runtime_pointer < OLD + allocation
    assert NEW <= runtime_pointer < NEW + allocation
    assert cpu.word(SERVICE_REQUEST + 10) == 5
    assert cpu.word(SERVICE_REQUEST + 12) == 0
    assert cpu.word(SERVICE_REQUEST + 14) == 0xFFFF
    assert cpu.mem[runtime_pointer:runtime_pointer + 4] == \
        bytes((0xA4, 0xB2, 0xC3, 0xD4))
    assert cpu.sp == 0x5F00
    print("STATEFUL carrier metadata drives an overlapping live move; mutable "
          "state and both internal pointer classes survive at the new base")


if __name__ == "__main__":
    main()
