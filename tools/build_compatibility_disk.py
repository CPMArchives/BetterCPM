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
    args = parser.parse_args()
    entry = args.suite / "suite/build/ENTRYTST.COM"
    bdos = args.suite / "suite/build/BDOSTEST.COM"
    filetest = args.suite / "suite/build/FILETEST.COM"
    payload = args.suite / "suite/runtime-payload"
    mdir = ROOT / "third_party/montezuma/MDIR.COM"
    fixtures = sorted(payload.glob("BT*.DAT"))
    for path in (entry, bdos, filetest, mdir, *fixtures):
        if not path.is_file():
            raise SystemExit(f"missing compatibility input: {path}")
    command = [
        "python3", str(ROOT / "tools/build_trs80_boot.py"),
        "--include", str(entry),
        "--include", str(bdos),
        "--include", str(filetest),
        "--include", str(mdir),
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


if __name__ == "__main__":
    main()
