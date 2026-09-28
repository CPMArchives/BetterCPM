#!/usr/bin/env python3
"""Prove the accepted z80pack ROM workspace layout and its exclusive lifetimes."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAM_MAP = ROOT / "metadata/rom-profile-ram-z80pack.tsv"
RECORD_IO = ROOT / "src/platform/z80pack/recordio.inc"
FILE_LOADER = ROOT / "src/system/fileload.mac"
CONFIG_OVERLAY = ROOT / "src/bios/config.mac"
Z80PACK_CONFIG = ROOT / "src/platform/z80pack/config.mac"
DISK_TABLES = ROOT / "src/bios/tables.mac"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="ascii") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def require_source(path: Path, fragments: tuple[str, ...]) -> None:
    text = path.read_text(encoding="ascii")
    missing = [fragment for fragment in fragments if fragment not in text]
    if missing:
        raise AssertionError(f"{path.relative_to(ROOT)} lost workspace contract: {missing}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", type=Path,
                        default=ROOT / "build/z80pack")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    image = args.image_dir.resolve()
    report_path = args.report or image / "rom/rom-workspace-lifetimes.json"

    placement = {row["entry"]: row for row in rows(RAM_MAP)}
    lower = placement["physical-sector-buffer"]
    upper = placement["module-config-buffer"]
    lower_start = int(lower["ram_start"], 16)
    lower_end = int(lower["ram_end"], 16) + 1
    upper_start = int(upper["ram_start"], 16)
    upper_end = int(upper["ram_end"], 16) + 1
    if (int(lower["bytes"]), int(upper["bytes"])) != (512, 512):
        raise AssertionError("workspace halves must remain 512 bytes each")
    if lower_end != upper_start or upper_end - lower_start != 1024:
        raise AssertionError("workspace must remain one contiguous 1,024-byte area")

    config_bytes = (image / "config.bin").stat().st_size
    if not 512 < config_bytes <= 1024:
        raise AssertionError(
            f"CONFIG overlay is {config_bytes} bytes; expected >512 and <=1024")

    require_source(RECORD_IO, (
        "CP      3", "LD      HL,LY_BUF", "LD      HL,LY_BUF+512",
        "A full 1024-byte sector necessarily consumes the complete shared buffer.",
    ))
    require_source(FILE_LOADER, (
        "FL_REOPEN:", "LD A,1", "LD (FL_FCB),A",
    ))
    require_source(DISK_TABLES, (
        "DPH0:", "DB 80,10,2,0E0H",
    ))
    require_source(Z80PACK_CONFIG, (
        "JP Z,ZC_UNSUP                   ; A: remains the fixed bootstrap filesystem",
    ))
    require_source(CONFIG_OVERLAY, (
        "executed from the idle physical-sector buffer",
        "must avoid any", "filesystem sector read",
    ))

    reloader = json.loads(
        (image / "rom/rom-reloader.json").read_text(encoding="ascii"))
    reloader_pairs = {
        (reference["old_target"], reference["new_target"])
        for reference in reloader["references"]
    }
    if (0xF000, lower_start) not in reloader_pairs:
        raise AssertionError("reloader does not map MODBUF to lower workspace")
    if (0xF200, upper_start) not in reloader_pairs:
        raise AssertionError("reloader does not map MODBUF+0200h to upper workspace")

    resident = json.loads(
        (image / "rom/rom-references.json").read_text(encoding="ascii"))
    bios_pairs = {
        (reference["old_target"], reference["new_target"])
        for reference in resident["references"]
        if reference["component"] == "bios"
    }
    if (0xF000, lower_start) not in bios_pairs:
        raise AssertionError("BIOS does not map LY_BUF to lower workspace")
    if (0xF200, upper_start) not in bios_pairs:
        raise AssertionError("BIOS does not map LY_BUF+512 to upper workspace")

    report = {
        "workspace_start": lower_start,
        "workspace_end_exclusive": upper_end,
        "workspace_bytes": upper_end - lower_start,
        "lower_bytes": 512,
        "upper_bytes": 512,
        "config_overlay_bytes": config_bytes,
        "maximum_physical_sector_bytes": 1024,
        "reduction_permitted": False,
        "lifetimes": {
            "physical_sector_1024": "exclusive full workspace",
            "carrier_reconstruction": (
                "lower module block plus upper fixed-A 512-byte sector staging"),
            "config_control_overlay": "exclusive full workspace while disk I/O is idle",
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"ROM workspace: {upper_end - lower_start} bytes retained; "
          f"{config_bytes}-byte CONFIG overlay and three lifetime classes verified")


if __name__ == "__main__":
    main()
