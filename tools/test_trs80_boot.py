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
EXPECTED_LINES = (
    b"",
    b"A0>DIR",
    b"A: HELLO    COM : CPX      COM : RSX      COM : RSXTEST  COM",
    b"A: RSX2TST  COM : ERA      COM : REN      COM : TYPE     COM",
    b"A: DIR      COM : USER     COM : CLR      COM : VER      COM",
    b"A: WARM     COM : BASIC    CPX : HELLO    CPX : HELLO    RSX",
    b"A: ECHO     RSX",
    b"",
    b"A0>HELLO WORLD",
    b"Hello from BetterCP/M WORLD",
    b"A0>\xA0",                 # reverse-video blank at end-of-line cursor
)


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
            "-id", "3000",
            "-ik", "0", "10", "-id", "4", "-ik", "0", "0", "-id", "4",
            "-ik", "1", "2", "-id", "4", "-ik", "1", "0", "-id", "4",
            "-ik", "2", "4", "-id", "4", "-ik", "2", "0", "-id", "4",
            "-ik", "6", "1", "-id", "4", "-ik", "6", "0", "-id", "5000",
            "-ik", "1", "1", "-id", "4", "-ik", "1", "0", "-id", "4",
            "-ik", "0", "20", "-id", "4", "-ik", "0", "0", "-id", "4",
            "-ik", "1", "10", "-id", "4", "-ik", "1", "0", "-id", "4",
            "-ik", "1", "10", "-id", "4", "-ik", "1", "0", "-id", "4",
            "-ik", "1", "80", "-id", "4", "-ik", "1", "0", "-id", "4",
            "-ik", "6", "80", "-id", "4", "-ik", "6", "0", "-id", "4",
            "-ik", "2", "80", "-id", "4", "-ik", "2", "0", "-id", "4",
            "-ik", "1", "80", "-id", "4", "-ik", "1", "0", "-id", "4",
            "-ik", "2", "4", "-id", "4", "-ik", "2", "0", "-id", "4",
            "-ik", "1", "10", "-id", "4", "-ik", "1", "0", "-id", "4",
            "-ik", "0", "10", "-id", "4", "-ik", "0", "0", "-id", "4",
            "-ik", "6", "1", "-id", "4", "-ik", "6", "0",
            "-id", "5000", "-it", "-ix",
        ], cwd=temporary, check=True)
        snapshot = Path(temporary, "trs80-text-0.bin")
        if not snapshot.is_file():
            raise SystemExit(f"trs80gp produced no text snapshot; files: "
                             f"{[path.name for path in Path(temporary).iterdir()]}")
        captured = snapshot.read_bytes()
        screen = captured[:80 * 24]
        expected = bytearray(b" " * len(screen))
        for row, line in enumerate(EXPECTED_LINES):
            expected[row * 80:row * 80 + len(line)] = line
        if screen != expected:
            visible = [(index, byte) for index, byte in enumerate(screen)
                       if byte != 0x20][:80]
            raise SystemExit(f"boot test failed; visible bytes {visible}; "
                             f"screen begins {screen[:240]!r}")
        if any(captured[80 * 24:]):
            raise SystemExit("boot test wrote beyond the 80x24 video region")
    for line in EXPECTED_LINES:
        visible = bytes(byte & 0x7F for byte in line).decode("ascii")
        print(visible + (" [reverse cursor]" if any(byte & 0x80 for byte in line)
                         else ""))
    print("TRS-80 Model 4 DIR, command-tail, and HELLO.COM test passed")


if __name__ == "__main__":
    main()
