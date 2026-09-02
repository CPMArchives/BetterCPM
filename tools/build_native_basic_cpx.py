#!/usr/bin/env python3
"""Build BASIC.CPX code under native CP/M and require cross parity."""
from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

from build_native_trs80 import (
    DEFAULT_CPMSIM, DEFAULT_SYSTEM, DEFAULT_TEMPLATE, DEFAULT_TOOLS,
    blank, cpm_text, run,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/cpx/basic.mac"
BUILD = ROOT / "build/cpx"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpmsim", type=Path, default=DEFAULT_CPMSIM)
    parser.add_argument("--system-disk", type=Path, default=DEFAULT_SYSTEM)
    parser.add_argument("--disk-template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--tools", type=Path, default=DEFAULT_TOOLS)
    args = parser.parse_args()
    required = (args.cpmsim, args.system_disk, args.disk_template,
                args.tools / "ZSM4.COM", args.tools / "LINK.COM",
                SOURCE, BUILD / "basic.bin")
    for path in required:
        if not path.is_file():
            raise SystemExit(f"missing native BASIC.CPX build input: {path}")
    with tempfile.TemporaryDirectory(prefix="bettercpm-native-basic-cpx-") as temporary:
        work = Path(temporary)
        disks = work / "disks"
        disks.mkdir()
        shutil.copy2(args.system_disk, disks / "drivea.dsk")
        for drive in "bcd":
            blank(args.disk_template, disks / f"drive{drive}.dsk")
        staged = work / "BASIC.MAC"
        staged.write_bytes(cpm_text(SOURCE))
        run("cpmcp", "-f", "ibm-3740", str(disks / "drivec.dsk"),
            str(staged), "0:BASIC.MAC")
        for tool in ("ZSM4.COM", "LINK.COM"):
            run("cpmcp", "-f", "ibm-3740", str(disks / "drived.dsk"),
                str(args.tools / tool), f"0:{tool}")
        commands = f'''set timeout 60
spawn {args.cpmsim} -z -d {disks}
expect "A>"
send -- "B:\r"
expect "B>"
send -- "D:ZSM4 B:BASIC=C:BASIC\r"
expect -re {{Errors: +0}}
expect "B>"
send -- "D:LINK BASIC\\[A\\]\r"
expect "CODE SIZE"
expect "B>"
send "\034"
expect eof
'''
        result = run("expect", "-c", commands, check=False)
        transcript = result.stdout + result.stderr
        (BUILD / "NATIVE-BASIC-CPX-BUILD.LOG").write_text(transcript,
                                                            encoding="utf-8")
        if result.returncode or "Errors: 0" not in transcript or "CODE SIZE" not in transcript:
            raise SystemExit(f"native BASIC.CPX build failed\n{transcript}")
        native_com = work / "BASIC.COM"
        run("cpmcp", "-f", "ibm-3740", str(disks / "driveb.dsk"),
            "0:BASIC.COM", str(native_com))
        cross = (BUILD / "basic.bin").read_bytes()
        native = native_com.read_bytes()[:len(cross)]
        if native != cross:
            raise SystemExit(f"native/cross BASIC.CPX mismatch: linked size {native_com.stat().st_size}")
        (BUILD / "basic-native.bin").write_bytes(native)
        print(f"BASIC.CPX: {len(native)} byte-identical bytes")


if __name__ == "__main__":
    main()
