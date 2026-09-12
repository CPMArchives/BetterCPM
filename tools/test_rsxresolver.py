#!/usr/bin/env python3
"""Exercise the disk-free Stage-2 Function 208 resolver in isolation."""
from __future__ import annotations

import struct
from pathlib import Path

from system_layout import LAYOUT
from test_bios import Z80, require

ROOT = Path(__file__).resolve().parents[1]
RESOLVER = ROOT / "build/system/rsxresolver.bin"
BASE = LAYOUT["RSX"]
HEAD = LAYOUT["SYSTEM"] + 0x84
CORE = LAYOUT["BDOS"]
REQUEST = 0x7000


def provider(cpu: Z80, base: int, next_dispatch: int,
             services: list[tuple[bytes, int, int, int, int]]) -> None:
    descriptor_offset = 0x80
    struct.pack_into("<HHBBH", cpu.mem, base, next_dispatch, base + 8,
                     len(services), 0, descriptor_offset)
    for index, service in enumerate(services):
        struct.pack_into("<4sBBHH", cpu.mem, base + descriptor_offset + 10 * index,
                         *service)
    cpu.mem[base + 0x20] = 0xC9


def request(cpu: Z80, operation: int, service: bytes = b"    ",
            major: int = 0, minor: int = 0, capabilities: int = 0,
            ordinal: int = 0) -> tuple[int, int]:
    cpu.mem[REQUEST:REQUEST + 20] = struct.pack(
        "<BBBB4sBBHHBBHBB", 1, 20, operation, 0, service, major, minor,
        capabilities, 0, 0, 0, 0, ordinal, 0)
    original_sp = cpu.sp
    cpu.de = REQUEST
    cpu.run(BASE, limit=10000)
    require(cpu.de == REQUEST and cpu.sp == original_sp,
            "resolver did not preserve DE/SP")
    return cpu.a, cpu.hl


def main() -> None:
    image = RESOLVER.read_bytes()
    require(0 < len(image) <= 893, "resolver does not fit overlay slot")
    cpu = Z80(b"")
    cpu.mem[BASE:BASE + len(image)] = image
    first, second = 0xCD04, 0xCC04
    provider(cpu, first, second + 8,
             [(b"TEST", 1, 2, 0x20, 0x0003)])
    provider(cpu, second, CORE,
             [(b"TIME", 1, 0, 0x20, 0x0000)])
    cpu.setword(HEAD, first)

    status, entry = request(cpu, 0, b"TEST", 1, 1, 1)
    require(status == 0 and entry == first + 0x20,
            "compatible TEST lookup failed")
    require(bytes(cpu.mem[REQUEST + 4:REQUEST + 8]) == b"TEST" and
            cpu.mem[REQUEST + 14:REQUEST + 19] == bytes((1, 2, 3, 0, 0)),
            "TEST result fields are incorrect")
    require(request(cpu, 0, b"TEST", 2)[0] == 2,
            "major-version filter failed")
    require(request(cpu, 0, b"TEST", 1, 3)[0] == 3,
            "minor-version filter failed")
    require(request(cpu, 0, b"TEST", 1, 0, 4)[0] == 4,
            "capability filter failed")
    require(request(cpu, 0, b"NONE", 1)[0] == 1,
            "unknown service did not report SERVICE_NOT_FOUND")

    status, entry = request(cpu, 1, ordinal=1)
    require(status == 0 and entry == 0 and cpu.word(REQUEST + 12) == second + 0x20 and
            bytes(cpu.mem[REQUEST + 4:REQUEST + 8]) == b"TIME" and
            cpu.mem[REQUEST + 18] == 1,
            "service enumeration did not return the second provider")
    require(request(cpu, 1, ordinal=2)[0] == 0x0A,
            "enumeration did not terminate cleanly")

    legacy = 0xCE04
    struct.pack_into("<HH", cpu.mem, legacy, first + 8, legacy + 4)
    cpu.setword(HEAD, legacy)
    require(request(cpu, 0, b"TIME", 1)[0] == 0,
            "legacy BRSX-v1 provider was not skipped")
    cpu.setword(HEAD, first)

    status, entry = request(cpu, 2)
    require(status == 0 and entry == 0 and cpu.word(REQUEST + 12) == 2 and
            cpu.mem[REQUEST + 14:REQUEST + 18] == bytes((4, 2, 8, 0)),
            "registry description is incorrect")

    cpu.setword(first + 2, first + 9)
    require(request(cpu, 0, b"TEST", 1)[0] == 9,
            "corrupt runtime header was followed")
    print("Function 208 lookup, filtering, enumeration, description, and corruption checks passed")


if __name__ == "__main__":
    main()
