#!/usr/bin/env python3
"""Merge real STATEFUL static/runtime pointer metadata with the Z80 preparer."""
from __future__ import annotations

from pathlib import Path
import struct

from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]
ENTRY = 0x7200
REQUEST = 0x6000
STATIC = 0x6100
RUNTIME = 0x6200
OUTPUT = 0x6300


def words(data: bytes) -> tuple[int, ...]:
    return tuple(struct.unpack_from("<H", data, offset)[0]
                 for offset in range(0, len(data), 2))


def invoke(static: tuple[int, ...], runtime: tuple[int, ...], allocation: int,
           capacity: int | None = None) -> tuple[Z80, bytes]:
    cpu = Z80(b"")
    code = (ROOT / "build/system/rsxslots.bin").read_bytes()
    cpu.mem[ENTRY:ENTRY + len(code)] = code
    cpu.mem[STATIC:STATIC + 2 * len(static)] = b"".join(
        value.to_bytes(2, "little") for value in static)
    cpu.mem[RUNTIME:RUNTIME + 2 * len(runtime)] = b"".join(
        value.to_bytes(2, "little") for value in runtime)
    cpu.mem[OUTPUT:OUTPUT + 128] = bytes((0xA5,)) * 128
    capacity = len(static) + len(runtime) if capacity is None else capacity
    request = struct.pack("<HBBHHHBB", allocation, len(static), len(runtime),
                          STATIC, RUNTIME, OUTPUT, capacity, 0) + bytes((0xCC,))
    cpu.mem[REQUEST:REQUEST + len(request)] = request
    before = bytes(cpu.mem[OUTPUT:OUTPUT + 128])
    cpu.de = REQUEST
    cpu.sp = 0x5F00
    cpu.run(ENTRY, limit=10000)
    return cpu, before


def carrier_lists() -> tuple[tuple[int, ...], tuple[int, ...], int]:
    carrier = (ROOT / "build/rsx/STATEFUL.RSX").read_bytes()
    allocation = struct.unpack_from("<H", carrier, 14)[0]
    count = struct.unpack_from("<H", carrier, 22)[0]
    table = struct.unpack_from("<H", carrier, 28)[0]
    static = tuple(struct.unpack_from("<H", carrier, table + 2 * index)[0]
                   for index in range(count))
    metadata = struct.unpack_from("<H", carrier, 30)[0]
    cursor = metadata + 12
    runtime: tuple[int, ...] = ()
    for _ in range(carrier[metadata + 7]):
        record_type, length = carrier[cursor:cursor + 2]
        payload = carrier[cursor + 2:cursor + 2 + length]
        if record_type == 3:
            runtime = words(payload)
        cursor += 2 + length
    return static, runtime, allocation


def main() -> None:
    static, runtime, allocation = carrier_lists()
    cpu, _before = invoke(static, runtime, allocation)
    assert cpu.a == 0
    count = cpu.mem[REQUEST + 12]
    expected = tuple(sorted(set(static) | set(runtime)))
    observed = tuple(cpu.word(OUTPUT + 2 * index) for index in range(count))
    assert observed == expected
    assert cpu.sp == 0x5F00

    for bad_static, bad_runtime, capacity in (
            ((static[1], static[0]) + static[2:], runtime, None),
            (static, runtime + runtime, None),
            (static, (allocation - 1,), None),
            (static, runtime, len(static) + len(runtime) - 1)):
        cpu, before = invoke(bad_static, bad_runtime, allocation, capacity)
        assert cpu.a == 0xFF
        assert bytes(cpu.mem[OUTPUT:OUTPUT + 128]) == before
        assert cpu.mem[REQUEST + 12] == 0xCC
    print("RSX slot preparer merges the real STATEFUL relocation/runtime "
          "union and rejects malformed inputs atomically")


if __name__ == "__main__":
    main()
