#!/usr/bin/env python3
"""Build RCP-derived transient commands natively and require cross parity."""
from __future__ import annotations

import argparse
import re
import shutil
import tempfile
from pathlib import Path
from system_layout import expand_layout

from build_rcp_transients import BUILD, COMMANDS, ROOT, SOURCE, copy_source, dir_source, symbol, transient
from build_native_trs80 import (
    DEFAULT_CPMSIM, DEFAULT_SYSTEM, DEFAULT_TEMPLATE, DEFAULT_TOOLS,
    blank, cpm_text, run,
)


def initialized_workspace(text: str) -> str:
    # LINK leaves DS bytes unspecified; cross assembly emits FF-filled space.
    # Emit the same initial bytes natively for reproducible full-image comparison.
    return re.sub(r"(?m)^(.*?:)\s+DS\s+([0-9*]+)\s*$",
                  r"\1\n        REPT \2\n        DB 0FFH\n        ENDM", text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpmsim", type=Path, default=DEFAULT_CPMSIM)
    parser.add_argument("--system-disk", type=Path, default=DEFAULT_SYSTEM)
    parser.add_argument("--disk-template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--tools", type=Path, default=DEFAULT_TOOLS)
    args = parser.parse_args()
    required = (args.cpmsim, args.system_disk, args.disk_template,
                args.tools / "ZSM4.COM", args.tools / "LINK.COM", SOURCE,
                BUILD / "rcp-transient.bin", BUILD / "rcp-transient.lst")
    for path in required:
        if not path.is_file():
            raise SystemExit(f"missing native RCP transient input: {path}")
    with tempfile.TemporaryDirectory(prefix="bettercpm-native-rcp-transient-") as temporary:
        work = Path(temporary)
        disks = work / "disks"
        disks.mkdir()
        shutil.copy2(args.system_disk, disks / "drivea.dsk")
        for drive in "bcd":
            blank(args.disk_template, disks / f"drive{drive}.dsk")
        text = expand_layout(SOURCE.read_text(encoding="ascii").replace(
            '; @rcp-shared-selector@', '').replace(
            "CPXBASE         EQU     08000H", "CPXBASE         EQU     00100H"))
        staged = work / "BASX.MAC"
        staged.write_bytes(initialized_workspace(text).replace("\n", "\r\n").encode("ascii") + b"\x1a")
        run("cpmcp", "-f", "ibm-3740", str(disks / "drivec.dsk"),
            str(staged), "0:BASX.MAC")
        copy_staged = work / "COPYX.MAC"
        copy_staged.write_bytes(initialized_workspace(copy_source(text)).replace("\n", "\r\n").encode("ascii") + b"\x1a")
        run("cpmcp", "-f", "ibm-3740", str(disks / "drivec.dsk"),
            str(copy_staged), "0:COPYX.MAC")
        dir_staged = work / "DIRX.MAC"
        dir_staged.write_bytes(initialized_workspace(expand_layout(dir_source())).replace(
            "\n", "\r\n").encode("ascii") + b"\x1a")
        run("cpmcp", "-f", "ibm-3740", str(disks / "driveb.dsk"),
            str(dir_staged), "0:DIRX.MAC")
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
send -- "D:ZSM4 B:COPYX=C:COPYX\r"
expect -re {{Errors: +0}}
expect "B>"
send -- "D:LINK COPYX\\[A\\]\r"
expect "CODE SIZE"
expect "B>"
send -- "D:ZSM4 B:DIRX=B:DIRX\r"
expect -re {{Errors: +0}}
expect "B>"
send -- "D:LINK DIRX\\[A\\]\r"
expect "CODE SIZE"
expect "B>"
send "\034"
expect eof
'''
        result = run("expect", "-c", commands, check=False)
        transcript = result.stdout + result.stderr
        (BUILD / "NATIVE-RCP-TRANSIENT-BUILD.LOG").write_text(
            transcript, encoding="utf-8")
        if result.returncode or "Errors: 0" not in transcript or "CODE SIZE" not in transcript:
            raise SystemExit(f"native RCP transient build failed\n{transcript}")
        native_com = work / "BASX.COM"
        run("cpmcp", "-f", "ibm-3740", str(disks / "driveb.dsk"),
            "0:BASX.COM", str(native_com))
        base = native_com.read_bytes()[:(BUILD / "rcp-transient.bin").stat().st_size]
        for command, entry_name in COMMANDS.items():
            command_base, listing = base, BUILD / "rcp-transient.lst"
            if command == "DIR":
                native_dir = work / "DIRX.COM"
                run("cpmcp", "-f", "ibm-3740", str(disks / "driveb.dsk"),
                    "0:DIRX.COM", str(native_dir))
                command_base = native_dir.read_bytes()[:(BUILD / "dir-transient.bin").stat().st_size]
                listing = BUILD / "dir-transient.lst"
            if command == "COPY":
                native_copy = work / "COPYX.COM"
                run("cpmcp", "-f", "ibm-3740", str(disks / "driveb.dsk"),
                    "0:COPYX.COM", str(native_copy))
                command_base = native_copy.read_bytes()[:(BUILD / "copy-transient.bin").stat().st_size]
                listing = BUILD / "copy-transient.lst"
            native = transient(command_base, symbol(listing, entry_name),
                               symbol(listing, "UV_CHECK"), symbol(listing, "UV_T" + command))
            cross = (BUILD / f"{command}.COM").read_bytes()
            if native != cross:
                (BUILD / f"{command}-native-mismatch.COM").write_bytes(native)
                first = next((i for i, pair in enumerate(zip(native, cross)) if pair[0] != pair[1]), min(len(native), len(cross)))
                raise SystemExit(f"native/cross {command}.COM mismatch at {first}: lengths {len(native)}/{len(cross)}")
            (BUILD / f"{command}-native.COM").write_bytes(native)
            print(f"{command}: {len(native)} byte-identical bytes")


if __name__ == "__main__":
    main()
