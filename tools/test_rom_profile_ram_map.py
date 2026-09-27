#!/usr/bin/env python3
"""Validate the initial z80pack ROM-profile RAM placement."""
from __future__ import annotations

import csv
from pathlib import Path

from system_layout import LAYOUT

ROOT = Path(__file__).resolve().parents[1]
OWNERSHIP = ROOT / "metadata/rom-ram-ownership.tsv"
RAM_MAP = ROOT / "metadata/rom-profile-ram-z80pack.tsv"
RAM_START = LAYOUT["TPA"]
PLANNING_LIMIT = 0xE300
EXPECTED_BOUNDARY = 0xDF00
EXPECTED_OBJECT_BYTES = 2254
EXPECTED_RESERVED_BYTES = 158


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="ascii") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def main() -> None:
    ownership = rows(OWNERSHIP)
    required = {
        row["object"]: int(row["bytes"])
        for row in ownership
        if row["platform"] in ("all", "z80pack") and
        row["disposition"] in (
            "relocate to ROM-profile RAM", "retain in ROM-profile RAM")
    }
    placement = rows(RAM_MAP)
    mapped = {row["source_object"] for row in placement if row["kind"] == "object"}
    if mapped != set(required):
        missing = sorted(set(required) - mapped)
        extra = sorted(mapped - set(required))
        raise AssertionError(f"RAM-map ownership mismatch: missing={missing}, extra={extra}")

    ranges = []
    object_bytes = 0
    reserved_bytes = 0
    for row in placement:
        if row["kind"] not in ("object", "reserved"):
            raise AssertionError(f"{row['entry']} has unknown map kind {row['kind']}")
        start = int(row["ram_start"], 16)
        end = int(row["ram_end"], 16) + 1
        size = int(row["bytes"])
        if size != end - start:
            raise AssertionError(f"{row['entry']} byte count does not match its range")
        if not row["purpose"].strip():
            raise AssertionError(f"{row['entry']} lacks a placement purpose")
        if row["kind"] == "object":
            if size != required[row["source_object"]]:
                raise AssertionError(f"{row['entry']} size differs from ownership inventory")
            object_bytes += size
        else:
            if row["source_object"] != "none":
                raise AssertionError(f"{row['entry']} reserved range claims an object")
            reserved_bytes += size
        ranges.append((start, end, row["entry"]))

    ranges.sort()
    cursor = RAM_START
    for start, end, name in ranges:
        if start != cursor:
            raise AssertionError(
                f"RAM map is not contiguous before {name}: {cursor:04X}h != {start:04X}h")
        cursor = end
    boundary = (cursor + 0xFF) & 0xFF00
    if object_bytes != EXPECTED_OBJECT_BYTES:
        raise AssertionError(f"mapped objects total {object_bytes}, expected {EXPECTED_OBJECT_BYTES}")
    if reserved_bytes != EXPECTED_RESERVED_BYTES:
        raise AssertionError(f"reserved RAM totals {reserved_bytes}, expected {EXPECTED_RESERVED_BYTES}")
    if boundary != EXPECTED_BOUNDARY or boundary > PLANNING_LIMIT:
        raise AssertionError(
            f"derived ROM boundary {boundary:04X}h; expected {EXPECTED_BOUNDARY:04X}h "
            f"at or below {PLANNING_LIMIT:04X}h")
    tpa = LAYOUT["TPA"] - 0x100
    if tpa < 53 * 1024:
        raise AssertionError(f"ROM profile exposes only {tpa} bytes of TPA")

    print(f"z80pack ROM RAM: {object_bytes} object + {reserved_bytes} reserved "
          f"= {cursor - RAM_START} bytes; ROM boundary {boundary:04X}h; "
          f"RAM slack {boundary - cursor} bytes; "
          f"ROM capacity {0x10000 - boundary} bytes; TPA {tpa} bytes")


if __name__ == "__main__":
    main()
