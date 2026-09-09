#!/usr/bin/env python3
"""Exercise RCP COPY and MOVE on disposable SYSTEM and DATA media."""
from __future__ import annotations

import tempfile
from pathlib import Path

from run_trs80_command import DEFAULT_EMULATOR
from test_save_compatibility import (
    build_data_image,
    build_image,
    file_bytes,
    run,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def same_records(content: bytes | None, expected: bytes) -> bool:
    if content is None:
        return False
    rounded = (len(expected) + 127) & ~127
    return len(content) == rounded and content[:len(expected)] == expected


def main() -> None:
    if not DEFAULT_EMULATOR.is_file():
        raise SystemExit(f"missing trs80gp: {DEFAULT_EMULATOR}")
    with tempfile.TemporaryDirectory(prefix="bettercpm-copy-move-") as temporary:
        work = Path(temporary)
        payload = bytes((index * 29 + 7) & 0xFF for index in range(777))
        source = work / "source.bin"
        source.write_bytes(payload)
        drive_a, drive_b = work / "a.dmk", work / "b.dmk"
        build_image(drive_a, ("SOURCE.DAT", source))
        build_data_image(drive_b)

        output = run("COPY A:SOURCE.DAT B:COPY.DAT", drive_a, drive_b, 15000)
        require(same_records(file_bytes(drive_b, "COPY.DAT", 0), payload),
                f"source-first COPY failed: {output!r}")
        require("A0>" in output, "COPY did not restore the caller DU")

        output = run("COPY B:ALT.DAT:=A:SOURCE.DAT", drive_a, drive_b, 15000)
        require(same_records(file_bytes(drive_b, "ALT.DAT", 0), payload),
                f"assignment-form COPY failed: {output!r}")

        before = file_bytes(drive_b, "COPY.DAT", 0)
        output = run("COPY A:SOURCE.DAT B:COPY.DAT", drive_a, drive_b, 10000)
        require("FILE EXISTS" in output and
                file_bytes(drive_b, "COPY.DAT", 0) == before,
                "COPY overwrote an existing destination")

        output = run("MOVE B:MOVED.DAT:=A:SOURCE.DAT", drive_a, drive_b, 15000)
        require(same_records(file_bytes(drive_b, "MOVED.DAT", 0), payload),
                f"MOVE destination failed: {output!r}")
        require(file_bytes(drive_a, "SOURCE.DAT") is None,
                "MOVE did not erase its source after a successful close")
        require("A0>" in output, "MOVE did not restore the caller DU")

    print("COPY/MOVE syntax, cross-DU data, overwrite, erase, and restore passed")


if __name__ == "__main__":
    main()
