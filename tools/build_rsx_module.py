#!/usr/bin/env python3
"""Build BetterCP/M BRSX version-1 relocatable module carriers."""
from __future__ import annotations

import struct

MAGIC = b"BRSX"
HEADER_SIZE = 512
RELOCATION_OFFSET = 48
NO_ENTRY = 0xFFFF


def make_module(*, name: str, version: tuple[int, int], services: list[int],
                linked_base: int, code: bytes, relocations: list[int],
                entry_offset: int = 4, init_offset: int = NO_ENTRY,
                shutdown_offset: int = NO_ENTRY, allocation: int | None = None,
                flags: int = 0) -> bytes:
    stem = name.upper().encode("ascii")
    if not 1 <= len(stem) <= 8 or any(not 0 <= service <= 255 for service in services):
        raise SystemExit("invalid RSX name or service number")
    runtime = (len(code) + 0xFF) & ~0xFF
    allocation = runtime if allocation is None else allocation
    if (not code or entry_offset >= len(code) or allocation < len(code)
            or allocation & 0xFF):
        raise SystemExit("invalid RSX code, entry, or allocation")
    for label, offset in (("initialization", init_offset),
                          ("shutdown", shutdown_offset)):
        if offset != NO_ENTRY and offset >= len(code):
            raise SystemExit(f"invalid RSX {label} entry")
    if len(set(relocations)) != len(relocations) or any(
            offset < 0 or offset + 1 >= len(code) for offset in relocations):
        raise SystemExit("invalid or duplicate RSX relocation offset")
    if RELOCATION_OFFSET + 2 * len(relocations) > HEADER_SIZE:
        raise SystemExit("RSX relocation directory exceeds its header")
    metadata_offset = HEADER_SIZE + len(code)
    header = bytearray(HEADER_SIZE)
    primary = services[0] if services else 0xFFFF
    struct.pack_into("<4sBBBBHHHHHHHHHHHH8sBBBBHH", header, 0,
                     MAGIC, 1, 2, 1, 0, flags, linked_base, len(code), allocation,
                     entry_offset, init_offset, shutdown_offset, len(relocations),
                     HEADER_SIZE, HEADER_SIZE, RELOCATION_OFFSET, metadata_offset,
                     stem.ljust(8, b" "), version[0], version[1], len(services), 0,
                     sum(code) & 0xFFFF, primary)
    for index, offset in enumerate(relocations):
        struct.pack_into("<H", header, RELOCATION_OFFSET + index * 2, offset)
    return bytes(header) + code + bytes(services)
