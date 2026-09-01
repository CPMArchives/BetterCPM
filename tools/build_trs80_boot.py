#!/usr/bin/env python3
"""Cross-assemble and install the first TRS-80 BetterCP/M boot milestone."""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path

from build_montezuma_extended_790k import (
    RAW_SIZE,
    SECTOR_SIZE,
    TRACK_DATA_SIZE,
    build,
    verify,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/platform/trs80m4"
BUILD = ROOT / "build/trs80"
BOOT_ADDRESS = 0x4300
STAGE1_ADDRESS = 0x5000
BOOT_SECTOR_LOGICAL_INDEX = 0
STAGE1_SECTOR_LOGICAL_INDEX = 1  # logical order sector 3
VERIFY_SECTOR_LOGICAL_INDEX = 2  # logical order sector 5
VERIFY_PAYLOAD = b"BetterCP/M verify" + bytes(SECTOR_SIZE - len(b"BetterCP/M verify"))
CROSS_FIXTURE = (b"BFILE-000 " * 12 + b"BFILE-00")
SYSTEM_FIRST_LOGICAL_INDEX = 2
SYSTEM_SECTORS = 28
FILESYSTEM_FIRST_SECTOR = 40   # DPB OFF=2, one logical track per cylinder
ALLOCATION_BLOCK_BYTES = 2048
DIRECTORY_ENTRIES = 128
FIRST_DATA_BLOCK = 2
BLOCK_COUNT = (RAW_SIZE - FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE) // ALLOCATION_BLOCK_BYTES
HELLO_COM = bytes((
    0x11, 0x1F, 0x01,       # LD DE,011Fh: sign-on text
    0x0E, 9, 0xCD, 5, 0,   # BDOS Print String
    0x3A, 0x80, 0x00, 0xB7, 0xC8,  # return if command tail is empty
    0x47, 0x21, 0x81, 0x00,         # B=length, HL=tail
    0x5E, 0x23, 0xC5, 0xE5, 0x0E, 2, 0xCD, 5, 0,
    0xE1, 0xC1, 0x10, 0xF3, 0xC9,  # print every tail character
)) + b"\nHello from BetterCP/M$"


def assemble(assembler: Path, source: Path, output: Path, origin: int) -> bytes:
    output.parent.mkdir(parents=True, exist_ok=True)
    # The host z80asm uses ASEG/ORG where ZSM4 uses CSEG/.PHASE to place
    # absolute-address code in a relocatable module.  This narrow mechanical
    # adapter changes segment directives only; instructions remain canonical.
    text = source.read_text(encoding="ascii")
    text = text.replace("        CSEG\n        .PHASE  ", "        ASEG\n        ORG     ")
    text = text.replace("        .DEPHASE\n", "")
    with tempfile.TemporaryDirectory(prefix="bettercpm-cross-") as temporary:
        staged = Path(temporary)
        (staged / source.name).write_text(text, encoding="ascii")
        shutil.copy2(SOURCE / "hardware.inc", staged / "hardware.inc")
        shutil.copy2(SOURCE / "hal.inc", staged / "hal.inc")
        shutil.copy2(SOURCE / "m4cons.inc", staged / "m4cons.inc")
        shutil.copy2(SOURCE / "m4disk.inc", staged / "m4disk.inc")
        shutil.copy2(ROOT / "src/core/bringup.inc", staged / "bringup.inc")
        subprocess.run(
            [str(assembler), "-fb", f"-o{output}", source.name],
            check=True,
            cwd=staged,
        )
    data = output.read_bytes()
    # Some z80asm builds emit an origin-sized prefix; accept and remove only
    # an all-zero prefix whose size exactly matches the source origin.
    if len(data) > origin and data[:origin] == bytes(origin):
        data = data[origin:]
        output.write_bytes(data)
    if not data or len(data) > SECTOR_SIZE:
        raise ValueError(f"{source.name} is {len(data)} bytes; expected 1..{SECTOR_SIZE}")
    return data


def cpm_name(name: str) -> tuple[bytes, bytes]:
    stem, dot, suffix = name.upper().partition(".")
    if not stem or len(stem) > 8 or len(suffix) > 3 or (not dot and suffix):
        raise ValueError(f"not a CP/M 8.3 name: {name}")
    return stem.ljust(8).encode("ascii"), suffix.ljust(3).encode("ascii")


def install_files(raw: bytearray,
                  files: list[tuple[str, bytes] | tuple[str, bytes, int]]) -> None:
    """Install files in the active 2K/16-bit CP/M layout."""
    directory = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE
    next_entry = 0
    next_block = FIRST_DATA_BLOCK
    expanded = []
    for item in files:
        filename, content = item[:2]
        user = item[2] if len(item) == 3 else 0
        if not 0 <= user <= 15:
            raise ValueError(f"invalid CP/M file user: {user}")
        expanded.append((filename, content, user))
        # DIRTEST requires the same controlled name to exist independently in
        # users zero and one. Allocate a real second copy; sharing allocation
        # blocks would make user-scoped Delete corrupt the surviving fixture.
        if user == 0 and filename.upper() == "BTUSR.DAT":
            expanded.append((filename, content, 1))
    for filename, content, user in expanded:
        name, suffix = cpm_name(filename)
        records = (len(content) + 127) // 128
        padded = content + bytes((0x1A,)) * (records * 128 - len(content))
        block_total = (len(padded) + ALLOCATION_BLOCK_BYTES - 1) // ALLOCATION_BLOCK_BYTES
        extent_total = max(1, (records + 127) // 128)
        content_at = 0
        for extent in range(extent_total):
            if next_entry >= DIRECTORY_ENTRIES:
                raise ValueError("files exceed the 128-entry directory")
            blocks_here = min(8, block_total - extent * 8)
            records_here = min(128, max(0, records - extent * 128))
            entry = bytearray(32)
            entry[0] = user
            entry[1:9], entry[9:12] = name, suffix
            # Host files have no CP/M directory attributes. Preserve the
            # compatibility suite's canonical file-read-only fixture when it
            # is installed into a generated image (T1 is extension byte 0).
            if filename.upper() == "BTRO.DAT":
                entry[9] |= 0x80
            entry[12], entry[14], entry[15] = extent & 0x1F, extent >> 5, records_here
            for slot in range(blocks_here):
                if next_block >= BLOCK_COUNT:
                    raise ValueError("files exceed the 790K disk capacity")
                entry[16 + slot * 2:18 + slot * 2] = next_block.to_bytes(2, "little")
                chunk = padded[content_at:content_at + ALLOCATION_BLOCK_BYTES]
                start = directory + next_block * ALLOCATION_BLOCK_BYTES
                raw[start:start + len(chunk)] = chunk
                content_at += len(chunk)
                next_block += 1
            start = directory + next_entry * 32
            raw[start:start + 32] = entry
            next_entry += 1


def install(boot: bytes, stage1: bytes, resident: bytes,
            files: list[tuple[str, bytes]]) -> bytes:
    raw = bytearray([0xE5]) * RAW_SIZE
    for logical_index, payload in (
        (BOOT_SECTOR_LOGICAL_INDEX, boot),
        (STAGE1_SECTOR_LOGICAL_INDEX, stage1),
    ):
        start = logical_index * SECTOR_SIZE
        raw[start:start + SECTOR_SIZE] = payload.ljust(SECTOR_SIZE, b"\x00")
    capacity = SYSTEM_SECTORS * SECTOR_SIZE
    if len(resident) > capacity:
        raise ValueError(f"resident image is {len(resident)} bytes; loader capacity is {capacity}")
    start = SYSTEM_FIRST_LOGICAL_INDEX * SECTOR_SIZE
    raw[start:start + capacity] = resident.ljust(capacity, b"\x00")
    install_files(raw, files)
    image = build(bytes(raw))
    verify(image, require_blank=False)
    return image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path, default=Path("/Users/nathanael/bin/z80asm"))
    parser.add_argument("--include", action="append", type=Path, default=[],
                        help="additional user-zero file to install (repeatable)")
    parser.add_argument("--include-as", action="append", default=[], metavar="NAME=PATH",
                        help="install PATH under a chosen CP/M 8.3 NAME")
    parser.add_argument("--include-user-as", action="append", default=[],
                        metavar="USER:NAME=PATH",
                        help="install PATH under NAME in CP/M user 0..15")
    parser.add_argument("--cross-fixture", action="store_true",
                        help="install the canonical one-record BTBFILE.DAT fixture")
    parser.add_argument("--full-fixture", action="store_true",
                        help="install the canonical RANDTEST full-disk fixture")
    parser.add_argument("--output", type=Path,
                        default=BUILD / "BetterCPM-Extended-80T-DS-System-790K.dmk")
    args = parser.parse_args()
    resident_path = ROOT / "build/system/resident.bin"
    if not resident_path.is_file():
        raise SystemExit(f"missing resident image: {resident_path}")
    boot = assemble(args.assembler, SOURCE / "boot.mac", BUILD / "boot.bin", BOOT_ADDRESS)
    stage1 = assemble(args.assembler, SOURCE / "stage1.mac", BUILD / "stage1.bin", STAGE1_ADDRESS)
    resident = resident_path.read_bytes()
    extras = []
    for path in args.include:
        if not path.is_file():
            raise SystemExit(f"missing included file: {path}")
        extras.append((path.name, path.read_bytes()))
    for specification in args.include_as:
        name, separator, source_name = specification.partition("=")
        path = Path(source_name)
        if not separator or not name or not path.is_file():
            raise SystemExit(f"invalid included-file alias: {specification}")
        cpm_name(name)            # validate before doing any image work
        extras.append((name, path.read_bytes()))
    for specification in args.include_user_as:
        user_text, colon, remainder = specification.partition(":")
        name, separator, source_name = remainder.partition("=")
        path = Path(source_name)
        try:
            user = int(user_text, 10)
        except ValueError:
            user = -1
        if (not colon or not separator or not name or not path.is_file()
                or not 0 <= user <= 15):
            raise SystemExit(f"invalid user included-file alias: {specification}")
        cpm_name(name)
        extras.append((name, path.read_bytes(), user))
    if args.cross_fixture:
        extras.append(("BTBFILE.DAT", CROSS_FIXTURE))
    if args.full_fixture:
        full = bytearray(128 * 128)
        full[127 * 128:127 * 128 + 8] = b"FULL-127"
        # HELLO, BTFULL, and BTREL consume ten allocation blocks after the
        # two directory blocks. Fill every block that remains.
        filler_blocks = BLOCK_COUNT - FIRST_DATA_BLOCK - 10
        extras.extend((
            ("BTFULL.DAT", bytes(full)),
            ("BTREL.DAT", bytes(128)),
            ("BTFILL.DAT", bytes(filler_blocks * ALLOCATION_BLOCK_BYTES)),
        ))
    image = install(boot, stage1, resident, [("HELLO.COM", HELLO_COM), *extras])
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(image)
    for path in (BUILD / "boot.bin", BUILD / "stage1.bin", output):
        try:
            label = path.relative_to(ROOT)
        except ValueError:
            label = path
        print(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {label}")
    print(f"boot bytes: {len(boot)}; stage-one bytes: {len(stage1)}; "
          f"resident bytes: {len(resident)} in {SYSTEM_SECTORS} sectors")


if __name__ == "__main__":
    main()
