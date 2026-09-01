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


def install(boot: bytes, stage1: bytes) -> bytes:
    raw = bytearray([0xE5]) * RAW_SIZE
    for logical_index, payload in (
        (BOOT_SECTOR_LOGICAL_INDEX, boot),
        (STAGE1_SECTOR_LOGICAL_INDEX, stage1),
        (VERIFY_SECTOR_LOGICAL_INDEX, VERIFY_PAYLOAD),
    ):
        start = logical_index * SECTOR_SIZE
        raw[start:start + SECTOR_SIZE] = payload.ljust(SECTOR_SIZE, b"\x00")
    image = build(bytes(raw))
    verify(image, require_blank=False)
    return image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path, default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    boot = assemble(args.assembler, SOURCE / "boot.mac", BUILD / "boot.bin", BOOT_ADDRESS)
    stage1 = assemble(args.assembler, SOURCE / "stage1.mac", BUILD / "stage1.bin", STAGE1_ADDRESS)
    image = install(boot, stage1)
    output = BUILD / "BetterCPM-Extended-80T-DS-System-790K.dmk"
    output.write_bytes(image)
    for path in (BUILD / "boot.bin", BUILD / "stage1.bin", output):
        print(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT)}")
    print(f"boot bytes: {len(boot)}; stage-one bytes: {len(stage1)}")


if __name__ == "__main__":
    main()
