#!/usr/bin/env python3
"""Exercise the completed CP/M 2.2 DIR contract on physical DMK media."""
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


def run(command: str, image: Path, drive_b: Path, drive_c: Path) -> str:
    completed = subprocess.run([
        "python3", str(ROOT / "tools/run_trs80_command.py"), command,
        "--emulator", str(DEFAULT_EMULATOR), "--image", str(image),
        "--drive-b", str(drive_b), "--drive-c", str(drive_c),
        "--boot-delay", "3000", "--run-delay", "3000",
    ], cwd=ROOT, check=True, capture_output=True, text=True)
    return completed.stdout


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    if not DEFAULT_EMULATOR.is_file():
        raise SystemExit(f"missing trs80gp: {DEFAULT_EMULATOR}")
    with tempfile.TemporaryDirectory(prefix="bettercpm-dir-") as temporary:
        work = Path(temporary)
        small = work / "small.bin"
        small.write_bytes(b"fixture")
        big = work / "big.bin"
        big.write_bytes(bytes(20_000))
        drive_a, drive_b, drive_c = (work / name for name in ("a.dmk", "b.dmk", "c.dmk"))
        build_image(
            drive_a,
            "--include-as", f"PLAIN={small}",
            "--include-as", f"BIGFILE.DAT={big}",
            "--include-system-as", f"HIDDEN.SYS={small}",
        )
        build_image(drive_b, "--include-as", f"BONLY.TXT={small}")
        build_image(
            drive_c,
            "--include-as", f"C0ONLY.DAT={small}",
            "--include-user-as", f"3:C3ONLY.DAT={small}",
        )

        output = run("DIR HELLO.COM", drive_a, drive_b, drive_c)
        require("HELLO    COM" in output and "RSXTEST" not in output,
                "DIR exact selection did not restrict the listing")

        output = run("DIR ZZZ.*", drive_a, drive_b, drive_c)
        require("NO FILE" in output, "empty DIR search did not report NO FILE")

        output = run("DIR HIDDEN.SYS", drive_a, drive_b, drive_c)
        require("A: HIDDEN" not in output and "NO FILE" not in output,
                "DIR did not reproduce stock suppression of a matching SYS file: "
                f"{output!r}")

        output = run("DIR BIGFILE.DAT", drive_a, drive_b, drive_c)
        require(output.count("BIGFILE  DAT") == 1,
                "DIR displayed more than one entry for a multi-extent file")

        output = run("DIR B:BONLY.TXT", drive_a, drive_b, drive_c)
        require("B: BONLY    TXT" in output and "A0>" in output,
                "drive-qualified DIR failed or changed the current DU")

        output = run("DIR C3:", drive_a, drive_b, drive_c)
        require("C: C3ONLY   DAT" in output and "C0ONLY" not in output
                and "A0>" in output,
                "combined drive/user DIR failed or changed the current DU")

    print("DIR selection, empty, SYS, multi-extent, drive, and DU tests passed")


if __name__ == "__main__":
    main()
