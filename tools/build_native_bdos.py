#!/usr/bin/env python3
"""Build the unified BDOS or a linked support unit under native CP/M."""
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
SOURCE = ROOT / "src/bdos/unified.mac"
VERSIONS = ROOT / "src/bdos/versions.inc"
BUILD = ROOT / "build/bdos"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--component", choices=("bdos", "extensions", "tables"),
                        default="bdos")
    parser.add_argument("--cpmsim", type=Path, default=DEFAULT_CPMSIM)
    parser.add_argument("--system-disk", type=Path, default=DEFAULT_SYSTEM)
    parser.add_argument("--disk-template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--tools", type=Path, default=DEFAULT_TOOLS)
    args = parser.parse_args()
    component = args.component
    source_path, build_dir = SOURCE, BUILD
    if component != "bdos":
        source_path = ROOT / ("src/system/extensions.mac" if component == "extensions"
                              else "src/bios/tables.mac")
        build_dir = ROOT / "build/system"
    for path in (args.cpmsim, args.system_disk, args.disk_template,
                 args.tools / "ZSM4.COM", args.tools / "LINK.COM",
                 source_path, VERSIONS, build_dir / f"{component}.bin"):
        if not path.is_file():
            raise SystemExit(f"missing native-build input: {path}")

    with tempfile.TemporaryDirectory(prefix="bettercpm-native-bdos-") as temporary:
        work = Path(temporary)
        disks = work / "disks"
        disks.mkdir()
        shutil.copy2(args.system_disk, disks / "drivea.dsk")
        for drive in "bcd":
            blank(args.disk_template, disks / f"drive{drive}.dsk")
        source = work / "BDOS.MAC"
        source.write_bytes(cpm_text(source_path))
        run("cpmcp", "-f", "ibm-3740", str(disks / "drivec.dsk"),
            str(source), "0:BDOS.MAC")
        version_include = work / "VERSIONS.INC"
        version_include.write_bytes(cpm_text(VERSIONS))
        # ZSM4 resolves INCLUDE files on the output drive (B: here), not the
        # source drive named to the right of the command-line equals sign.
        run("cpmcp", "-f", "ibm-3740", str(disks / "driveb.dsk"),
            str(version_include), "0:VERSIONS.INC")
        if component == "extensions":
            core_include = work / "CORE.INC"
            core_include.write_bytes(cpm_text(build_dir / "core.inc"))
            run("cpmcp", "-f", "ibm-3740", str(disks / "driveb.dsk"),
                str(core_include), "0:CORE.INC")
        for tool in ("ZSM4.COM", "LINK.COM"):
            run("cpmcp", "-f", "ibm-3740", str(disks / "drived.dsk"),
                str(args.tools / tool), f"0:{tool}")
        commands = f'''set timeout 60
spawn {args.cpmsim} -z -d {disks}
expect "A>"
send -- "B:\\r"
expect "B>"
send -- "D:ZSM4 B:BDOS=C:BDOS\\r"
expect -re {{Errors: +0}}
expect "B>"
send -- "D:LINK BDOS\\[A\\]\\r"
expect "CODE SIZE"
expect "B>"
send "\\034"
expect eof
'''
        result = run("expect", "-c", commands, check=False)
        transcript = result.stdout + result.stderr
        (build_dir / f"NATIVE-{component.upper()}-BUILD.LOG").write_text(transcript, encoding="utf-8")
        if result.returncode or "Errors: 0" not in transcript or "CODE SIZE" not in transcript:
            raise SystemExit(f"native BDOS build failed\n{transcript}")
        native_com = work / "BDOS.COM"
        run("cpmcp", "-f", "ibm-3740", str(disks / "driveb.dsk"),
            "0:BDOS.COM", str(native_com))
        cross = (build_dir / f"{component}.bin").read_bytes()
        native = native_com.read_bytes()[:len(cross)]
        if native != cross:
            raise SystemExit(f"native/cross BDOS mismatch: linked size {native_com.stat().st_size}")
        (build_dir / f"{component}-native.bin").write_bytes(native)
        print(f"{component.upper()}: {len(native)} byte-identical bytes")


if __name__ == "__main__":
    main()
