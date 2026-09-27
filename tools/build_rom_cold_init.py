#!/usr/bin/env python3
"""Build the position-independent z80pack ROM cold initializer."""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from build_ccp import assemble
from system_layout import expand_layout

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/platform/z80pack/rominit.mac"
TEST_ORIGIN = 0x8000


def build(assembler: Path, template_dir: Path, output: Path) -> dict[str, object]:
    template_manifest = json.loads(
        (template_dir / "ram-init.json").read_text(encoding="ascii"))
    template_bytes = int(template_manifest["bytes"])
    expanded = expand_layout(SOURCE.read_text(encoding="ascii"))
    def source_at(origin: int) -> str:
        links = (f"RI_ORIGIN EQU 0{origin:04X}H\n"
                 f"RI_BYTES EQU {template_bytes}\n")
        return expanded.replace("        INCLUDE romlinks.inc", links.rstrip())
    output.mkdir(parents=True, exist_ok=True)
    binary = output / "cold-init.bin"
    data = assemble(assembler, source_at(TEST_ORIGIN), binary,
                    output / "cold-init.lst", TEST_ORIGIN)
    if not data:
        raise ValueError("ROM cold initializer is empty")
    with tempfile.TemporaryDirectory(prefix="bettercpm-rom-init-") as temporary:
        alternate_dir = Path(temporary)
        alternate_origin = TEST_ORIGIN + 0x1000
        alternate = assemble(
            assembler, source_at(alternate_origin), alternate_dir / "cold-init.bin",
            alternate_dir / "cold-init.lst", alternate_origin)
    if alternate != data:
        raise ValueError("ROM cold initializer depends on its assembly origin")
    spare_before = int(template_manifest["rom_spare_before_initializer"])
    if len(data) > spare_before:
        raise ValueError(
            f"ROM cold initializer requires {len(data)} bytes; {spare_before} remain")
    manifest: dict[str, object] = {
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "position_independent": True,
        "test_origin": TEST_ORIGIN,
        "template_bytes": template_bytes,
        "entry": {
            "hl": "immutable RAM-template address",
            "ix": "immutable BDOS entry address",
            "sp": "valid stack outside the destination RAM image",
        },
        "rom_spare_after_initializer": spare_before - len(data),
    }
    (output / "cold-init.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"ROM cold initializer: {len(data)} bytes; "
          f"{manifest['rom_spare_after_initializer']} ROM bytes remain; "
          f"{manifest['sha256']}")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path, default=Path.home() / "bin/z80asm")
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.assembler.resolve(), args.template.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
