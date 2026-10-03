#!/usr/bin/env python3
"""Qualify CONFIG's combined active-plus-pending save transaction."""
from __future__ import annotations

import shutil
from pathlib import Path

from add_cpm_file_to_dmk import extract_raw
from run_trs80_command import DEFAULT_EMULATOR, key_args
from startup_record import build as startup_record
from system_layout import LAYOUT
from test_config_sysgen import logical, probe
from test_disk_utilities import ROOT, medium
from trs80gp_launch import run as run_trs80gp


OUT = ROOT / "build/test-results/config-save-all"


def screen(path: Path) -> str:
    raw = path.read_bytes()[:1920]
    return "\n".join(bytes(c & 127 for c in raw[i:i + 80]).decode("ascii").rstrip()
                     for i in range(0, 1920, 80))


def execute(name: str, image: bytes, actions: tuple[str, ...], delay: int = 2000) -> tuple[bytes, str]:
    work = OUT / name
    work.mkdir()
    disk = work / "a.dmk"
    disk.write_bytes(image)
    args = [str(DEFAULT_EMULATOR), "-m4", "-batch", "-turbo", "-d0", str(disk),
            "-id", "2500"]
    for action in actions:
        args += key_args(action) + ["-id", str(delay)]
    args += ["-it", "-ix"]
    run_trs80gp(args, cwd=work, check=True, timeout=40)
    return disk.read_bytes(), screen(work / "trs80-text-0.bin")


def main() -> None:
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)
    setup = probe(OUT)
    check = probe(OUT, check=True)
    original = medium((("SETUP.COM", setup), ("CHECK.COM", check)))
    actions = ("SETUP\r", "\r", "CONFIG\r", "J", "E", "VER\r", "\x03",
               "H", "B", "Y")
    saved, text = execute("save", original, actions)
    assert "All current settings saved and verified." in text, text
    before = logical(original)
    after = logical(saved)
    resident = (ROOT / "build/system/resident.bin").read_bytes()
    signature = resident.index(b"BDCF" + bytes((5, 4, 4, 64)))
    physical = int.from_bytes(resident[signature + 8:signature + 10], "little")
    table = int.from_bytes(resident[signature + 10:signature + 12], "little")
    base = 8 * 128 - LAYOUT["SYSTEM"]
    allowed = set(range(128, 384))
    allowed.update(range(base + physical, base + physical + 24))
    for number in range(4):
        allowed.update(range(base + table + number * 80 + 16,
                             base + table + number * 80 + 80))
    changed = {index for index, (old, new) in enumerate(zip(before, after))
               if old != new}
    assert changed <= allowed, changed - allowed
    assert after[128:384] == startup_record("VER", system_base=LAYOUT["SYSTEM"])

    _checked, text = execute("cold-check", saved, ("CHECK\r", "\r"))
    assert "SYSGEN PROBE PASS" in text, text
    _viewed, text = execute("cold-view", saved, ("CONFIG\r", "J"))
    assert "Pending startup command: VER" in text, text

    fault_setup = probe(OUT, fault=True)
    fault_image = medium((("SETUP.COM", fault_setup),))
    restored, text = execute("rollback", fault_image, actions)
    assert "Save failed. Original configuration restored." in text, text
    assert logical(restored) == logical(fault_image), "rollback changed protected media"
    print("PASS: all-current save merges active and pending state and rolls back")


if __name__ == "__main__":
    main()
