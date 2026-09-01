#!/usr/bin/env python3
"""Build a blank Montezuma Micro Extended 80T DS SYSTEM DMK image.

This creates the exact physical container and an empty CP/M filesystem area.
It deliberately does not claim to be bootable: BetterCP/M stage-zero and
resident-system bytes must later be installed in the two reserved tracks.
"""
from __future__ import annotations

import argparse
from pathlib import Path

CYLINDERS = 80
SIDES = 2
TRACK_LENGTH = 0x18EA
SECTOR_COUNT = 10
SECTOR_SIZE = 512
TRACK_DATA_SIZE = SECTOR_COUNT * SECTOR_SIZE
RAW_SIZE = CYLINDERS * SIDES * TRACK_DATA_SIZE
IMAGE_SIZE = 16 + CYLINDERS * SIDES * TRACK_LENGTH
RESERVED_TRACKS = 2
LOGICAL_SECTOR_ORDER = (0, 2, 4, 6, 8, 1, 3, 5, 7, 9)
IDAM_FIRST = 175
IDAM_SPACING = 610
DATA_MARK_OFFSET = 44


def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def make_track(cylinder: int, head: int, logical_data: bytes) -> bytes:
    if len(logical_data) != TRACK_DATA_SIZE:
        raise ValueError("wrong logical track size")
    physical_data = [b""] * SECTOR_COUNT
    offset = 0
    for physical_index in LOGICAL_SECTOR_ORDER:
        physical_data[physical_index] = logical_data[offset:offset + SECTOR_SIZE]
        offset += SECTOR_SIZE

    track = bytearray([0x4E] * TRACK_LENGTH)
    track[:128] = bytes(128)
    for index in range(SECTOR_COUNT):
        sector = index + 1
        idam = IDAM_FIRST + index * IDAM_SPACING
        track[index * 2:index * 2 + 2] = (0x8000 | idam).to_bytes(2, "little")
        track[idam - 15:idam - 3] = bytes(12)
        track[idam - 3:idam] = b"\xA1\xA1\xA1"
        ident = bytes((0xFE, cylinder, head, sector, 2))
        track[idam:idam + 5] = ident
        track[idam + 5:idam + 7] = crc16(b"\xA1\xA1\xA1" + ident).to_bytes(2, "big")

        data_mark = idam + DATA_MARK_OFFSET
        track[data_mark - 15:data_mark - 3] = bytes(12)
        track[data_mark - 3:data_mark] = b"\xA1\xA1\xA1"
        field = b"\xFB" + physical_data[index]
        track[data_mark:data_mark + len(field)] = field
        crc_at = data_mark + len(field)
        track[crc_at:crc_at + 2] = crc16(b"\xA1\xA1\xA1" + field).to_bytes(2, "big")
    track[-1] = 0
    return bytes(track)


def build() -> bytes:
    blank_track = bytes([0xE5]) * TRACK_DATA_SIZE
    header = bytearray(16)
    header[1] = CYLINDERS
    header[2:4] = TRACK_LENGTH.to_bytes(2, "little")
    header[4] = 0x00
    image = bytearray(header)
    for cylinder in range(CYLINDERS):
        for head in range(SIDES):
            image.extend(make_track(cylinder, head, blank_track))
    return bytes(image)


def verify(image: bytes) -> None:
    if len(image) != IMAGE_SIZE:
        raise ValueError(f"expected {IMAGE_SIZE} bytes, got {len(image)}")
    if image[1] != CYLINDERS or int.from_bytes(image[2:4], "little") != TRACK_LENGTH or image[4] != 0:
        raise ValueError("bad DMK header")
    for cylinder in range(CYLINDERS):
        for head in range(SIDES):
            start = 16 + (cylinder * SIDES + head) * TRACK_LENGTH
            track = image[start:start + TRACK_LENGTH]
            for index in range(SECTOR_COUNT):
                pointer = int.from_bytes(track[index * 2:index * 2 + 2], "little")
                idam = pointer & 0x3FFF
                ident = bytes((0xFE, cylinder, head, index + 1, 2))
                if pointer & 0x8000 == 0 or track[idam:idam + 5] != ident:
                    raise ValueError(f"bad ID on cylinder {cylinder}, head {head}, sector {index + 1}")
                if int.from_bytes(track[idam + 5:idam + 7], "big") != crc16(b"\xA1\xA1\xA1" + ident):
                    raise ValueError("bad ID CRC")
                data_mark = idam + DATA_MARK_OFFSET
                field = track[data_mark:data_mark + 1 + SECTOR_SIZE]
                if field != b"\xFB" + bytes([0xE5]) * SECTOR_SIZE:
                    raise ValueError("sector is not blank")
                stored = int.from_bytes(track[data_mark + 1 + SECTOR_SIZE:data_mark + 3 + SECTOR_SIZE], "big")
                if stored != crc16(b"\xA1\xA1\xA1" + field):
                    raise ValueError("bad data CRC")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", nargs="?", type=Path,
                        default=Path("build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk"))
    args = parser.parse_args()
    image = build()
    verify(image)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(image)
    print(f"created {args.output} ({len(image)} DMK bytes; {RAW_SIZE} formatted bytes)")
    print("system tracks reserved: 2; bootable system content installed: no")


if __name__ == "__main__":
    main()
