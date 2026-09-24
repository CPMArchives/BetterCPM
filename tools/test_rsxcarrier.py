#!/usr/bin/env python3
"""Qualify bounded BRSX carrier normalization for the Stage-3 coordinator."""
from __future__ import annotations

import struct
from pathlib import Path

from build_rsx_module import make_module
from system_layout import LAYOUT
from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]
ENTRY = LAYOUT["CONFIG"]
CARRIER = 0x6200
FACTS = 0x6000
REQUEST = 0x6040
EXPECTED = 0x6080
SCRATCH = 0x6800
HIGH = 0x6900
SNAPSHOT = 0x7000
LIVE = 0x9000


def word(data: bytes | bytearray, offset: int) -> int:
    return data[offset] | data[offset + 1] << 8


def run_phase(cpu: Z80, overlay: str, request: bytes) -> None:
    code = (ROOT / f"build/system/{overlay}").read_bytes()
    cpu.mem[ENTRY:ENTRY + 1024] = b"\0" * 1024
    cpu.mem[ENTRY:ENTRY + len(code)] = code
    cpu.mem[REQUEST:REQUEST + len(request)] = request
    cpu.de = REQUEST
    cpu.sp = 0x5F00
    cpu.run(ENTRY, limit=50000)


def phase_one(carrier: bytes, name: bytes = b"STATEFUL") -> tuple[Z80, bytes]:
    cpu = Z80(b"")
    cpu.mem[CARRIER:CARRIER + len(carrier)] = carrier
    cpu.mem[EXPECTED:EXPECTED + 8] = name
    cpu.mem[FACTS:FACTS + 26] = b"\xA5" * 26
    before = bytes(cpu.mem[FACTS:FACTS + 26])
    request = struct.pack("<6HB", CARRIER, len(carrier), EXPECTED,
                          SCRATCH, HIGH, FACTS, 0xCC)
    run_phase(cpu, "R3CARR.RSX", request)
    return cpu, before


def phase_two(cpu: Z80, carrier_length: int) -> bytes:
    before = bytes(cpu.mem[FACTS:FACTS + 26])
    request = struct.pack("<5HB", CARRIER, carrier_length, SCRATCH,
                          HIGH, FACTS, 0xCC)
    run_phase(cpu, "R3META.RSX", request)
    return before


def main() -> None:
    carrier = (ROOT / "build/rsx/STATEFUL.RSX").read_bytes()
    code_size = word(carrier, 12)
    allocation = word(carrier, 14)
    linked = word(carrier, 10)
    dispatch = word(carrier, 16)
    relocation_count = word(carrier, 22)

    cpu, _ = phase_one(carrier)
    assert cpu.a == 0 and cpu.mem[REQUEST + 12] == 1
    assert tuple(cpu.word(FACTS + offset) for offset in range(0, 14, 2)) == (
        CARRIER + 512, code_size, allocation, linked, dispatch,
        CARRIER + 48, relocation_count)
    assert cpu.word(FACTS + 14) == 0
    assert cpu.mem[FACTS + 16:FACTS + 18] == b"\0\0"
    assert cpu.word(FACTS + 18) == SCRATCH
    assert cpu.mem[FACTS + 20:FACTS + 22] == bytes((1, 2))
    assert cpu.word(FACTS + 24) == SCRATCH

    phase_two(cpu, len(carrier))
    assert cpu.a == 0 and cpu.mem[REQUEST + 10] == 1
    assert cpu.mem[FACTS + 16] == 1
    assert cpu.mem[FACTS + 17] == 1
    assert cpu.word(FACTS + 18) == SCRATCH
    assert cpu.word(FACTS + 24) == SCRATCH + 10
    metadata = word(carrier, 30)
    assert cpu.word(FACTS + 14) >= CARRIER + metadata + 12
    assert cpu.mem[SCRATCH:SCRATCH + 4] == b"STAT"

    # Feed the normalized facts directly into the commit-ready snapshot phase.
    request = struct.pack(
        "<8HBBHHB", cpu.word(FACTS), cpu.word(FACTS + 2),
        cpu.word(FACTS + 4), cpu.word(FACTS + 6), LIVE,
        cpu.word(FACTS + 10), cpu.word(FACTS + 12),
        cpu.word(FACTS + 18), cpu.mem[FACTS + 17], cpu.mem[FACTS + 21],
        SNAPSHOT, cpu.word(FACTS + 8), 0xCC)
    run_phase(cpu, "R3SNAP.RSX", request)
    assert cpu.a == 0 and cpu.mem[REQUEST + 22] == 1
    relocations = [word(carrier, 48 + 2 * index)
                   for index in range(relocation_count)]
    first_relocation = next(offset for offset in relocations if offset >= 8)
    linked_value = word(carrier, 512 + first_relocation)
    assert cpu.word(SNAPSHOT + first_relocation) == \
        (linked_value + LIVE - linked) & 0xFFFF
    assert cpu.mem[SNAPSHOT + 4:SNAPSHOT + 6] == b"\x01\0"

    # Header failures publish neither facts nor completion.
    broken = bytearray(carrier)
    broken[512] ^= 1
    cpu, before = phase_one(bytes(broken))
    assert cpu.a == 0xFF and cpu.mem[REQUEST + 12] == 0xCC
    assert bytes(cpu.mem[FACTS:FACTS + 26]) == before
    cpu, before = phase_one(carrier, name=b"NOTSTATE")
    assert cpu.a == 0xFF and bytes(cpu.mem[FACTS:FACTS + 26]) == before

    # Metadata failure may consume scratch but cannot publish metadata facts.
    broken = bytearray(carrier)
    broken[word(carrier, 30)] ^= 1
    cpu, _ = phase_one(bytes(broken))
    before = phase_two(cpu, len(broken))
    assert cpu.a == 0xFF and cpu.mem[REQUEST + 10] == 0xCC
    assert bytes(cpu.mem[FACTS:FACTS + 26]) == before

    duplicate = make_module(
        name="DUPL", version=(1, 0), services=[], linked_base=0x8000,
        code=b"\0" * 32, relocations=[], entry_offset=8, format_version=2,
        callable_services=[(b"DUPL", 1, 0, 8, 0),
                           (b"DUPL", 1, 0, 12, 0)])
    cpu, _ = phase_one(duplicate, name=b"DUPL    ")
    before = phase_two(cpu, len(duplicate))
    assert cpu.a == 0xFF and bytes(cpu.mem[FACTS:FACTS + 26]) == before

    # A converted stateless public carrier follows the same v2 preparation
    # path without publishing callable descriptors.
    hello = (ROOT / "build/rsx/HELLO.RSX").read_bytes()
    cpu, _ = phase_one(hello, name=b"HELLO   ")
    assert cpu.a == 0 and cpu.mem[FACTS + 20:FACTS + 22] == bytes((0, 2))
    before = phase_two(cpu, len(hello))
    assert cpu.a == 0 and cpu.mem[REQUEST + 10] == 1
    assert cpu.mem[FACTS + 16:FACTS + 18] == b"\0\0"
    assert cpu.word(FACTS + 18) == SCRATCH
    assert cpu.word(FACTS + 24) == SCRATCH

    print("BRSX carrier phases validate STATELESS and STATEFUL v2 input, normalize "
          "bounded facts, feed snapshot construction, and publish nothing "
          "on failure")


if __name__ == "__main__":
    main()
