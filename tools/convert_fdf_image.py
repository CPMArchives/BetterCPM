#!/usr/bin/env python3
"""Convert uniform MFM DISK.FDF media between canonical raw and DMK images."""
from __future__ import annotations

import argparse
from pathlib import Path

from fdf_format import FDFFormat, select_fdf


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FDF = ROOT / "third_party/montezuma/DISK.FDF"
DEFAULT_FORMAT = "California Computer Systems (40T, DS, DD, 332K)"
TRACK_LENGTH = 0x18EA
IDAM_FIRST = 175
DATA_MARK_OFFSET = 44
MFM_POINTER = 0x8000
POINTER_OFFSET_MASK = 0x3FFF


def crc16(data: bytes) -> int:
    """Return the WD-compatible CRC-16 used by MFM ID and data fields."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def require_supported(fmt: FDFFormat) -> None:
    """Reject definitions whose physical meaning this converter cannot preserve."""
    fmt.raw_record_map()
    if not fmt.flags & 0x80:
        raise ValueError(f"{fmt.name}: FM conversion is not implemented")
    if fmt.flags & 0x2F:
        raise ValueError(
            f"{fmt.name}: optional track/side/ID conventions are not implemented"
        )
    if fmt.physical_sectors > 64:
        raise ValueError(f"{fmt.name}: DMK permits at most 64 IDAM pointers per track")


def _physical_payload(payload: bytes, inverted: bool) -> bytes:
    if not inverted:
        return payload
    return bytes(value ^ 0xFF for value in payload)


def _make_track(fmt: FDFFormat, cylinder: int, side: int, raw_track: bytes) -> bytes:
    if len(raw_track) != fmt.raw_track_bytes:
        raise ValueError("wrong raw track size")
    sorted_ids = sorted(fmt.sector_ids)
    slot_for_id = {sector_id: index for index, sector_id in enumerate(sorted_ids)}
    spacing = (TRACK_LENGTH - IDAM_FIRST - 1) // fmt.physical_sectors
    minimum = DATA_MARK_OFFSET + 1 + fmt.sector_bytes + 2 + 16
    if spacing < minimum:
        raise ValueError(
            f"{fmt.name}: {fmt.physical_sectors} x {fmt.sector_bytes}-byte sectors "
            f"do not fit a {TRACK_LENGTH}-byte MFM track"
        )

    track = bytearray([0x4E] * TRACK_LENGTH)
    track[:128] = bytes(128)
    for index, sector_id in enumerate(fmt.sector_ids):
        idam = IDAM_FIRST + index * spacing
        track[index * 2:index * 2 + 2] = (MFM_POINTER | idam).to_bytes(2, "little")
        track[idam - 15:idam - 3] = bytes(12)
        track[idam - 3:idam] = b"\xA1\xA1\xA1"
        ident = bytes((0xFE, cylinder, side, sector_id, fmt.size_code))
        track[idam:idam + 5] = ident
        track[idam + 5:idam + 7] = crc16(b"\xA1\xA1\xA1" + ident).to_bytes(2, "big")

        data_mark = idam + DATA_MARK_OFFSET
        track[data_mark - 15:data_mark - 3] = bytes(12)
        track[data_mark - 3:data_mark] = b"\xA1\xA1\xA1"
        slot = slot_for_id[sector_id]
        start = slot * fmt.sector_bytes
        payload = _physical_payload(
            raw_track[start:start + fmt.sector_bytes], bool(fmt.flags & 0x10)
        )
        field = b"\xFB" + payload
        track[data_mark:data_mark + len(field)] = field
        crc_at = data_mark + len(field)
        track[crc_at:crc_at + 2] = crc16(b"\xA1\xA1\xA1" + field).to_bytes(2, "big")
    track[-1] = 0
    return bytes(track)


def raw_to_dmk(raw: bytes, fmt: FDFFormat) -> bytes:
    """Wrap one canonical z80pack raw image in a physical DMK representation."""
    require_supported(fmt)
    if len(raw) != fmt.image_bytes:
        raise ValueError(f"expected {fmt.image_bytes} raw bytes, got {len(raw)}")
    header = bytearray(16)
    header[1] = fmt.cylinders
    header[2:4] = TRACK_LENGTH.to_bytes(2, "little")
    header[4] = 0x00 if fmt.sides == 2 else 0x10
    image = bytearray(header)
    for cylinder in range(fmt.cylinders):
        for side in range(fmt.sides):
            track_index = cylinder * fmt.sides + side
            start = track_index * fmt.raw_track_bytes
            image.extend(_make_track(
                fmt, cylinder, side, raw[start:start + fmt.raw_track_bytes]
            ))
    return bytes(image)


def _track_pointers(track: bytes) -> list[int]:
    pointers = []
    for index in range(64):
        pointer = int.from_bytes(track[index * 2:index * 2 + 2], "little")
        if pointer == 0:
            continue
        if not pointer & MFM_POINTER:
            raise ValueError("DMK track contains an FM sector")
        offset = pointer & POINTER_OFFSET_MASK
        if offset < 128 or offset + 7 > len(track):
            raise ValueError("DMK IDAM pointer is outside the track")
        pointers.append(offset)
    if len(set(pointers)) != len(pointers):
        raise ValueError("DMK track contains duplicate IDAM pointers")
    return pointers


def _extract_track(fmt: FDFFormat, cylinder: int, side: int, track: bytes) -> bytes:
    pointers = _track_pointers(track)
    if len(pointers) != fmt.physical_sectors:
        raise ValueError(
            f"cylinder {cylinder}, side {side}: expected {fmt.physical_sectors} sectors, "
            f"found {len(pointers)}"
        )
    sorted_offsets = sorted(pointers)
    payloads: dict[int, bytes] = {}
    for idam in pointers:
        ident = track[idam:idam + 5]
        if len(ident) != 5 or ident[0] != 0xFE:
            raise ValueError(f"cylinder {cylinder}, side {side}: bad ID address mark")
        if ident[1:3] != bytes((cylinder, side)):
            raise ValueError(
                f"cylinder {cylinder}, side {side}: ID field names "
                f"cylinder {ident[1]}, side {ident[2]}"
            )
        sector_id, size_code = ident[3], ident[4]
        if size_code != fmt.size_code:
            raise ValueError(f"sector {sector_id}: expected size code {fmt.size_code}, got {size_code}")
        stored_id_crc = int.from_bytes(track[idam + 5:idam + 7], "big")
        expected_id_crc = crc16(b"\xA1\xA1\xA1" + ident)
        if stored_id_crc != expected_id_crc:
            raise ValueError(f"sector {sector_id}: bad ID CRC")

        next_offsets = [offset for offset in sorted_offsets if offset > idam]
        field_end = next_offsets[0] if next_offsets else len(track)
        marker = track.find(b"\xA1\xA1\xA1\xFB", idam + 7, field_end)
        if marker < 0:
            if track.find(b"\xA1\xA1\xA1\xF8", idam + 7, field_end) >= 0:
                raise ValueError(f"sector {sector_id}: deleted-data marks cannot be preserved in raw images")
            raise ValueError(f"sector {sector_id}: data address mark is absent")
        data_mark = marker + 3
        data_start = data_mark + 1
        data_end = data_start + fmt.sector_bytes
        if data_end + 2 > field_end:
            raise ValueError(f"sector {sector_id}: truncated data field")
        field = track[data_mark:data_end]
        stored_data_crc = int.from_bytes(track[data_end:data_end + 2], "big")
        expected_data_crc = crc16(b"\xA1\xA1\xA1" + field)
        if stored_data_crc != expected_data_crc:
            raise ValueError(f"sector {sector_id}: bad data CRC")
        if sector_id in payloads:
            raise ValueError(f"cylinder {cylinder}, side {side}: duplicate sector ID {sector_id}")
        payloads[sector_id] = _physical_payload(field[1:], bool(fmt.flags & 0x10))

    expected_ids = set(fmt.sector_ids)
    if set(payloads) != expected_ids:
        missing = sorted(expected_ids - set(payloads))
        extra = sorted(set(payloads) - expected_ids)
        raise ValueError(
            f"cylinder {cylinder}, side {side}: sector IDs differ "
            f"(missing {missing}, extra {extra})"
        )
    return b"".join(payloads[sector_id] for sector_id in sorted(fmt.sector_ids))


def dmk_to_raw(image: bytes, fmt: FDFFormat) -> bytes:
    """Extract decoded sectors from a DMK into canonical z80pack raw ordering."""
    require_supported(fmt)
    if len(image) < 16:
        raise ValueError("DMK image is shorter than its 16-byte header")
    track_length = int.from_bytes(image[2:4], "little")
    expected_length = 16 + fmt.raw_tracks * track_length
    if image[1] != fmt.cylinders:
        raise ValueError(f"expected {fmt.cylinders} DMK cylinders, got {image[1]}")
    expected_flags = 0x00 if fmt.sides == 2 else 0x10
    if image[4] & 0x50 != expected_flags:
        raise ValueError("DMK side count or recording density does not match the FDF")
    if track_length < 128 or len(image) != expected_length:
        raise ValueError(f"expected {expected_length} DMK bytes, got {len(image)}")

    raw = bytearray()
    for cylinder in range(fmt.cylinders):
        for side in range(fmt.sides):
            track_index = cylinder * fmt.sides + side
            start = 16 + track_index * track_length
            raw.extend(_extract_track(
                fmt, cylinder, side, image[start:start + track_length]
            ))
    return bytes(raw)


def _write_output(path: Path, data: bytes, force: bool) -> None:
    if path.exists() and not force:
        raise ValueError(f"output already exists: {path} (use --force to replace it)")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert uniform MFM DISK.FDF media between raw and DMK images"
    )
    parser.add_argument("direction", choices=("raw-to-dmk", "dmk-to-raw"))
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--fdf", type=Path, default=DEFAULT_FDF)
    parser.add_argument("--format", default=DEFAULT_FORMAT,
                        help=f"exact DISK.FDF name (default: {DEFAULT_FORMAT})")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        fmt = select_fdf(args.fdf, args.format)
        source = args.input.read_bytes()
        result = raw_to_dmk(source, fmt) if args.direction == "raw-to-dmk" else dmk_to_raw(source, fmt)
        _write_output(args.output, result, args.force)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"converted {args.input} -> {args.output} as {fmt.name}")
    print(f"{len(source)} input bytes; {len(result)} output bytes")


if __name__ == "__main__":
    main()
