#!/usr/bin/env python3
"""Exercise resident SAVE on disposable physical DMKs."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build
from build_trs80_boot import (
    ALLOCATION_BLOCK_BYTES,
    DIRECTORY_ENTRIES,
    FILESYSTEM_FIRST_SECTOR,
    SECTOR_SIZE,
    cpm_name,
)
from run_trs80_command import DEFAULT_EMULATOR, ROOT


def build_image(output: Path, *files: tuple[str, Path]) -> None:
    command = ["python3", str(ROOT / "tools/build_trs80_boot.py"),
               "--output", str(output)]
    for name, source in files:
        command.extend(("--include-as", f"{name}={source}"))
    subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)


def fill_directory(image: Path) -> None:
    """Consume every free directory entry without consuming data blocks."""
    raw = extract_raw(image.read_bytes())
    directory = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE
    for index in range(DIRECTORY_ENTRIES):
        start = directory + index * 32
        if raw[start] != 0xE5:
            continue
        entry = bytearray(32)
        entry[0] = 0
        entry[1:9] = f"X{index:07d}".encode("ascii")
        entry[9:12] = b"TMP"
        raw[start:start + 32] = entry
    image.write_bytes(build(bytes(raw)))


def run(command: str, image: Path, drive_b: Path) -> str:
    completed = subprocess.run([
        "python3", str(ROOT / "tools/run_trs80_command.py"), command,
        "--emulator", str(DEFAULT_EMULATOR), "--image", str(image),
        "--drive-b", str(drive_b), "--boot-delay", "3000",
        "--run-delay", "5000", "--in-place",
    ], cwd=ROOT, check=True, capture_output=True, text=True)
    return completed.stdout


def file_bytes(image: Path, filename: str) -> bytes | None:
    raw = extract_raw(image.read_bytes())
    name, suffix = cpm_name(filename)
    directory = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE
    extents: list[tuple[int, bytes]] = []
    for index in range(DIRECTORY_ENTRIES):
        entry = raw[directory + index * 32:directory + (index + 1) * 32]
        if (entry[0] == 0 and entry[1:9] == name and
                bytes(value & 0x7F for value in entry[9:12]) == suffix):
            extent = entry[12] + (entry[14] << 5)
            extents.append((extent, bytes(entry)))
    if not extents:
        return None
    content = bytearray()
    for _extent, entry in sorted(extents):
        records = entry[15]
        remaining = records * 128
        for offset in range(16, 32, 2):
            block = int.from_bytes(entry[offset:offset + 2], "little")
            if not block or not remaining:
                break
            amount = min(ALLOCATION_BLOCK_BYTES, remaining)
            start = directory + block * ALLOCATION_BLOCK_BYTES
            content.extend(raw[start:start + amount])
            remaining -= amount
    return bytes(content)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    if not DEFAULT_EMULATOR.is_file():
        raise SystemExit(f"missing trs80gp: {DEFAULT_EMULATOR}")
    with tempfile.TemporaryDirectory(prefix="bettercpm-save-") as temporary:
        work = Path(temporary)
        old = work / "old.bin"
        old.write_bytes(b"OLD DESTINATION" * 20)
        drive_a, drive_b = work / "a.dmk", work / "b.dmk"
        build_image(drive_a, ("OLD.COM", old))
        build_image(drive_b)

        run("SAVE 4 SNAP.COM", drive_a, drive_b)
        require(len(file_bytes(drive_a, "SNAP.COM") or b"") == 4 * 256,
                "SAVE 4 did not create exactly four 256-byte pages")

        run("SAVE 0 EMPTY.COM", drive_a, drive_b)
        require(file_bytes(drive_a, "EMPTY.COM") == b"",
                "SAVE 0 did not create a valid empty file")

        run("SAVE 1 OLD.COM", drive_a, drive_b)
        replacement = file_bytes(drive_a, "OLD.COM")
        require(replacement is not None and len(replacement) == 256 and
                not replacement.startswith(b"OLD DESTINATION"),
                "SAVE did not replace an existing destination")

        output = run("SAVE 1 B:OTHER.COM", drive_a, drive_b)
        require(len(file_bytes(drive_b, "OTHER.COM") or b"") == 256 and
                "A0>" in output,
                "drive-qualified SAVE failed or changed the current DU")

        for command in ("SAVE 256 LARGE.COM", "SAVE X BAD.COM",
                        "SAVE 1 WILD.*", "SAVE 1 TWO.COM EXTRA"):
            require("?" in run(command, drive_a, drive_b),
                    f"invalid SAVE syntax was accepted: {command}")

        full = work / "full-directory.dmk"
        build_image(full)
        fill_directory(full)
        full_output = run("SAVE 1 FULL.COM", full, drive_b)
        require("NO SPACE" in full_output,
                f"full-directory SAVE did not report NO SPACE: {full_output!r}")

    print("SAVE page-count, zero, replacement, DU, syntax, and no-space tests passed")


if __name__ == "__main__":
    main()
