#!/usr/bin/env python3
"""Verify visible CCP Ctrl-C acknowledgement and physical warm boot."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from run_trs80_command import DEFAULT_EMULATOR, ROOT

DEFAULT_IMAGE = ROOT / "build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk"


def main() -> None:
    for path in (DEFAULT_EMULATOR, DEFAULT_IMAGE):
        if not path.is_file():
            raise SystemExit(f"missing Ctrl-C test input: {path}")
    with tempfile.TemporaryDirectory(prefix="bettercpm-ctrl-c-") as temporary:
        work = Path(temporary)
        image = work / "drive-a.dmk"
        shutil.copy2(DEFAULT_IMAGE, image)
        command = [
            str(DEFAULT_EMULATOR), "-m4", "-batch", "-turbo",
            "-d0", str(image), "-id", "3000",
            # Model 4 modifier row bit 2 is Control; C is row 0 bit 3.
            "-ik", "7", "4", "-ik", "0", "8", "-id", "20",
            "-ik", "0", "0", "-ik", "7", "0", "-id", "3000",
            "-it", "-ix",
        ]
        subprocess.run(command, cwd=work, check=True)
        captured = (work / "trs80-text-0.bin").read_bytes()[:80 * 24]
    rows = [captured[index:index + 80].rstrip()
            for index in range(0, len(captured), 80)]
    try:
        acknowledgement = rows.index(b"A0>^C")
    except ValueError as error:
        raise SystemExit(f"Ctrl-C acknowledgement was not visible: {rows!r}") from error
    # The active reverse-video cursor follows the prompt as a high-bit byte,
    # so the captured row need not compare equal to the three printable bytes.
    if not any(row.startswith(b"A0>")
               for row in rows[acknowledgement + 1:]):
        raise SystemExit("Ctrl-C did not return to a fresh A0> prompt")
    print("physical Ctrl-C displayed ^C and completed warm boot")


if __name__ == "__main__":
    main()
