#!/usr/bin/env python3
"""Qualify the integrated BetterCP/M ROM under the locked cpmsim guard."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from test_cpmsim_rom_guard import (
    ROM_START, build_guarded_simulator, prove_guard_primitives,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", type=Path,
                        default=ROOT / "build/z80pack")
    parser.add_argument("--z80pack-source", type=Path,
                        default=Path.home() / "projects/git/z80pack")
    args = parser.parse_args()
    image = args.image_dir.resolve()
    source = args.z80pack_source.expanduser().resolve()
    manifest_path = image / "rom/rom-boot.json"
    manifest = json.loads(manifest_path.read_text(encoding="ascii"))
    payload = (image / "rom/rom-boot.bin").read_bytes()
    if hashlib.sha256(payload).hexdigest() != manifest["sha256"]:
        raise AssertionError("ROM boot payload does not match its manifest")
    if manifest["base"] != int(ROM_START, 16):
        raise AssertionError("guard boundary does not match the ROM image base")
    overlays_path = image / "rom/rsx-overlays/rom-rsx-overlays.json"
    overlays = json.loads(overlays_path.read_text(encoding="ascii"))
    if (overlays["file_count"] != 18 or overlays["reference_count"] != 704 or
            overlays["unresolved_targets"] != 0):
        raise AssertionError("ROM RSX-overlay relocation inventory changed")
    for name, entry in overlays["files"].items():
        artifact = (image / "rom/rsx-overlays" / name).read_bytes()
        if hashlib.sha256(artifact).hexdigest() != entry["sha256"]:
            raise AssertionError(f"{name}: relocated artifact hash mismatch")
    selector_gateway = [
        row for row in overlays["files"]["RSXSEL.BIN"]["references"]
        if row["old_target"] == 0xF07D
    ]
    if (len(selector_gateway) != 1 or
            selector_gateway[0]["new_target"] != 0xDAEA or
            selector_gateway[0]["target_class"] != "live-ram"):
        raise AssertionError("ROM RSX selector retained its conventional gateway")

    with tempfile.TemporaryDirectory(prefix="bettercpm-rom-xip-") as temporary:
        work = Path(temporary)
        simulator = build_guarded_simulator(source, work)
        prove_guard_primitives(simulator, work)
        stack_report = image / "rom/rom-stack-qualification.json"
        subprocess.run([
            sys.executable, str(ROOT / "tools/test_z80pack_rom_boot.py"),
            "--image-dir", str(image), "--simulator", str(simulator),
            "--rom-start", ROM_START, "--stack-report", str(stack_report),
        ], cwd=ROOT, check=True)
        workspace_report = image / "rom/rom-workspace-lifetimes.json"
        subprocess.run([
            sys.executable, str(ROOT / "tools/test_rom_workspace_lifetimes.py"),
            "--image-dir", str(image), "--report", str(workspace_report),
        ], cwd=ROOT, check=True)
    stacks = json.loads(stack_report.read_text(encoding="ascii"))["stacks"]
    workspace = json.loads(workspace_report.read_text(encoding="ascii"))

    report = {
        "boundary": int(ROM_START, 16),
        "image_sha256": manifest["sha256"],
        "boot_integrated": True,
        "protected_xip_qualified": True,
        "cpu_write_rejected": True,
        "dma_write_rejected": True,
        "control_change_rejected": True,
        "cpx_load_list_reconstruct_unload_qualified": True,
        "rsx_load_list_unload_qualified": True,
        "rsx_overlay_file_count": overlays["file_count"],
        "rsx_overlay_reference_count": overlays["reference_count"],
        "rsx_overlay_manifest_sha256": hashlib.sha256(
            overlays_path.read_bytes()).hexdigest(),
        "stacks": stacks,
        "workspace": workspace,
    }
    (image / "rom/rom-xip-qualification.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print("PASS: BetterCP/M executes in place at DF00h with locked CPU and DMA "
          "write protection")


if __name__ == "__main__":
    main()
