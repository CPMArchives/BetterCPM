#!/usr/bin/env python3
"""Exercise BetterCP/M STAT on disposable physical-format media."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from run_trs80_command import DEFAULT_EMULATOR, ROOT


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(command: str, image: Path) -> str:
    completed = subprocess.run([
        "python3", str(ROOT / "tools/run_trs80_command.py"), command,
        "--emulator", str(DEFAULT_EMULATOR), "--image", str(image),
        "--boot-delay", "3000", "--run-delay", "4000",
    ], cwd=ROOT, check=True, capture_output=True, text=True)
    return completed.stdout


def main() -> None:
    if not DEFAULT_EMULATOR.is_file():
        raise SystemExit(f"missing trs80gp: {DEFAULT_EMULATOR}")
    subprocess.run(["python3", str(ROOT / "tools/build_stat.py")],
                   cwd=ROOT, check=True)
    with tempfile.TemporaryDirectory(prefix="bettercpm-stat-") as temporary:
        work = Path(temporary)
        small = work / "small.bin"
        small.write_bytes(b"STAT fixture")
        large = work / "large.bin"
        large.write_bytes(bytes(20_000))
        image = work / "stat.dmk"
        subprocess.run([
            "python3", str(ROOT / "tools/build_trs80_boot.py"),
            "--output", str(image),
            "--include-as", f"TARGET.DAT={small}",
            "--include-as", f"LARGE.DAT={large}",
            "--include-user-as", f"3:U3ONLY.DAT={small}",
        ], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)

        output = run("STAT MEM", image)
        require("Current TPA                  : 54273 bytes" in output,
                f"bad live TPA report: {output!r}")
        require("Maximum loadable COM         : 54272 bytes" in output,
                f"COM record-size ceiling is wrong: {output!r}")
        require("Protected RSX allocation     : 0 bytes" in output
                and "Reclaimable CCP/CPX region" in output,
                f"incomplete memory report: {output!r}")

        output = run("STAT LARGE.DAT", image)
        require(output.count("LARGE   .DAT") == 1 and "K Bytes" in output,
                f"multi-extent file was not aggregated: {output!r}")

        output = run("STAT 3:U3ONLY.DAT", image)
        require("U3ONLY  .DAT" in output and "\nA0>" in output,
                f"numeric user qualifier failed or leaked state: {output!r}")

        output = run("STAT DSK:", image)
        require("128 Byte Records/Track" in output
                and "Kilobytes Remaining" in output and "\n0: Allocation" not in output,
                f"DPB report is empty: {output!r}")

        output = run("STAT VAL:", image)
        require("$R/O $R/W $SYS $DIR" in output and "Memory Status: MEM" in output,
                f"operand inventory is incomplete: {output!r}")

        output = run("STAT CON:=CRT:", image)
        require("CON: is CRT:" in output, f"IOBYTE assignment failed: {output!r}")

        output = run("STAT TARGET.DAT $R/O", image)
        require("TARGET  .DAT set to R/O" in output,
                f"file attribute operation failed: {output!r}")

    print("STAT disk, file, attribute, device, DU, and memory tests passed")


if __name__ == "__main__":
    main()
