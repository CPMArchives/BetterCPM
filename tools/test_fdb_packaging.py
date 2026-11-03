#!/usr/bin/env python3
"""Qualify deterministic FDB generation and CP/M-file packaging."""
from pathlib import Path
import tempfile

from build_fdf_catalog import build
from build_source_disk import extract_files, install_files
from fdf_v1 import read_fdb, compile_file


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        first = build(Path(directory) / "first" / "DISK.FDB").read_bytes()
        second = build(Path(directory) / "second" / "DISK.FDB").read_bytes()
        assert first == second
        database = read_fdb(first)
        assert len(database.descriptors) == 108
        assert all(item.supported for item in database.descriptors)
        historical = read_fdb(compile_file(Path(__file__).resolve().parents[1]/"metadata/DISK.FDF"))
        assert database.descriptors[:107] == historical.descriptors
        native = database.descriptors[-1].format
        assert native.ident == "BCPM780"
        assert (native.spt, native.off, native.dsm, native.logical_track) == (80, 2, 389, "CYLINDER")
        assert native.off * native.spt * 128 == 20480
        compatibility = next(d.format for d in database.descriptors if d.ident == "MMI012")
        assert compatibility.off * compatibility.spt * 128 == 10240

        image = install_files([(0, "DISK.FDB", first)])
        recovered = extract_files(image)[(0, "DISK.FDB")]
        assert recovered[:len(first)] == first
        assert len(recovered) == len(first)
        read_fdb(recovered)

    print("FDB packaging: deterministic 108-entry catalogue survives CP/M read-back")


if __name__ == "__main__":
    main()
