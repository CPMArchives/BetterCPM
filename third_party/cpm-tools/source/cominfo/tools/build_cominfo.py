#!/usr/bin/env python3
"""Build COMINFO under CP/M with ZSM4 and Digital Research LINK."""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "src/COMINFO.MAC"
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
    with tempfile.TemporaryDirectory(prefix="cominfo-zsm4-") as temporary:
        work = Path(temporary)
        disks = work / "disks"
        disks.mkdir()
        shutil.copy2(args.system_disk, disks / "drivea.dsk")
        for drive in "bcd":
            blank_disk(args.boot_template, disks / f"drive{drive}.dsk")

        host_source = work / "COMINFO.MAC"
        host_source.write_bytes(cpm_text(SOURCE))
        run("cpmcp", "-f", "ibm-3740", str(disks / "drivec.dsk"),
            str(host_source), "0:COMINFO.MAC")
        sample = work / "SAMPLE.COM"
        patterns = bytes((
            0xCD, 0x05, 0x00,              # dynamic/unknown CALL 0005H
            0xC3, 0x00, 0x00,              # definite JMP 0000H
            0x3A, 0x80, 0x00,              # direct page-zero reference
            0xED, 0x44,                    # heuristic Z80 prefix
            0x0E, 15, 0xCD, 0x05, 0x00,   # MVI C,15 / CALL 5
            0x11, 0x34, 0x12, 0x0E, 9,
            0xCD, 0x05, 0x00,              # LXI D,1234 / MVI C,9 / CALL 5
            0x0E, 26, 0x11, 0x00, 0x20,
            0xCD, 0x05, 0x00,              # MVI C,26 / LXI D,2000 / CALL 5
        ))
        payload = bytearray(256)
        payload[:len(patterns)] = patterns
        payload[124:132] = bytes((
            0x0E, 32, 0x11, 0x34, 0x12, 0xCD, 0x05, 0x00,
        ))  # function idiom crossing the 128-byte DMA boundary
        sample.write_bytes(payload)
        run("cpmcp", "-f", "ibm-3740", str(disks / "driveb.dsk"),
            str(sample), "0:SAMPLE.COM")
        for tool in ("ZSM4.COM", "LINK.COM"):
            run("cpmcp", "-f", "ibm-3740", str(disks / "drived.dsk"),
                str(args.tools / tool), f"0:{tool}")

        commands = f'''set timeout 10
spawn {args.cpmsim} -z -d {disks}
expect "A>"
send -- "B:\\r"
expect "B>"
send -- "D:ZSM4 B:COMINFO=C:COMINFO\\r"
expect {{
    -re {{Errors: +0}} {{}}
    -re {{Errors: +[1-9][0-9]*}} {{exit 20}}
    timeout {{exit 21}}
}}
expect "B>"
send -- "D:LINK COMINFO\\[A\\]\\r"
expect {{
    "CODE SIZE" {{}}
    timeout {{exit 22}}
}}
expect "B>"
send -- "COMINFO SAMPLE.COM\\r"
expect "Logical records:       2"
expect "Logical bytes:         256"
expect "Load range:            0100-01FF"
expect "Definite CALL 0005H:   5"
expect "Immediate BDOS func:   4"
expect "Dynamic/unknown calls: 1"
expect "Definite JMP 0000H:    1"
expect "Other page-zero refs:  1"
expect "Z80 prefix bytes:      1"
expect "B>"
send -- "COMINFO SAMPLE.COM /VERBOSE\\r"
expect "Offset 0000  BDOS ?  function dynamic/unknown"
expect "Offset 0003  definite JMP 0000H"
expect "Offset 0006  direct page-zero reference"
expect "Offset 0009  heuristic Z80 prefix byte"
expect "Offset 000D  BDOS 15 OPEN FILE  function immediate"
expect "Offset 0015  BDOS 9 PRINT STRING  function immediate  DE=1234H"
expect "Offset 001D  BDOS 26 SET DMA ADDRESS  function immediate  DE=2000H"
expect "Offset 0081  BDOS 32 GET/SET USER CODE  function immediate  DE=1234H"
expect "Recognized BDOS functions:"
expect "15 OPEN FILE  count 1"
expect "B>"
send -- "COMINFO MISSING.COM\\r"
expect "COMINFO: file not found."
expect "B>"
send -- "COMINFO /H\\r"
expect "COMINFO file.COM"
expect "B>"
send -- "COMINFO /INFO\\r"
expect "Built with ZSM4 and Digital Research LINK."
expect "B>"
send -- "COMINFO /VERSION\\r"
expect "COMINFO 0.1.0-dev2"
expect "B>"
send -- "COMINFO SAMPLE.COM /V /INFO\\r"
expect "COMINFO: invalid command. Use COMINFO /HELP."
expect "B>"
send "\\034"
expect "User Interrupt"
close
'''
        result = run("expect", "-c", commands, check=False)
        transcript = result.stdout + result.stderr
        (output / "BUILD.LOG").write_text(transcript, encoding="utf-8")
        if (result.returncode or "Errors: 0" not in transcript
                or "Logical bytes:         256" not in transcript
                or "Load range:            0100-01FF" not in transcript
                or "Definite CALL 0005H:   5" not in transcript
                or "Immediate BDOS func:   4" not in transcript
                or "Offset 0015  BDOS 9 PRINT STRING" not in transcript
                or "Offset 0081  BDOS 32 GET/SET USER CODE" not in transcript
                or "15 OPEN FILE  count 1" not in transcript
                or "COMINFO: file not found." not in transcript
                or "Built with ZSM4" not in transcript):
            raise SystemExit(
                f"CP/M build failed (expect status {result.returncode})\n{transcript}"
            )
        run("cpmcp", "-f", "ibm-3740", str(disks / "driveb.dsk"),
            "0:COMINFO.COM", str(output / "COMINFO.COM"))

    digest_com = hashlib.sha256((output / "COMINFO.COM").read_bytes()).hexdigest()
    digest_src = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    (output / "SHA256SUMS.txt").write_text(
        f"{digest_com}  COMINFO.COM\n{digest_src}  ../src/COMINFO.MAC\n",
        encoding="ascii",
    )
    print(f"COMINFO.COM: {(output / 'COMINFO.COM').stat().st_size} bytes")
    print("ZSM4 errors: 0; LINK and CP/M smoke test passed")


if __name__ == "__main__":
    main()
