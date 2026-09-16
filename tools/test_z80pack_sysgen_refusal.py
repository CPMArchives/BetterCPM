#!/usr/bin/env python3
"""Prove SYSGEN safely rejects z80pack's data-only destination drives."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", type=Path,
                        default=ROOT / "build/z80pack")
    parser.add_argument("--simulator", type=Path,
                        default=Path.home() / "projects/git/z80pack/cpmsim/cpmsim")
    args = parser.parse_args()
    image = args.image_dir.resolve()
    simulator = args.simulator.expanduser().resolve()

    with tempfile.TemporaryDirectory(prefix="bettercpm-sysgen-refusal-",
                                     dir="/private/tmp") as temporary:
        work = Path(temporary)
        shutil.copytree(image / "disks", work / "disks")
        shutil.copy2(image / "diskdefs", work / "diskdefs")
        target = work / "disks/driveb.dsk"
        before = target.read_bytes()
        script = r'''set timeout 30
expect_before timeout {puts "TEST TIMEOUT"; exit 1}
proc prompt {} {
 expect {
  -re {\r+\nA0>} {}
  timeout {puts "PROMPT TIMEOUT"; exit 1}
  eof {puts "UNEXPECTED EXIT"; exit 1}
 }
}
spawn [lindex $argv 0] -z -d [lindex $argv 1]
expect -exact "Booting..."
prompt
send -- "SYSGEN A: B:\r"
expect -exact "Destination bootstrap geometry is not supported by this system package."
prompt
send -- "BYE\r"
expect eof
'''
        test = work / "test.exp"
        test.write_text(script)
        environment = dict(os.environ)
        environment["PATH"] = (str(simulator.parent / "srctools") +
                               os.pathsep + environment["PATH"])
        run = subprocess.run(
            ["expect", str(test), str(simulator), str(work / "disks")],
            cwd=work, env=environment, capture_output=True, text=True,
            timeout=90,
        )
        report = image / "sysgen-refusal-verification.txt"
        report.write_text(run.stdout + run.stderr)
        if run.returncode:
            raise AssertionError(
                f"z80pack SYSGEN refusal failed: {report}\n{run.stdout[-1500:]}"
            )
        assert target.read_bytes() == before, "SYSGEN changed rejected target"
    print("PASS: z80pack data-only target rejected without changing the image")


if __name__ == "__main__":
    main()
