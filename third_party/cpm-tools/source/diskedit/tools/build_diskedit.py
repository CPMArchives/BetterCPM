#!/usr/bin/env python3
"""Build DISKEDIT under CP/M with ZSM4 and Digital Research LINK."""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "src/DISKEDIT.MAC"
DEFAULT_TOOLS = Path("/Users/nathanael/git/cpm-compatibility/suite/build-tools")
DEFAULT_BOOT = Path(
    "/Users/nathanael/git/cpm-compatibility/suite/disk-images/"
    "z80pack/ibm-3740/drivea.dsk"
)
DEFAULT_SYSTEM = Path(
    "/Users/nathanael/z80pack/cpmsim/disks/library/cpm22-62khd.dsk"
)
DEFAULT_CPMSIM = Path("/Users/nathanael/z80pack/cpmsim/cpmsim")


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, text=True, capture_output=True)


def cpm_text(path: Path) -> bytes:
    text = path.read_text(encoding="ascii")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.replace("\n", "\r\n").encode("ascii") + b"\x1a"


def blank_disk(template: Path, destination: Path) -> None:
    shutil.copy2(template, destination)
    run("mkfs.cpm", "-f", "ibm-3740", str(destination))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpmsim", type=Path, default=DEFAULT_CPMSIM)
    parser.add_argument("--system-disk", type=Path, default=DEFAULT_SYSTEM)
    parser.add_argument("--boot-template", type=Path, default=DEFAULT_BOOT)
    parser.add_argument("--tools", type=Path, default=DEFAULT_TOOLS)
    parser.add_argument("--output", type=Path, default=ROOT / "build")
    args = parser.parse_args()

    required = (
        SOURCE,
        args.cpmsim,
        args.system_disk,
        args.boot_template,
        args.tools / "ZSM4.COM",
        args.tools / "LINK.COM",
    )
    for path in required:
        if not path.is_file():
            raise SystemExit(f"missing build input: {path}")

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="diskedit-zsm4-") as temporary:
        work = Path(temporary)
        disks = work / "disks"
        disks.mkdir()
        shutil.copy2(args.system_disk, disks / "drivea.dsk")
        for drive in "bcd":
            blank_disk(args.boot_template, disks / f"drive{drive}.dsk")

        host_source = work / "DISKEDIT.MAC"
        host_source.write_bytes(cpm_text(SOURCE))
        run("cpmcp", "-f", "ibm-3740", str(disks / "drivec.dsk"),
            str(host_source), "0:DISKEDIT.MAC")
        for tool in ("ZSM4.COM", "LINK.COM"):
            run("cpmcp", "-f", "ibm-3740", str(disks / "drived.dsk"),
                str(args.tools / tool), f"0:{tool}")

        commands = f'''set timeout 10
spawn {args.cpmsim} -z -d {disks}
expect "A>"
send -- "B:\\r"
expect "B>"
send -- "D:ZSM4 B:DISKEDIT=C:DISKEDIT\\r"
expect {{
    -re {{Errors: +0}} {{}}
    -re {{Errors: +[1-9][0-9]*}} {{exit 20}}
    timeout {{exit 21}}
}}
expect "B>"
send -- "D:LINK DISKEDIT\\[A\\]\\r"
expect {{
    "CODE SIZE" {{}}
    timeout {{exit 22}}
}}
expect "B>"
send -- "DISKEDIT\\r"
expect "Trk 0  Log 0"
expect "Reg SYSTEM"
expect "S-system  D-directory  T-data"
send -- "N"
expect "Log 1"
expect "S-system  D-directory  T-data"
send -- "P"
expect "Log 0"
expect "S-system  D-directory  T-data"
send -- "D"
expect "Reg DIRECTORY"
expect "S-system  D-directory  T-data"
send -- "T"
expect "Reg DATA  Blk 2  Own 0:DISKEDIT.REL"
expect "S-system  D-directory  T-data"
send -- "S"
expect "Reg SYSTEM"
expect "S-system  D-directory  T-data"
send -- "Q"
expect "B>"
send -- "DISKEDIT C:\\r"
expect "DISKEDIT 0.1.0-dev2  Drive C:"
expect "S-system  D-directory  T-data"
send -- "T"
expect "Reg DATA  Blk 2  Own 0:DISKEDIT.MAC"
expect "S-system  D-directory  T-data"
send -- "Q"
expect "B>"
send -- "DISKEDIT /H\\r"
expect "DISKEDIT \\[drive:\\]"
expect "B>"
send -- "DISKEDIT /INFO\\r"
expect "Built with ZSM4 and Digital Research LINK."
expect "B>"
send -- "DISKEDIT /VERSION\\r"
expect "DISKEDIT 0.1.0-dev2"
expect "B>"
send -- "DISKEDIT FOO\\r"
expect "DISKEDIT: unknown option. Use DISKEDIT /HELP."
expect "B>"
send -- "DISKEDIT C: D:\\r"
expect "DISKEDIT: unknown option. Use DISKEDIT /HELP."
expect "B>"
send "\\034"
expect "User Interrupt"
close
'''
        result = run("expect", "-c", commands, check=False)
        transcript = result.stdout + result.stderr
        (output / "BUILD.LOG").write_text(transcript, encoding="utf-8")
        command_checks = {
            "DISKEDIT C:": "S-system  D-directory  T-data",
            "DISKEDIT /H": "DISKEDIT [drive:]",
            "DISKEDIT /INFO": "Built with ZSM4 and Digital Research LINK.",
            "DISKEDIT /VERSION": "DISKEDIT 0.1.0-dev2",
        }
        for command, expected in command_checks.items():
            marker = f"B>{command}\n"
            if marker not in transcript:
                raise SystemExit(f"missing CP/M test command: {command}")
            segment = transcript.split(marker, 1)[1].split("\nB>", 1)[0]
            if expected not in segment or "unknown option" in segment:
                raise SystemExit(f"CP/M test failed: {command}\n{segment}")
        if (result.returncode or "Errors: 0" not in transcript
                or "Reg SYSTEM" not in transcript
                or "Reg DIRECTORY" not in transcript
                or "Reg DATA  Blk 2  Own 0:DISKEDIT.REL" not in transcript
                or "Drive C:" not in transcript
                or "unknown option" not in transcript
                or "Built with ZSM4" not in transcript):
            raise SystemExit(
                f"CP/M build failed (expect status {result.returncode})\n{transcript}"
            )
        run("cpmcp", "-f", "ibm-3740", str(disks / "driveb.dsk"),
            "0:DISKEDIT.COM", str(output / "DISKEDIT.COM"))

    digest_com = hashlib.sha256((output / "DISKEDIT.COM").read_bytes()).hexdigest()
    digest_src = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    (output / "SHA256SUMS.txt").write_text(
        f"{digest_com}  DISKEDIT.COM\n{digest_src}  ../src/DISKEDIT.MAC\n",
        encoding="ascii",
    )
    print(f"DISKEDIT.COM: {(output / 'DISKEDIT.COM').stat().st_size} bytes")
    print("ZSM4 errors: 0; LINK and CP/M smoke test passed")


if __name__ == "__main__":
    main()
