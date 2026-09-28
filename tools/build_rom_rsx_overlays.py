#!/usr/bin/env python3
"""Relocate file-backed RSX transaction overlays for the z80pack ROM map."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from build_rom_reference_inventory import (
    DELTAS, live_target_ranges, relocation_offsets, resolve_target, shift_layout,
)
from build_ccp import assemble
from system_layout import LAYOUT

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build/system"
CFG_FILES = {
    "R3PLAN.RSX", "R3SLOTS.RSX", "R3SNAP.RSX", "R3CARR.RSX",
    "R3META.RSX", "R3MOVE.RSX",
}
RSX_FILES = {
    "R3COORD.RSX", "R3PROF.RSX", "R3KCTX.RSX", "R3KEEP.RSX",
    "R3KPRE.RSX", "R3FINAL.RSX", "R3DROP.RSX", "R3COMIT.RSX",
    "R3RESOL.RSX",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def artifact_paths(root: Path) -> dict[str, Path]:
    build = root / "build/system"
    result = {
        "RSXLOAD.BIN": build / "rsxloader.bin",
        "RSXRESOL.BIN": build / "rsxresolver.bin",
    }
    for name in sorted(CFG_FILES | RSX_FILES):
        result[name] = build / name
    return result


def selector_source(root: Path) -> str:
    text = (root / "src/platform/z80pack/rsxsel.mac").read_text(encoding="ascii")
    layout = (root / "src/system/layout.inc").read_text(encoding="ascii").rstrip()
    text = text.replace("        INCLUDE layout.inc", layout)
    order = (1, 3, 5, 7, 9, 2, 4, 6, 8, 10)

    def table(start: int, count: int) -> str:
        return "\n".join(
            f"        DB {number // 20},{number // 10 % 2},{order[number % 10]}"
            for number in range(start, start + count))

    sectors = LAYOUT["BOOT_SECTORS"]
    return text.replace("; @rsx-sector-table@", table(6 + sectors, 2)).replace(
        "; @rsx-validator-sector-table@", table(8 + sectors, 2)).replace(
        "; @rsx-publisher-sector-table@", table(10 + sectors, 2)).replace(
        "; @rsx-resolver-sector-table@", table(12 + sectors, 2)).replace(
        "        CSEG\n        .PHASE  ", "        ASEG\n        ORG     ").replace(
        "        .DEPHASE\n", "")


def alternate_build(delta: int, assembler: Path) -> dict[str, bytes]:
    with tempfile.TemporaryDirectory(
            prefix=f"bettercpm-rom-rsx-{delta:03x}-") as temporary:
        clone = Path(temporary) / "BetterCPM"
        shutil.copytree(
            ROOT, clone,
            ignore=shutil.ignore_patterns(".git", "build", "__pycache__", "*.pyc"))
        shift_layout(clone / "src/system/layout.inc", delta)
        for script in ("build_rsxloader.py", "build_rsxresolver.py",
                       "build_rsx_runtime_overlays.py"):
            result = subprocess.run(
                [sys.executable, str(clone / "tools" / script)], cwd=clone,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if result.returncode:
                tail = "\n".join(result.stdout.splitlines()[-30:])
                raise RuntimeError(
                    f"shifted RSX-overlay build +{delta:04X}h failed:\n{tail}")
        result = {name: path.read_bytes()
                  for name, path in artifact_paths(clone).items()}
        selector = clone / "alternate/rsxselect.bin"
        selector.parent.mkdir()
        base = LAYOUT["CONFIG"] + 0x380 + delta
        result["RSXSEL.BIN"] = assemble(
            assembler, selector_source(clone), selector,
            selector.with_suffix(".lst"), base)
        return result


def build(pack: Path, output: Path, selector: Path,
          assembler: Path = Path("/Users/nathanael/bin/z80asm")) -> dict[str, object]:
    manifest = json.loads((pack / "rom-pack.json").read_text(encoding="ascii"))
    placement = {
        row.split("\t")[0]: row.split("\t")
        for row in (ROOT / "metadata/rom-profile-ram-z80pack.tsv").read_text(
            encoding="ascii").splitlines()[1:]
    }
    cfg_base = int(placement["physical-sector-buffer"][3], 16)
    baseline = {name: path.read_bytes()
                for name, path in artifact_paths(ROOT).items()}
    baseline["RSXSEL.BIN"] = selector.read_bytes()
    shifted = [(alternate_build(delta, assembler), delta) for delta in DELTAS]
    live = live_target_ranges()
    output.mkdir(parents=True, exist_ok=True)
    reports: dict[str, object] = {}
    total = 0

    for name, source in baseline.items():
        if name == "RSXSEL.BIN":
            linked_base, runtime_base = (
                LAYOUT["CONFIG"] + 0x380, cfg_base + 0x380)
        else:
            linked_base = LAYOUT["CONFIG"] if name in CFG_FILES else LAYOUT["RSX"]
            runtime_base = cfg_base if name in CFG_FILES else LAYOUT["RSX"]
        alternates = [(images[name], delta) for images, delta in shifted]
        offsets = relocation_offsets(source, alternates, name)
        image = bytearray(source)
        references = []
        occupied: set[int] = set()
        for offset in offsets:
            if occupied.intersection((offset, offset + 1)):
                raise ValueError(f"{name}: overlapping address word at {offset:04X}h")
            occupied.update((offset, offset + 1))
            old = int.from_bytes(source[offset:offset + 2], "little")
            if linked_base <= old < linked_base + len(source):
                kind, new, owners = (
                    "overlay-internal", runtime_base + old - linked_base, [name])
            elif old < LAYOUT["TPA"]:
                kind, new, owners = "transient-ram", old, ["TPA"]
            else:
                kind, new, owners = resolve_target(manifest, old, name, live)
            image[offset:offset + 2] = new.to_bytes(2, "little")
            references.append({
                "offset": offset, "old_target": old, "new_target": new,
                "target_class": kind, "target_owners": owners,
            })
        payload = bytes(image)
        (output / name).write_bytes(payload)
        reports[name] = {
            "linked_base": linked_base, "runtime_base": runtime_base,
            "bytes": len(payload), "sha256": digest(payload),
            "source_sha256": digest(source), "reference_count": len(references),
            "changed_words": sum(
                item["old_target"] != item["new_target"] for item in references),
            "references": references,
        }
        total += len(references)

    result: dict[str, object] = {
        "files": reports, "file_count": len(reports),
        "reference_count": total, "unresolved_targets": 0,
    }
    (output / "rom-rsx-overlays.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"ROM RSX overlays: {len(reports)} files, {total} address words resolved")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--selector", type=Path, required=True)
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    build(args.pack.resolve(), args.output.resolve(), args.selector.resolve(),
          args.assembler.expanduser().resolve())


if __name__ == "__main__":
    main()
