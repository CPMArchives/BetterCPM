#!/usr/bin/env python3
"""Add one user-zero CP/M file to an existing MM Extended 790K DMK."""
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

from build_montezuma_extended_790k import (
    CYLINDERS,
    DATA_MARK_OFFSET,
    LOGICAL_SECTOR_ORDER,
    SECTOR_COUNT,
    SECTOR_SIZE,
    SIDES,
    TRACK_LENGTH,
    build,
    verify,
)
from build_trs80_boot import (
    ALLOCATION_BLOCK_BYTES,
    BLOCK_COUNT,
    DIRECTORY_ENTRIES,
    FILESYSTEM_FIRST_SECTOR,
    FIRST_DATA_BLOCK,
    cpm_name,
)


def extract_raw(image: bytes) -> bytearray:
    """Recover logical track bytes from the fixed DMK physical layout."""
    verify(image, require_blank=False)
    raw = bytearray()
    for track_index in range(CYLINDERS * SIDES):
        start = 16 + track_index * TRACK_LENGTH
        track = image[start:start + TRACK_LENGTH]
        physical = []
        for sector in range(SECTOR_COUNT):
            pointer = int.from_bytes(track[sector * 2:sector * 2 + 2], "little")
            idam = pointer & 0x3FFF
            data_mark = idam + DATA_MARK_OFFSET
            physical.append(track[data_mark + 1:data_mark + 1 + SECTOR_SIZE])
        for physical_index in LOGICAL_SECTOR_ORDER:
            raw.extend(physical[physical_index])
    return raw


def add_file(raw: bytearray, filename: str, content: bytes) -> tuple[int, list[int]]:
    name, suffix = cpm_name(filename)
    directory = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE
    free_entries: list[int] = []
    used_blocks = set(range(FIRST_DATA_BLOCK))
    for index in range(DIRECTORY_ENTRIES):
        start = directory + index * 32
        entry = raw[start:start + 32]
        if entry[0] == 0xE5:
            free_entries.append(index)
            continue
        if entry[0] >= 16:
            continue
        if entry[0] == 0 and entry[1:9] == name and bytes(value & 0x7F for value in entry[9:12]) == suffix:
            raise ValueError(f"{filename} already exists")
        for offset in range(16, 32, 2):
            block = int.from_bytes(entry[offset:offset + 2], "little")
            if block:
                used_blocks.add(block)

    records = (len(content) + 127) // 128
    padded = content + bytes((0x1A,)) * (records * 128 - len(content))
    block_total = (len(padded) + ALLOCATION_BLOCK_BYTES - 1) // ALLOCATION_BLOCK_BYTES
    extent_total = max(1, (records + 127) // 128)
    if len(free_entries) < extent_total:
        raise ValueError("no free directory entries")
    free_blocks = [block for block in range(FIRST_DATA_BLOCK, BLOCK_COUNT)
                   if block not in used_blocks]
    if len(free_blocks) < block_total:
        raise ValueError("insufficient free allocation blocks")

    allocated = free_blocks[:block_total]
    content_at = 0
    for extent in range(extent_total):
        entry = bytearray(32)
        entry[0] = 0
        entry[1:9], entry[9:12] = name, suffix
        entry[12], entry[14] = extent & 0x1F, extent >> 5
        entry[15] = min(128, max(0, records - extent * 128))
        extent_blocks = allocated[extent * 8:(extent + 1) * 8]
        for slot, block in enumerate(extent_blocks):
            entry[16 + slot * 2:18 + slot * 2] = block.to_bytes(2, "little")
            chunk = padded[content_at:content_at + ALLOCATION_BLOCK_BYTES]
            destination = directory + block * ALLOCATION_BLOCK_BYTES
            raw[destination:destination + len(chunk)] = chunk
            content_at += len(chunk)
        start = directory + free_entries[extent] * 32
        raw[start:start + 32] = entry
    return free_entries[0], allocated


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("--name", required=True, help="destination CP/M 8.3 name")
    parser.add_argument("--backup", type=Path)
    args = parser.parse_args()
    image = args.image.resolve()
    source = args.source.resolve()
    if not image.is_file() or not source.is_file():
        raise SystemExit("image and source must both exist")
    original = image.read_bytes()
    raw = extract_raw(original)
    entry, blocks = add_file(raw, args.name.upper(), source.read_bytes())
    updated = build(bytes(raw))
    verify(updated, require_blank=False)
    if args.backup:
        backup = args.backup.resolve()
        if backup.exists():
            raise SystemExit(f"backup already exists: {backup}")
        shutil.copy2(image, backup)
    temporary = image.with_name(f".{image.name}.tmp")
    temporary.write_bytes(updated)
    os.replace(temporary, image)
    print(f"installed {args.name.upper()} in directory entry {entry}, blocks {blocks}")
    if args.backup:
        print(f"backup: {args.backup.resolve()}")


if __name__ == "__main__":
    main()
