#!/usr/bin/env python3
"""Format trs80gp's internal unformatted DMK after a live media change."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from build_montezuma_extended_790k import crc16
from run_trs80_command import DEFAULT_EMULATOR
from test_disk_utilities import keys


ROOT = Path(__file__).resolve().parents[1]
BOOT = ROOT / "build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk"
INITIAL = ROOT / "build/trs80/BetterCPM-Build-80T-DS-800K.dmk"
RESULTS = ROOT / "build/test-results/disk-utilities/unformatted-internal"
IDS = (1, 3, 5, 7, 9, 2, 4, 6, 8, 10)


def verify_disk(path: Path) -> None:
    """Check every ID, CRC and erased byte without trusting the BIOS."""
    image = path.read_bytes()
    track_length = int.from_bytes(image[2:4], "little")
    assert image[1] == 80 and track_length == 0x18EA
    for cylinder in range(80):
        for side in range(2):
            base = 16 + (cylinder * 2 + side) * track_length
            track = image[base:base + track_length]
            found = []
            for slot in range(10):
                idam = int.from_bytes(track[slot * 2:slot * 2 + 2], "little") & 0x3FFF
                assert track[idam:idam + 3] == bytes((0xFE, cylinder, side))
                found.append(track[idam + 3])
                assert track[idam + 4] == 2
                ident = track[idam:idam + 5]
                assert track[idam + 5:idam + 7] == crc16(b"\xA1" * 3 + ident).to_bytes(2, "big")
                mark = track.find(b"\xA1\xA1\xA1\xFB", idam + 7)
                assert mark >= 0
                assert track[mark + 4:mark + 516] == bytes([0xE5]) * 512
                assert track[mark + 516:mark + 518] == crc16(
                    track[mark:mark + 516]).to_bytes(2, "big")
            assert tuple(found) == IDS


def main() -> None:
    for path in (DEFAULT_EMULATOR, BOOT, INITIAL):
        if not path.is_file():
            raise SystemExit(f"missing unformatted-media test input: {path}")
    with tempfile.TemporaryDirectory(prefix="bettercpm-unformatted-") as temporary:
        work = Path(temporary)
        old_disk = work / "old.dmk"
        shutil.copy2(INITIAL, old_disk)
        command = [
            str(DEFAULT_EMULATOR), "-m4", "-batch", "-turbo",
            "-d0", str(BOOT), "-d1", str(old_disk), "-id", "3500",
            # Match the operator's GUI sequence: eject a mounted disk, then
            # insert trs80gp's built-in single-sided unformatted DMK object.
            "-im", "eject", "1", "1", "-id", "30",
            "-im", "insert", "1", "dmk", "-id", "30",
        ]
        for entered, delay in (("DUP\r", 6000), ("A", 700),
                               ("B", 1000), ("Y", 0)):
            command += keys(entered)
            if delay:
                command += ["-id", str(delay)]
        command += ["-itime", "0", "-iw", "Format complete.", "-it", "-ix"]
        subprocess.run(command, cwd=work, check=True, timeout=180)

        capture = next(work.glob("trs80-text-*.bin"))
        raw = capture.read_bytes()[:80 * 24]
        screen = "\n".join(
            bytes(value & 0x7F for value in raw[offset:offset + 80])
            .decode("ascii", "replace").rstrip()
            for offset in range(0, 80 * 24, 80)
        )
        assert "Format complete." in screen
        assert "Tracks written and verified: 00160" in screen
        formatted = next(work.glob("trs80-disk1-*.dsk"))
        verify_disk(formatted)
        RESULTS.mkdir(parents=True, exist_ok=True)
        shutil.copy2(formatted, RESULTS / "formatted-from-internal.dmk")
        (RESULTS / "screen.txt").write_text(screen + "\n")
    print("PASS: live-inserted internal unformatted DMK; 160 tracks and 1,600 sectors verified")


if __name__ == "__main__":
    main()
