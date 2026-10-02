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


def run_case(name: str, image: bytes, expected: tuple[str, ...],
             actions: tuple[str, ...] = (), final_delay: int = 2000) -> None:
    work = OUT / name
    work.mkdir()
    disk = work / "a.dmk"
    disk.write_bytes(image)
    original_record = extract_raw(image)[128:384]
    args = [str(DEFAULT_EMULATOR), "-m4", "-batch", "-turbo", "-d0", str(disk),
            "-id", "2500"]
    args += key_args("CONFIG\r") + ["-id", "2000"]
    args += key_args("J") + ["-id", "2000", "-it", "-ix"]
    if actions:
        args = args[:-2]
        for index, action in enumerate(actions):
            delay = final_delay if index == len(actions) - 1 else 2000
            args += key_args(action) + ["-id", str(delay)]
        args += ["-it", "-ix"]
    run_trs80gp(args, cwd=work, check=True, timeout=35)
    text = screen(work / "trs80-text-0.bin")
    for phrase in expected:
        assert phrase in text, text
    assert extract_raw(disk.read_bytes())[128:384] == original_record, \
        "pending command edit changed protected media"


def main() -> None:
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)
    image = medium()
    run_case("disabled", image, ("Pending startup command: disabled.",))

    enabled = extract_raw(image)
    enabled[128:384] = startup_record("VER", system_base=LAYOUT["SYSTEM"])
    enabled_image = build(bytes(enabled))
    run_case("enabled", enabled_image, ("Pending startup command: VER",))

    invalid = extract_raw(image)
    invalid[128 + 12] ^= 1
    run_case("invalid", build(bytes(invalid)),
             ("Saved startup command record is invalid.",))

    run_case("edit", image,
             ("Pending startup command has not been saved.",
              "Pending startup command: VER"),
             ("E", "VER\r", "\x03", "J"))
    run_case("clear", enabled_image,
             ("Pending startup command has not been saved.",
              "Pending startup command: disabled."),
             ("C",))
    run_case("test-disabled", image,
             ("There is no pending startup command to test.",),
             ("T",))
    run_case("test-now", image, ("BetterCP/M 0.3",),
             ("E", "VER\r", "T"), final_delay=5000)

    maximum = extract_raw(image)
    maximum[128:384] = startup_record("A" * 126,
                                      system_base=LAYOUT["SYSTEM"])
    run_case("test-126", build(bytes(maximum)),
             ("A 126-byte command can run at cold boot but cannot use Test now.",),
             ("T",))
    print("PASS: CONFIG reads, edits, clears and immediately tests pending BCST records")


if __name__ == "__main__":
    main()
