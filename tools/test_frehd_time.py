#!/usr/bin/env python3
"""Focused physical TIME-provider qualification under trs80gp FreHD."""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from run_trs80_command import DEFAULT_EMULATOR, ROOT, key_args

IMAGE = ROOT / "build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk"


def run(command: str) -> bytes:
    with tempfile.TemporaryDirectory(prefix="bettercpm-frehd-time-") as temporary:
        work = Path(temporary)
        disk = work / "clock.dmk"
        disk.write_bytes(IMAGE.read_bytes())
        frehd = work / "frehd"
        frehd.mkdir()
        invocation = [str(DEFAULT_EMULATOR), "-m4", "-batch", "-turbo",
                      "-frehd_dir", str(frehd), "-d0", str(disk), "-id", "5000"]
        invocation.extend(key_args("RSX LOAD FREHDCLK\r"))
        invocation.extend(("-id", "3000"))
        invocation.extend(key_args(command + "\r"))
        invocation.extend(("-id", "3000"))
        invocation.extend(key_args("VER\r"))
        invocation.extend(("-id", "5000", "-it", "-ix"))
        subprocess.run(invocation, cwd=work, check=True, timeout=75)
        return (work / "trs80-text-0.bin").read_bytes()[:80 * 24]


def main() -> None:
    for path in (DEFAULT_EMULATOR, IMAGE):
        if not path.is_file():
            raise SystemExit(f"missing physical TIME test input: {path}")
    display = run("TIME")
    if not re.search(rb"20[0-9]{2}-[01][0-9]-[0-3][0-9] [0-2][0-9]:[0-5][0-9]:[0-5][0-9]",
                     display):
        raise SystemExit(f"TIME did not display a clock sample: {display!r}")
    if b"BetterCP/M 0.3" not in display:
        raise SystemExit("TIME did not return to a working CCP prompt")
    provider = run("TIME /PROVIDER")
    for expected in (b"Provider: FREHDCLK", b"TIME service ABI 01.00",
                     b"GET, read-only", b"BetterCP/M 0.3"):
        if expected not in provider:
            raise SystemExit(f"provider report lacks {expected!r}: {provider!r}")
    print("FREHDCLK discovery, RTC read, conversion, and provider report passed")


if __name__ == "__main__":
    main()
