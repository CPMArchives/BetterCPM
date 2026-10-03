#!/usr/bin/env python3
"""Boot the integrated z80pack ROM profile through its relocated cold path."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from system_layout import LAYOUT

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", type=Path,
                        default=ROOT / "build/z80pack")
    parser.add_argument("--simulator", type=Path,
                        default=Path.home() / "projects/git/z80pack/cpmsim/cpmsim")
    parser.add_argument("--rom-start")
    parser.add_argument("--stack-report", type=Path)
    args = parser.parse_args()
    image = args.image_dir.resolve()
    manifest = json.loads(
        (image / "rom/rom-boot.json").read_text(encoding="ascii"))
    if (manifest["boot_integrated"] is not True or
            manifest["protected_xip_qualified"] is not False):
        raise AssertionError("ROM boot manifest overclaims or omits boot status")
    if (manifest["entry"] != 0xFD77 or manifest["stub_bytes"] != 34 or
            manifest["reloader_reference_count"] != 43 or
            manifest["ccp_external_reference_count"] != 81 or
            manifest["spare_bytes"] != 615):
        raise AssertionError("accepted ROM boot layout changed")
    config_report = json.loads(
        (image / "rom/rom-config.json").read_text(encoding="ascii"))
    config_image = (image / "rom/rom-config.bin").read_bytes()
    config_source = (image / "config.bin").read_bytes()
    references = config_report["references"]
    if (config_report["bytes"] != 907 or
            config_report["relocation_words"] != len(references) or
            hashlib.sha256(config_source).hexdigest() !=
            config_report["source_sha256"] or
            hashlib.sha256(config_image).hexdigest() != config_report["sha256"]):
        raise AssertionError("ROM CONFIG relocation manifest changed")
    reproduced = bytearray(config_source)
    seen: set[int] = set()
    for reference in references:
        offset = reference["overlay_operand"]
        if offset in seen or offset + 1 in seen:
            raise AssertionError("ROM CONFIG relocation operands overlap")
        seen.update((offset, offset + 1))
        if int.from_bytes(config_source[offset:offset + 2], "little") != \
                reference["old_target"]:
            raise AssertionError("ROM CONFIG source operand changed")
        reproduced[offset:offset + 2] = \
            reference["new_target"].to_bytes(2, "little")
    if bytes(reproduced) != config_image:
        raise AssertionError("ROM CONFIG relocation is not reproducible")

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
send -s -- "WARM\r"
prompt
send -s -- "DIR\r"
expect -exact "RCP"
prompt
send -s -- "CPX LIST\r"
expect -exact "RCP.CPX"
expect -exact "TPA available: 53K"
prompt
send -s -- "CPX LOAD HELLO\r"
prompt
send -s -- "CPX LIST\r"
expect -exact "RCP.CPX"
expect -exact "HELLO.CPX"
prompt
send -s -- "HELLO\r"
expect -exact "Hello from HELLO.CPX"
prompt
send -s -- "WARM\r"
prompt
send -s -- "HELLO\r"
expect -exact "Hello from HELLO.CPX"
prompt
send -s -- "CPX UNLOAD RCP\r"
prompt
send -s -- "HELLO\r"
expect -exact "Hello from HELLO.CPX"
prompt
send -s -- "CPX UNLOAD HELLO\r"
prompt
send -s -- "CPX LIST\r"
expect -exact "No CPXs loaded"
expect -exact "TPA available: 53K"
prompt
send -s -- "HELLO\r"
expect -exact "BetterCP/M on z80pack"
prompt
send -s -- "RSX LOAD ECHO\r"
prompt
send -s -- "RSX LIST\r"
expect -exact "ECHO : BDOS 199"
expect -exact "TPA available: 51K"
prompt
send -s -- "RSX UNLOAD ECHO\r"
prompt
send -s -- "RSX LIST\r"
expect -exact "No RSXs loaded"
expect -exact "TPA available: 53K"
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
        if args.stack_report:
            if not args.rom_start:
                raise AssertionError("stack measurement requires protected ROM mode")
            transcript = report.read_text(errors="replace")
            pattern = re.compile(
                r"ROM STACK HIGH-WATER NAME=(\w+) LOW=([0-9A-F]{4}) "
                r"TOP=([0-9A-F]{4}) USED=(\d+) CAPACITY=(\d+) MARGIN=(\d+)")
            stacks = {
                match.group(1): {
                    "low": int(match.group(2), 16),
                    "top": int(match.group(3), 16),
                    "used": int(match.group(4)),
                    "capacity": int(match.group(5)),
                    "margin": int(match.group(6)),
                }
                for match in pattern.finditer(transcript)
            }
            expected = {
                "loader": (LAYOUT["STACK_LOW"], LAYOUT["STACK_TOP"],
                           LAYOUT["STACK_TOP"] - LAYOUT["STACK_LOW"]),
                "system": (0xD618, 0xD638, 32),
                "bdos": (0xD701, 0xD729, 40),
            }
            if set(stacks) != set(expected):
                raise AssertionError(f"incomplete stack measurement: {stacks}")
            for name, (low, top, capacity) in expected.items():
                measured = stacks[name]
                if (measured["low"], measured["top"], measured["capacity"]) != (
                        low, top, capacity):
                    raise AssertionError(f"{name} stack layout changed: {measured}")
                if measured["used"] <= 0 or measured["margin"] < 8:
                    raise AssertionError(f"{name} stack lacks measured reserve: {measured}")
            args.stack_report.write_text(
                json.dumps({"stacks": stacks}, indent=2, sort_keys=True) + "\n",
                encoding="ascii")
    protected = f" under enforced {args.rom_start}h protection" if args.rom_start else ""
    print("ROM cold entry verified" + protected + ": RAM initialized, relocated "
          "BIOS BOOT entered, relocated disk reloader reached A0>, DIR, "
          "transient execution, CPX load/list/reconstruction/unload, and "
          "dynamic RSX load/list/unload passed")


if __name__ == "__main__":
    main()
