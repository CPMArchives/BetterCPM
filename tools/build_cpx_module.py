#!/usr/bin/env python3
"""Build BetterCP/M BCPX version-1 relocatable module carriers."""
from __future__ import annotations

import struct

MAGIC = b"BCPX"
FORMAT_VERSION = 1
MODULE_CLASS_CPX = 1
ABI_MAJOR = 1
ABI_MINOR = 0
HEADER_SIZE = 512
RELOCATION_OFFSET = 48
NO_ENTRY = 0xFFFF


def relocation_offsets(linked: bytes, alternate: bytes, delta: int) -> list[int]:
    if len(linked) != len(alternate):
        raise SystemExit("CPX alternate-origin size changed")
    changed = {i for i, pair in enumerate(zip(linked, alternate))
               if pair[0] != pair[1]}
    candidates = []
    for offset in range(len(linked) - 1):
        old = int.from_bytes(linked[offset:offset + 2], "little")
        new = int.from_bytes(alternate[offset:offset + 2], "little")
        covered = changed.intersection((offset, offset + 1))
        if covered and (old + delta) & 0xFFFF == new:
            candidates.append((offset, covered))
    selected, uncovered = [], set(changed)
    while uncovered:
        useful = [(len(covered & uncovered), offset, covered)
                  for offset, covered in candidates if covered & uncovered]
        if not useful:
            raise SystemExit(f"unexplained CPX relocation bytes: {sorted(uncovered)}")
        _score, offset, covered = max(useful)
        selected.append(offset)
        uncovered -= covered
    selected.sort()
    relocated = bytearray(linked)
    for offset in selected:
        value = int.from_bytes(relocated[offset:offset + 2], "little")
        relocated[offset:offset + 2] = ((value + delta) & 0xFFFF).to_bytes(2, "little")
    if bytes(relocated) != alternate:
        raise SystemExit("CPX relocation table does not reproduce alternate image")
    return selected


def make_module(*, name: str, version: tuple[int, int], commands: list[str],
                linked_base: int, code: bytes, relocations: list[int],
                entry_offset: int = 4, init_offset: int = NO_ENTRY,
                shutdown_offset: int = NO_ENTRY, flags: int = 0) -> bytes:
    """Return one BCPX v1 carrier. All public addresses are image offsets."""
    stem = name.upper().encode("ascii")
    if not 1 <= len(stem) <= 8 or any(len(c) > 8 for c in commands):
        raise SystemExit("CPX names and command names must fit CP/M 8.3 stems")
    allocation = (len(code) + 0xFF) & ~0xFF
    if not code or entry_offset >= len(code) or allocation == 0:
        raise SystemExit("invalid CPX code or entry offset")
    relocation_end = RELOCATION_OFFSET + 2 * len(relocations)
    if relocation_end > HEADER_SIZE:
        raise SystemExit("CPX relocation directory exceeds its reserved area")
    metadata = b"".join(c.upper().encode("ascii").ljust(8, b" ")
                        for c in commands)
    metadata_offset = HEADER_SIZE + len(code)
    header = bytearray(HEADER_SIZE)
    struct.pack_into("<4sBBBBHHHHHHHHHHHH8sBBBBH", header, 0,
                     MAGIC, FORMAT_VERSION, MODULE_CLASS_CPX,
                     ABI_MAJOR, ABI_MINOR, flags, linked_base, len(code),
                     allocation, entry_offset, init_offset, shutdown_offset,
                     len(relocations), HEADER_SIZE, HEADER_SIZE,
                     RELOCATION_OFFSET, metadata_offset,
                     stem.ljust(8, b" "), version[0], version[1],
                     len(commands), 0, sum(code) & 0xFFFF)
    for index, offset in enumerate(relocations):
        struct.pack_into("<H", header, RELOCATION_OFFSET + index * 2, offset)
    return bytes(header) + code + metadata
