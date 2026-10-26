#!/usr/bin/env python3
"""Build SEARCH with ZSM4/LINK and require byte parity."""
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
SOURCE = ROOT / "src/utilities/search.mac"
BUILD = ROOT / "build/search-development"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpmsim", type=Path, default=DEFAULT_CPMSIM)
    parser.add_argument("--system-disk", type=Path, default=DEFAULT_SYSTEM)
    parser.add_argument("--disk-template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--tools", type=Path, default=DEFAULT_TOOLS)
    parser.add_argument("--verify", action="store_true", help="Run native command fixtures after linking")
    args = parser.parse_args()
    os.environ["PATH"] = str(args.cpmsim.parent / "srctools") + os.pathsep + os.environ.get("PATH", "")
    for path in (args.cpmsim, args.system_disk, args.disk_template,
                 args.tools / "ZSM4.COM", args.tools / "LINK.COM",
                 SOURCE, ROOT / "build/utilities/SEARCH.COM"):
        if not path.is_file():
            raise SystemExit(f"missing native-build input: {path}")

    BUILD.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bettercpm-native-search-") as temporary:
        work = Path(temporary)
        disks = work / "disks"
        disks.mkdir()
        shutil.copy2(args.system_disk, disks / "drivea.dsk")
        for drive in "bcd":
            blank(args.disk_template, disks / f"drive{drive}.dsk")
        source = work / "SEARCH.MAC"
        from build_search import expanded_source
        import re
        text = expanded_source()
        text = re.sub(r'(?m)^(?:(\w+:)\s*)? +DS +([0-9]+) *$',
                      r'\1\n        REPT \2\n        DB 0FFH\n        ENDM', text)
        expanded = work / 'expanded.mac'
        expanded.write_text(text, encoding='ascii')
        source.write_bytes(cpm_text(expanded))
        run("cpmcp", "-f", "ibm-3740", str(disks / "drivec.dsk"),
            str(source), "0:SEARCH.MAC")
        for tool in ("ZSM4.COM", "LINK.COM"):
            run("cpmcp", "-f", "ibm-3740", str(disks / "drived.dsk"),
                str(args.tools / tool), f"0:{tool}")
        verify = ''
        if args.verify:
            prefix = b'4142 AB 4142\r\n'
            data = prefix + b'\x1a'*(65535-len(prefix)) + b'4142'
            fixture = work/'FIX.DAT'
            fixture.write_bytes(data+b'\x1a'*(513*128-len(data)))
            pages = work/'PAGES.TXT'
            pages.write_bytes(b'X\r\n'*80+b'\x1a'*16)
            for path in (fixture, pages):
                run('cpmcp', '-f', 'ibm-3740', str(disks/'driveb.dsk'), str(path), '0:'+path.name)
            verify = r'''
send -- "SEARCH /HELP /VER\r"
expect "Usage: SEARCH"
expect "/NOHEX"
expect "Display utility identification."
expect "B>"
send -- "SEARCH \"4142\" B0:FIX.DAT\r"
expect "Files searched: 1"
expect "Text matches: 3"
expect "Hex matches: 1"
expect "Total matches: 4"
expect "B>"
send -- "SEARCH \"X\" B0:PAGES.TXT /NOHEX /P\r"
expect "Space/Enter:"
send -- "\003"
expect "DISPLAY INTERRUPTED"
expect "SEARCH CONTINUING..."
expect "Total matches: 80"
expect "B>"
'''
        commands = f'''set timeout 60
spawn {args.cpmsim} -z -d {disks}
expect_before timeout {{exit 2}}
expect "A>"
send -- "B:\r"
expect "B>"
send -- "D:ZSM4 B:SEARCH=C:SEARCH\r"
expect -re {{Errors: +0}}
expect "B>"
send -- "D:LINK SEARCH\\[A\\]\r"
expect "CODE SIZE"
expect "B>"
{verify}send "\034"
expect eof
'''
        result = run("expect", "-c", commands, check=False)
        transcript = result.stdout + result.stderr
        (BUILD / "NATIVE-SEARCH-BUILD.LOG").write_text(transcript,
                                                      encoding="utf-8")
        if result.returncode or "Errors: 0" not in transcript or "CODE SIZE" not in transcript:
            raise SystemExit(f"native SEARCH build failed\n{transcript}")
        native_com = work / "SEARCH.COM"
        run("cpmcp", "-f", "ibm-3740", str(disks / "driveb.dsk"),
            "0:SEARCH.COM", str(native_com))
        cross = (ROOT / "build/utilities/SEARCH.COM").read_bytes()
        native = native_com.read_bytes()[:len(cross)]
        (BUILD / "SEARCH-native.COM").write_bytes(native)
        if native != cross:
            raise SystemExit(f"native/cross SEARCH mismatch: linked size {native_com.stat().st_size}")
        if args.verify:
            restored = work/'FIX-READ.DAT'
            run('cpmcp', '-f', 'ibm-3740', str(disks/'driveb.dsk'), '0:FIX.DAT', str(restored))
            if restored.read_bytes() != fixture.read_bytes():
                raise SystemExit('Native SEARCH changed fixture content')
            if 'Total matches: 80' not in transcript or 'Search incomplete' in transcript:
                raise SystemExit('Native SEARCH fixture output failed')
        print(f"SEARCH: {len(native)} byte-identical bytes" + ('; native command fixtures pass' if args.verify else ''))


if __name__ == "__main__":
    main()
