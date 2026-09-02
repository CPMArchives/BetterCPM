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
            # Model 4 punctuation uses the shift row simultaneously with its
            # base key: '*' is Shift-minus and '?' is Shift-slash.
            shifted = {"*": (5, 5), "?": (5, 7)}
            if character in shifted:
                row, column = shifted[character]
                result.extend(("-ik", "7", "1",
                               "-ik", str(row), f"{1 << column:X}",
                               "-id", str(delay),
                               "-ik", str(row), "0",
                               "-ik", "7", "0",
                               "-id", str(delay)))
                continue
            raise ValueError(f"character is not on the Model 4 matrix: {character!r}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command")
    parser.add_argument("--emulator", type=Path, default=DEFAULT_EMULATOR)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--drive-b", type=Path,
                        help="optional DMK to mount as the second floppy")
    parser.add_argument("--drive-c", type=Path,
                        help="optional DMK to mount as the third floppy")
    parser.add_argument("--drive-d", type=Path,
                        help="optional DMK to mount as the fourth floppy")
    parser.add_argument("--boot-delay", type=int, default=1200)
    parser.add_argument("--run-delay", type=int, default=8000)
    parser.add_argument("--response", action="append", default=[],
                        help="delayed text, optionally DELAY:TEXT; repeatable")
    parser.add_argument("--response-delay", type=int, default=1200,
                        help="emulator delay before each interactive response")
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--in-place", action="store_true",
                        help="allow the emulator to modify the supplied images")
    args = parser.parse_args()
    inputs = [args.emulator, args.image]
    if args.drive_b:
        inputs.append(args.drive_b)
    if args.drive_c:
        inputs.append(args.drive_c)
    if args.drive_d:
        inputs.append(args.drive_d)
    for path in inputs:
        if not path.is_file():
            raise SystemExit(f"missing test input: {path}")
    image = args.image.resolve()
    drive_b = args.drive_b.resolve() if args.drive_b else None
    drive_c = args.drive_c.resolve() if args.drive_c else None
    drive_d = args.drive_d.resolve() if args.drive_d else None

    with tempfile.TemporaryDirectory(prefix="bettercpm-command-") as temporary:
        # Compatibility programs deliberately create, extend, and delete files.
        # Give every automated run private media so an interrupted emulator can
        # neither alter a reproducible build artifact nor collide with a later
        # run.  --in-place remains available for explicit persistence testing.
        if not args.in_place:
            isolated = Path(temporary, "drive-a.dmk")
            shutil.copy2(image, isolated)
            image = isolated
            if drive_b:
                isolated = Path(temporary, "drive-b.dmk")
                shutil.copy2(drive_b, isolated)
                drive_b = isolated
            if drive_c:
                isolated = Path(temporary, "drive-c.dmk")
                shutil.copy2(drive_c, isolated)
                drive_c = isolated
            if drive_d:
                isolated = Path(temporary, "drive-d.dmk")
                shutil.copy2(drive_d, isolated)
                drive_d = isolated
        command = [str(args.emulator), "-m4", "-batch", "-turbo",
                   "-d0", str(image), "-id", str(args.boot_delay)]
        if drive_b:
            command[6:6] = ["-d1", str(drive_b)]
        if drive_c:
            command[6:6] = ["-d2", str(drive_c)]
        if drive_d:
            command[6:6] = ["-d3", str(drive_d)]
        command.extend(key_args(args.command + "\r"))
        for response in args.response:
            delay_text, separator, response_text = response.partition(":")
            if separator and delay_text.isdigit():
                delay = int(delay_text)
                response = response_text
            else:
                delay = args.response_delay
            response = response.replace("\\r", "\r")
            command.extend(("-id", str(delay)))
            command.extend(key_args(response))
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
