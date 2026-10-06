#!/usr/bin/env python3
"""Validate the measured z80pack packed-code address inventory."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from build_rom_pack import component_inputs

# Allocation publication shares Close/Make paths: -3 RAM references,
# +2 ROM references; each remaining operand still undergoes independent checks.
EXPECTED_REFERENCES = {
    "gateway": 23,
    "bdos": 519,
    "extensions": 57,
    "disk": 82,
    "bios": 64,
    "fileloader": 13,
    "tables": 0,
}
EXPECTED_DISCOVERED = {
    "gateway": 26,
    "bdos": 519,
    "extensions": 57,
    "disk": 82,
    "bios": 64,
    "fileloader": 13,
    "tables": 16,
}
EXPECTED_CLASSES = {"immutable-rom": 431, "live-ram": 327}
EXPECTED_OVERLAY_CLASSES = {"immutable-rom": 3, "live-ram": 102}
EXPECTED_OVERLAY_REFERENCES = 105


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--z80pack-build", type=Path, required=True)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    args = parser.parse_args()
    build = args.z80pack_build.resolve()
    pack_dir = args.pack.resolve()
    inventory = json.loads(args.inventory.resolve().read_text(encoding="ascii"))
    manifest = json.loads(
        (pack_dir / "rom-pack.json").read_text(encoding="ascii"))
    image = (pack_dir / "rom-pack.bin").read_bytes()
    sources = {
        name: (base, path.read_bytes())
        for name, base, path in component_inputs(build)
    }
    config_source = (build / "config.bin").read_bytes()
    components = {row["name"]: row for row in manifest["components"]}

    if inventory["layout_deltas"] != [0x101, 0x203]:
        raise AssertionError("address inventory lacks both accepted layout deltas")
    if inventory["discovered_word_counts"] != EXPECTED_DISCOVERED:
        raise AssertionError("shifted-layout discovered-word counts changed")
    if inventory["reference_counts"] != EXPECTED_REFERENCES:
        raise AssertionError("packed-code reference counts changed")
    if inventory["target_class_counts"] != EXPECTED_CLASSES:
        raise AssertionError("ROM/RAM reference classification changed")
    if inventory["reference_count"] != 758:
        raise AssertionError("packed-code reference total changed")
    if (inventory["overlay_discovered_word_count"] !=
            EXPECTED_OVERLAY_REFERENCES or
            inventory["overlay_reference_count"] !=
            EXPECTED_OVERLAY_REFERENCES):
        raise AssertionError("CONFIG overlay reference total changed")
    if (inventory["unexplained_changed_bytes"] != 0 or
            inventory["unresolved_targets"] != 0):
        raise AssertionError("inventory reports an unexplained or unresolved fact")

    seen = set()
    counts = Counter()
    classes = Counter()
    for reference in inventory["references"]:
        component = reference["component"]
        base, source = sources[component]
        offset = reference["source_offset"]
        source_operand = reference["source_operand"]
        if source_operand != base + offset:
            raise AssertionError(f"{component}: inconsistent source operand")
        old = int.from_bytes(source[offset:offset + 2], "little")
        if old != reference["old_target"]:
            raise AssertionError(f"{component}: recorded old target changed")
        key = (component, offset)
        if key in seen:
            raise AssertionError(f"{component}: duplicate operand {offset:04X}h")
        seen.add(key)

        matching = [
            fragment for fragment in components[component]["fragments"]
            if (fragment["source_start"] <= source_operand and
                source_operand + 2 <= fragment["source_end"])
        ]
        if len(matching) != 1:
            raise AssertionError(f"{component}: operand is not in one immutable fragment")
        fragment = matching[0]
        packed = fragment["rom_start"] + source_operand - fragment["source_start"]
        if packed != reference["packed_operand"]:
            raise AssertionError(f"{component}: packed operand mapping changed")
        image_offset = packed - manifest["base"]
        if image[image_offset:image_offset + 2] != source[offset:offset + 2]:
            raise AssertionError(f"{component}: packed operand bytes changed")
        if reference["target_class"] not in EXPECTED_CLASSES:
            raise AssertionError(f"{component}: unknown target class")
        if not reference["target_owners"]:
            raise AssertionError(f"{component}: target lacks an owner")
        if not reference["source"] or reference["source"] == "continuation data":
            raise AssertionError(f"{component}: operand lacks source context")
        counts[component] += 1
        classes[reference["target_class"]] += 1
    if dict(counts) != {key: value for key, value in EXPECTED_REFERENCES.items()
                        if value}:
        raise AssertionError("reference records do not match component totals")
    if dict(classes) != EXPECTED_CLASSES:
        raise AssertionError("reference records do not match class totals")
    overlay_seen = set()
    overlay_classes = Counter()
    for reference in inventory["overlay_references"]:
        offset = reference["overlay_operand"]
        if (reference["component"] != "config" or
                reference["source_offset"] != offset or
                reference["source_operand"] != 0xF000 + offset):
            raise AssertionError("CONFIG overlay operand mapping changed")
        if offset in overlay_seen or offset + 1 in overlay_seen:
            raise AssertionError("CONFIG overlay operands overlap")
        overlay_seen.update((offset, offset + 1))
        if int.from_bytes(config_source[offset:offset + 2], "little") != \
                reference["old_target"]:
            raise AssertionError("CONFIG overlay source operand changed")
        if not reference["target_owners"] or not reference["source"]:
            raise AssertionError("CONFIG overlay reference lacks provenance")
        overlay_classes[reference["target_class"]] += 1
    if dict(sorted(overlay_classes.items())) != EXPECTED_OVERLAY_CLASSES:
        raise AssertionError("CONFIG overlay target classification changed")
    stack_tops = [row for row in inventory["references"]
                  if "STKTOP" in row["source"]]
    extension_entries = [row for row in inventory["references"]
                         if row["component"] == "bdos" and
                         row["old_target"] == 0xE49F and
                         "LY_EXT" in row["source"]]
    if (len(stack_tops) != 4 or
            any(row["target_class"] != "live-ram" for row in stack_tops)):
        raise AssertionError("exclusive stack-top references lost RAM semantics")
    if (len(extension_entries) != 2 or
            any(row["target_class"] != "immutable-rom"
                for row in extension_entries)):
        raise AssertionError("E49Fh extension entries lost ROM semantics")
    print("ROM address inventory verified: 758 packed-code words and 105 CONFIG "
          "overlay words; no unresolved references")


if __name__ == "__main__":
    main()
