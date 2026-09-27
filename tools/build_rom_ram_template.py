#!/usr/bin/env python3
"""Build the z80pack ROM profile's deterministic RAM initialization template."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from system_layout import LAYOUT

ROOT = Path(__file__).resolve().parents[1]
RAM_MAP = ROOT / "metadata/rom-profile-ram-z80pack.tsv"
RAM_BASE = LAYOUT["TPA"]
MUTABLE_COMPONENT_BYTES = {
    "gateway.bin": 90,
    "bdos.bin": 109,
    "extensions.bin": 5,
    "disk.bin": 38,
    "bios.bin": 12,
    "fileloader.bin": 36,
    "tables.bin": 576,
}


def read_map() -> list[dict[str, str]]:
    with RAM_MAP.open(newline="", encoding="ascii") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def current_image(z80pack_build: Path) -> bytearray:
    image = bytearray(LAYOUT["RAM_END"] - RAM_BASE)
    parts = (
        (LAYOUT["SYSTEM"], z80pack_build / "gateway.bin"),
        (LAYOUT["BDOS"], ROOT / "build/bdos/bdos.bin"),
        (LAYOUT["EXTENSIONS"], z80pack_build / "extensions.bin"),
        (LAYOUT["DISK"], z80pack_build / "disk.bin"),
        (LAYOUT["BIOS"], z80pack_build / "bios.bin"),
        (LAYOUT["FILE"], ROOT / "build/system/fileloader.bin"),
        (LAYOUT["TABLES"], z80pack_build / "tables.bin"),
    )
    for address, path in parts:
        data = path.read_bytes()
        offset = address - RAM_BASE
        image[offset:offset + len(data)] = data
    return image


def component_paths(z80pack_build: Path) -> tuple[Path, ...]:
    return (
        z80pack_build / "gateway.bin",
        ROOT / "build/bdos/bdos.bin",
        z80pack_build / "extensions.bin",
        z80pack_build / "disk.bin",
        z80pack_build / "bios.bin",
        ROOT / "build/system/fileloader.bin",
        z80pack_build / "tables.bin",
    )


def put_word(data: bytearray, offset: int, value: int) -> None:
    data[offset:offset + 2] = bytes((value & 0xFF, value >> 8))


def fix_disk_table_pointers(template: bytearray, target: int) -> list[dict[str, int]]:
    """Relocate the four live DPH pointer quartets inside their 576-byte object."""
    table = target - RAM_BASE
    directory = 0xD9ED
    alv = target + 320
    csv_base = target + 448
    fixups = []
    for drive in range(4):
        record = table + drive * 80
        values = (
            (8, directory),
            (10, target + drive * 80 + 17),
            (12, csv_base + drive * 32),
            (14, alv),
        )
        for field, value in values:
            put_word(template, record + field, value)
            fixups.append({"offset": drive * 80 + field, "value": value})
    return fixups


def build(z80pack_build: Path) -> tuple[bytes, dict[str, object]]:
    rows = read_map()
    end = max(int(row["ram_end"], 16) for row in rows) + 1
    template = bytearray(end - RAM_BASE)
    current = current_image(z80pack_build)
    copied = []
    fixups: list[dict[str, int]] = []
    for row in rows:
        start = int(row["ram_start"], 16)
        size = int(row["bytes"])
        destination = start - RAM_BASE
        policy = row["init_policy"]
        if policy in ("zero", "runtime"):
            if row["template_start"] != "none":
                raise ValueError(f"{row['entry']}: {policy} policy has a template source")
            continue
        if policy not in ("copy", "copy-fixup"):
            raise ValueError(f"{row['entry']}: unknown initialization policy {policy}")
        source = int(row["template_start"], 16)
        source_offset = source - RAM_BASE
        template[destination:destination + size] = current[source_offset:source_offset + size]
        copied.append(row["entry"])
        if policy == "copy-fixup":
            if row["entry"] != "live-disk-tables":
                raise ValueError(f"{row['entry']}: no declared pointer-fixup implementation")
            fixups.extend(fix_disk_table_pointers(template, start))
    payload = bytes(template)
    boundary = (end + 0xFF) & 0xFF00
    immutable_source_bytes = sum(
        path.stat().st_size - MUTABLE_COMPONENT_BYTES[path.name]
        for path in component_paths(z80pack_build))
    rom_capacity = 0x10000 - boundary
    rom_used = len(payload) + immutable_source_bytes
    if rom_used > rom_capacity:
        raise ValueError(
            f"RAM template plus immutable source requires {rom_used} ROM bytes; "
            f"boundary permits {rom_capacity}")
    manifest: dict[str, object] = {
        "base": RAM_BASE,
        "end": end,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "copied": copied,
        "fixups": fixups,
        "immutable_source_bytes": immutable_source_bytes,
        "rom_capacity": rom_capacity,
        "rom_spare_before_initializer": rom_capacity - rom_used,
        "rom_used_before_initializer": rom_used,
    }
    return payload, manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--z80pack-build", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload, manifest = build(args.z80pack_build.resolve())
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / "ram-init.bin").write_bytes(payload)
    (output / "ram-init.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"ROM RAM template: {len(payload)} bytes; "
          f"conservative ROM spare {manifest['rom_spare_before_initializer']} bytes; "
          f"{manifest['sha256']}")


if __name__ == "__main__":
    main()
