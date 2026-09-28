#!/usr/bin/env python3
"""Connect the relocated z80pack ROM image to cold boot and its reloader."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path

from build_ccp import assemble
from build_rom_reference_inventory import (
    DELTAS, SHIFTED_SYMBOLS, listing_context, live_target_ranges,
    relocation_offsets, resolve_target,
)
from system_layout import LAYOUT, expand_layout

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/platform/trs80m4/ccprelod.mac"
ROM_BOOT = ROOT / "src/platform/z80pack/romboot.mac"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def z80pack_reloader_source(text: str) -> str:
    first = text.index("        PUSH    HL\n", text.index("CRNEXT:"))
    last = text.index("\nCRFAIL:", first)
    return text[:first] + """        INC     A
        LD      (CRSLOT),A
        DEC     A
        ADD     A,A
        ADD     A,A
        ADD     A,108
        LD      E,A
        LD      D,0
        LD      B,4
        JP      LY_DISK+15
""" + text[last:]


def normalized(text: str) -> str:
    return text.replace("        CSEG\n        .PHASE  ",
                        "        ASEG\n        ORG     ").replace(
                            "        .DEPHASE\n", "")


def shifted_layout_source(text: str, delta: int) -> str:
    text = expand_layout(text)
    for symbol in SHIFTED_SYMBOLS:
        pattern = rf"^({symbol}\s+EQU\s+)0([0-9A-F]+)H(.*)$"

        def replace(match: re.Match[str]) -> str:
            return (f"{match.group(1)}0{int(match.group(2), 16) + delta:04X}H"
                    f"{match.group(3)}")

        text, count = re.subn(pattern, replace, text, count=1,
                              flags=re.MULTILINE)
        if count != 1:
            raise ValueError(f"could not shift exactly one {symbol} definition")
    return text


def intel_hex(data: bytes, base: int, entry: int) -> bytes:
    lines = []
    for offset in range(0, len(data), 16):
        chunk = data[offset:offset + 16]
        address = base + offset
        fields = bytes((len(chunk), address >> 8, address & 0xFF, 0)) + chunk
        checksum = (-sum(fields)) & 0xFF
        lines.append(":" + fields.hex().upper() + f"{checksum:02X}")
    eof = bytes((0, entry >> 8, entry & 0xFF, 1))
    lines.append(":" + eof.hex().upper() + f"{(-sum(eof)) & 0xFF:02X}")
    return ("\n".join(lines) + "\n").encode("ascii")


def build(z80pack_build: Path, rom: Path, assembler: Path,
          raw_tracks: int, raw_slots: int) -> dict[str, object]:
    pack = json.loads((rom / "rom-pack.json").read_text(encoding="ascii"))
    relocated = json.loads(
        (rom / "rom-image.json").read_text(encoding="ascii"))
    baseline = (z80pack_build / "reloader.bin").read_bytes()
    source = normalized(z80pack_reloader_source(
        SOURCE.read_text(encoding="ascii")))
    alternates = []
    with tempfile.TemporaryDirectory(prefix="bettercpm-rom-reloader-") as temporary:
        temporary_path = Path(temporary)
        for delta in DELTAS:
            alternate = assemble(
                assembler, shifted_layout_source(source, delta),
                temporary_path / f"reloader-{delta:04x}.bin",
                temporary_path / f"reloader-{delta:04x}.lst", LAYOUT["RELOADER"])
            alternates.append((alternate, delta))
    offsets = relocation_offsets(baseline, alternates, "reloader")
    live = live_target_ranges()
    image = bytearray(baseline)
    references = []
    for offset in offsets:
        operand = LAYOUT["RELOADER"] + offset
        old = int.from_bytes(image[offset:offset + 2], "little")
        context = listing_context(z80pack_build / "reloader.lst", operand)
        kind, new, owners = resolve_target(
            pack, old, str(context["source"]), live)
        image[offset:offset + 2] = new.to_bytes(2, "little")
        references.append({
            "offset": offset, "operand": operand, "old_target": old,
            "new_target": new, "target_class": kind,
            "target_owners": owners, **context,
        })
    reloader = bytes(image)
    (rom / "rom-reloader.bin").write_bytes(reloader)
    (rom / "rom-reloader.json").write_text(json.dumps({
        "bytes": len(reloader), "sha256": digest(reloader),
        "source_sha256": digest(baseline), "reference_count": len(references),
        "unresolved_targets": 0, "references": references,
    }, indent=2, sort_keys=True) + "\n", encoding="ascii")

    entries = relocated["entries"]
    origin = int(pack["base"]) + int(pack["used_bytes"])
    links = (f"RB_ORIGIN EQU 0{origin:04X}H\n"
             f"RB_TRACKS EQU {raw_tracks}\n"
             f"RB_SLOTS EQU {raw_slots}\n"
             f"RB_TEMPLATE EQU 0{int(entries['ram_template']):04X}H\n"
             f"RB_BDOS EQU 0{int(entries['bdos']):04X}H\n"
             f"RB_INITIALIZER EQU 0{int(entries['cold_initializer']):04X}H\n"
             f"RB_BIOS_BOOT EQU 0{int(entries['bios_boot']):04X}H\n")
    boot_source = ROM_BOOT.read_text(encoding="ascii").replace(
        "        INCLUDE romboot.inc", links.rstrip())
    stub = assemble(assembler, boot_source, rom / "rom-boot-stub.bin",
                    rom / "rom-boot-stub.lst", origin)
    if len(stub) > int(pack["spare_bytes"]):
        raise ValueError("ROM cold entry exceeds accepted spare space")
    rom_image = bytearray((rom / "rom-image.bin").read_bytes())
    start = origin - int(pack["base"])
    rom_image[start:start + len(stub)] = stub
    payload = bytes(rom_image)
    (rom / "rom-boot.bin").write_bytes(payload)
    (rom / "rom-boot.hex").write_bytes(
        intel_hex(payload, int(pack["base"]), origin))
    manifest: dict[str, object] = {
        "base": int(pack["base"]), "end": int(pack["end"]),
        "bytes": len(payload), "sha256": digest(payload),
        "source_image_sha256": relocated["sha256"],
        "boot_integrated": True, "protected_xip_qualified": False,
        "entry": origin, "stub_bytes": len(stub),
        "spare_bytes": int(pack["spare_bytes"]) - len(stub),
        "bios_boot": int(entries["bios_boot"]),
        "reloader_sha256": digest(reloader),
        "reloader_reference_count": len(references),
    }
    (rom / "rom-boot.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"ROM boot integration: {len(stub)}-byte entry at {origin:04X}h; "
          f"{len(references)} reloader references; {manifest['spare_bytes']} bytes spare")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--z80pack-build", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--assembler", type=Path,
                        default=Path.home() / "bin/z80asm")
    parser.add_argument("--raw-tracks", type=int, required=True)
    parser.add_argument("--raw-slots", type=int, required=True)
    args = parser.parse_args()
    build(args.z80pack_build.resolve(), args.rom.resolve(),
          args.assembler.expanduser().resolve(), args.raw_tracks, args.raw_slots)


if __name__ == "__main__":
    main()
