#!/usr/bin/env python3
"""Build a BetterCP/M disk carrying the complete independent compatibility suite."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", type=Path,
                        default=ROOT.parent / "cpm-compatibility")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/trs80/BetterCPM-Conformance-First-Pass.dmk")
    parser.add_argument("--drive-b-output", type=Path,
                        default=ROOT / "build/trs80/BetterCPM-Conformance-Drive-B.dmk")
    parser.add_argument("--drive-c-output", type=Path,
                        default=ROOT / "build/trs80/BetterCPM-Conformance-Drive-C.dmk")
    parser.add_argument("--drive-d-output", type=Path,
                        default=ROOT / "build/trs80/BetterCPM-Conformance-Drive-D-Full.dmk")
    parser.add_argument("--blank-output", type=Path,
                        default=ROOT / "build/trs80/BetterCPM-BIOSTEST-Blank-790K.dmk")
    parser.add_argument("--system-only", action="store_true",
                        help="build only the suite boot disk, without legacy scratch images")
    args = parser.parse_args()
    programs = ("ENTRYTST", "BDOSTEST", "FILETEST", "RANDTEST", "DIRTEST",
                "CONSTEST", "CCPTEST", "DISKTEST", "BIOSTEST", "ERRTEST",
                "ECOTEST", "CPUTEST", "SCRATCH")
    build = args.suite / "suite/build"
    payload = args.suite / "suite/runtime-payload"
    bdos = build / "BDOSTEST.COM"
    paths = [build / (name + ".COM") for name in programs]
    paths += sorted(payload.glob("BT*.DAT"))
    paths += [payload / "CPMTEST.CFG", args.suite / "external/sysinfo/SYSINFO.COM"]
    for path in paths:
        if not path.is_file():
            raise SystemExit(f"missing compatibility input: {path}")
    # Keep the suite's published binaries tied to their published sources.
    # A test disk made with a stray old COM is no yardstick for the new BIOS.
    import hashlib
    for line in (build / "SHA256SUMS.txt").read_text().splitlines():
        digest, name = line.split()
        if hashlib.sha256((build / name).read_bytes()).hexdigest() != digest:
            raise SystemExit(f"suite checksum mismatch: {name}")
    command = ["python3", str(ROOT / "tools/build_trs80_boot.py")]
    for path in paths:
        command.extend(("--include", str(path)))
    command.extend(("--include-user-as", f"1:DIRTEST.COM={build / 'DIRTEST.COM'}"))
    for name in ("BDSA.TMP", "BDSB.TMP"):
        command.extend(("--include-as", f"{name}={bdos}"))
    command.extend(("--include-as", f"COPYING.TXT={args.suite / 'LICENSE'}"))
    command.extend(("--output", str(args.output)))
    subprocess.run(command, cwd=ROOT, check=True)
    if args.system_only:
        return
    # BDOSTEST's multi-drive cases expect these conventional scratch fixtures.
    subprocess.run([
        "python3", str(ROOT / "tools/build_trs80_boot.py"),
        "--include-as", f"BDSA.TMP={bdos}",
        "--include-as", f"BDSB.TMP={bdos}",
        "--output", str(args.drive_b_output),
    ], cwd=ROOT, check=True)
    subprocess.run([
        "python3", str(ROOT / "tools/build_trs80_boot.py"),
        "--cross-fixture",
        "--output", str(args.drive_c_output),
    ], cwd=ROOT, check=True)
    # D: is a data-only capacity fixture.  Building it as a boot disk also
    # installs the growing BetterCP/M utility collection, making the amount of
    # filler stale whenever the distribution changes.
    import build_trs80_boot as boot
    from build_montezuma_extended_790k import build, RAW_SIZE
    boot.FILESYSTEM_FIRST_SECTOR = 0
    boot.BLOCK_COUNT = RAW_SIZE // boot.ALLOCATION_BLOCK_BYTES
    raw = bytearray(b"\xe5" * RAW_SIZE)
    full = bytearray(128 * 128)
    full[-128:-120] = b"FULL-127"
    filler_blocks = boot.BLOCK_COUNT - boot.FIRST_DATA_BLOCK - 9
    boot.install_files(raw, [
        ("BTFULL.DAT", bytes(full)),
        ("BTREL.DAT", bytes(128)),
        ("BTFILL.DAT", bytes(filler_blocks * boot.ALLOCATION_BLOCK_BYTES)),
    ])
    args.drive_d_output.parent.mkdir(parents=True, exist_ok=True)
    args.drive_d_output.write_bytes(build(bytes(raw)))
    # Patch 2026-09-02: do not use build_trs80_boot.py for the controlled
    # BIOSTEST medium.  Every bootable image deliberately contains HELLO.COM,
    # so an image made that way is not a blank CP/M filesystem even when no
    # extra files are requested.  The scratch drive need not itself boot.
    subprocess.run([
        "python3", str(ROOT / "tools/build_montezuma_extended_790k.py"),
        str(args.blank_output),
    ], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
