#!/usr/bin/env python3
"""Discover and resolve absolute words in packed z80pack resident code."""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

from build_rom_pack import component_inputs

ROOT = Path(__file__).resolve().parents[1]
OWNERSHIP = ROOT / "metadata/rom-ram-ownership.tsv"
RAM_MAP = ROOT / "metadata/rom-profile-ram-z80pack.tsv"
DELTAS = (0x101, 0x203)
SHIFTED_SYMBOLS = (
    "LY_SYS", "LY_BDOS", "LY_EXT", "LY_DISK", "LY_BIOS", "LY_FILE",
    "LY_TAB", "LY_RSTA", "LY_DIR", "LY_BUF", "LY_CFG", "LY_CPX",
    "LY_RSSEL",
    "LY_LIMIT", "LY_RAMEND", "LY_HIST", "LY_TPA",
)


def table(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="ascii") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def shift_layout(path: Path, delta: int) -> None:
    text = path.read_text(encoding="ascii")
    for symbol in SHIFTED_SYMBOLS:
        pattern = rf"^({symbol}\s+EQU\s+)0([0-9A-F]+)H(.*)$"

        def replace(match: re.Match[str]) -> str:
            value = int(match.group(2), 16) + delta
            return f"{match.group(1)}0{value:04X}H{match.group(3)}"

        text, count = re.subn(pattern, replace, text, count=1,
                              flags=re.MULTILINE)
        if count != 1:
            raise ValueError(f"could not shift exactly one {symbol} definition")
    path.write_text(text, encoding="ascii")


def alternate_build(delta: int) -> dict[str, bytes]:
    with tempfile.TemporaryDirectory(prefix=f"bettercpm-rom-ref-{delta:03x}-") as temporary:
        clone = Path(temporary) / "BetterCPM"
        shutil.copytree(
            ROOT, clone,
            ignore=shutil.ignore_patterns(".git", "build", "__pycache__", "*.pyc"))
        shift_layout(clone / "src/system/layout.inc", delta)
        output = clone / "alternate"
        result = subprocess.run(
            [sys.executable, str(clone / "tools/build_z80pack_image.py"),
             "--resident-only", "--output", str(output)],
            cwd=clone, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        if result.returncode:
            tail = "\n".join(result.stdout.splitlines()[-30:])
            raise RuntimeError(
                f"shifted resident build +{delta:04X}h failed:\n{tail}")
        return {
            "gateway": (output / "gateway.bin").read_bytes(),
            "bdos": (clone / "build/bdos/bdos.bin").read_bytes(),
            "extensions": (output / "extensions.bin").read_bytes(),
            "disk": (output / "disk.bin").read_bytes(),
            "bios": (output / "bios.bin").read_bytes(),
            "fileloader": (clone / "build/system/fileloader.bin").read_bytes(),
            "tables": (output / "tables.bin").read_bytes(),
        }


def relocation_offsets(linked: bytes,
                       alternates: list[tuple[bytes, int]], name: str) -> list[int]:
    if any(len(linked) != len(image) for image, _delta in alternates):
        raise ValueError(f"{name}: shifted-layout size changed")
    changed = {
        index
        for image, _delta in alternates
        for index, pair in enumerate(zip(linked, image))
        if pair[0] != pair[1]
    }
    candidates = []
    for offset in range(len(linked) - 1):
        old = int.from_bytes(linked[offset:offset + 2], "little")
        covered = changed.intersection((offset, offset + 1))
        if covered and all(
            (old + delta) & 0xFFFF ==
            int.from_bytes(image[offset:offset + 2], "little")
            for image, delta in alternates
        ):
            candidates.append((offset, covered))
    selected = []
    uncovered = set(changed)
    while uncovered:
        useful = [(len(covered & uncovered), -offset, offset, covered)
                  for offset, covered in candidates if covered & uncovered]
        if not useful:
            sample = ", ".join(f"{index:04X}" for index in sorted(uncovered)[:16])
            raise ValueError(f"{name}: unexplained shifted bytes at {sample}")
        _score, _order, offset, covered = max(useful)
        selected.append(offset)
        uncovered -= covered
    selected.sort()
    for alternate, delta in alternates:
        reproduced = bytearray(linked)
        for offset in selected:
            value = int.from_bytes(reproduced[offset:offset + 2], "little")
            reproduced[offset:offset + 2] = (
                (value + delta) & 0xFFFF).to_bytes(2, "little")
        if bytes(reproduced) != alternate:
            raise ValueError(f"{name}: discovered words do not reproduce shifted build")
    return selected


def packed_address(manifest: dict[str, object], component: str,
                   source: int) -> int | None:
    item = next(row for row in manifest["components"] if row["name"] == component)
    for fragment in item["fragments"]:
        if (fragment["source_start"] <= source and
                source + 2 <= fragment["source_end"]):
            return fragment["rom_start"] + source - fragment["source_start"]
    return None


def live_target_ranges() -> list[dict[str, object]]:
    placement = table(RAM_MAP)
    by_owner = {
        row["source_object"]: row for row in placement
        if row["kind"] == "object"
    }
    ranges: list[dict[str, object]] = []
    for row in table(OWNERSHIP):
        if row["platform"] not in ("all", "z80pack"):
            continue
        if row["disposition"] not in (
                "relocate to ROM-profile RAM", "retain in ROM-profile RAM"):
            continue
        placed = by_owner[row["object"]]
        ranges.append({
            "start": int(row["current_start"], 16),
            "end": int(row["current_end"], 16) + 1,
            "new": int(placed["ram_start"], 16),
            "owner": row["object"],
        })
    # Explicit template sources are live RAM objects even when their constant
    # source bytes also appear in the immutable packing input.
    for row in placement:
        if row["template_start"] == "none":
            continue
        start = int(row["template_start"], 16)
        ranges.append({
            "start": start,
            "end": start + int(row["bytes"]),
            "new": int(row["ram_start"], 16),
            "owner": row["entry"],
        })
    return ranges


def stack_top_target(target: int, source: str) -> tuple[str, int, list[str]] | None:
    if "STKTOP" not in source.upper():
        return None
    placement = {
        row["source_object"]: row for row in table(RAM_MAP)
        if row["kind"] == "object"
    }
    matches = []
    for row in table(OWNERSHIP):
        if row["platform"] not in ("all", "z80pack"):
            continue
        if row["storage_class"] != "stack":
            continue
        if target != int(row["current_end"], 16) + 1:
            continue
        placed = placement[row["object"]]
        matches.append((int(placed["ram_end"], 16) + 1, row["object"]))
    destinations = {address for address, _owner in matches}
    if len(destinations) != 1:
        raise ValueError(f"stack top {target:04X}h does not resolve uniquely")
    address = next(iter(destinations))
    return "live-ram", address, sorted(owner for _address, owner in matches)


def resolve_target(manifest: dict[str, object], target: int, source: str,
                   live: list[dict[str, object]]) -> tuple[str, int, list[str]]:
    stack = stack_top_target(target, source)
    if stack is not None:
        return stack
    matches: list[tuple[str, int, str]] = []
    for row in live:
        if row["start"] <= target < row["end"]:
            matches.append(("live-ram", row["new"] + target - row["start"],
                            str(row["owner"])))
    # A declared live template is authoritative over its packed source copy.
    if not matches:
        for component in manifest["components"]:
            for fragment in component["fragments"]:
                if fragment["source_start"] <= target < fragment["source_end"]:
                    matches.append((
                        "immutable-rom",
                        fragment["rom_start"] + target - fragment["source_start"],
                        str(component["name"])))
    destinations = {(kind, address) for kind, address, _owner in matches}
    if len(destinations) != 1:
        rendered = ", ".join(
            f"{kind}:{address:04X}h/{owner}" for kind, address, owner in matches)
        raise ValueError(
            f"target {target:04X}h has {len(destinations)} destinations: {rendered}")
    kind, address = next(iter(destinations))
    owners = sorted({owner for match_kind, match_address, owner in matches
                     if (match_kind, match_address) == (kind, address)})
    return kind, address, owners


def listing_context(path: Path, address: int) -> dict[str, object]:
    pattern = re.compile(
        r"^([0-9A-Fa-f]{4})\s+((?:[0-9A-Fa-f]{2}\s+)+)"
        r"(\d+)\s+(\d+)(?:\s+(.*))?$")
    contexts: dict[int, str] = {}
    for raw in path.read_text(encoding="ascii", errors="replace").splitlines():
        match = pattern.match(raw)
        if not match:
            continue
        source_line = int(match.group(3))
        source = (match.group(5) or "").strip()
        if source:
            contexts[source_line] = source
        start = int(match.group(1), 16)
        emitted = re.findall(r"[0-9A-Fa-f]{2}", match.group(2))
        if start <= address < start + len(emitted):
            try:
                listing = str(path.relative_to(ROOT))
            except ValueError:
                listing = path.name
            return {
                "listing": listing,
                "source_line": source_line,
                "source": source or contexts.get(source_line, "continuation data"),
            }
    raise ValueError(f"{path.name}: no listing context for {address:04X}h")


def build(z80pack_build: Path, pack: Path, output: Path) -> dict[str, object]:
    manifest = json.loads((pack / "rom-pack.json").read_text(encoding="ascii"))
    baseline = {
        name: {"base": base, "path": path, "data": path.read_bytes()}
        for name, base, path in component_inputs(z80pack_build)
    }
    listings = {
        "gateway": z80pack_build / "gateway.lst",
        "bdos": ROOT / "build/bdos/bdos.lst",
        "extensions": z80pack_build / "extensions.lst",
        "disk": z80pack_build / "disk.lst",
        "bios": z80pack_build / "bios.lst",
        "fileloader": ROOT / "build/system/fileloader.lst",
        "tables": z80pack_build / "tables.lst",
    }
    shifted = [(alternate_build(delta), delta) for delta in DELTAS]
    live = live_target_ranges()
    references = []
    discovered_counts = {}
    ignored_mutable_counts = {}
    for name, item in baseline.items():
        alternates = [(images[name], delta) for images, delta in shifted]
        offsets = relocation_offsets(item["data"], alternates, name)
        discovered_counts[name] = len(offsets)
        ignored = 0
        for offset in offsets:
            source = item["base"] + offset
            packed = packed_address(manifest, name, source)
            if packed is None:
                ignored += 1
                continue
            target = int.from_bytes(item["data"][offset:offset + 2], "little")
            context = listing_context(listings[name], source)
            kind, destination, owners = resolve_target(
                manifest, target, str(context["source"]), live)
            references.append({
                "component": name,
                "source_operand": source,
                "source_offset": offset,
                "packed_operand": packed,
                "old_target": target,
                "new_target": destination,
                "target_class": kind,
                "target_owners": owners,
                **context,
            })
        ignored_mutable_counts[name] = ignored
    counts = Counter(row["component"] for row in references)
    classes = Counter(row["target_class"] for row in references)
    result: dict[str, object] = {
        "method": "dual shifted-layout comparison",
        "layout_deltas": list(DELTAS),
        "fixed_ram_symbols": ["LY_RSX", "LY_LOAD", "LY_STKL", "LY_STKT", "LY_SECTS"],
        "discovered_word_counts": discovered_counts,
        "ignored_mutable_operand_counts": ignored_mutable_counts,
        "reference_counts": {name: counts[name] for name in baseline},
        "target_class_counts": dict(sorted(classes.items())),
        "reference_count": len(references),
        "unexplained_changed_bytes": 0,
        "unresolved_targets": 0,
        "references": references,
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="ascii")
    print("ROM reference inventory: " + ", ".join(
        f"{name} {counts[name]}" for name in baseline) +
        f"; total {len(references)}; all targets resolved")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--z80pack-build", type=Path, required=True)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.z80pack_build.resolve(), args.pack.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
