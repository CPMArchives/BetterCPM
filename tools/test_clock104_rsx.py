#!/usr/bin/env python3
"""Execute optional clock carriers against the frozen four/five-byte contracts.

This is a CPU-level contract test, not admission or historical-client evidence.
"""
from __future__ import annotations

import re
import struct
from pathlib import Path

from test_bios import Z80, require
from test_p2dos_rsx import BASE, CALLER_BUFFER, REGISTRY, PROVIDER_A, PROVIDER_B
from test_p2dos_rsx import invoke, provider, registry

ROOT = Path(__file__).resolve().parents[1]


def check(stem: str, width: int) -> None:
    carrier = (ROOT / f"build/rsx/{stem}.RSX").read_bytes()
    size, allocation = struct.unpack_from("<HH", carrier, 12)
    require(allocation == 256, "frontend exceeds one resident page")
    names = {}
    pattern = re.compile(r"^([0-9a-f]{4})\s+.*\s([A-Z][A-Z0-9_]*):", re.I)
    for line in (ROOT / f"build/rsx/{stem.lower()}.lst").read_text().splitlines():
        match = pattern.match(line)
        if match:
            names[match.group(2).upper()] = int(match.group(1), 16)
    cpu = Z80(b"")
    cpu.mem[BASE:BASE + size] = carrier[512:512 + size]
    cpu.setword(names["C4_NEXT"], REGISTRY)
    entry, request = names["C4_DISPATCH"], names["C4_REQUEST"]
    cpu.iy = 0x5AA5
    guarded = b"\xC3" + b"\xA5" * 5 + b"\x3C"
    samples = (bytes((0x34, 0x12, 0x09, 0x08, 0x07)),
               bytes((0x78, 0x56, 0x23, 0x59, 0x58)))
    for address, sample in zip((PROVIDER_A, PROVIDER_B), samples):
        cpu.mem[CALLER_BUFFER - 1:CALLER_BUFFER + 6] = guarded
        cpu.mem[REGISTRY:REGISTRY + 6] = registry(address)
        code = provider(request + 4, sample)
        cpu.mem[address:address + len(code)] = code
        invoke(cpu, entry, 105, CALLER_BUFFER)
        expected = b"\xC3" + sample[:width] + b"\xA5" * (5 - width) + b"\x3C"
        require(bytes(cpu.mem[CALLER_BUFFER - 1:CALLER_BUFFER + 6]) == expected,
                "GET changed guards, copied wrong width, or cached a provider")
        require(cpu.a == (sample[4] if width == 4 else 0) and cpu.hl == 0,
                "GET returned incorrect historical A/HL")
        require(cpu.mem[request + 2] == 0, "105 did not request native GET")

    # A provider may partially write its private sample before failing.
    for status in (1, 2, 3, 4, 5, 6, 8):
        for length in (1, 3, 5):
            cpu.mem[CALLER_BUFFER - 1:CALLER_BUFFER + 6] = guarded
            cpu.mem[REGISTRY:REGISTRY + 6] = registry(PROVIDER_A)
            code = provider(request + 4, b"\xDE" * length, status)
            cpu.mem[PROVIDER_A:PROVIDER_A + len(code)] = code
            invoke(cpu, entry, 105, CALLER_BUFFER)
            require(cpu.a == 0xFE and cpu.hl == 0xFE, "GET failure status")
            require(bytes(cpu.mem[CALLER_BUFFER - 1:CALLER_BUFFER + 6]) == guarded,
                    "failed GET published partial output")
    for target, status in ((0, 1), (0, 0)):
        cpu.mem[REGISTRY:REGISTRY + 6] = registry(target, status)
        invoke(cpu, entry, 105, CALLER_BUFFER)
        require(cpu.a == 0xFE and cpu.hl == 0xFE, "missing TIME result")
        require(bytes(cpu.mem[CALLER_BUFFER - 1:CALLER_BUFFER + 6]) == guarded,
                "missing TIME changed caller output")

    # A later provider works without reloading the frontend.
    cpu.mem[REGISTRY:REGISTRY + 6] = registry(PROVIDER_B)
    code = provider(request + 4, samples[0])
    cpu.mem[PROVIDER_B:PROVIDER_B + len(code)] = code
    invoke(cpu, entry, 105, CALLER_BUFFER)
    require(bytes(cpu.mem[CALLER_BUFFER:CALLER_BUFFER + width]) == samples[0][:width],
            "GET did not recover after provider replacement")

    for status in (0, 8):
        cpu.mem[CALLER_BUFFER - 1:CALLER_BUFFER + 6] = guarded
        cpu.mem[CALLER_BUFFER:CALLER_BUFFER + 5] = samples[1]
        original = bytes(cpu.mem[CALLER_BUFFER - 1:CALLER_BUFFER + 6])
        cpu.mem[REGISTRY:REGISTRY + 6] = registry(PROVIDER_A)
        code = provider(request + 4, b"", status)
        cpu.mem[PROVIDER_A:PROVIDER_A + len(code)] = code
        invoke(cpu, entry, 104, CALLER_BUFFER)
        canonical = samples[1][:width] + (b"\0" if width == 4 else b"")
        require(bytes(cpu.mem[request + 4:request + 9]) == canonical,
                "SET copied incorrect width or failed to reset seconds")
        require(cpu.mem[request + 2] == 1, "104 did not request native SET")
        require(cpu.a == (0xFE if status else 0) and cpu.hl == (0xFE if status else 0),
                "SET success/unsupported result")
        require(bytes(cpu.mem[CALLER_BUFFER - 1:CALLER_BUFFER + 6]) == original,
                "SET changed caller input or guards")

    # Unclaimed selectors, including P2DOS and version reporting, still chain.
    cpu.mem[REGISTRY:REGISTRY + 6] = registry(0x1234, 0x42)
    for selector in (12, 200, 201):
        invoke(cpu, entry, selector, CALLER_BUFFER)
        require(cpu.a == 0x42 and cpu.hl == 0x1234 and cpu.c == selector,
                "frontend intercepted an unrelated selector")
    require(cpu.iy == 0x5AA5, "frontend clobbered IY")
    print(f"{stem}: {size} bytes, {allocation}-byte allocation; contract checks passed")


def main() -> None:
    check("T104C3", 4)
    check("T104Z8", 5)


if __name__ == "__main__":
    main()
