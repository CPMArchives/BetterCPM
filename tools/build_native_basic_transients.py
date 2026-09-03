#!/usr/bin/env python3
"""Build BASIC-derived transient commands natively and require cross parity."""
from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path
from system_layout import expand_layout

from build_basic_transients import BUILD, COMMANDS, ROOT, SOURCE, symbol, transient
from build_native_trs80 import (
    DEFAULT_CPMSIM, DEFAULT_SYSTEM, DEFAULT_TEMPLATE, DEFAULT_TOOLS,
    blank, cpm_text, run,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpmsim", type=Path, default=DEFAULT_CPMSIM)
    parser.add_argument("--system-disk", type=Path, default=DEFAULT_SYSTEM)
    parser.add_argument("--disk-template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--tools", type=Path, default=DEFAULT_TOOLS)
    args = parser.parse_args()
    required = (args.cpmsim, args.system_disk, args.disk_template,
                args.tools / "ZSM4.COM", args.tools / "LINK.COM", SOURCE,
                BUILD / "basic-transient.bin", BUILD / "basic-transient.lst")
    for path in required:
        if not path.is_file():
            raise SystemExit(f"missing native BASIC transient input: {path}")
    with tempfile.TemporaryDirectory(prefix="bettercpm-native-basic-transient-") as temporary:
        work = Path(temporary)
        disks = work / "disks"
        disks.mkdir()
        shutil.copy2(args.system_disk, disks / "drivea.dsk")
        for drive in "bcd":
            blank(args.disk_template, disks / f"drive{drive}.dsk")
        text = expand_layout(SOURCE.read_text(encoding="ascii")).replace(
            "CPXBASE         EQU     08000H", "CPXBASE         EQU     00100H")
        staged = work / "BASX.MAC"
        staged.write_bytes(text.replace("\n", "\r\n").encode("ascii") + b"\x1a")
        run("cpmcp", "-f", "ibm-3740", str(disks / "drivec.dsk"),
            str(staged), "0:BASX.MAC")
        for tool in ("ZSM4.COM", "LINK.COM"):
            run("cpmcp", "-f", "ibm-3740", str(disks / "drived.dsk"),
                str(args.tools / tool), f"0:{tool}")
        commands = f'''set timeout 60
spawn {args.cpmsim} -z -d {disks}
expect "A>"
send -- "B:\r"
expect "B>"
send -- "D:ZSM4 B:BASX=C:BASX\r"
expect -re {{Errors: +0}}
expect "B>"
send -- "D:LINK BASX\\[A\\]\r"
expect "CODE SIZE"
expect "B>"
send "\034"
expect eof
'''
        result = run("expect", "-c", commands, check=False)
        transcript = result.stdout + result.stderr
        (BUILD / "NATIVE-BASIC-TRANSIENT-BUILD.LOG").write_text(
            transcript, encoding="utf-8")
        if result.returncode or "Errors: 0" not in transcript or "CODE SIZE" not in transcript:
            raise SystemExit(f"native BASIC transient build failed\n{transcript}")
        native_com = work / "BASX.COM"
        run("cpmcp", "-f", "ibm-3740", str(disks / "driveb.dsk"),
            "0:BASX.COM", str(native_com))
        base = native_com.read_bytes()[:(BUILD / "basic-transient.bin").stat().st_size]
        for command, entry_name in COMMANDS.items():
            native = transient(base, symbol(BUILD / "basic-transient.lst", entry_name))
            cross = (BUILD / f"{command}.COM").read_bytes()
            if native != cross:
                raise SystemExit(f"native/cross {command}.COM mismatch")
            (BUILD / f"{command}-native.COM").write_bytes(native)
            print(f"{command}: {len(native)} byte-identical bytes")


if __name__ == "__main__":
    main()
