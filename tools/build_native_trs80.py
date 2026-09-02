#!/usr/bin/env python3
"""Build TRS-80 boot stages under native CP/M with ZSM4 and DRI LINK."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/platform/trs80m4"
CORE = ROOT / "src/core"
BUILD = ROOT / "build/trs80"
DEFAULT_CPMSIM = Path("/Users/nathanael/z80pack/cpmsim/cpmsim")
DEFAULT_SYSTEM = Path("/Users/nathanael/z80pack/cpmsim/disks/library/cpm22-62khd.dsk")
DEFAULT_TEMPLATE = Path("/Users/nathanael/git/cpm-compatibility/suite/disk-images/z80pack/ibm-3740/drivea.dsk")
DEFAULT_TOOLS = Path("/Users/nathanael/git/cpm-compatibility/suite/build-tools")
STAGES = (("BOOT", 0x4300, "boot.bin"), ("STAGE1", 0x5000, "stage1.bin"),
          ("DISKREAD", 0x5000, "diskread.bin"))
STAGES = STAGES + (("DISKWRIT", 0x5000, "diskwrit.bin"),)
STAGES = STAGES + (("CCPRELOD", 0xE900, "ccpreload.bin"),)


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, text=True, capture_output=True)


def cpm_text(path: Path) -> bytes:
    text = path.read_text(encoding="ascii").replace("\r\n", "\n").replace("\r", "\n")
    return text.replace("\n", "\r\n").encode("ascii") + b"\x1a"


def blank(template: Path, destination: Path) -> None:
    shutil.copy2(template, destination)
    run("mkfs.cpm", "-f", "ibm-3740", str(destination))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpmsim", type=Path, default=DEFAULT_CPMSIM)
    parser.add_argument("--system-disk", type=Path, default=DEFAULT_SYSTEM)
    parser.add_argument("--disk-template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--tools", type=Path, default=DEFAULT_TOOLS)
    args = parser.parse_args()
    required = [args.cpmsim, args.system_disk, args.disk_template,
                args.tools / "ZSM4.COM", args.tools / "LINK.COM",
                SOURCE / "hardware.inc", SOURCE / "hal.inc", SOURCE / "m4cons.inc",
                SOURCE / "m4disk.inc",
                CORE / "bringup.inc",
                SOURCE / "boot.mac", SOURCE / "stage1.mac", SOURCE / "diskread.mac",
                SOURCE / "diskwrit.mac", SOURCE / "commandreload.mac"]
    for path in required:
        if not path.is_file():
            raise SystemExit(f"missing native-build input: {path}")
    BUILD.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="bettercpm-native-") as temporary:
        work = Path(temporary)
        disks = work / "disks"
        disks.mkdir()
        shutil.copy2(args.system_disk, disks / "drivea.dsk")
        for drive in "bcd":
            blank(args.disk_template, disks / f"drive{drive}.dsk")
        source_files = ((SOURCE / "hardware.inc", "HARDWARE.INC"),
                        (SOURCE / "hal.inc", "HAL.INC"),
                        (SOURCE / "m4cons.inc", "M4CONS.INC"),
                        (SOURCE / "m4disk.inc", "M4DISK.INC"),
                        (CORE / "bringup.inc", "BRINGUP.INC"),
                        (SOURCE / "boot.mac", "BOOT.MAC"),
                        (SOURCE / "stage1.mac", "STAGE1.MAC"))
        source_files = source_files + ((SOURCE / "diskread.mac", "DISKREAD.MAC"),)
        source_files = source_files + ((SOURCE / "diskwrit.mac", "DISKWRIT.MAC"),)
        source_files = source_files + ((SOURCE / "commandreload.mac", "CCPRELOD.MAC"),)
        for source_path, cpm_name in source_files:
            host = work / cpm_name
            host.write_bytes(cpm_text(source_path))
            run("cpmcp", "-f", "ibm-3740", str(disks / "drivec.dsk"),
                str(host), f"0:{cpm_name}")
        # INCLUDE files are resolved on the current output drive by ZSM4.
        for include_name in ("HARDWARE.INC", "HAL.INC", "M4CONS.INC", "M4DISK.INC",
                             "BRINGUP.INC"):
            run("cpmcp", "-f", "ibm-3740", str(disks / "driveb.dsk"),
                str(work / include_name), f"0:{include_name}")
        for tool in ("ZSM4.COM", "LINK.COM"):
            run("cpmcp", "-f", "ibm-3740", str(disks / "drived.dsk"),
                str(args.tools / tool), f"0:{tool}")

        commands = f'''set timeout 60
spawn {args.cpmsim} -z -d {disks}
expect "A>"
send -- "B:\\r"
expect "B>"
send -- "D:ZSM4 B:BOOT=C:BOOT\\r"
expect -re {{Errors: +0}}
expect "B>"
send -- "D:LINK BOOT\\[A\\]\\r"
expect "CODE SIZE"
expect "B>"
send -- "D:ZSM4 B:STAGE1=C:STAGE1\\r"
expect -re {{Errors: +0}}
expect "B>"
send -- "D:LINK STAGE1\\[A\\]\\r"
expect "CODE SIZE"
expect "B>"
send -- "D:ZSM4 B:DISKREAD=C:DISKREAD\\r"
expect -re {{Errors: +0}}
expect "B>"
send -- "D:LINK DISKREAD\\[A\\]\\r"
expect "CODE SIZE"
expect "B>"
send -- "D:ZSM4 B:DISKWRIT=C:DISKWRIT\\r"
expect -re {{Errors: +0}}
expect "B>"
send -- "D:LINK DISKWRIT\\[A\\]\\r"
expect "CODE SIZE"
expect "B>"
send -- "D:ZSM4 B:CCPRELOD=C:CCPRELOD\\r"
expect -re {{Errors: +0}}
expect "B>"
send -- "D:LINK CCPRELOD\\[A\\]\\r"
expect "CODE SIZE"
expect "B>"
send "\\034"
expect eof
'''
        result = run("expect", "-c", commands, check=False)
        transcript = result.stdout + result.stderr
        (BUILD / "NATIVE-BUILD.LOG").write_text(transcript, encoding="utf-8")
        if result.returncode or transcript.count("Errors: 0") != 5 or transcript.count("CODE SIZE") < 5:
            raise SystemExit(f"native CP/M build failed\n{transcript}")

        for name, _origin, cross_name in STAGES:
            native_com = work / f"{name}.COM"
            run("cpmcp", "-f", "ibm-3740", str(disks / "driveb.dsk"),
                f"0:{name}.COM", str(native_com))
            cross = (BUILD / cross_name).read_bytes()
            linked = native_com.read_bytes()
            native = linked[:len(cross)]
            if native != cross:
                raise SystemExit(f"native/cross mismatch for {name}: linked size {len(linked)}")
            (BUILD / f"{name.lower()}-native.bin").write_bytes(native)
            print(f"{name}: {len(native)} byte-identical bytes")


if __name__ == "__main__":
    main()
