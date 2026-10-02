#!/usr/bin/env python3
"""Qualify CONFIG's native read-only BCST panel on protected media."""
from __future__ import annotations

import shutil
from pathlib import Path

from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build
from run_trs80_command import DEFAULT_EMULATOR, key_args
from startup_record import build as startup_record
from system_layout import LAYOUT
from test_disk_utilities import ROOT, medium
from trs80gp_launch import run as run_trs80gp

OUT = ROOT / "build/test-results/config-startup-read"


def screen(path: Path) -> str:
    raw = path.read_bytes()[:1920]
    return "\n".join(bytes(c & 127 for c in raw[i:i + 80]).decode("ascii").rstrip()
                     for i in range(0, 1920, 80))


def run_case(name: str, image: bytes, expected: str) -> None:
    work = OUT / name
    work.mkdir()
    disk = work / "a.dmk"
    disk.write_bytes(image)
    args = [str(DEFAULT_EMULATOR), "-m4", "-batch", "-turbo", "-d0", str(disk),
            "-id", "2500"]
    args += key_args("CONFIG\r") + ["-id", "2000"]
    args += key_args("J") + ["-id", "2000", "-it", "-ix"]
    run_trs80gp(args, cwd=work, check=True, timeout=35)
    text = screen(work / "trs80-text-0.bin")
    assert expected in text, text


def main() -> None:
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)
    image = medium()
    run_case("disabled", image, "Saved startup command: disabled.")

    enabled = extract_raw(image)
    enabled[128:384] = startup_record("VER", system_base=LAYOUT["SYSTEM"])
    run_case("enabled", build(bytes(enabled)), "Saved startup command: VER")

    invalid = extract_raw(image)
    invalid[128 + 12] ^= 1
    run_case("invalid", build(bytes(invalid)),
             "Saved startup command record is invalid.")
    print("PASS: CONFIG reads disabled, enabled and invalid BCST records")


if __name__ == "__main__":
    main()
