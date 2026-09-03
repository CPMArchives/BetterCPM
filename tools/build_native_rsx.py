#!/usr/bin/env python3
"""Build HELLO.RSX code and its utilities under CP/M; require cross parity."""
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
BUILD_RSX = ROOT / "build/rsx"
BUILD_UTIL = ROOT / "build/utilities"
VERSION_INCLUDE = ROOT / "src/utilities/rsxvers.inc"
MODULES = (
    ("HELLO", ROOT / "src/rsx/hello.mac", BUILD_RSX / "hello.bin",
     BUILD_RSX / "hello-native.bin"),
    ("ECHO", ROOT / "src/rsx/echo.mac", BUILD_RSX / "echo.bin",
     BUILD_RSX / "echo-native.bin"),
    ("RSX", ROOT / "src/utilities/rsx.mac", BUILD_UTIL / "RSX.COM",
     BUILD_UTIL / "RSX-native.COM"),
    ("RSXTEST", ROOT / "src/utilities/rsxtest.mac", BUILD_UTIL / "RSXTEST.COM",
     BUILD_UTIL / "RSXTEST-native.COM"),
    ("RSX2TST", ROOT / "src/utilities/rsx2test.mac", BUILD_UTIL / "RSX2TST.COM",
     BUILD_UTIL / "RSX2TST-native.COM"),
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpmsim", type=Path, default=DEFAULT_CPMSIM)
    parser.add_argument("--system-disk", type=Path, default=DEFAULT_SYSTEM)
    parser.add_argument("--disk-template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--tools", type=Path, default=DEFAULT_TOOLS)
    args = parser.parse_args()
    inputs = [args.cpmsim, args.system_disk, args.disk_template,
              args.tools / "ZSM4.COM", args.tools / "LINK.COM"]
    inputs += [path for _name, path, cross, _native in MODULES
               for path in (path, cross)]
    inputs.append(VERSION_INCLUDE)
    for path in inputs:
        if not path.is_file():
            raise SystemExit(f"missing native RSX build input: {path}")

    with tempfile.TemporaryDirectory(prefix="bettercpm-native-rsx-") as temporary:
        work = Path(temporary)
        disks = work / "disks"
        disks.mkdir()
        shutil.copy2(args.system_disk, disks / "drivea.dsk")
        for drive in "bcd":
            blank(args.disk_template, disks / f"drive{drive}.dsk")
        for name, source, _cross, _native in MODULES:
            staged = work / f"{name}.MAC"
            staged.write_bytes(cpm_text(source))
            run("cpmcp", "-f", "ibm-3740", str(disks / "drivec.dsk"),
                str(staged), f"0:{name}.MAC")
        include = work / "RSXVERS.INC"
        include.write_bytes(cpm_text(VERSION_INCLUDE))
        run("cpmcp", "-f", "ibm-3740", str(disks / "driveb.dsk"),
            str(include), "0:RSXVERS.INC")
        for tool in ("ZSM4.COM", "LINK.COM"):
            run("cpmcp", "-f", "ibm-3740", str(disks / "drived.dsk"),
                str(args.tools / tool), f"0:{tool}")
        actions = []
        for name, _source, _cross, _native in MODULES:
            actions.append(f'send -- "D:ZSM4 B:{name}=C:{name}\\r"\n'
                           'expect -re {Errors: +0}\nexpect "B>"\n'
                           f'send -- "D:LINK {name}\\[A\\]\\r"\n'
                           'expect "CODE SIZE"\nexpect "B>"\n')
        commands = f'''set timeout 90
spawn {args.cpmsim} -z -d {disks}
expect "A>"
send -- "B:\r"
expect "B>"
{''.join(actions)}send "\034"
expect eof
'''
        result = run("expect", "-c", commands, check=False)
        transcript = result.stdout + result.stderr
        (BUILD_RSX / "NATIVE-RSX-BUILD.LOG").write_text(
            transcript, encoding="utf-8")
        if (result.returncode or transcript.count("Errors: 0") != len(MODULES)
                or transcript.count("CODE SIZE") < len(MODULES)):
            raise SystemExit(f"native RSX build failed\n{transcript}")
        for name, _source, cross_path, native_path in MODULES:
            linked = work / f"{name}.COM"
            run("cpmcp", "-f", "ibm-3740", str(disks / "driveb.dsk"),
                f"0:{name}.COM", str(linked))
            cross = cross_path.read_bytes()
            native = linked.read_bytes()[:len(cross)]
            if native != cross:
                mismatch = next((index for index, pair in
                                 enumerate(zip(native, cross))
                                 if pair[0] != pair[1]), min(len(native), len(cross)))
                raise SystemExit(f"native/cross {name} mismatch: "
                                 f"linked size {linked.stat().st_size}; "
                                 f"first difference {mismatch:04X}h")
            native_path.write_bytes(native)
            print(f"{name}: {len(native)} byte-identical bytes")


if __name__ == "__main__":
    main()
