#!/usr/bin/env python3
"""Prove DIR lists a cpmtools compact first extent on an EXM=1 disk."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
FORMAT = "bettercpm-default"
IMAGE_SIZE = 40 * 2 * 18 * 256


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", type=Path, default=ROOT / "build/z80pack")
    parser.add_argument("--simulator", type=Path,
                        default=Path.home() / "projects/git/z80pack/cpmsim/cpmsim")
    args = parser.parse_args()
    image = args.image_dir.resolve()
    simulator = args.simulator.expanduser().resolve()
    if not simulator.is_file():
        raise SystemExit(f"missing cpmsim: {simulator}")

    with tempfile.TemporaryDirectory(prefix="bettercpm-dir-exm-",
                                     dir="/private/tmp") as temporary:
        work = Path(temporary)
        shutil.copytree(image / "disks", work / "disks")
        shutil.copy2(image / "diskdefs", work / "diskdefs")
        medium = work / "disks/driveb.dsk"
        medium.unlink(missing_ok=True)
        medium.write_bytes(b"\xE5" * IMAGE_SIZE)
        subprocess.run(["mkfs.cpm", "-f", FORMAT, str(medium)],
                       check=True, cwd=work)
        payload = work / "BIGFILE.DAT"
        payload.write_bytes(bytes(20_000))
        subprocess.run(["cpmcp", "-T", "raw", "-f", FORMAT, str(medium),
                        str(payload), "0:BIGFILE.DAT"], check=True, cwd=work)

        script = work / "dir-exm.exp"
        report = work / "report.txt"
        script.write_text(r'''set timeout 30
set send_slow {1 .02}
log_file -noappend [lindex $argv 2]
expect_before timeout {puts "TEST TIMEOUT"; exit 1}
proc prompt {} {
 expect {
  -re {\r+\n[A-D]0>} {}
  timeout {puts "PROMPT TIMEOUT"; exit 1}
  eof {puts "UNEXPECTED EXIT"; exit 1}
 }
}
spawn [lindex $argv 0] -z -d [lindex $argv 1]
expect -exact "Booting..."
prompt
send -s -- "DIR B:BIGFILE.DAT\r"
expect -exact "B: BIGFILE  DAT"
prompt
send -s -- "BYE\r"
expect eof
''')
        environment = dict(os.environ)
        environment["PATH"] = (str(simulator.parent / "srctools") +
                               os.pathsep + environment["PATH"])
        run = subprocess.run(["expect", str(script), str(simulator),
                              str(work / "disks"), str(report)], cwd=work,
                             env=environment, capture_output=True, text=True,
                             timeout=120)
        if run.returncode:
            raise AssertionError(f"z80pack EXM DIR failed\n{run.stdout[-2000:]}")
        transcript = report.read_text(errors="replace")
        count = transcript.count("B: BIGFILE  DAT")
        if count != 1:
            raise AssertionError(
                f"DIR displayed the EXM=1 file {count} times\n{transcript[-2000:]}"
            )
    print("PASS: DIR lists one cpmtools 20K EX=1 file exactly once")


if __name__ == "__main__":
    main()
