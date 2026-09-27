#!/usr/bin/env python3
"""Verify the complete but deliberately unrelocated z80pack ROM packing artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from build_rom_pack import ROM_BASE, ROM_END, build, component_inputs


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--z80pack-build", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--pack", type=Path, required=True)
    args = parser.parse_args()
    pack_dir = args.pack.resolve()
    with tempfile.TemporaryDirectory(prefix="bettercpm-rom-pack-") as temporary:
        regenerated = Path(temporary)
        expected = build(args.z80pack_build.resolve(), args.artifacts.resolve(), regenerated)
        expected_image = (regenerated / "rom-pack.bin").read_bytes()
    image = (pack_dir / "rom-pack.bin").read_bytes()
    manifest = json.loads((pack_dir / "rom-pack.json").read_text(encoding="ascii"))
    if manifest != expected:
        raise AssertionError("ROM packing manifest differs from regenerated facts")
    if image != expected_image:
        raise AssertionError("ROM packing image differs from independent regeneration")
    if len(image) != ROM_END - ROM_BASE or digest(image) != manifest["sha256"]:
        raise AssertionError("ROM packing image size or hash is incorrect")
    if manifest["executable"] is not False:
        raise AssertionError("unrelocated packing artifact claims to be executable")

    sources = {name: (base, path.read_bytes())
               for name, base, path in component_inputs(args.z80pack_build.resolve())}
    covered = 0
    for component in manifest["components"]:
        base, source = sources[component["name"]]
        if base != component["source_base"] or digest(source) != component["source_sha256"]:
            raise AssertionError(f"{component['name']} source identity changed")
        for fragment in component["fragments"]:
            old = fragment["source_start"] - base
            packed = fragment["rom_start"] - ROM_BASE
            count = fragment["bytes"]
            if image[packed:packed + count] != source[old:old + count]:
                raise AssertionError(f"{component['name']} fragment is not byte exact")
            covered += count
    if covered != manifest["immutable_source_bytes"]:
        raise AssertionError("immutable fragment coverage is incomplete")
    if sum(component["mutable_bytes"] for component in manifest["components"]) != 866:
        raise AssertionError("mutable complement is not the accepted 866 source bytes")

    for segment, filename in zip(manifest["segments"], ("ram-init.bin", "cold-init.bin")):
        data = (args.artifacts.resolve() / filename).read_bytes()
        start = segment["rom_start"] - ROM_BASE
        if image[start:start + len(data)] != data or digest(data) != segment["sha256"]:
            raise AssertionError(f"{segment['name']} segment is not byte exact")
    used = manifest["used_bytes"]
    if image[used:] != b"\xFF" * manifest["spare_bytes"]:
        raise AssertionError("ROM packing padding is not erased-state FFh")
    if manifest["used_bytes"] != 7799 or manifest["spare_bytes"] != 649:
        raise AssertionError("accepted ROM packing budget changed")
    if manifest["candidate_entry_inputs"] != {
            "template": 0xF3F5, "cold_initializer": 0xFD61, "bdos": 0xDF9E}:
        raise AssertionError("accepted candidate entry addresses changed")
    print("ROM packing verified: 5365 immutable-source + 2412 template + "
          "22 initializer bytes; 649 spare; relocation still required")


if __name__ == "__main__":
    main()
