#!/usr/bin/env python3
"""Exercise resident and transient REN against disposable physical DMKs."""
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
        "--run-delay", "3000", "--in-place",
    ]
    for response in responses:
        arguments.extend(("--response", f"3000:{response}\\r"))
    completed = subprocess.run(arguments, cwd=ROOT, check=True,
                               capture_output=True, text=True)
    return completed.stdout


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    if not DEFAULT_EMULATOR.is_file():
        raise SystemExit(f"missing trs80gp: {DEFAULT_EMULATOR}")
    with tempfile.TemporaryDirectory(prefix="bettercpm-ren-") as temporary:
        work = Path(temporary)
        fixture = work / "fixture.bin"
        fixture.write_bytes(b"rename fixture")
        drive_a, drive_b = work / "a.dmk", work / "b.dmk"
        build_image(drive_a, ("OLD.DAT", fixture), ("KEEP.DAT", fixture))
        build_image(drive_b, ("OLD.DAT", fixture))

        run("REN NEW.DAT=OLD.DAT", drive_a, drive_b)
        new_output = run("DIR NEW.DAT", drive_a, drive_b)
        old_output = run("DIR OLD.DAT", drive_a, drive_b)
        require("NEW      DAT" in new_output and "NO FILE" in old_output,
                "exact resident rename did not move the directory name")

        output = run("REN KEEP.DAT=OLD.DAT", drive_a, drive_b)
        require("FILE EXISTS" in output,
                "existing destination did not report FILE EXISTS")

        output = run("REN ABSENT.DAT=MISSING.DAT", drive_a, drive_b)
        require("NO FILE" in output, "missing source did not report NO FILE")

        output = run("REN NEW.DAT OLD.DAT", drive_a, drive_b)
        require("?" in output, "space was incorrectly accepted as REN separator")

        output = run("REN WILD.DAT=K*.DAT", drive_a, drive_b)
        require("?" in output, "ambiguous REN source was not rejected")

        output = run("REN NEW.DAT=OLD.DAT EXTRA", drive_a, drive_b)
        require("?" in output, "REN ignored a trailing operand")

        output = run("REN B:XNEW.DAT=A:KEEP.DAT", drive_a, drive_b)
        require("?" in output, "cross-drive REN was not rejected")

        run("REN B:NEW.DAT=B:OLD.DAT", drive_a, drive_b)
        output = run("DIR B:NEW.DAT", drive_a, drive_b)
        require("NEW      DAT" in output and "A0>" in output,
                "same-drive qualified rename failed or changed current DU")

        # Removing BASIC.CPX must expose the ordinary transient fallback.
        build_image(drive_a, ("OLD.DAT", fixture))
        run("CPX UNLOAD BASIC", drive_a, drive_b, "REN NEW.DAT=OLD.DAT")
        output = run("DIR NEW.DAT", drive_a, drive_b)
        require("NEW      DAT" in output,
                "transient REN.COM fallback did not rename its source")

    print("REN resident and transient physical compatibility tests passed")


if __name__ == "__main__":
    main()
