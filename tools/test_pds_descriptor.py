#!/usr/bin/env python3
"""Validate the PDS ABI 1 static-layout descriptor."""
from pathlib import Path

from system_layout import LAYOUT
from test_bios import require

ROOT = Path(__file__).resolve().parents[1]
RESIDENT = ROOT / "build/system/resident.bin"


def word(data: bytes, offset: int) -> int:
    return data[offset] | data[offset + 1] << 8


def main() -> None:
    resident = RESIDENT.read_bytes()
    base = LAYOUT["SYSTEM"]
    descriptor = LAYOUT["PDS_DESCRIPTOR"] - base

    require(resident[descriptor:descriptor + 3] == b"BM\x01",
            "system/PDS descriptor magic or ABI version is wrong")
    require(resident[descriptor + 3] & 1,
            "PDS ABI 1 static-layout-valid flag is clear")
    require(word(resident, descriptor + 8) == LAYOUT["PDS_LOW"],
            "PDS descriptor does not publish the live lower boundary")
    require(LAYOUT["PDS_TOP"] - word(resident, descriptor + 8) ==
            LAYOUT["PDS_SIZE"] == 192,
            "PDS descriptor boundaries do not describe the 192-byte baseline")
    require(LAYOUT["PDS_LOW"] == LAYOUT["HISTORY"] and
            LAYOUT["TPA"] == LAYOUT["PDS_LOW"] - 3,
            "PDS descriptor bridge changed history or gateway placement")
    print("PDS ABI 1 descriptor publishes the unchanged 192-byte static layout")


if __name__ == "__main__":
    main()
