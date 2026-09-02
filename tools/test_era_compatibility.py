#!/usr/bin/env python3
"""Exercise resident ERA against physical DMK directory state."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from run_trs80_command import DEFAULT_EMULATOR, ROOT


def build_image(output: Path, *arguments: str) -> None:
    subprocess.run([
        "python3", str(ROOT / "tools/build_trs80_boot.py"),
        "--output", str(output), *arguments,
    ], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)


def run(command: str, image: Path, drive_b: Path, *responses: str) -> str:
    arguments = [
        "python3", str(ROOT / "tools/run_trs80_command.py"), command,
        "--emulator", str(DEFAULT_EMULATOR), "--image", str(image),
        "--drive-b", str(drive_b), "--boot-delay", "3000",
        "--run-delay", "3000",
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
    with tempfile.TemporaryDirectory(prefix="bettercpm-era-") as temporary:
        work = Path(temporary)
        small, big = work / "small.bin", work / "big.bin"
        small.write_bytes(b"fixture")
        big.write_bytes(bytes(20_000))
        drive_a, drive_b = work / "a.dmk", work / "b.dmk"
        build_image(
            drive_a,
            "--include-as", f"DELETE.ME={small}",
            "--include-as", f"KEEP.COM={small}",
            "--include-as", f"BIGFILE.DAT={big}",
        )
        build_image(drive_b, "--include-as", f"BONLY.DAT={small}")

        output = run("ERA DELETE.ME", drive_a, drive_b, "DIR DELETE.ME")
        require("NO FILE" in output, "ERA exact name did not delete its file")

        output = run("ERA BIGFILE.DAT", drive_a, drive_b, "DIR BIGFILE.DAT")
        require("NO FILE" in output, "ERA did not delete every file extent")

        output = run("ERA B:BONLY.DAT", drive_a, drive_b, "DIR B:BONLY.DAT")
        require("NO FILE" in output and "A0>" in output,
                "drive-qualified ERA failed or changed the current DU")

        output = run("ERA MISSING.X", drive_a, drive_b)
        require("NO FILE" in output, "missing ERA target did not report NO FILE")

        output = run("ERA", drive_a, drive_b)
        require("NO FILE" in output, "argument-free ERA did not match stock behavior")

        # BASIC.CPX is optional.  Verify that removing it exposes the ordinary
        # ERA.COM fallback and that the fallback performs the same deletion.
        build_image(drive_a, "--include-as", f"DELETE.ME={small}")
        output = run(
            "CPX UNLOAD BASIC", drive_a, drive_b,
            "ERA DELETE.ME", "CPX LOAD BASIC", "DIR DELETE.ME",
        )
        require("NO FILE" in output,
                "transient ERA.COM fallback did not delete its target")

    print("ERA resident and transient physical compatibility tests passed")


if __name__ == "__main__":
    main()
