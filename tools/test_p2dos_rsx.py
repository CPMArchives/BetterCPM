#!/usr/bin/env python3
"""Exercise P2DOS.RSX result, buffer, and per-call discovery contracts."""
from __future__ import annotations

import re
import struct
from pathlib import Path

from test_bios import Z80, require

ROOT = Path(__file__).resolve().parents[1]
BASE = 0x8000
CALLER_BUFFER = 0x7200
REGISTRY = 0x7000
PROVIDER_A = 0x7100
PROVIDER_B = 0x7140


def symbols() -> dict[str, int]:
    result: dict[str, int] = {}
    pattern = re.compile(r"^([0-9a-f]{4})\s+.*\s([A-Z][A-Z0-9_]*):", re.I)
    listing = ROOT / "build/rsx/p2dos.lst"
    for line in listing.read_text(errors="replace").splitlines():
        match = pattern.match(line)
        if match:
            result[match.group(2).upper()] = int(match.group(1), 16)
    return result


def provider(sample_address: int, sample: bytes) -> bytes:
    code = bytearray()
    for offset, value in enumerate(sample):
        code.extend((0x3E, value, 0x32,
                     (sample_address + offset) & 0xFF,
                     (sample_address + offset) >> 8))
    code.extend((0xAF, 0xC9))
    return bytes(code)


def registry(service: int, status: int = 0) -> bytes:
    return bytes((0x21, service & 0xFF, service >> 8,
                  0x3E, status, 0xC9))


def invoke(cpu: Z80, entry: int, selector: int, buffer: int) -> None:
    cpu.c, cpu.de, cpu.ix = selector, buffer, 0xA55A
    old_sp = cpu.sp
    cpu.run(entry, limit=5000)
    require(cpu.sp == old_sp, f"Function {selector} unbalanced the stack")
    require(cpu.de == buffer and cpu.ix == 0xA55A,
            f"Function {selector} did not preserve DE/IX")


def main() -> None:
    carrier = (ROOT / "build/rsx/P2DOS.RSX").read_bytes()
    code_size = struct.unpack_from("<H", carrier, 12)[0]
    code = carrier[512:512 + code_size]
    names = symbols()
    entry = names["P2_DISPATCH"]
    request = names["P2_REQUEST"]

    cpu = Z80(b"")
    cpu.mem[BASE:BASE + len(code)] = code
    cpu.setword(names["P2_NEXT"], REGISTRY)

    first = bytes((0x34, 0x12, 0x09, 0x08, 0x07))
    cpu.mem[REGISTRY:REGISTRY + 6] = registry(PROVIDER_A)
    cpu.mem[PROVIDER_A:PROVIDER_A + 27] = provider(request + 4, first)
    cpu.mem[CALLER_BUFFER:CALLER_BUFFER + 5] = bytes((0xA5,)) * 5
    invoke(cpu, entry, 200, CALLER_BUFFER)
    require(cpu.a == 0 and cpu.hl == 0 and
            bytes(cpu.mem[CALLER_BUFFER:CALLER_BUFFER + 5]) == first,
            "P2DOS GET did not publish the native TIME sample")

    second = bytes((0x78, 0x56, 0x23, 0x59, 0x58))
    cpu.mem[REGISTRY:REGISTRY + 6] = registry(PROVIDER_B)
    cpu.mem[PROVIDER_B:PROVIDER_B + 27] = provider(request + 4, second)
    invoke(cpu, entry, 200, CALLER_BUFFER)
    require(bytes(cpu.mem[CALLER_BUFFER:CALLER_BUFFER + 5]) == second,
            "P2DOS GET retained a stale provider address")

    sentinel = bytes((1, 2, 3, 4, 5))
    cpu.mem[CALLER_BUFFER:CALLER_BUFFER + 5] = sentinel
    cpu.mem[REGISTRY:REGISTRY + 6] = registry(0, 1)
    invoke(cpu, entry, 200, CALLER_BUFFER)
    require(cpu.a == 0xFE and cpu.hl == 0x00FE and
            bytes(cpu.mem[CALLER_BUFFER:CALLER_BUFFER + 5]) == sentinel,
            "failed P2DOS GET changed the caller buffer or result")

    cpu.mem[REGISTRY:REGISTRY + 6] = registry(PROVIDER_A)
    cpu.mem[PROVIDER_A:PROVIDER_A + 5] = bytes((0x3E, 8, 0x21, 0, 0))
    cpu.mem[PROVIDER_A + 5] = 0xC9
    invoke(cpu, entry, 201, CALLER_BUFFER)
    require(cpu.a == 0xFE and cpu.hl == 0x00FE and
            bytes(cpu.mem[request + 4:request + 9]) == sentinel,
            "P2DOS SET did not copy input or map SET_UNSUPPORTED")

    cpu.mem[PROVIDER_A:PROVIDER_A + 2] = bytes((0xAF, 0xC9))
    invoke(cpu, entry, 201, CALLER_BUFFER)
    require(cpu.a == 0 and cpu.hl == 0,
            "P2DOS SET did not return historical success")
    print("P2DOS.RSX GET/SET, failure atomicity, and per-call discovery passed")


if __name__ == "__main__":
    main()
