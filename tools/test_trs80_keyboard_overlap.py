#!/usr/bin/env python3
"""Verify that overlapping Model 4 key releases do not drop the next key."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from run_trs80_command import DEFAULT_EMULATOR, ROOT, key_args

DEFAULT_IMAGE = ROOT / "build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk"


def main() -> None:
    for path in (DEFAULT_EMULATOR, DEFAULT_IMAGE):
        if not path.is_file():
            raise SystemExit(f"missing keyboard-test input: {path}")
    with tempfile.TemporaryDirectory(prefix="bettercpm-key-overlap-") as temporary:
        command = [str(DEFAULT_EMULATOR), "-m4", "-batch", "-turbo",
                   "-d0", str(DEFAULT_IMAGE), "-id", "1200"]
        command.extend(key_args("HELLO "))
        # Hold A, press B before releasing A, then release them in order. The
        # former whole-matrix KEYUP loop returned A only after B had vanished.
        command.extend(("-ik", "0", "2", "-id", "500",
                        "-ik", "0", "6", "-id", "100",
                        "-ik", "0", "4", "-id", "500",
                        "-ik", "0", "0", "-id", "8"))
        command.extend(key_args("\r"))
        command.extend(("-id", "2500", "-it", "-ix"))
        subprocess.run(command, cwd=temporary, check=True)
        captured = Path(temporary, "trs80-text-0.bin").read_bytes()[:80 * 24]
    if b"A>HELLO AB" not in captured or b"Hello from BetterCP/M AB" not in captured:
        raise SystemExit(f"overlapping A/B input was not preserved: {captured[:320]!r}")
    print("overlapping A/B key transitions preserved both characters")


if __name__ == "__main__":
    main()
