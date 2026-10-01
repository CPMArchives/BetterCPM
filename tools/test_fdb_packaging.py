#!/usr/bin/env python3
"""Qualify deterministic FDB generation and CP/M-file packaging."""
from pathlib import Path
import tempfile

from build_fdf_catalog import build
from build_source_disk import extract_files, install_files
from fdf_v1 import read_fdb


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        first = build(Path(directory) / "first" / "DISK.FDB").read_bytes()
        second = build(Path(directory) / "second" / "DISK.FDB").read_bytes()
        assert first == second
        database = read_fdb(first)
        assert len(database.descriptors) == 107
        assert all(item.supported for item in database.descriptors)

        image = install_files([(0, "DISK.FDB", first)])
        recovered = extract_files(image)[(0, "DISK.FDB")]
        assert recovered[:len(first)] == first
        assert len(recovered) == len(first)
        read_fdb(recovered)

    print("FDB packaging: deterministic 107-entry catalogue survives CP/M read-back")


if __name__ == "__main__":
    main()
