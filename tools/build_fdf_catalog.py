#!/usr/bin/env python3
"""Compile and independently verify the qualified FDF v1 catalogue."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import tempfile

from fdf_v1 import parse, serialize, read_fdb


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "metadata" / "DISK.FDF"
DEFAULT_OUTPUT = ROOT / "build" / "catalog" / "DISK.FDB"


def catalogue_payload() -> bytes:
    historical = parse(SOURCE.read_text(), str(SOURCE))
    independent_path = ROOT / "metadata" / "release-formats.fdf"
    independent = {item.ident: item for item in parse(independent_path.read_text(), str(independent_path))}
    # Keep the compatibility catalogue ordering and public CONFIG names stable.
    for old in historical:
        if old.ident in independent and independent[old.ident] != old:
            raise ValueError("independent replacement changes compatibility descriptor: " + old.ident)
    formats = tuple(independent.get(item.ident, item) for item in historical)
    formats += tuple(item for ident, item in independent.items()
                     if ident not in {old.ident for old in historical})
    payload = serialize(formats)
    database = read_fdb(payload)
    if len(database.descriptors) != 108 or not all(
            descriptor.supported for descriptor in database.descriptors):
        raise ValueError("qualified catalogue is not 108 supported descriptors")
    return payload


def build(output: Path = DEFAULT_OUTPUT) -> Path:
    payload = catalogue_payload()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(payload)
    try:
        if temporary.read_bytes() != payload:
            raise ValueError("catalogue temporary-file read-back failed")
        read_fdb(temporary.read_bytes())
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    path = build(args.output)
    payload = path.read_bytes()
    print(f"{len(payload)} bytes, 108 descriptors")
    print(f"{hashlib.sha256(payload).hexdigest()}  {path}")


if __name__ == "__main__":
    main()
