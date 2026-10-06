#!/usr/bin/env python3
"""Focused physical TIME-provider qualification under trs80gp FreHD."""
from __future__ import annotations

import re
import subprocess
import hashlib
import json
import argparse
from trs80gp_launch import run as run_trs80gp
from add_cpm_file_to_dmk import extract_raw, add_file
from build_montezuma_extended_790k import build, SECTOR_SIZE
from build_trs80_boot import FILESYSTEM_FIRST_SECTOR, DIRECTORY_ENTRIES
from pathlib import Path

from run_trs80_command import DEFAULT_EMULATOR, ROOT, key_args

IMAGE = ROOT / "build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk"


def run(command: str, report: Path) -> bytes:
    work = report
    work.mkdir(parents=True, exist_ok=False)
    raw = extract_raw(IMAGE.read_bytes())
    directory = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE
    for index in range(DIRECTORY_ENTRIES):
        offset = directory + index * 32
        if raw[offset] == 0 and bytes(value & 0x7F for value in raw[offset+1:offset+12]) == b'TIME    COM':
            raw[offset] = 0xE5
    add_file(raw, 'TIME.COM', (ROOT / 'build/utilities/TIME.COM').read_bytes())
    disk = work / "clock.dmk"
    disk.write_bytes(build(bytes(raw)))
    frehd = work / "frehd"
    frehd.mkdir()
    invocation = [str(DEFAULT_EMULATOR), "-m4", "-batch", "-turbo",
                  "-frehd_dir", str(frehd), "-d0", str(disk), "-id", "5000"]
    invocation.extend(key_args("RSX LOAD FREHDCLK\r"))
    invocation.extend(("-id", "8000", "-it"))
    invocation.extend(key_args(command + "\r"))
    invocation.extend(("-id", "3000"))
    invocation.extend(key_args("VER\r"))
    invocation.extend(("-id", "5000", "-it", "-ix"))
    (work / 'invocation.json').write_text(json.dumps(invocation, indent=2) + '\n')
    run_trs80gp(invocation, cwd=work, check=True, timeout=90)
    display = (work / "trs80-text-1.bin").read_bytes()[:80 * 24]
    (work / 'screen.txt').write_bytes(display)
    return display


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path,
                        default=ROOT / 'build/test-results/frehd-time')
    args = parser.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    for path in (DEFAULT_EMULATOR, IMAGE):
        if not path.is_file():
            raise SystemExit(f"missing physical TIME test input: {path}")
    display = run("TIME", report / "get")
    if not re.search(rb"20[0-9]{2}-[01][0-9]-[0-3][0-9] [0-2][0-9]:[0-5][0-9]:[0-5][0-9]",
                     display):
        raise SystemExit(f"TIME did not display a clock sample: {display!r}")
    if b"BetterCP/M 0.3" not in display:
        raise SystemExit("TIME did not return to a working CCP prompt")
    provider = run("TIME /PROVIDER", report / "provider")
    for expected in (b"Provider: FREHDCLK", b"TIME service ABI 01.00",
                     b"GET, read-only", b"BetterCP/M 0.3"):
        if expected not in provider:
            raise SystemExit(f"provider report lacks {expected!r}: {provider!r}")
    rejected = run("TIME /SET 01 00 12 34 56", report / "set")
    for expected in (b"Clock provider does not support SET.", b"BetterCP/M 0.3"):
        if expected not in rejected:
            raise SystemExit(f"SET rejection lacks {expected!r}: {rejected!r}")
    if b"Clock set." in rejected:
        raise SystemExit("read-only provider falsely reported SET success")
    (report / 'evidence.json').write_text(json.dumps({
        'result': 'PASS',
        'utility_sha256': hashlib.sha256((ROOT / 'build/utilities/TIME.COM').read_bytes()).hexdigest(),
        'simulator_sha256': hashlib.sha256(DEFAULT_EMULATOR.read_bytes()).hexdigest(),
        'source_image_sha256': hashlib.sha256(IMAGE.read_bytes()).hexdigest(),
        'checks': ['GET', 'provider name and read-only capability', 'SET_UNSUPPORTED', 'live CCP']
    }, indent=2) + '\n')
    print("FREHDCLK discovery, RTC read, provider report and read-only SET passed")


if __name__ == "__main__":
    main()
