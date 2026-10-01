#!/usr/bin/env python3
"""Prove that CONFIG accepts the packaged DISK.FDB under cpmsim."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", type=Path, default=ROOT / "build/z80pack")
    parser.add_argument(
        "--simulator", type=Path,
        default=Path.home() / "projects/git/z80pack/cpmsim/cpmsim",
    )
    args = parser.parse_args()
    image = args.image_dir.resolve()
    simulator = args.simulator.expanduser().resolve()
    with tempfile.TemporaryDirectory(prefix="bettercpm-config-fdb-") as tmp:
        work = Path(tmp)
        shutil.copytree(image / "disks", work / "disks")
        script = r'''set timeout 25
expect_before timeout {puts "TEST TIMEOUT"; exit 1}
proc prompt {} {
 expect {
  -exact {A0>_ } {}
  timeout {puts "PROMPT TIMEOUT"; exit 1}
  eof {puts "UNEXPECTED EXIT"; exit 1}
 }
}
spawn [lindex $argv 0] -z -d [lindex $argv 1]
expect -exact "Booting..."
prompt
send -- "CONFIG\r"
expect -exact "Configuration options:"
send -- "G"
expect -exact "Choose the letter of the drive to change:"
send -- "B"
expect -exact "Choose the format to be used for drive B"
expect -exact "Access Matrix 40T SS"
send -- "A"
expect -exact "Format selected:"
expect -exact "Access Matrix 40T SS"
expect -exact "Which physical disk drive is to be used \[0-3\]?"
send -- "1"
expect -exact "Disk configuration changed (until cold boot)."
send -- "\r"
expect -exact "Choose the letter of the drive to change:"
send -- "\003"
expect -exact "Configuration options:"
send -- "\003"
prompt
send -- "BYE\r"
expect eof
'''
        (work / "test.exp").write_text(script)
        env = dict(os.environ)
        env["PATH"] = str(simulator.parent / "srctools") + os.pathsep + env["PATH"]
        run = subprocess.run(
            ["expect", str(work / "test.exp"), str(simulator), str(work / "disks")],
            cwd=work, env=env, capture_output=True, text=True, timeout=60,
        )
        if run.returncode:
            raise AssertionError("CONFIG FDB startup failed\n" + run.stdout[-2000:])
    print("PASS: CONFIG selects and attaches a packaged FDB descriptor under cpmsim")


if __name__ == "__main__":
    main()
