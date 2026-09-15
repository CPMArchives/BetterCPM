#!/usr/bin/env python3
"""Verify that unsupported logical drives cannot alias the current disk."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from run_trs80_command import DEFAULT_EMULATOR, ROOT


def main() -> None:
    if not DEFAULT_EMULATOR.is_file():
        raise SystemExit(f"missing trs80gp: {DEFAULT_EMULATOR}")
    with tempfile.TemporaryDirectory(prefix="bettercpm-invalid-drive-") as temporary:
        work = Path(temporary)
        sentinel = work / "sentinel.bin"
        sentinel.write_bytes(b"drive A sentinel")
        image = work / "boot.dmk"
        subprocess.run([
            "python3", str(ROOT / "tools/build_trs80_boot.py"),
            "--output", str(image), "--include-as", f"AONLY.TXT={sentinel}",
        ], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        result = subprocess.run([
            "python3", str(ROOT / "tools/run_trs80_command.py"), "DIR E:",
            "--emulator", str(DEFAULT_EMULATOR), "--image", str(image),
            "--boot-delay", "3000", "--run-delay", "3000",
        ], cwd=ROOT, check=True, capture_output=True, text=True).stdout
        if "INVALID DRIVE" not in result or "AONLY" in result:
            raise SystemExit(f"unsupported drive E reached drive A: {result!r}")
    print("Unsupported logical drive E is rejected without accessing drive A")


if __name__ == "__main__":
    main()
