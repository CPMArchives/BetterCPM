#!/usr/bin/env python3
"""Apply the measured z80pack address inventory to the packed ROM image."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def packed_entry(manifest: dict[str, object], component: str,
                 source: int) -> int:
    item = next(row for row in manifest["components"]
                if row["name"] == component)
    for fragment in item["fragments"]:
        if fragment["source_start"] <= source < fragment["source_end"]:
            return fragment["rom_start"] + source - fragment["source_start"]
    raise ValueError(
        f"{component} entry {source:04X}h is not in immutable packed code")


def build(pack: Path, inventory_path: Path, output: Path) -> dict[str, object]:
    pack_manifest = json.loads(
        (pack / "rom-pack.json").read_text(encoding="ascii"))
    inventory_data = inventory_path.read_bytes()
    inventory = json.loads(inventory_data.decode("ascii"))
    source = (pack / "rom-pack.bin").read_bytes()
    base = int(pack_manifest["base"])
    end = int(pack_manifest["end"])
    if len(source) != end - base or digest(source) != pack_manifest["sha256"]:
        raise ValueError("packed ROM identity does not match its manifest")
    if pack_manifest["executable"] is not False:
        raise ValueError("relocation source unexpectedly claims to be executable")
    if (inventory["reference_count"] != len(inventory["references"]) or
            inventory["unexplained_changed_bytes"] != 0 or
            inventory["unresolved_targets"] != 0):
        raise ValueError("address inventory is incomplete")
    expected_ignored = {
        "gateway": 3, "bdos": 0, "extensions": 0, "disk": 0,
        "bios": 0, "fileloader": 0, "tables": 16,
    }
    if inventory["ignored_mutable_operand_counts"] != expected_ignored:
        raise ValueError("mutable address-word inventory changed")
    ram_manifest = json.loads(
        (pack / "ram-init.json").read_text(encoding="ascii"))
    ram_template = (pack / "ram-init.bin").read_bytes()
    if len(ram_manifest["fixups"]) != 16:
        raise ValueError("RAM template no longer records sixteen DPH fixups")
    stable_words = {0xD64C: 0xD504, 0xD64E: 0xD501, 0xD654: 0xD501}
    for address, value in stable_words.items():
        offset = address - int(ram_manifest["base"])
        actual = int.from_bytes(ram_template[offset:offset + 2], "little")
        if actual != value:
            raise ValueError(
                f"RAM template word {address:04X}h contains {actual:04X}h, "
                f"expected final address {value:04X}h")

    image = bytearray(source)
    occupied: set[int] = set()
    changed_words = 0
    class_counts: Counter[str] = Counter()
    component_counts: Counter[str] = Counter()
    for reference in sorted(
            inventory["references"], key=lambda row: row["packed_operand"]):
        address = int(reference["packed_operand"])
        offset = address - base
        if offset < 0 or offset + 2 > len(image):
            raise ValueError(f"operand {address:04X}h lies outside packed ROM")
        operand_bytes = {offset, offset + 1}
        if occupied & operand_bytes:
            raise ValueError(f"overlapping relocation operand at {address:04X}h")
        occupied |= operand_bytes
        old = int.from_bytes(image[offset:offset + 2], "little")
        if old != int(reference["old_target"]):
            raise ValueError(
                f"operand {address:04X}h contains {old:04X}h, expected "
                f"{int(reference['old_target']):04X}h")
        new = int(reference["new_target"])
        if not 0 <= new <= 0xFFFF:
            raise ValueError(f"target {new:X}h does not fit a Z80 address")
        image[offset:offset + 2] = new.to_bytes(2, "little")
        changed_words += old != new
        class_counts[str(reference["target_class"])] += 1
        component_counts[str(reference["component"])] += 1

    payload = bytes(image)
    changed_bytes = sum(left != right for left, right in zip(source, payload))
    manifest: dict[str, object] = {
        "base": base,
        "end": end,
        "bytes": len(payload),
        "sha256": digest(payload),
        "source_pack_sha256": digest(source),
        "reference_inventory_sha256": digest(inventory_data),
        "executable": True,
        "boot_integrated": False,
        "protected_xip_qualified": False,
        "relocation_status": "all inventoried packed-code address words applied",
        "relocation_words": len(inventory["references"]),
        "changed_words": changed_words,
        "unchanged_final_words": len(inventory["references"]) - changed_words,
        "changed_bytes": changed_bytes,
        "accounted_layout_words": len(inventory["references"]) + 19,
        "mutable_template_fixups": 16,
        "mutable_already_final_words": 3,
        "target_class_counts": dict(sorted(class_counts.items())),
        "component_counts": dict(sorted(component_counts.items())),
        "entries": {
            "system_init": packed_entry(pack_manifest, "gateway", 0xD5C4),
            "system_boot": packed_entry(pack_manifest, "gateway", 0xD5E4),
            "bios_boot": packed_entry(pack_manifest, "bios", 0xEA08),
            "bdos": pack_manifest["candidate_entry_inputs"]["bdos"],
            "ram_template": pack_manifest["candidate_entry_inputs"]["template"],
            "cold_initializer": pack_manifest["candidate_entry_inputs"]["cold_initializer"],
        },
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "rom-image.bin").write_bytes(payload)
    (output / "rom-image.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"Relocated ROM image: {manifest['relocation_words']} words; "
          f"{changed_words} changed, {manifest['unchanged_final_words']} already final; "
          f"{changed_bytes} changed bytes; {manifest['sha256']}")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.pack.resolve(), args.inventory.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
