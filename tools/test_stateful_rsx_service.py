#!/usr/bin/env python3
"""Execute the STATEFUL qualification service at two linked addresses."""
from __future__ import annotations

import struct
from pathlib import Path

from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]
REQUEST = 0x7000


def provider(base: int) -> tuple[Z80, int, int]:
    carrier = (ROOT / "build/rsx/STATEFUL.RSX").read_bytes()
    linked = struct.unpack_from("<H", carrier, 10)[0]
    size = struct.unpack_from("<H", carrier, 12)[0]
    count = struct.unpack_from("<H", carrier, 22)[0]
    code = carrier[512:512 + size]
    cpu = Z80(b"")
    cpu.mem[base:base + size] = code
    for index in range(count):
        offset = struct.unpack_from("<H", carrier, 48 + 2 * index)[0]
        cpu.setword(base + offset,
                    (cpu.word(base + offset) + base - linked) & 0xFFFF)
    metadata = struct.unpack_from("<H", carrier, 30)[0]
    service = struct.unpack_from("<H", carrier, metadata + 20)[0]
    runtime_record = metadata + 24
    runtime = struct.unpack_from("<H", carrier, runtime_record + 2)[0]
    cpu.sp = 0x6000
    return cpu, base + service, base + runtime


def call(cpu: Z80, entry: int, operation: int) -> None:
    cpu.mem[REQUEST:REQUEST + 16] = bytes((1, 16, operation)) + bytes(13)
    cpu.de = REQUEST
    cpu.run(entry, limit=2000)
    if operation != 2 and cpu.a:
        raise SystemExit(f"STAT operation {operation} failed: {cpu.a:02x}")


def main() -> None:
    for base in (0x8000, 0xB103):
        cpu, entry, runtime_slot = provider(base)
        call(cpu, entry, 0)
        runtime = cpu.word(runtime_slot)
        for _ in range(3):
            call(cpu, entry, 1)
        call(cpu, entry, 2)
        values = tuple(cpu.word(REQUEST + offset)
                       for offset in (4, 6, 8, 10, 12, 14))
        counter, reported_runtime, linked, fixed, null, sentinel = values
        assert counter == 3
        assert reported_runtime == runtime == linked == cpu.hl
        assert fixed == 5 and null == 0 and sentinel == 0xFFFF
        assert cpu.mem[runtime:runtime + 4] == bytes((0xA4, 0xB2, 0xC3, 0xD4))
        assert cpu.a == 0xA4
        assert cpu.sp == 0x6000
    print("STATEFUL STAT service initializes and mutates the complete fixture "
          "at two relocation addresses")


if __name__ == "__main__":
    main()
