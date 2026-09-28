#!/usr/bin/env python3
"""Verify the executable but not yet boot-integrated z80pack ROM image."""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path

from build_rom_relocated_image import build

EXPECTED_COMPONENTS = {
    "bdos": 520,
    "bios": 64,
    "disk": 82,
    "extensions": 57,
    "fileloader": 13,
    "gateway": 23,
}
EXPECTED_CLASSES = {"immutable-rom": 429, "live-ram": 330}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    args = parser.parse_args()
    pack = args.pack.resolve()
    inventory_path = args.inventory.resolve()
    image_dir = args.image.resolve()

    with tempfile.TemporaryDirectory(prefix="bettercpm-rom-relocated-") as temporary:
        regenerated = Path(temporary)
        expected = build(pack, inventory_path, regenerated)
        expected_image = (regenerated / "rom-image.bin").read_bytes()
    manifest = json.loads(
        (image_dir / "rom-image.json").read_text(encoding="ascii"))
    image = (image_dir / "rom-image.bin").read_bytes()
    source = (pack / "rom-pack.bin").read_bytes()
    inventory = json.loads(inventory_path.read_text(encoding="ascii"))
    if manifest != expected or image != expected_image:
        raise AssertionError("relocated ROM differs from independent regeneration")
    if len(image) != 0x2100 or digest(image) != manifest["sha256"]:
        raise AssertionError("relocated ROM size or hash is incorrect")
    if manifest["source_pack_sha256"] != digest(source):
        raise AssertionError("relocated ROM identifies the wrong packing source")
    if manifest["executable"] is not True:
        raise AssertionError("fully relocated image is not marked executable")
    if (manifest["boot_integrated"] is not False or
            manifest["protected_xip_qualified"] is not False):
        raise AssertionError("relocation artifact overclaims later qualification")
    if (manifest["relocation_words"] != 759 or
            manifest["changed_words"] != 748 or
            manifest["unchanged_final_words"] != 11 or
            manifest["changed_bytes"] != 1496):
        raise AssertionError("accepted relocation totals changed")
    if (manifest["accounted_layout_words"] != 778 or
            manifest["mutable_template_fixups"] != 16 or
            manifest["mutable_already_final_words"] != 3):
        raise AssertionError("mutable layout-word accounting changed")
    if manifest["component_counts"] != EXPECTED_COMPONENTS:
        raise AssertionError("component relocation totals changed")
    if manifest["target_class_counts"] != EXPECTED_CLASSES:
        raise AssertionError("target-class relocation totals changed")
    if manifest["entries"] != {
            "system_cold": 0xDF00,
            "bdos": 0xDF9E,
            "ram_template": 0xF3F5,
            "cold_initializer": 0xFD61}:
        raise AssertionError("accepted executable entry inputs changed")

    base = manifest["base"]
    operand_bytes: set[int] = set()
    components: Counter[str] = Counter()
    classes: Counter[str] = Counter()
    for reference in inventory["references"]:
        offset = reference["packed_operand"] - base
        positions = {offset, offset + 1}
        if operand_bytes & positions:
            raise AssertionError("relocation operands overlap")
        operand_bytes |= positions
        if int.from_bytes(source[offset:offset + 2], "little") != reference["old_target"]:
            raise AssertionError("packing source no longer contains recorded old target")
        if int.from_bytes(image[offset:offset + 2], "little") != reference["new_target"]:
            raise AssertionError("relocated image does not contain recorded new target")
        components[reference["component"]] += 1
        classes[reference["target_class"]] += 1
    if dict(sorted(components.items())) != EXPECTED_COMPONENTS:
        raise AssertionError("relocation records do not match component totals")
    if dict(sorted(classes.items())) != EXPECTED_CLASSES:
        raise AssertionError("relocation records do not match target-class totals")
    for offset, (old, new) in enumerate(zip(source, image)):
        if offset not in operand_bytes and old != new:
            raise AssertionError(f"non-operand byte changed at {base + offset:04X}h")

    reversed_image = bytearray(image)
    for reference in inventory["references"]:
        offset = reference["packed_operand"] - base
        reversed_image[offset:offset + 2] = int(reference["old_target"]).to_bytes(2, "little")
    if bytes(reversed_image) != source:
        raise AssertionError("inverse relocation does not reproduce packed source")
    print("Relocated ROM verified: all 778 layout words accounted; 759 disjoint "
          "ROM words, 748 changed values, 1496 changed bytes, and no changes "
          "outside inventoried operands")


if __name__ == "__main__":
    main()
