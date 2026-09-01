#!/usr/bin/env python3
"""Boot a BetterCP/M DMK, type one command, and print the captured screen."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EMULATOR = Path(
    "/Users/nathanael/trs80/trs80gp-2/mac/trs80gp.app/Contents/MacOS/trs80gp"
)
DEFAULT_IMAGE = ROOT / "build/trs80/BetterCPM-Conformance-First-Pass.dmk"
KEY_ROWS = (
    "@ABCDEFG",
    "HIJKLMNO",
    "PQRSTUVW",
    "XYZ\0\0\0\0\0",
    "01234567",
    "89:;,-./",
    "\r\0\0\0\0\0\0 ",
)


def key_args(text: str, delay: int = 4) -> list[str]:
    result: list[str] = []
    for character in text.upper():
        for row, characters in enumerate(KEY_ROWS):
            column = characters.find(character)
            if column >= 0:
                mask = f"{1 << column:X}"
                result.extend(("-ik", str(row), mask, "-id", str(delay),
                               "-ik", str(row), "0", "-id", str(delay)))
                break
        else:
            raise ValueError(f"character is not on the Model 4 matrix: {character!r}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command")
    parser.add_argument("--emulator", type=Path, default=DEFAULT_EMULATOR)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--boot-delay", type=int, default=1200)
    parser.add_argument("--run-delay", type=int, default=8000)
    parser.add_argument("--snapshot", type=Path)
    args = parser.parse_args()
    for path in (args.emulator, args.image):
        if not path.is_file():
            raise SystemExit(f"missing test input: {path}")

    with tempfile.TemporaryDirectory(prefix="bettercpm-command-") as temporary:
        command = [str(args.emulator), "-m4", "-batch", "-turbo",
                   "-d0", str(args.image), "-id", str(args.boot_delay)]
        command.extend(key_args(args.command + "\r"))
        command.extend(("-id", str(args.run_delay), "-it", "-ix"))
        subprocess.run(command, cwd=temporary, check=True)
        capture = Path(temporary, "trs80-text-0.bin")
        if not capture.is_file():
            raise SystemExit("trs80gp did not produce a text capture")
        data = capture.read_bytes()
        if args.snapshot:
            args.snapshot.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(capture, args.snapshot)

    screen = data[:80 * 24]
    for row in range(24):
        line = screen[row * 80:(row + 1) * 80].decode("ascii", "replace").rstrip()
        if line:
            print(line)


if __name__ == "__main__":
    main()
