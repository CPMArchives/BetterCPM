#!/usr/bin/env python3
"""Boot the generated disk in trs80gp and verify the stage-one screen."""
from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EMULATOR = Path("/Users/nathanael/trs80/trs80gp-2/mac/trs80gp.app/Contents/MacOS/trs80gp")
DEFAULT_IMAGE = ROOT / "build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk"
EXPECTED = b"BetterCP/M stage 1 - TRS-80 Model 4"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emulator", type=Path, default=DEFAULT_EMULATOR)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    args = parser.parse_args()
    for path in (args.emulator, args.image):
        if not path.is_file():
            raise SystemExit(f"missing test input: {path}")
    with tempfile.TemporaryDirectory(prefix="bettercpm-trs80gp-") as temporary:
        subprocess.run([
            str(args.emulator), "-m4", "-batch", "-turbo", "-d0", str(args.image),
            "-id", "120", "-it", "-ix",
        ], cwd=temporary, check=True)
        screen = Path(temporary, "trs80-text-0.bin").read_bytes()
        if not screen.startswith(EXPECTED):
            raise SystemExit(f"boot test failed; screen begins {screen[:80]!r}")
    print(EXPECTED.decode("ascii"))
    print("TRS-80 Model 4 boot test passed")


if __name__ == "__main__":
    main()
