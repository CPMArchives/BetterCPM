#!/usr/bin/env python3
"""Validate the measured BetterCP/M 1.0 ROM/RAM ownership inventory."""
from __future__ import annotations

import csv
import argparse
import re
from pathlib import Path

from system_layout import LAYOUT

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "metadata/rom-ram-ownership.tsv"

RELOCATION_BYTES = {"trs80": 2252, "z80pack": 2251}
ROM_RAM_BYTES = {"trs80": 2255, "z80pack": 2254}
STORAGE_CLASSES = {
    "bounded PDS state",
    "fixed subsystem state",
    "stack",
    "temporary/shared workspace",
}

# Source-derived anchors make address drift fail loudly. An integer end anchor is
# the exclusive end of a fixed layout reservation.
ANCHORS = {
    "page-zero": (0x0000, 0x0100),
    "transient-loader-stack": (LAYOUT["STACK_LOW"], LAYOUT["STACK_TOP"]),
    "dynamic-bdos-gateway": (LAYOUT["TPA"], LAYOUT["HISTORY"]),
    "command-history": (LAYOUT["HISTORY"], LAYOUT["SYSTEM"]),
    "system-stack": ("system/gateway.lst:SYS_STACK", "system/gateway.lst:SYS_STKTOP"),
    "extension-control-live": ("system/gateway.lst:ECB_FLAGS", "system/gateway.lst:CPTCOUNT"),
    "cpx-profile": ("system/gateway.lst:CPTCOUNT", "system/gateway.lst:SINIBODY"),
    "bdos-live-state": ("bdos/bdos.lst:UB_OLDSP", "bdos/bdos.lst:UB_STACK"),
    "bdos-stack": ("bdos/bdos.lst:UB_STACK", "bdos/bdos.lst:UB_STKTOP"),
    "extension-live-state": ("system/extensions.lst:EX_OLDSP", "system/extensions.lst:BCV_DESC"),
    "trs80-physical-drive-profiles": ("system/disk.lst:DC_PHYS", "system/disk.lst:DC_IDTRK"),
    "trs80-disk-session-state": ("system/disk.lst:DC_IDTRK", LAYOUT["BIOS"]),
    "z80pack-physical-drive-profiles": ("disk.lst:Z_PHYSICAL", "disk.lst:ZP_DRIVE"),
    "z80pack-disk-session-state": ("disk.lst:ZP_DRIVE", "disk.lst:ZP_END"),
    "trs80-bios-disk-state": ("bios/bios.lst:BIO_DRIVE", "bios/bios.lst:M4_INIT"),
    "trs80-bios-console-state": ("bios/bios.lst:M4CURSOR", "bios/bios.lst:M4_SCROLL_OUT"),
    "z80pack-bios-disk-state": ("bios.lst:BIO_DRIVE", "bios.lst:PL_INIT"),
    "file-stream-fcb": ("system/fileloader.lst:FL_FCB", LAYOUT["TABLES"]),
    "trs80-live-disk-tables": ("system/tables.lst:DPH0", LAYOUT["RSX_STATE"]),
    "z80pack-live-disk-tables": ("tables.lst:ZDPH0", LAYOUT["RSX_STATE"]),
    "rsx-profile": (LAYOUT["RSX_STATE"], LAYOUT["DIRBUF"]),
    "directory-buffer": (LAYOUT["DIRBUF"], LAYOUT["MODULEBUF"]),
    "physical-sector-buffer": (LAYOUT["MODULEBUF"], LAYOUT["MODULEBUF"] + 512),
    "module-config-buffer": (LAYOUT["MODULEBUF"] + 512, LAYOUT["RAM_END"]),
}


def symbol(anchor: int | str, listing_root: Path) -> int:
    if isinstance(anchor, int):
        return anchor
    relative, name = anchor.split(":", 1)
    path = listing_root / relative
    if not path.is_file():
        path = listing_root / Path(relative).name
    if not path.is_file():
        path = ROOT / "build" / relative
    listing = path.read_text(errors="replace")
    matches = re.findall(
        rf"^([0-9a-f]{{4}})\s+.*?\b{re.escape(name)}:", listing,
        re.MULTILINE | re.IGNORECASE)
    if not matches:
        raise AssertionError(f"missing ownership anchor {name} in {relative}")
    return int(matches[-1], 16)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=("trs80", "z80pack"), default="trs80")
    parser.add_argument("--listing-root", type=Path, default=ROOT / "build")
    args = parser.parse_args()
    with INVENTORY.open(newline="", encoding="ascii") as stream:
        all_rows = list(csv.DictReader(stream, delimiter="\t"))
    if set(row["object"] for row in all_rows) != set(ANCHORS):
        missing = sorted(set(ANCHORS) - {row["object"] for row in all_rows})
        extra = sorted({row["object"] for row in all_rows} - set(ANCHORS))
        raise AssertionError(f"inventory mismatch: missing={missing}, extra={extra}")
    rows = [row for row in all_rows if row["platform"] in ("all", args.platform)]

    ranges = []
    relocation = 0
    rom_ram = 0
    for row in rows:
        start = int(row["current_start"], 16)
        end = int(row["current_end"], 16) + 1
        expected_start, expected_end = (
            symbol(anchor, args.listing_root) for anchor in ANCHORS[row["object"]])
        if (start, end) != (expected_start, expected_end):
            raise AssertionError(
                f"{row['object']} is {start:04X}h..{end - 1:04X}h; "
                f"build says {expected_start:04X}h..{expected_end - 1:04X}h")
        if int(row["bytes"]) != end - start:
            raise AssertionError(f"{row['object']} byte count does not match its range")
        if row["storage_class"] not in STORAGE_CLASSES:
            raise AssertionError(f"{row['object']} has unknown storage class")
        for field in ("owner", "lifetime", "cold_boot", "warm_boot",
                      "overlay_group", "immutable_template", "disposition"):
            if not row[field].strip():
                raise AssertionError(f"{row['object']} lacks {field}")
        ranges.append((start, end, row["object"]))
        if row["disposition"] == "relocate to ROM-profile RAM":
            relocation += end - start
        if row["disposition"] in (
                "relocate to ROM-profile RAM", "retain in ROM-profile RAM"):
            rom_ram += end - start

    ranges.sort()
    for left, right in zip(ranges, ranges[1:]):
        if left[1] > right[0]:
            raise AssertionError(f"ownership ranges overlap: {left[2]} and {right[2]}")
    expected_relocation = RELOCATION_BYTES[args.platform]
    if relocation != expected_relocation:
        raise AssertionError(
            f"ROM relocation inventory is {relocation} bytes, expected {expected_relocation}")
    expected_rom_ram = ROM_RAM_BYTES[args.platform]
    if rom_ram != expected_rom_ram:
        raise AssertionError(
            f"ROM-profile RAM inventory is {rom_ram} bytes, expected {expected_rom_ram}")

    print(f"ROM/RAM inventory ({args.platform}): {len(rows)} objects; "
          f"{relocation} bytes require relocation; {rom_ram} bytes require RAM")


if __name__ == "__main__":
    main()
