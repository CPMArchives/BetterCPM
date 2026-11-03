#!/usr/bin/env python3
"""Build and verify the shared CP/M Tools Montezuma Micro 880K image."""
from __future__ import annotations

import argparse
import hashlib
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT_TOOLS = Path("/Users/nathanael/git/cpm-compatibility/suite/build-tools")

CYLINDERS = 80
SIDES = 2
TRACK_LENGTH = 0x18EA
SECTOR_SIZES = (1024, 1024, 1024, 1024, 1024, 512)
LOGICAL_SECTOR_ORDER = (0, 2, 4, 1, 3, 5)
TRACK_DATA_SIZE = sum(SECTOR_SIZES)
RAW_SIZE = CYLINDERS * SIDES * TRACK_DATA_SIZE
IDAM_FIRST = 175
IDAM_SPACING = 1110
DATA_MARK_OFFSET = 44

BLOCK_SIZE = 2048
DIRECTORY_ENTRIES = 128
DIRECTORY_BYTES = DIRECTORY_ENTRIES * 32
FIRST_DATA_BLOCK = DIRECTORY_BYTES // BLOCK_SIZE
BLOCK_COUNT = RAW_SIZE // BLOCK_SIZE
BLOCKS_PER_EXTENT = 8


def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def make_track(cylinder: int, head: int, track_data: bytes) -> bytes:
    physical_data: list[bytes] = [b""] * len(SECTOR_SIZES)
    logical_at = 0
    for physical_index in LOGICAL_SECTOR_ORDER:
        size = SECTOR_SIZES[physical_index]
        physical_data[physical_index] = track_data[logical_at:logical_at + size]
        logical_at += size
    track = bytearray([0x4E] * TRACK_LENGTH)
    track[:128] = bytes(128)
    for index, size in enumerate(SECTOR_SIZES):
        idam = IDAM_FIRST + index * IDAM_SPACING
        track[index * 2:index * 2 + 2] = (0x8000 | idam).to_bytes(2, "little")
        track[idam - 15:idam - 3] = bytes(12)
        track[idam - 3:idam] = b"\xA1\xA1\xA1"
        ident = bytes((0xFE, cylinder, head, index + 1, 3 if size == 1024 else 2))
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


def build_dmk(raw: bytes) -> bytes:
    if len(raw) != RAW_SIZE:
        raise ValueError("wrong logical image size")
    header = bytearray(16)
    header[1] = CYLINDERS
    header[2:4] = TRACK_LENGTH.to_bytes(2, "little")
    image = bytearray(header)
    for cylinder in range(CYLINDERS):
        for head in range(SIDES):
            track_index = cylinder * SIDES + head
            start = track_index * TRACK_DATA_SIZE
            image.extend(make_track(cylinder, head, raw[start:start + TRACK_DATA_SIZE]))
    return bytes(image)


def extract_raw(image: bytes) -> bytes:
    if len(image) != 16 + CYLINDERS * SIDES * TRACK_LENGTH:
        raise ValueError("wrong DMK image size")
    raw = bytearray()
    for track_index in range(CYLINDERS * SIDES):
        start = 16 + track_index * TRACK_LENGTH
        track = image[start:start + TRACK_LENGTH]
        physical: list[bytes] = []
        for index, size in enumerate(SECTOR_SIZES):
            pointer = int.from_bytes(track[index * 2:index * 2 + 2], "little")
            idam = pointer & 0x3FFF
            ident = bytes((0xFE, track_index // 2, track_index % 2,
                           index + 1, 3 if size == 1024 else 2))
            if track[idam:idam + 5] != ident:
                raise ValueError("bad DMK sector identity")
            if int.from_bytes(track[idam + 5:idam + 7], "big") != crc16(b"\xA1\xA1\xA1" + ident):
                raise ValueError("bad DMK ID CRC")
            data_mark = idam + DATA_MARK_OFFSET
            field = track[data_mark:data_mark + 1 + size]
            if not field or field[0] != 0xFB:
                raise ValueError("bad DMK data mark")
            stored = int.from_bytes(track[data_mark + 1 + size:data_mark + 3 + size], "big")
            if stored != crc16(b"\xA1\xA1\xA1" + field):
                raise ValueError("bad DMK data CRC")
            physical.append(field[1:])
        for physical_index in LOGICAL_SECTOR_ORDER:
            raw.extend(physical[physical_index])
    return bytes(raw)


def cpm_name(name: str) -> tuple[bytes, bytes]:
    stem, _, suffix = name.upper().partition(".")
    if not stem or len(stem) > 8 or len(suffix) > 3:
        raise ValueError(f"not a CP/M 8.3 name: {name}")
    return stem.ljust(8).encode("ascii"), suffix.ljust(3).encode("ascii")


def install_files(paths: list[Path]) -> bytes:
    raw = bytearray([0xE5] * RAW_SIZE)
    directory_index = 0
    next_block = FIRST_DATA_BLOCK
    for path in paths:
        content = path.read_bytes()
        records = (len(content) + 127) // 128
        padded = content + bytes([0x1A]) * (records * 128 - len(content))
        block_total = (len(padded) + BLOCK_SIZE - 1) // BLOCK_SIZE
        extent_total = max(1, (records + 127) // 128)
        stem, suffix = cpm_name(path.name)
        content_at = 0
        for extent_number in range(extent_total):
            entry = bytearray(32)
            entry[0] = 0
            entry[1:9] = stem
            entry[9:12] = suffix
            entry[12] = extent_number & 0x1F
            entry[14] = extent_number >> 5
            entry[15] = min(128, max(0, records - extent_number * 128))
            blocks_here = min(BLOCKS_PER_EXTENT,
                              block_total - extent_number * BLOCKS_PER_EXTENT)
            for slot in range(blocks_here):
                if next_block >= BLOCK_COUNT:
                    raise SystemExit("image payload exceeds disk capacity")
                entry[16 + slot * 2:18 + slot * 2] = next_block.to_bytes(2, "little")
                chunk = padded[content_at:content_at + BLOCK_SIZE]
                raw[next_block * BLOCK_SIZE:next_block * BLOCK_SIZE + len(chunk)] = chunk
                content_at += len(chunk)
                next_block += 1
            raw[directory_index * 32:(directory_index + 1) * 32] = entry
            directory_index += 1
    return bytes(raw)


def recover_files(raw: bytes) -> dict[str, bytes]:
    entries: dict[str, list[tuple[int, int, list[int]]]] = {}
    for index in range(DIRECTORY_ENTRIES):
        entry = raw[index * 32:(index + 1) * 32]
        if entry[0] == 0xE5:
            continue
        stem = bytes(b & 0x7F for b in entry[1:9]).decode("ascii").rstrip()
        suffix = bytes(b & 0x7F for b in entry[9:12]).decode("ascii").rstrip()
        name = stem + (("." + suffix) if suffix else "")
        extent = entry[12] + (entry[14] << 5)
        blocks = [int.from_bytes(entry[pos:pos + 2], "little")
                  for pos in range(16, 32, 2)]
        entries.setdefault(name, []).append((extent, entry[15], [b for b in blocks if b]))
    recovered: dict[str, bytes] = {}
    for name, extents in entries.items():
        content = bytearray()
        for _, records, blocks in sorted(extents):
            extent_data = bytearray()
            for block in blocks:
                extent_data.extend(raw[block * BLOCK_SIZE:(block + 1) * BLOCK_SIZE])
            content.extend(extent_data[:records * 128])
        recovered[name] = bytes(content)
    return recovered


def cpm_text(path: Path) -> bytes:
    text = path.read_text(encoding="ascii")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.replace("\n", "\r\n").encode("ascii") + b"\x1A"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", nargs="?", type=Path,
                        default=ROOT / "build/CPM-TOOLS-880K.dmk")
    parser.add_argument("--tools", type=Path, default=DEFAULT_TOOLS)
    args = parser.parse_args()
    required = (
        ROOT / "sysinfo/build/SYSINFO.COM",
        ROOT / "sysinfo/src/SYSINFO.ASM",
        ROOT / "diskinfo/build/DISKINFO.COM",
        ROOT / "diskinfo/src/DISKINFO.MAC",
        ROOT / "dpbchk/build/DPBCHK.COM",
        ROOT / "dpbchk/src/DPBCHK.MAC",
        ROOT / "fsck/build/FSCK.COM",
        ROOT / "fsck/src/FSCK.MAC",
        ROOT / "diskedit/build/DISKEDIT.COM",
        ROOT / "diskedit/src/DISKEDIT.MAC",
        ROOT / "cominfo/build/COMINFO.COM",
        ROOT / "cominfo/src/COMINFO.MAC",
        ROOT / "bdosprobe/build/BDOSPRB.COM",
        ROOT / "bdosprobe/src/BDOSPRB.MAC",
        ROOT / "docs/BDOSPROBE-DESIGN.md",
        ROOT / "BUILD.SUB",
        ROOT / "docs/TOOLS.DOC",
        ROOT / "ROADMAP.md",
        args.tools / "ZSM4.COM",
        args.tools / "LINK.COM",
    )
    for path in required:
        if not path.is_file():
            raise SystemExit(f"missing image input: {path}")

    with tempfile.TemporaryDirectory(prefix="cpm-tools-dmk-") as temporary:
        stage = Path(temporary)
        payload: list[Path] = []
        binary_inputs = {
            "SYSINFO.COM": ROOT / "sysinfo/build/SYSINFO.COM",
            "DISKINFO.COM": ROOT / "diskinfo/build/DISKINFO.COM",
            "DPBCHK.COM": ROOT / "dpbchk/build/DPBCHK.COM",
            "FSCK.COM": ROOT / "fsck/build/FSCK.COM",
            "DISKEDIT.COM": ROOT / "diskedit/build/DISKEDIT.COM",
            "COMINFO.COM": ROOT / "cominfo/build/COMINFO.COM",
            "BDOSPRB.COM": ROOT / "bdosprobe/build/BDOSPRB.COM",
            "ZSM4.COM": args.tools / "ZSM4.COM",
            "LINK.COM": args.tools / "LINK.COM",
        }
        for name, source in binary_inputs.items():
            target = stage / name
            target.write_bytes(source.read_bytes())
            payload.append(target)
        for name, source in (
            ("SYSINFO.ASM", ROOT / "sysinfo/src/SYSINFO.ASM"),
            ("DISKINFO.MAC", ROOT / "diskinfo/src/DISKINFO.MAC"),
            ("DPBCHK.MAC", ROOT / "dpbchk/src/DPBCHK.MAC"),
            ("FSCK.MAC", ROOT / "fsck/src/FSCK.MAC"),
            ("DISKEDIT.MAC", ROOT / "diskedit/src/DISKEDIT.MAC"),
            ("COMINFO.MAC", ROOT / "cominfo/src/COMINFO.MAC"),
            ("BDOSPRB.MAC", ROOT / "bdosprobe/src/BDOSPRB.MAC"),
            ("BDOSPRB.DOC", ROOT / "docs/BDOSPROBE-DESIGN.md"),
            ("BUILD.SUB", ROOT / "BUILD.SUB"),
            ("TOOLS.DOC", ROOT / "docs/TOOLS.DOC"),
            ("ROADMAP.DOC", ROOT / "ROADMAP.md"),
        ):
            target = stage / name
            target.write_bytes(cpm_text(source))
            payload.append(target)
        note = stage / "README.TXT"
        note.write_bytes(
            b"CP/M Tools development disk\r\n"
            b"SYSINFO 1.0.0-dev8  DISKINFO 0.1.0-dev4\r\n"
            b"DPBCHK 0.1.0-dev2\r\n"
            b"FSCK 0.1.0-dev1\r\n"
            b"DISKEDIT 0.1.0-dev2\r\n"
            b"COMINFO 0.1.0-dev2\r\n"
            b"BDOSPROBE 0.1.0-dev4 (command BDOSPRB)\r\n"
            b"TYPE TOOLS.DOC for commands. SUBMIT BUILD toolname rebuilds.\r\n\x1A"
        )
        payload.append(note)
        payload.sort(key=lambda path: path.name)

        expected = {path.name: path.read_bytes() for path in payload}
        rows = [(path.name, len(expected[path.name])) for path in payload]
        raw = install_files(payload)
        image = build_dmk(raw)
        if extract_raw(image) != raw:
            raise SystemExit("DMK logical-sector round-trip failed")
        recovered = recover_files(extract_raw(image))
        for name, content in expected.items():
            if name not in recovered or not recovered[name].startswith(content):
                raise SystemExit(f"image recovery failed: {name}")

        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(image)

    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    listing = "\n".join(f"  {name:12s} {size:6d} bytes"
                        for name, size in rows)
    (output.parent / "CPM-TOOLS-880K-SHA256.txt").write_text(
        f"{digest}  {output.name}\n", encoding="ascii")
    (output.parent / "CPM-TOOLS-880K-listing.txt").write_text(
        listing + "\n", encoding="ascii")
    print(f"created: {output}")
    print(f"sha256:  {digest}")
    print(listing)


if __name__ == "__main__":
    main()
