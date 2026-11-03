#!/usr/bin/env python3
"""Build BDOSPROBE under CP/M and test its 8080-compatible dev4 probes."""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "src/BDOSPRB.MAC"
DEFAULT_TOOLS = Path("/Users/nathanael/git/cpm-compatibility/suite/build-tools")
DEFAULT_BOOT = Path("/Users/nathanael/git/cpm-compatibility/suite/disk-images/z80pack/ibm-3740/drivea.dsk")
DEFAULT_SYSTEM = Path("/Users/nathanael/z80pack/cpmsim/disks/library/cpm22-62khd.dsk")
DEFAULT_CPMSIM = Path("/Users/nathanael/z80pack/cpmsim/cpmsim")


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, text=True, capture_output=True)


def blank_disk(template: Path, destination: Path) -> None:
    shutil.copy2(template, destination)
    run("mkfs.cpm", "-f", "ibm-3740", str(destination))


def cpm_text(path: Path) -> bytes:
    text = path.read_text(encoding="ascii").replace("\r\n", "\n").replace("\r", "\n")
    return text.replace("\n", "\r\n").encode("ascii") + b"\x1a"


def session(cpmsim: Path, disks: Path, cpu: str, build: bool) -> subprocess.CompletedProcess[str]:
    preparation = ""
    if build:
        preparation = r'''
send -- "D:ZSM4 B:BDOSPRB=C:BDOSPRB\r"
expect {
    -re {Errors: +0} {}
    -re {Errors: +[1-9][0-9]*} {exit 20}
    timeout {exit 21}
}
expect "B>"
send -- "D:LINK BDOSPRB\[A\]\r"
expect { "CODE SIZE" {} timeout {exit 22} }
expect "B>"
'''
    commands = f'''set timeout 12
spawn {cpmsim} {cpu} -d {disks}
expect "A>"
send -- "B:\\r"
expect "B>"
{preparation}
send -- "BDOSPRB /CPM\\r"
expect "BDOSPROBE 0.1.0-dev4"
expect "BDOS Function 12 - Return Version Number"
expect "C:     0CH"
expect "DE:    0000H"
expect "A:     22H"
expect "HL:    0022H"
expect "Flags:"
expect "SP:"
expect "CP/M 2.2"
expect "B>"
send -- "BDOSPRB /DISK\\r"
expect "BDOS Function 24 - Return Login Vector"
expect "BDOS Function 25 - Return Current Disk"
expect "Current drive: A"
expect "BDOS Function 29 - Get Read-Only Vector"
expect "B>"
send -- "BDOSPRB /MEM\\r"
expect "BDOS Function 27 - Get Allocation Vector Address"
expect "Allocation vector address:"
expect "BDOS Function 31 - Get DPB Address"
expect "DPB address:"
expect "B>"
send -- "BDOSPRB /CONSOLE\\r"
expect "BDOS Function 11 - Console Status"
expect "console character ready."
expect "B>"
send -- "BDOSPRB /USER\\r"
expect "BDOS Function 32 - Get User Number"
expect "DE:    00FFH"
expect "Current user: 0"
expect "Query left user number unchanged."
expect "B>"
send -- "BDOSPRB /SELECT\r"
expect "BDOS Function 14 - Select Disk"
expect "Same-drive selection left public state unchanged."
expect "B>"
send -- "BDOSPRB /HELP\\r"
expect "BDOSPRB /CPM"
expect "B>"
send -- "BDOSPRB /INFO\\r"
expect "guarded same-drive selection"
expect "B>"
send -- "BDOSPRB /VERSION\\r"
expect "BDOSPROBE 0.1.0-dev4"
expect "B>"
send -- "BDOSPRB /CPM EXTRA\\r"
expect "BDOSPRB: invalid command"
expect "B>"
send "\\034"
expect "User Interrupt"
close
'''
    return run("expect", "-c", commands, check=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpmsim", type=Path, default=DEFAULT_CPMSIM)
    parser.add_argument("--system-disk", type=Path, default=DEFAULT_SYSTEM)
    parser.add_argument("--boot-template", type=Path, default=DEFAULT_BOOT)
    parser.add_argument("--tools", type=Path, default=DEFAULT_TOOLS)
    parser.add_argument("--output", type=Path, default=ROOT / "build")
    args = parser.parse_args()
    for path in (SOURCE, args.cpmsim, args.system_disk, args.boot_template,
                 args.tools / "ZSM4.COM", args.tools / "LINK.COM"):
        if not path.is_file():
            raise SystemExit(f"missing build input: {path}")

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bdosprobe-zsm4-") as temporary:
        work = Path(temporary)
        disks = work / "disks"
        disks.mkdir()
        shutil.copy2(args.system_disk, disks / "drivea.dsk")
        for drive in "bcd":
            blank_disk(args.boot_template, disks / f"drive{drive}.dsk")
        source = work / "BDOSPRB.MAC"
        source.write_bytes(cpm_text(SOURCE))
        run("cpmcp", "-f", "ibm-3740", str(disks / "drivec.dsk"), str(source), "0:BDOSPRB.MAC")
        for tool in ("ZSM4.COM", "LINK.COM"):
            run("cpmcp", "-f", "ibm-3740", str(disks / "drived.dsk"), str(args.tools / tool), f"0:{tool}")

        z80 = session(args.cpmsim, disks, "-z", True)
        z80_text = z80.stdout + z80.stderr
        if z80.returncode or "Errors: 0" not in z80_text or "CP/M 2.2" not in z80_text:
            raise SystemExit(f"Z80 build/test failed ({z80.returncode})\n{z80_text}")
        run("cpmcp", "-f", "ibm-3740", str(disks / "driveb.dsk"), "0:BDOSPRB.COM", str(output / "BDOSPRB.COM"))
        intel = session(args.cpmsim, disks, "-8", False)
        intel_text = intel.stdout + intel.stderr
        if intel.returncode or "CP/M 2.2" not in intel_text or "HL:    0022H" not in intel_text:
            raise SystemExit(f"8080 test failed ({intel.returncode})\n{intel_text}")
        (output / "BUILD.LOG").write_text("=== Z80 ===\n" + z80_text + "\n=== 8080 ===\n" + intel_text, encoding="utf-8")

    digest_com = hashlib.sha256((output / "BDOSPRB.COM").read_bytes()).hexdigest()
    digest_src = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    (output / "SHA256SUMS.txt").write_text(
        f"{digest_com}  BDOSPRB.COM\n{digest_src}  ../src/BDOSPRB.MAC\n", encoding="ascii")
    print(f"BDOSPRB.COM: {(output / 'BDOSPRB.COM').stat().st_size} bytes")
    print("ZSM4 errors: 0; Z80 and 8080 CP/M tests passed")


if __name__ == "__main__":
    main()
