#!/usr/bin/env python3
"""Prove raw images are interchangeable between BetterCP/M and cpmtools."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MARKER = b"BETTERCPM CPMTOOLS INTERCHANGE PASS\r\n"
PAYLOAD = (MARKER * ((1280 + len(MARKER) - 1) // len(MARKER)))[:1280]
CASES = (
    ("mm-standard-system", 40 * 18 * 256, "A", 40,
     "Montezuma Micro Standard SYSTEM"),
    ("mm-80t-ds-data", 160 * 10 * 512, "H", 80,
     "Montezuma Micro 80T DS DATA"),
    ("ampro-little-board", 40 * 10 * 512, ".F", 40,
     "Ampro Little Board"),
    ("ampro-little-board-ds", 80 * 10 * 512, ".G", 40,
     "Ampro Little Board double-sided"),
)


def run_case(image: Path, simulator: Path,
             case: tuple[str, int, str, int, str]) -> None:
    slug, image_size, selection, cylinders, description = case
    fmt = "bettercpm-" + slug
    with tempfile.TemporaryDirectory(prefix=f"bettercpm-z80pack-{slug}-",
                                     dir="/private/tmp") as tmp:
        work = Path(tmp)
        shutil.copytree(image / "disks", work / "disks")
        shutil.copy2(image / "diskdefs", work / "diskdefs")
        medium = work / "disks/driveb.dsk"
        medium.write_bytes(b"\xe5" * image_size)
        subprocess.run(["mkfs.cpm", "-f", fmt, str(medium)], check=True,
                       cwd=work)
        source = work / "HOST.DAT"
        source.write_bytes(PAYLOAD)
        subprocess.run(["cpmcp", "-T", "raw", "-f", fmt, str(medium),
                        str(source), "0:HOST.DAT"], check=True, cwd=work)

        select = ""
        for key in selection:
            select += (f'send -s -- "{key}"\n'
                       'expect -exact "Your choice:"\n')
        select = select.rsplit('expect -exact "Your choice:"\n', 1)[0]
        physical = ""
        if cylinders == 80:
            physical = r'''send -s -- "F"
expect -exact "Your choice:"
send -s -- "B"
expect -exact "Physical disk drive 1"
expect -exact "Your choice:"
send -s -- "B"
expect -exact "Track choices:"
expect -exact "Your choice:"
send -s -- "D"
expect -exact "Physical disk drive 1"
expect -exact "Your choice:"
send -s -- "\003"
prompt
send -s -- "CONFIG\r"
expect -exact "Your choice:"
'''
        script = r'''set timeout 30
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
send -s -- "CONFIG\r"
expect -exact "Your choice:"
@PHYSICAL@
send -s -- "G"
expect -exact "Choose the letter of the drive to change:"
expect -exact "Your choice:"
send -s -- "B"
expect -exact "Choose the format to be used for drive B"
expect -exact "Your choice:"
@SELECT@
expect -exact {Which physical disk drive is to be used [0-3]?}
send -s -- "1"
expect -exact "Disk configuration changed (until cold boot)."
expect -exact "Push ENTER"
send -s -- "\r"
expect -exact "Your choice:"
send -s -- "\003"
prompt
send -s -- "TYPE B:HOST.DAT\r"
expect -exact "BETTERCPM CPMTOOLS INTERCHANGE PASS"
prompt
send -s -- "COPY B:HOST.DAT B:ROUND.DAT\r"
prompt
send -s -- "BYE\r"
expect eof
'''.replace("@PHYSICAL@", physical).replace("@SELECT@", select)
        test = work / "interchange.exp"
        test.write_text(script)
        env = dict(os.environ)
        env["PATH"] = str(simulator.parent / "srctools") + os.pathsep + env["PATH"]
        report = image / f"interchange-{slug}.txt"
        run = subprocess.run(["expect", str(test), str(simulator),
                              str(work / "disks"), str(report)], cwd=work, env=env,
                             capture_output=True, text=True, timeout=240)
        if run.returncode:
            raise AssertionError(
                f"z80pack interchange failed: {report}\n{run.stdout[-2000:]}")

        extracted = work / "ROUND.DAT"
        subprocess.run(["cpmcp", "-T", "raw", "-f", fmt, str(medium),
                        "0:ROUND.DAT", str(extracted)], check=True, cwd=work)
        actual = extracted.read_bytes()
        if actual != PAYLOAD:
            mismatch = next((index for index, pair in
                             enumerate(zip(actual, PAYLOAD))
                             if pair[0] != pair[1]),
                            min(len(actual), len(PAYLOAD)))
            raise AssertionError(f"{description}: extracted length {len(actual)} "
                                 f"!= {len(PAYLOAD)}, first mismatch {mismatch}")
        print(f"PASS: {description} is byte-identical after cpmtools -> "
              "BetterCP/M -> cpmtools")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", type=Path,
                        default=ROOT / "build/z80pack")
    parser.add_argument("--simulator", type=Path,
                        default=Path.home() / "projects/git/z80pack/cpmsim/cpmsim")
    args = parser.parse_args()
    image = args.image_dir.resolve()
    simulator = args.simulator.expanduser().resolve()
    for case in CASES:
        run_case(image, simulator, case)


if __name__ == "__main__":
    main()
