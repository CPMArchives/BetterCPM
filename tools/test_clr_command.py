#!/usr/bin/env python3
"""Verify the resident CLR command on the Model 4 console."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from run_trs80_command import DEFAULT_EMULATOR, ROOT, key_args

IMAGE = ROOT / "build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk"


def main() -> None:
    for path in (DEFAULT_EMULATOR, IMAGE):
        if not path.is_file():
            raise SystemExit(f"missing CLR test input: {path}")
    with tempfile.TemporaryDirectory(prefix="bettercpm-clr-") as temporary:
        disk = Path(temporary, IMAGE.name)
        disk.write_bytes(IMAGE.read_bytes())
        invocation = [str(DEFAULT_EMULATOR), "-m4", "-batch", "-turbo",
                      "-d0", str(disk), "-id", "3000"]
        for command in ("VER", "CLR"):
            invocation.extend(key_args(command + "\r"))
            invocation.extend(("-id", "2500"))
        invocation.extend(("-it", "-ix"))
        subprocess.run(invocation, cwd=temporary, check=True)
        screen = Path(temporary, "trs80-text-0.bin").read_bytes()[:80 * 24]
    if b"BetterCP/M 0.3" in screen or b"A0>CLR" in screen:
        raise SystemExit(f"CLR left old screen contents visible: {screen!r}")
    if b"A0>" not in screen:
        raise SystemExit(f"CLR did not leave a fresh prompt: {screen!r}")
    print("CLR cleared the Model 4 display and left a fresh prompt")


if __name__ == "__main__":
    main()
