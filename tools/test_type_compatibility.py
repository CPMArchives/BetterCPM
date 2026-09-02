#!/usr/bin/env python3
"""Exercise resident and transient TYPE on disposable physical DMKs."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from run_trs80_command import DEFAULT_EMULATOR, ROOT


def build_image(output: Path, *files: tuple[str, Path]) -> None:
    command = ["python3", str(ROOT / "tools/build_trs80_boot.py"),
               "--output", str(output)]
    for name, source in files:
        command.extend(("--include-as", f"{name}={source}"))
    subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)


def run(command: str, image: Path, drive_b: Path, *responses: str) -> str:
    arguments = [
        "python3", str(ROOT / "tools/run_trs80_command.py"), command,
        "--emulator", str(DEFAULT_EMULATOR), "--image", str(image),
        "--drive-b", str(drive_b), "--boot-delay", "3000",
        "--run-delay", "3000",
    ]
    for response in responses:
        arguments.extend(("--response", f"3000:{response}"))
    completed = subprocess.run(arguments, cwd=ROOT, check=True,
                               capture_output=True, text=True)
    return completed.stdout


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    if not DEFAULT_EMULATOR.is_file():
        raise SystemExit(f"missing trs80gp: {DEFAULT_EMULATOR}")
    with tempfile.TemporaryDirectory(prefix="bettercpm-type-") as temporary:
        work = Path(temporary)
        literal = work / "literal.txt"
        literal.write_bytes(b"ALPHA\r\nDOLLAR $ SIGN\r\nEND\x1aHIDDEN\r\n")
        long_file = work / "long.txt"
        long_file.write_bytes(b"".join(
            f"LINE {number:02d}\r\n".encode("ascii") for number in range(1, 31)
        ) + b"\x1a")
        other = work / "other.txt"
        other.write_bytes(b"DRIVE B TEXT\r\n\x1a")
        drive_a, drive_b = work / "a.dmk", work / "b.dmk"
        build_image(drive_a, ("README.TXT", literal), ("LONG.TXT", long_file))
        build_image(drive_b, ("README.TXT", other))

        output = run("TYPE README.TXT", drive_a, drive_b)
        require("ALPHA" in output and "DOLLAR $ SIGN" in output and
                "END" in output and "HIDDEN" not in output,
                "resident TYPE did not preserve literal text or CP/M EOF")

        output = run("TYPE B:README.TXT", drive_a, drive_b)
        require("DRIVE B TEXT" in output and "A0>" in output,
                "drive-qualified TYPE failed or changed the current DU")

        require("?" in run("TYPE MISSING.TXT", drive_a, drive_b),
                "missing TYPE target did not report a command error")
        require("?" in run("TYPE R*.TXT", drive_a, drive_b),
                "TYPE accepted an ambiguous filename")

        paused = run("TYPE LONG.TXT /P", drive_a, drive_b)
        require("--More--" in paused and "LINE 30" not in paused,
                "TYPE /P did not stop after its first page")
        continued = run("TYPE LONG.TXT /P", drive_a, drive_b, " ")
        require("LINE 30" in continued,
                "space did not continue TYPE /P to the final page")

        output = run("CPX UNLOAD BASIC", drive_a, drive_b,
                     "TYPE README.TXT\\r")
        require("DOLLAR $ SIGN" in output and "HIDDEN" not in output,
                "transient TYPE.COM fallback did not display the file")

    print("TYPE resident, paging, DU, EOF, and transient tests passed")


if __name__ == "__main__":
    main()
