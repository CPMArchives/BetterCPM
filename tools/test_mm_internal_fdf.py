#!/usr/bin/env python3
"""Verify DISK-INT.FDF against the authenticated MM CONFIG catalogue."""
from __future__ import annotations

import json
from pathlib import Path

from fdf_format import parse_fdf


ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "third_party/montezuma/DISK-INT.FDF"
METADATA = ROOT / "metadata/mm-builtin-formats.json"


def main() -> None:
    source = json.loads(METADATA.read_text(encoding="ascii"))["formats"]
    formats = parse_fdf(CATALOGUE)
    assert len(formats) == len(source) == 16

    for actual, expected in zip(formats, source):
        parameters = (
            actual.spt, actual.bsh, actual.blm, actual.exm,
            actual.dsm, actual.drm, actual.al0, actual.al1,
            actual.cks, actual.off, actual.physical_sectors,
            actual.size_code, actual.cylinders, actual.flags,
        )
        assert actual.name == expected["name"]
        assert parameters == tuple(expected["parameters"])
        assert actual.sector_ids == tuple(expected["sector_ids"])

    image = CATALOGUE.read_bytes()
    text = image.split(b"\x1a", 1)[0]
    assert len(image) % 128 == 0
    assert image[len(text):] == b"\x1a" * (len(image) - len(text))
    assert b"\n" not in text.replace(b"\r\n", b"")
    print("PASS: 16 CONFIG formats match metadata and CP/M FDF serialization")


if __name__ == "__main__":
    main()
