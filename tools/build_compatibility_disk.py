#!/usr/bin/env python3
"""Build the first BetterCP/M disk carrying independent compatibility tools."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", type=Path,
                        default=ROOT.parent / "cpm-compatibility")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/trs80/BetterCPM-Conformance-First-Pass.dmk")
    parser.add_argument("--drive-b-output", type=Path,
                        default=ROOT / "build/trs80/BetterCPM-Conformance-Drive-B.dmk")
    parser.add_argument("--drive-c-output", type=Path,
                        default=ROOT / "build/trs80/BetterCPM-Conformance-Drive-C.dmk")
    parser.add_argument("--drive-d-output", type=Path,
                        default=ROOT / "build/trs80/BetterCPM-Conformance-Drive-D-Full.dmk")
    parser.add_argument("--blank-output", type=Path,
                        default=ROOT / "build/trs80/BetterCPM-BIOSTEST-Blank-790K.dmk")
    args = parser.parse_args()
    entry = args.suite / "suite/build/ENTRYTST.COM"
    bdos = args.suite / "suite/build/BDOSTEST.COM"
    filetest = args.suite / "suite/build/FILETEST.COM"
    randtest = args.suite / "suite/build/RANDTEST.COM"
    dirtest = args.suite / "suite/build/DIRTEST.COM"
    cputest = args.suite / "suite/build/CPUTEST.COM"
    biostest = args.suite / "suite/build/BIOSTEST.COM"
    payload = args.suite / "suite/runtime-payload"
    mdir = ROOT / "third_party/montezuma/MDIR.COM"
    era = ROOT / "build/utilities/ERA.COM"
    fixtures = sorted(payload.glob("BT*.DAT"))
    for path in (entry, bdos, filetest, randtest, dirtest, cputest, biostest,
                 mdir, era, *fixtures):
        if not path.is_file():
            raise SystemExit(f"missing compatibility input: {path}")
    command = [
        "python3", str(ROOT / "tools/build_trs80_boot.py"),
        "--include", str(entry),
        "--include", str(bdos),
        "--include", str(filetest),
        "--include", str(randtest),
        "--include", str(dirtest),
        "--include-user-as", f"1:DIRTEST.COM={dirtest}",
        "--include", str(cputest),
        "--include", str(biostest),
        "--include", str(mdir),
        "--include", str(era),
    ]
    for fixture in fixtures:
        command.extend(("--include", str(fixture)))
    command.extend(("--output", str(args.output)))
    subprocess.run(command, cwd=ROOT, check=True)
    # BDOSTEST's multi-drive cases expect these conventional scratch fixtures.
    subprocess.run([
        "python3", str(ROOT / "tools/build_trs80_boot.py"),
        "--include-as", f"BDSA.TMP={bdos}",
        "--include-as", f"BDSB.TMP={bdos}",
        "--output", str(args.drive_b_output),
    ], cwd=ROOT, check=True)
    subprocess.run([
        "python3", str(ROOT / "tools/build_trs80_boot.py"),
        "--cross-fixture",
        "--output", str(args.drive_c_output),
    ], cwd=ROOT, check=True)
    subprocess.run([
        "python3", str(ROOT / "tools/build_trs80_boot.py"),
        "--full-fixture",
        "--output", str(args.drive_d_output),
    ], cwd=ROOT, check=True)
    # Patch 2026-09-02: do not use build_trs80_boot.py for the controlled
    # BIOSTEST medium.  Every bootable image deliberately contains HELLO.COM,
    # so an image made that way is not a blank CP/M filesystem even when no
    # extra files are requested.  The scratch drive need not itself boot.
    subprocess.run([
        "python3", str(ROOT / "tools/build_montezuma_extended_790k.py"),
        str(args.blank_output),
    ], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
