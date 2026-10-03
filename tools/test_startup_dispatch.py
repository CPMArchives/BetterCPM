#!/usr/bin/env python3
"""Prove that BCST dispatch occurs once on cold boot and rejects bad input."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from fdf_format import select_fdf
from startup_record import build as startup_record
from system_layout import LAYOUT

ROOT = Path(__file__).resolve().parents[1]
FORMAT_NAME = "California Computer Systems (40T, DS, DD, 332K)"
MARKER = "STARTUP-PROBE"


def install_record(disk: Path, record: bytes) -> None:
    """Install the two logical BCST records in one raw CCS image."""
    fmt = select_fdf(ROOT / "third_party/montezuma/DISK.FDF", FORMAT_NAME)
    raw = bytearray(disk.read_bytes())
    record_map = fmt.raw_record_map()
    for index in range(2):
        logical = index + 1
        track, slot = divmod(logical, fmt.spt)
        offset = track * fmt.raw_track_bytes + record_map[slot] * 128
        raw[offset:offset + 128] = record[index * 128:(index + 1) * 128]
    disk.write_bytes(raw)


def marker_program() -> bytes:
    """Return a COM file that prints one unique marker and warm-boots."""
    code = bytes((
        0x11, 0x0B, 0x01,       # LD DE,010BH
        0x0E, 0x09,             # LD C,9
        0xCD, 0x05, 0x00,       # CALL 0005H
        0xC3, 0x00, 0x00,       # JP 0000H
    ))
    return code + MARKER.encode("ascii") + b"$"


def run_case(image: Path, simulator: Path, name: str, record: bytes,
             expected_count: int) -> None:
    with tempfile.TemporaryDirectory(prefix=f"bettercpm-startup-{name}-") as tmp:
        work = Path(tmp)
        shutil.copytree(image / "disks", work / "disks")
        shutil.copy2(image / "diskdefs", work / "diskdefs")
        disk = work / "disks/drivea.dsk"
        install_record(disk, record)
        program = work / "MARK.COM"
        program.write_bytes(marker_program())
        subprocess.run([
            "cpmcp", "-T", "raw", "-f", "bettercpm-default",
            str(disk), str(program), "0:MARK.COM",
        ], cwd=work, check=True)

        log = work / "session.txt"
        script = work / "test.exp"
        script.write_text("""set timeout 20
log_file -noappend [lindex $argv 2]
expect_before timeout {puts "TEST TIMEOUT"; exit 1}
spawn [lindex $argv 0] -z -d [lindex $argv 1]
expect -exact {A0>_ }
send -- "WARM\\r"
expect -exact {A0>_ }
send -- "BYE\\r"
expect eof
""")
        env = dict(os.environ)
        env["PATH"] = str(simulator.parent / "srctools") + os.pathsep + env["PATH"]
        run = subprocess.run(
            ["expect", str(script), str(simulator), str(work / "disks"), str(log)],
            cwd=work, env=env, capture_output=True, text=True, timeout=60,
        )
        text = log.read_text(errors="replace") if log.exists() else run.stdout
        if run.returncode:
            raise AssertionError(f"{name}: cpmsim failed\n{text[-1500:]}")
        count = text.count(MARKER)
        if count != expected_count:
            raise AssertionError(
                f"{name}: expected {expected_count} startup markers, observed {count}\n"
                f"{text[-1500:]}"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", type=Path,
                        default=ROOT / "build/z80pack")
    parser.add_argument("--simulator", type=Path,
                        default=Path.home() / "projects/git/z80pack/cpmsim/cpmsim")
    args = parser.parse_args()
    image = args.image_dir.resolve()
    simulator = args.simulator.expanduser().resolve()

    enabled = startup_record("MARK", system_base=LAYOUT["SYSTEM"])
    run_case(image, simulator, "enabled", enabled, 1)

    invalid = bytearray(enabled)
    invalid[12] ^= 1
    run_case(image, simulator, "invalid-checksum", bytes(invalid), 0)
    print("PASS: cold startup dispatches once, does not repeat after WARM, "
          "and rejects a corrupt BCST record")


if __name__ == "__main__":
    main()
