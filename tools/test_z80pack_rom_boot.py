#!/usr/bin/env python3
"""Boot the integrated z80pack ROM profile through its relocated cold path."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", type=Path,
                        default=ROOT / "build/z80pack")
    parser.add_argument("--simulator", type=Path,
                        default=Path.home() / "projects/git/z80pack/cpmsim/cpmsim")
    parser.add_argument("--rom-start")
    args = parser.parse_args()
    image = args.image_dir.resolve()
    manifest = json.loads(
        (image / "rom/rom-boot.json").read_text(encoding="ascii"))
    if (manifest["boot_integrated"] is not True or
            manifest["protected_xip_qualified"] is not False):
        raise AssertionError("ROM boot manifest overclaims or omits boot status")
    if (manifest["entry"] != 0xFD77 or manifest["stub_bytes"] != 34 or
            manifest["reloader_reference_count"] != 43 or
            manifest["ccp_external_reference_count"] != 63 or
            manifest["spare_bytes"] != 615):
        raise AssertionError("accepted ROM boot layout changed")

    with tempfile.TemporaryDirectory(prefix="bettercpm-rom-boot-") as temporary:
        work = Path(temporary)
        shutil.copytree(image / "rom-disks", work / "disks",
                        symlinks=False)
        report = work / "verification.txt"
        script = r'''set timeout 25
set send_slow {1 .02}
log_file -noappend [lindex $argv 3]
expect_before timeout {puts "ROM BOOT TIMEOUT"; exit 1}
proc prompt {} {
 expect {
  -exact {A0>} {}
  timeout {puts "ROM PROMPT TIMEOUT"; exit 1}
  eof {puts "ROM UNEXPECTED EXIT"; exit 1}
 }
}
spawn [lindex $argv 0] -z -x [lindex $argv 1] -d [lindex $argv 2]
if {[lindex $argv 4] ne ""} {
 expect -exact "ROM QUALIFICATION ACTIVE START=[lindex $argv 4] END=FFFF"
}
prompt
send -s -- "DIR\r"
expect -exact "RCP"
prompt
send -s -- "HELLO\r"
expect -exact "BetterCP/M on z80pack"
prompt
send -s -- "BYE\r"
expect eof
'''
        test = work / "test.exp"
        test.write_text(script, encoding="ascii")
        simulator = args.simulator.expanduser().resolve()
        env = dict(os.environ)
        env["PATH"] = str(simulator.parent / "srctools") + os.pathsep + env["PATH"]
        if args.rom_start:
            env["CPMSIM_ROM_START"] = args.rom_start
        else:
            env.pop("CPMSIM_ROM_START", None)
        run = subprocess.run(
            ["expect", str(test), str(simulator),
             str(image / "rom/rom-boot.hex"), str(work / "disks"), str(report),
             args.rom_start or ""],
            cwd=work, env=env, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=90)
        if run.returncode:
            detail = report.read_text(errors="replace")[-1800:] if report.exists() else run.stdout[-1800:]
            raise AssertionError(f"ROM boot failed:\n{detail}")
    protected = f" under enforced {args.rom_start}h protection" if args.rom_start else ""
    print("ROM cold entry verified" + protected + ": RAM initialized, relocated "
          "BIOS BOOT entered, relocated disk reloader reached A0>, DIR and "
          "transient execution passed")


if __name__ == "__main__":
    main()
