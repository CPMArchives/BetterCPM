#!/usr/bin/env python3
"""Qualify construction of commit-ready fresh and STATELESS snapshots."""
from __future__ import annotations

import struct
from pathlib import Path

from system_layout import LAYOUT
from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]
ENTRY = LAYOUT["CONFIG"]
REQUEST = 0x6000
SOURCE = 0x6200
RELOCS = 0x6300
SERVICES = 0x6320
OUTPUT = 0x6800
LINKED = 0x8000
LIVE = 0x9000
CODE_SIZE = 0x80
ALLOCATION = 0x100


def invoke(*, relocation_values: tuple[int, ...] = (0x20, 0x30),
           code_size: int = CODE_SIZE, dispatch: int = 8,
           service_count: int = 2, source: int = SOURCE,
           format_version: int = 2) -> tuple[Z80, bytes]:
    cpu = Z80(b"")
    code = (ROOT / "build/system/R3SNAP.RSX").read_bytes()
    cpu.mem[ENTRY:ENTRY + len(code)] = code

    payload = bytearray((index * 3) & 0xFF for index in range(CODE_SIZE))
    struct.pack_into("<H", payload, 0x20, LINKED + 0x44)
    struct.pack_into("<H", payload, 0x30, LINKED + 0x66)
    struct.pack_into("<H", payload, 0x40, 0x0005)
    cpu.mem[source:source + len(payload)] = payload
    if relocation_values:
        cpu.mem[RELOCS:RELOCS + 2 * len(relocation_values)] = struct.pack(
            "<" + "H" * len(relocation_values), *relocation_values)
    descriptors = (
        struct.pack("<4sBBHH", b"ONE ", 1, 0, 0x18, 0x1111) +
        struct.pack("<4sBBHH", b"TWO ", 1, 1, 0x28, 0x2222)
    )
    cpu.mem[SERVICES:SERVICES + len(descriptors)] = descriptors
    cpu.mem[OUTPUT:OUTPUT + ALLOCATION] = b"\xA5" * ALLOCATION
    before = bytes(cpu.mem[OUTPUT:OUTPUT + ALLOCATION])
    request = struct.pack(
        "<8HBBHHB", source, code_size, ALLOCATION, LINKED, LIVE,
        RELOCS, len(relocation_values), SERVICES, service_count, format_version,
        OUTPUT, dispatch, 0xCC)
    cpu.mem[REQUEST:REQUEST + len(request)] = request
    cpu.de = REQUEST
    cpu.sp = 0x5F00
    cpu.run(ENTRY, limit=30000)
    return cpu, before


def main() -> None:
    cpu, _ = invoke()
    assert cpu.a == 0 and cpu.mem[REQUEST + 22] == 1
    assert cpu.word(OUTPUT + 0x20) == LIVE + 0x44
    assert cpu.word(OUTPUT + 0x30) == LIVE + 0x66
    assert cpu.word(OUTPUT + 0x40) == 0x0005
    assert cpu.mem[OUTPUT:OUTPUT + 4] == b"\0\0\0\0"
    assert cpu.mem[OUTPUT + 4:OUTPUT + 8] == bytes((2, 0, 0xEC, 0))
    assert cpu.mem[OUTPUT + CODE_SIZE:OUTPUT + 0xEC] == \
        b"\0" * (0xEC - CODE_SIZE)
    assert cpu.mem[OUTPUT + 0xEC:OUTPUT + 0xF6] == \
        cpu.mem[SERVICES + 10:SERVICES + 20]
    assert cpu.mem[OUTPUT + 0xF6:OUTPUT + 0x100] == \
        cpu.mem[SERVICES:SERVICES + 10]
    assert cpu.sp == 0x5F00

    cpu, _ = invoke(format_version=1, dispatch=4, service_count=0)
    assert cpu.a == 0 and cpu.mem[REQUEST + 22] == 1
    assert cpu.mem[OUTPUT:OUTPUT + 4] == b"\0\0\0\0"
    assert cpu.mem[OUTPUT + 4] == (4 * 3) & 0xFF

    # Complete validation precedes the first destination write.
    for arguments in (
        {"relocation_values": (0x30, 0x20)},
        {"relocation_values": (CODE_SIZE - 1,)},
        {"dispatch": CODE_SIZE},
        {"code_size": 0xF8, "service_count": 1},
        {"source": OUTPUT + 0x40},
        {"format_version": 1, "service_count": 1, "dispatch": 4},
        {"format_version": 3},
    ):
        cpu, before = invoke(**arguments)
        assert cpu.a == 0xFF and cpu.mem[REQUEST + 22] == 0xCC
        assert bytes(cpu.mem[OUTPUT:OUTPUT + ALLOCATION]) == before

    print("RSX snapshot construction validates before writing, handles legacy "
          "and current headers, relocates for the prospective live base, clears "
          "the allocation tail, and materializes services")


if __name__ == "__main__":
    main()
