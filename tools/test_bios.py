#!/usr/bin/env python3
"""Verify the structural contract of the BetterCP/M BIOS artifact."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "build/bios/bios.bin"
BIOS_BASE = 0xF000
ENTRY_COUNT = 17
ENTRY_SIZE = 3


def main() -> None:
    data = IMAGE.read_bytes()
    table_size = ENTRY_COUNT * ENTRY_SIZE
    if len(data) < table_size:
        raise SystemExit("BIOS image is shorter than its jump table")
    for index in range(ENTRY_COUNT):
        offset = index * ENTRY_SIZE
        if data[offset] != 0xC3:
            raise SystemExit(f"BIOS entry {index} is not a JP instruction")
        target = int.from_bytes(data[offset + 1:offset + 3], "little")
        if not BIOS_BASE <= target < BIOS_BASE + len(data):
            raise SystemExit(f"BIOS entry {index} target {target:04x} is outside image")
    page_zero_wboot_operand = BIOS_BASE + ENTRY_SIZE
    if page_zero_wboot_operand - ENTRY_SIZE != BIOS_BASE:
        raise SystemExit("WBOOT entry does not support page-zero BIOS discovery")
    print(f"verified {ENTRY_COUNT} three-byte BIOS entries at {BIOS_BASE:04X}h")


if __name__ == "__main__":
    main()
