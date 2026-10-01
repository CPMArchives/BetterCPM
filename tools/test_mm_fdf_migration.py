#!/usr/bin/env python3
"""Prove the qualified FDF v1 catalogue preserves admitted MM source facts."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import tempfile

from fdf_v1 import parse, read_fdb, serialize
from migrate_mm_fdf import EXCLUDED, migrate, records


ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "metadata" / "DISK.FDF"
EXCLUSIONS = ROOT / "metadata" / "mm-fdf-exclusions.json"
EXPECTED_FDB_SHA256 = "4dea7bd989580fc13f61e79d47e92466a440799c41b002f4caba65ec8f893c03"


def main() -> None:
    generated, rejected = migrate()
    assert CATALOGUE.read_text(encoding="ascii") == generated
    assert json.loads(EXCLUSIONS.read_text(encoding="ascii")) == rejected

    formats = parse(generated, str(CATALOGUE))
    binary = serialize(formats)
    digest = hashlib.sha256(binary).hexdigest()
    decoded = read_fdb(binary)
    assert len(formats) == len(decoded.descriptors) == 107
    assert len(binary) == 8320
    assert digest == EXPECTED_FDB_SHA256
    assert all(item.supported and item.format is not None for item in decoded.descriptors)

    admitted = [item for item in records() if item.name not in EXCLUDED]
    assert len(admitted) == 107
    assert len(rejected["excluded_records"]) == 5
    assert {item["name"] for item in rejected["excluded_records"]} == set(EXCLUDED)

    mixed = cylinder = 0
    for source, compiled in zip(admitted, formats):
        p = source.parameters
        expected_id = ("MMF" if source.source == "DISK.FDF" else "MMI") + \
            f"{source.ordinal:03d}"
        assert compiled.ident == expected_id
        assert (compiled.spt, compiled.bsh, compiled.blm, compiled.exm,
                compiled.dsm, compiled.drm, compiled.al0, compiled.al1,
                compiled.cks, compiled.off) == p[:10]
        assert compiled.psectors == p[10]
        assert compiled.secsize == 128 << p[11]
        assert compiled.cylinders == p[12]
        assert compiled.sides == (2 if p[13] & 0x40 else 1)
        assert compiled.encoding == ("MFM" if p[13] & 0x80 else "FM")
        assert compiled.invert == bool(p[13] & 0x10)
        assert compiled.sector_ids == source.sector_ids
        assert compiled.side_order == ("SIDE_MAJOR" if p[13] & 0x02 else "ALTERNATING")
        assert compiled.side1_direction == ("REVERSE" if p[13] & 0x01 else "FORWARD")
        assert compiled.track_id_mode == ("CONTINUOUS" if p[13] & 0x04 else "PER_CYLINDER")
        assert compiled.sector_id_mode == ("CONTINUOUS" if p[13] & 0x08 else "RESTART")
        if "SUPER" in source.name and source.name.startswith("Montezuma Micro"):
            assert compiled.sector_sizes == (1024,) * 5 + (512,)
            mixed += 1
        else:
            assert compiled.sector_sizes is None
        if source.name.startswith("Micro-Abacus"):
            assert compiled.logical_track == "CYLINDER"
            cylinder += 1
        else:
            assert compiled.logical_track == "SURFACE"

    assert mixed == 4 and cylinder == 1
    assert len({item.ident for item in formats}) == 107
    assert len({item.description for item in formats}) == 107
    assert max(map(lambda item: len(item.description), formats)) <= 32

    # Regeneration is deterministic and does not depend on the output location.
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "DISK.FDF"
        path.write_text(generated, encoding="ascii")
        assert serialize(parse(path.read_text(encoding="ascii"), str(path))) == binary

    print("MM FDF migration: 107 admitted, 5 preserved exclusions, 8320-byte FDB")
    print("FDB SHA-256:", digest)


if __name__ == "__main__":
    main()
