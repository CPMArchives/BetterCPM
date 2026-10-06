#!/usr/bin/env python3
"""Qualify TIME.COM GET, provider display and read-only SET under cpmsim."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from test_z80pack_sysgen_install import session

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", type=Path, default=ROOT / "build/z80pack")
    parser.add_argument("--simulator", type=Path,
                        default=Path.home() / "projects/git/z80pack/cpmsim/cpmsim")
    parser.add_argument("--report", type=Path,
                        default=ROOT / "build/test-results/z80pack-time")
    args = parser.parse_args()
    report = args.report.resolve()
    # Keep failures and media intact; choose another report path for a rerun.
    report.mkdir(parents=True, exist_ok=False)
    work = report / "runtime"
    work.mkdir()
    shutil.copytree(args.image_dir / "disks", work / "disks")
    shutil.copy2(args.image_dir / "diskdefs", work / "diskdefs")
    utility = ROOT / "build/utilities/TIME.COM"
    subprocess.run(["cpmrm", "-T", "raw", "-f", "bettercpm-default",
                    str(work / "disks/drivea.dsk"), "0:TIME.COM"],
                   cwd=work, check=True)
    subprocess.run(["cpmcp", "-T", "raw", "-f", "bettercpm-default",
                    str(work / "disks/drivea.dsk"), str(utility), "0:TIME.COM"],
                   cwd=work, check=True)
    commands = ["TIME", "RSX LOAD ZPRTC", "TIME /PROVIDER", "TIME",
                "TIME /SET 01 00 12 34 56", "TIME",
                "TIME /SET 01 00 24 00 00", "VER"]
    transcript = session(args.simulator.resolve(), work / "disks",
                         [(command.encode() + b"\r", b"A0>_ ", 15)
                          for command in commands], report / "transcript.txt")
    # Slice at echoed commands so stale earlier output cannot satisfy a check.
    blocks = []
    cursor = 0
    for command in commands:
        start = transcript.index(command.encode(), cursor)
        end = transcript.index(b"A0>_ ", start)
        blocks.append(transcript[start:end])
        cursor = end
    assert b"No TIME provider is loaded" in blocks[0], blocks[0]
    assert b"Provider: ZPRTC" in blocks[2], blocks[2]
    assert b"GET, read-only" in blocks[2], blocks[2]
    assert b"does not support SET" in blocks[4], blocks[4]
    assert b"Clock set." not in blocks[4], blocks[4]
    assert b"Usage: TIME" in blocks[6], blocks[6]
    assert b"BetterCP/M" in blocks[7], blocks[7]
    samples = []
    pattern = rb"([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})"
    for index in [3, 5]:
        match = re.search(pattern, blocks[index])
        assert match, blocks[index]
        samples.append(datetime.datetime.strptime(match[1].decode(), "%Y-%m-%d %H:%M:%S"))
    assert 0 <= (samples[1] - samples[0]).total_seconds() <= 30, samples
    (report / "evidence.json").write_text(json.dumps({
        "commands": commands, "samples": list(map(str, samples)),
        "utility_sha256": hashlib.sha256(utility.read_bytes()).hexdigest(),
        "simulator": str(args.simulator.resolve()),
        "simulator_sha256": hashlib.sha256(args.simulator.read_bytes()).hexdigest(),
        "result": "PASS"}, indent=2) + "\n")
    print("PASS: TIME missing service, ZPRTC GET/provider, read-only SET, input rejection and live CCP")


if __name__ == "__main__":
    main()
