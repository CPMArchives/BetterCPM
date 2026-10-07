#!/usr/bin/env python3
"""Pack z80pack immutable inputs and publish their exact address map."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from system_layout import LAYOUT

ROOT = Path(__file__).resolve().parents[1]
OWNERSHIP = ROOT / "metadata/rom-ram-ownership.tsv"
ROM_BASE = 0xDF00
ROM_END = 0x10000
EXPECTED_IMMUTABLE = 5370
EXPECTED_MUTABLE = 866


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def mutable_ranges() -> list[tuple[int, int, str]]:
    with OWNERSHIP.open(newline="", encoding="ascii") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    ranges = []
    for row in rows:
        if row["platform"] not in ("all", "z80pack"):
            continue
        if row["disposition"] != "relocate to ROM-profile RAM":
            continue
        ranges.append((int(row["current_start"], 16),
                       int(row["current_end"], 16) + 1, row["object"]))
    return sorted(ranges)


def component_inputs(z80pack_build: Path) -> tuple[tuple[str, int, Path], ...]:
    return (
        ("gateway", LAYOUT["SYSTEM"], z80pack_build / "gateway.bin"),
        ("bdos", LAYOUT["BDOS"], ROOT / "build/bdos/bdos.bin"),
        ("extensions", LAYOUT["EXTENSIONS"], z80pack_build / "extensions.bin"),
        ("disk", LAYOUT["DISK"], z80pack_build / "disk.bin"),
        ("bios", LAYOUT["BIOS"], z80pack_build / "bios.bin"),
        ("fileloader", LAYOUT["FILE"], ROOT / "build/system/fileloader.bin"),
        ("tables", LAYOUT["TABLES"], z80pack_build / "tables.bin"),
    )


def immutable_fragments(base: int, data: bytes,
                        mutable: list[tuple[int, int, str]]) -> tuple[list[tuple[int, bytes]], list[str]]:
    end = base + len(data)
    mask = bytearray(len(data))
    owners = []
    for start, stop, owner in mutable:
        left, right = max(base, start), min(end, stop)
        if left >= right:
            continue
        for index in range(left - base, right - base):
            if mask[index]:
                raise ValueError(f"overlapping mutable ownership at {base + index:04X}h")
            mask[index] = 1
        owners.append(owner)
    fragments = []
    index = 0
    while index < len(data):
        while index < len(data) and mask[index]:
            index += 1
        first = index
        while index < len(data) and not mask[index]:
            index += 1
        if first < index:
            fragments.append((base + first, data[first:index]))
    return fragments, owners


def build(z80pack_build: Path, artifacts: Path, output: Path) -> dict[str, object]:
    mutable = mutable_ranges()
    image = bytearray(b"\xFF" * (ROM_END - ROM_BASE))
    cursor = ROM_BASE
    components = []
    immutable_total = 0
    mutable_total = 0
    for name, base, path in component_inputs(z80pack_build):
        data = path.read_bytes()
        fragments, owners = immutable_fragments(base, data, mutable)
        component = {
            "name": name,
            "source_base": base,
            "source_bytes": len(data),
            "source_sha256": digest(data),
            "mutable_owners": owners,
            "fragments": [],
        }
        for source, fragment in fragments:
            start, end = cursor, cursor + len(fragment)
            if end > ROM_END:
                raise ValueError(f"{name} exceeds protected ROM")
            image[start - ROM_BASE:end - ROM_BASE] = fragment
            component["fragments"].append({
                "source_start": source,
                "source_end": source + len(fragment),
                "rom_start": start,
                "rom_end": end,
                "bytes": len(fragment),
                "sha256": digest(fragment),
            })
            cursor = end
            immutable_total += len(fragment)
        component["immutable_bytes"] = sum(
            fragment["bytes"] for fragment in component["fragments"])
        component["mutable_bytes"] = len(data) - component["immutable_bytes"]
        mutable_total += component["mutable_bytes"]
        components.append(component)
    if immutable_total != EXPECTED_IMMUTABLE:
        raise ValueError(
            f"packed immutable source is {immutable_total} bytes; expected {EXPECTED_IMMUTABLE}")
    if mutable_total != EXPECTED_MUTABLE:
        raise ValueError(
            f"classified mutable source is {mutable_total} bytes; expected {EXPECTED_MUTABLE}")

    segments = []
    for name, filename in (("ram-template", "ram-init.bin"),
                           ("cold-initializer", "cold-init.bin")):
        data = (artifacts / filename).read_bytes()
        start, end = cursor, cursor + len(data)
        if end > ROM_END:
            raise ValueError(f"{name} exceeds protected ROM")
        image[start - ROM_BASE:end - ROM_BASE] = data
        segments.append({"name": name, "rom_start": start, "rom_end": end,
                         "bytes": len(data), "sha256": digest(data)})
        cursor = end

    manifest: dict[str, object] = {
        "base": ROM_BASE,
        "end": ROM_END,
        "bytes": len(image),
        "sha256": digest(bytes(image)),
        "executable": False,
        "relocation_status": "absolute resident references remain linked to the RAM layout",
        "immutable_source_bytes": immutable_total,
        "mutable_source_bytes": mutable_total,
        "components": components,
        "segments": segments,
        "candidate_entry_inputs": {
            "template": segments[0]["rom_start"],
            "cold_initializer": segments[1]["rom_start"],
            "bdos": next(
                fragment["rom_start"] for component in components
                if component["name"] == "bdos" for fragment in component["fragments"]
                if fragment["source_start"] == LAYOUT["BDOS"]),
        },
        "used_bytes": cursor - ROM_BASE,
        "spare_bytes": ROM_END - cursor,
        "padding_byte": 0xFF,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "rom-pack.bin").write_bytes(image)
    (output / "rom-pack.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"ROM packing artifact: {manifest['used_bytes']} used, "
          f"{manifest['spare_bytes']} spare; {manifest['sha256']}")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--z80pack-build", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.z80pack_build.resolve(), args.artifacts.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
