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
    args = parser.parse_args()
    entry = args.suite / "suite/build/ENTRYTST.COM"
    bdos = args.suite / "suite/build/BDOSTEST.COM"
    mdir = ROOT / "third_party/montezuma/MDIR.COM"
    for path in (entry, bdos, mdir):
        if not path.is_file():
            raise SystemExit(f"missing compatibility input: {path}")
    subprocess.run([
        "python3", str(ROOT / "tools/build_trs80_boot.py"),
        "--include", str(entry),
        "--include", str(bdos),
        "--include", str(mdir),
        "--output", str(args.output),
    ], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
