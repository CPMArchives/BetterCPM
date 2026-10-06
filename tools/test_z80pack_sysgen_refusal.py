#!/usr/bin/env python3
"""Reject a real data-only target before any SYSGEN write."""
from pathlib import Path
import argparse
import shutil
import subprocess
import tempfile
from build_source_disk import install_files, z80pack_raw
from test_z80pack_native_build import build_binding_program
from test_z80pack_sysgen_install import session

ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", type=Path, default=ROOT / "build/z80pack")
    parser.add_argument("--simulator", type=Path,
                        default=Path.home() / "projects/git/z80pack/cpmsim/cpmsim")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="bettercpm-sysgen-refusal-") as temp:
        work = Path(temp)
        shutil.copytree(args.image_dir / "disks", work / "disks")
        shutil.copy2(args.image_dir / "diskdefs", work / "diskdefs")
        setup = build_binding_program(work)
        subprocess.run(["cpmcp", "-T", "raw", "-f", "bettercpm-default",
                        str(work / "disks/drivea.dsk"), str(setup), "0:"],
                       cwd=work, check=True)
        target = work / "disks/driveb.dsk"
        target.unlink()
        before = z80pack_raw(install_files([]))
        target.write_bytes(before)
        transcript = session(args.simulator, work / "disks", [
            (b"SETBUILD\r", b"A0>_ ", 30),
            (b"SYSGEN A: B:\r", b"A0>_ ", 30),
        ])
        (args.image_dir / "sysgen-refusal-verification.txt").write_bytes(transcript)
        assert b"Destination bootstrap geometry is not supported" in transcript
        assert b"Proceed (Y/N)?" not in transcript
        assert target.read_bytes() == before, "SYSGEN changed rejected target"
    print("PASS: data-only SYSGEN target refused before confirmation or writes")

if __name__ == "__main__":
    main()
