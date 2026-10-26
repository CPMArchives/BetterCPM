#!/usr/bin/env python3
"""Build COMPARE with ZSM4/LINK and require byte parity."""
from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from pathlib import Path

from build_native_trs80 import blank, cpm_text, run

ROOT = Path(__file__).resolve().parents[1]
Z80PACK = Path.home() / "projects/git/z80pack"
DEFAULT_CPMSIM = Z80PACK / "cpmsim/cpmsim"
DEFAULT_SYSTEM = Z80PACK / "cpmsim/disks/library/cpm22-62khd.dsk"
DEFAULT_TEMPLATE = Z80PACK / "cpmsim/disks/library/cpm22-1.dsk"
DEFAULT_TOOLS = Path.home() / "projects/git/cpm-compatibility/suite/build-tools"
SOURCE = ROOT / "src/utilities/compare.mac"
BUILD = ROOT / "build/compare-development"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpmsim", type=Path, default=DEFAULT_CPMSIM)
    parser.add_argument("--system-disk", type=Path, default=DEFAULT_SYSTEM)
    parser.add_argument("--disk-template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--tools", type=Path, default=DEFAULT_TOOLS)
    args = parser.parse_args()
    os.environ["PATH"] = str(args.cpmsim.parent / "srctools") + os.pathsep + os.environ.get("PATH", "")
    for path in (args.cpmsim, args.system_disk, args.disk_template,
                 args.tools / "ZSM4.COM", args.tools / "LINK.COM",
                 SOURCE, ROOT / "build/utilities/COMPARE.COM"):
        if not path.is_file():
            raise SystemExit(f"missing native-build input: {path}")

    BUILD.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bettercpm-native-compare-") as temporary:
        work = Path(temporary)
        disks = work / "disks"
        disks.mkdir()
        shutil.copy2(args.system_disk, disks / "drivea.dsk")
        for drive in "bcd":
            blank(args.disk_template, disks / f"drive{drive}.dsk")
        source = work / "COMPARE.MAC"
        from build_compare import expanded_source
        import re
        text = expanded_source()
        text = re.sub(r'(?m)^(?:(\w+:)\s*)? +DS +([0-9]+) *$',
                      r'\1\n        REPT \2\n        DB 0FFH\n        ENDM', text)
        expanded = work / 'expanded.mac'
        expanded.write_text(text, encoding='ascii')
        source.write_bytes(cpm_text(expanded))
        run("cpmcp", "-f", "ibm-3740", str(disks / "drivec.dsk"),
            str(source), "0:COMPARE.MAC")
        for tool in ("ZSM4.COM", "LINK.COM"):
            run("cpmcp", "-f", "ibm-3740", str(disks / "drived.dsk"),
                str(args.tools / tool), f"0:{tool}")
        commands = f'''set timeout 60
spawn {args.cpmsim} -z -d {disks}
expect "A>"
send -- "B:\r"
expect "B>"
send -- "D:ZSM4 B:COMPARE=C:COMPARE\r"
expect -re {{Errors: +0}}
expect "B>"
send -- "D:LINK COMPARE\\[A\\]\r"
expect "CODE SIZE"
expect "B>"
send "\034"
expect eof
'''
        result = run("expect", "-c", commands, check=False)
        transcript = result.stdout + result.stderr
        (BUILD / "NATIVE-COMPARE-BUILD.LOG").write_text(transcript,
                                                      encoding="utf-8")
        if result.returncode or "Errors: 0" not in transcript or "CODE SIZE" not in transcript:
            raise SystemExit(f"native COMPARE build failed\n{transcript}")
        native_com = work / "COMPARE.COM"
        run("cpmcp", "-f", "ibm-3740", str(disks / "driveb.dsk"),
            "0:COMPARE.COM", str(native_com))
        cross = (ROOT / "build/utilities/COMPARE.COM").read_bytes()
        native = native_com.read_bytes()[:len(cross)]
        (BUILD / "COMPARE-native.COM").write_bytes(native)
        if native != cross:
            raise SystemExit(f"native/cross COMPARE mismatch: linked size {native_com.stat().st_size}")
        print(f"COMPARE: {len(native)} byte-identical bytes")


if __name__ == "__main__":
    main()
