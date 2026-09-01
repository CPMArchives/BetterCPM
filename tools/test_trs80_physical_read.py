#!/usr/bin/env python3
"""Boot a dedicated image and verify an off-track, opposite-side read."""
import subprocess
import tempfile
from pathlib import Path

from build_montezuma_extended_790k import RAW_SIZE, SECTOR_SIZE, TRACK_DATA_SIZE, build
from build_trs80_boot import ROOT, SOURCE, BUILD, assemble

EMULATOR = Path("/Users/nathanael/trs80/trs80gp-2/mac/trs80gp.app/Contents/MacOS/trs80gp")
ASSEMBLER = Path("/Users/nathanael/bin/z80asm")
EXPECTED = b"BIOS physical read verified"
SIGNATURE = b"BetterCP/M C2 H1 S10"


def main() -> None:
    boot = assemble(ASSEMBLER, SOURCE / "boot.mac", BUILD / "boot.bin", 0x4300)
    test = assemble(ASSEMBLER, SOURCE / "diskread.mac", BUILD / "diskread.bin", 0x5000)
    raw = bytearray([0xE5]) * RAW_SIZE
    raw[:SECTOR_SIZE] = boot.ljust(SECTOR_SIZE, b"\0")
    raw[SECTOR_SIZE:2 * SECTOR_SIZE] = test.ljust(SECTOR_SIZE, b"\0")
    track = (2 * 2 + 1) * TRACK_DATA_SIZE
    raw[track + 9 * SECTOR_SIZE:track + 9 * SECTOR_SIZE + len(SIGNATURE)] = SIGNATURE
    image = BUILD / "BetterCPM-physical-read-test.dmk"
    image.write_bytes(build(bytes(raw)))
    with tempfile.TemporaryDirectory(prefix="bettercpm-physical-read-") as temporary:
        subprocess.run([str(EMULATOR), "-m4", "-batch", "-turbo", "-d0", str(image),
                        "-id", "180", "-it", "-ix"], cwd=temporary, check=True)
        screen = Path(temporary, "trs80-text-0.bin").read_bytes()
    if not screen.startswith(EXPECTED):
        raise SystemExit(f"physical-read test failed: {screen[:80]!r}")
    print(EXPECTED.decode("ascii"))
    print("cylinder 2, side 1, sector 10 test passed")


if __name__ == "__main__":
    main()
