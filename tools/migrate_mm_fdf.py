#!/usr/bin/env python3
"""Migrate the preserved 112-record MM corpus to qualified FDF version 1."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "third_party" / "montezuma" / "DISK.FDF"
INTERNAL = ROOT / "metadata" / "mm-builtin-formats.json"

EXCLUDED = {
    "Acorn (80T, SS, SD, 392K)": "declared allocation exceeds available media bytes",
    "Eagle (80T, SS, DD, 390K)": "directory bitmap does not reserve its full directory",
    "Omikron Mapper II (40T, SS, DD, 134K)": "declared allocation exceeds available media bytes",
    "Pied Piper Executive (80T, DS, DD, 784K)": "directory bitmap does not reserve its full directory",
    "Zenith H89 (40T, SS, SD, 94K)": "declared allocation exceeds available media bytes",
}

# Every shortening is explicit.  The migration never slices a historical name.
ALIASES = {
    "Adler Textriter Series III": "Adler Textriter III",
    "AOS/VT Basic 4 S-10": "AOS/VT Basic 4",
    "ATR-8000 512 byte sector": "ATR-8000 512-byte",
    "ATR-8000 1024 byte sector": "ATR-8000 1024-byte",
    "Aust. Comp. & Telecomm.": "Australian Comp & Telecom",
    "AVATAR TC1 Terminal Converter": "AVATAR TC1",
    "California Computer Systems": "California Computer Systems",
    "Computer Operation NCHQ": "Computer Operation NCHQ",
    "Dictaphone 6000 CP/M Rev. A": "Dictaphone 6000 Rev A",
    "Dictaphone 6000 CP/M v. 2.26": "Dictaphone 6000 v2.26",
    'Digital Research 8" CP/M Standard': "DRI 8-inch CP/M Standard",
    "Heath H8 with Trionyx H-C8 controller": "Heath H8 Trionyx H-C8",
    "Holmes Engineering VID80": "Holmes VID80",
    "Hurricane Labs Inc. Compactor I & II": "Hurricane Compactor I/II",
    "IBM PC using CP/M 86": "IBM PC CP/M-86",
    "Lifeboat TRS-80 Mod 1": "Lifeboat TRS-80 Model I",
    "Memory Merchant Shuffle Board": "Memory Merchant Shuffle",
    "Morrow Micro Decision": "Morrow Micro Decision",
    "Morrow Micro Decision MD3": "Morrow Micro Decision MD3",
    "Octagon 8/16 CP/M-86": "Octagon 8/16 CP/M-86",
    "Omikron Mapper I, Model 1 & 3": "Omikron Mapper I",
    "Osborne 1 with 2x2 upgrade": "Osborne 1 2x2",
    "Radio Shack TRS-80 Model 4 CP/M Plus": "TRS-80 Model 4 CP/M Plus",
    "Tektronics 4170 CP/M 86": "Tektronics 4170 CP/M-86",
    "Montezuma Micro CP/M v 1.26 & 1.30": "MM CP/M 1.26/1.30",
    "Montezuma Micro CP/M v 1.32": "MM CP/M 1.32",
    "Montezuma Micro CP/M v 1.42 & 1.44": "MM CP/M 1.42/1.44",
    "Montezuma Micro Standard SYSTEM": "MM Standard SYSTEM",
    "Montezuma Micro Standard DATA": "MM Standard DATA",
    "Montezuma Micro Standard DS SYSTEM": "MM Standard DS SYSTEM",
    "Montezuma Micro Standard DS DATA": "MM Standard DS DATA",
    "Montezuma Micro 80T SYSTEM": "MM 80T SYSTEM",
    "Montezuma Micro 80T DATA": "MM 80T DATA",
    "Montezuma Micro 80T DS SYSTEM": "MM 80T DS SYSTEM",
    "Montezuma Micro 80T DS DATA": "MM 80T DS DATA",
    "Montezuma Micro Extended SYSTEM": "MM Extended SYSTEM",
    "Montezuma Micro Extended DS SYSTEM": "MM Extended DS SYSTEM",
    "Montezuma Micro Extended 80T SYSTEM": "MM Extended 80T SYSTEM",
    "Montezuma Micro Extended 80T DS SYSTEM": "MM Extended 80T DS SYSTEM",
    "Montezuma Micro SUPER DATA": "MM SUPER DATA",
    "Montezuma Micro SUPER DS DATA": "MM SUPER DS DATA",
    "Montezuma Micro 80T SUPER DATA": "MM 80T SUPER DATA",
    "Montezuma Micro 80T SUPER DS DATA": "MM 80T SUPER DS DATA",
}


@dataclass(frozen=True)
class Legacy:
    source: str
    ordinal: int
    name: str
    parameters: tuple[int, ...]
    sector_ids: tuple[int, ...]


def records() -> tuple[Legacy, ...]:
    lines = LEGACY.read_text(encoding="ascii").split("\x1a", 1)[0].splitlines()
    result = []
    for index in range(0, len(lines), 3):
        if not lines[index].startswith("*"):
            raise ValueError(f"legacy record {index // 3 + 1}: missing name marker")
        result.append(Legacy("DISK.FDF", index // 3 + 1, lines[index][1:],
                             tuple(map(int, lines[index + 1].split(","))),
                             tuple(map(int, lines[index + 2].split(",")))))
    builtins = json.loads(INTERNAL.read_text(encoding="ascii"))["formats"]
    for index, item in enumerate(builtins, 1):
        result.append(Legacy("CONFIG.COM", index, item["name"],
                             tuple(item["parameters"]), tuple(item["sector_ids"])))
    if len(result) != 112:
        raise ValueError(f"expected 112 source records, found {len(result)}")
    return tuple(result)


def base_name(name: str) -> str:
    match = re.fullmatch(r"(.+?) \([^()]*(?:\([^()]*\)[^()]*)?\)", name)
    if not match:
        raise ValueError(f"cannot separate historical geometry: {name}")
    return match.group(1)


def descriptions(items: tuple[Legacy, ...]) -> dict[str, str]:
    bases = Counter(base_name(item.name) for item in items)
    result = {}
    for item in items:
        base = base_name(item.name)
        display = ALIASES.get(base, base)
        if bases[base] > 1:
            p = item.parameters
            suffix = f" {p[12]}T {'DS' if p[13] & 0x40 else 'SS'}"
            # Distinguish same-track/sides variants such as ATR sector sizes.
            if any(other.name != item.name and base_name(other.name) == base and
                   other.parameters[12] == p[12] and
                   bool(other.parameters[13] & 0x40) == bool(p[13] & 0x40)
                   for other in items):
                suffix += f" {128 << p[11]}"
            display += suffix
        if len(display) > 32:
            raise ValueError(f"explicit display abbreviation required: {display!r}")
        if display in result.values():
            raise ValueError(f"duplicate display description: {display}")
        result[item.name] = display
    return result


def statement(item: Legacy, display: str) -> str:
    p = item.parameters
    if len(p) != 14 or len(item.sector_ids) != p[10]:
        raise ValueError(f"{item.name}: malformed legacy record")
    ident = ("MMF" if item.source == "DISK.FDF" else "MMI") + f"{item.ordinal:03d}"
    options = p[13]
    lines = [
        f"# {item.name}",
        f"# Recovered from {item.source} record {item.ordinal}; ID preserves that ordinal.",
        "FORMAT", f"ID            {ident}", f'DESCRIPTION   "{display}"',
        f"SPT           {p[0]}", f"BSH           {p[1]}", f"BLM           {p[2]}",
        f"EXM           {p[3]}", f"DSM           {p[4]}", f"DRM           {p[5]}",
        f"AL0           0x{p[6]:02X}", f"AL1           0x{p[7]:02X}",
        f"CKS           {p[8]}", f"OFF           {p[9]}",
        f"PSECTORS      {p[10]}", f"SECSIZE       {128 << p[11]}",
        f"CYLINDERS     {p[12]}", f"SIDES         {2 if options & 0x40 else 1}",
        f"ENCODING      {'MFM' if options & 0x80 else 'FM'}",
        "SECTOR_IDS    " + ",".join(map(str, item.sector_ids)),
    ]
    if options & 0x10:
        lines.append("INVERT        YES")
    if options & 0x02:
        lines.append("SIDE_ORDER    SIDE_MAJOR")
    if options & 0x01:
        lines.append("SIDE1_DIRECTION REVERSE")
    if options & 0x04:
        lines.append("TRACK_ID_MODE CONTINUOUS")
    if options & 0x08:
        lines.append("SECTOR_ID_MODE CONTINUOUS")
    if item.name.startswith("Montezuma Micro") and "SUPER" in item.name:
        lines.append("SECTOR_SIZES  1024,1024,1024,1024,1024,512")
    if item.name.startswith("Micro-Abacus"):
        lines.append("LOGICAL_TRACK CYLINDER")
    lines.extend(("END", ""))
    return "\n".join(lines)


def migrate() -> tuple[str, dict]:
    items = records()
    displays = descriptions(items)
    admitted = [item for item in items if item.name not in EXCLUDED]
    text = [
        "# Qualified migration of the preserved Montezuma Micro format corpus.",
        "# Full historical names and source ordinals precede every admitted record.",
        f"# DISK.FDF SHA-256: {hashlib.sha256(LEGACY.read_bytes()).hexdigest()}",
        f"# Built-in metadata SHA-256: {hashlib.sha256(INTERNAL.read_bytes()).hexdigest()}",
        "FDF_VERSION 1", "",
    ]
    text.extend(statement(item, displays[item.name]) for item in admitted)
    excluded = {
        "source_records": len(items), "admitted_records": len(admitted),
        "source_sha256": {
            str(LEGACY.relative_to(ROOT)): hashlib.sha256(LEGACY.read_bytes()).hexdigest(),
            str(INTERNAL.relative_to(ROOT)): hashlib.sha256(INTERNAL.read_bytes()).hexdigest(),
        },
        "excluded_records": [
            {"source": item.source, "ordinal": item.ordinal, "name": item.name,
             "parameters": list(item.parameters), "sector_ids": list(item.sector_ids),
             "diagnostic": EXCLUDED[item.name]}
            for item in items if item.name in EXCLUDED
        ],
    }
    return "\n".join(text), excluded


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--exclusions", type=Path)
    args = parser.parse_args()
    text, exclusions = migrate()
    args.output.write_text(text, encoding="ascii")
    if args.exclusions:
        args.exclusions.write_text(json.dumps(exclusions, indent=2) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
