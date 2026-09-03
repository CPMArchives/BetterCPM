#!/usr/bin/env python3
"""Build transient fallbacks directly from the BASIC.CPX command code."""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

from build_ccp import assemble

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/cpx/basic.mac"
BUILD = ROOT / "build/utilities"
ORIGIN = 0x0100
COMMANDS = {
    "DIR": "BC_DIR",
    "USER": "BC_USER",
    "CLR": "BC_CLR",
    "VER": "BC_VER",
}


def symbol(listing: Path, name: str) -> int:
    matches = re.findall(rf"^([0-9a-f]{{4}})\s+.*\b{name}:?\s*$",
                         listing.read_text(encoding="ascii"),
                         re.MULTILINE | re.IGNORECASE)
    if not matches:
        raise SystemExit(f"BASIC transient listing lacks {name}")
    return int(matches[-1], 16)


def transient(image: bytes, entry: int) -> bytes:
    # CP/M supplies a blank-prefixed command tail. Strip its leading spaces,
    # call the very same routine used by BASIC.CPX, then warm boot. Keeping the
    # complete command body is intentionally a first parity implementation;
    # later dead-code removal may reduce the files without changing behavior.
    prefix = bytes((
        0x21, 0x81, 0x00,       # LD HL,0081h
        0x3A, 0x80, 0x00,       # LD A,(0080h)
        0x47,                   # LD B,A
        0x78, 0xB7, 0x28, 0x09, # skip: LD A,B / OR A / JR Z,ready
        0x7E, 0xFE, 0x20,       # LD A,(HL) / CP ' '
        0x20, 0x04,             # JR NZ,ready
        0x23, 0x05, 0x18, 0xF3, # INC HL / DEC B / JR skip
        0xCD, entry & 0xFF, entry >> 8,
        0x0E, 0x00,             # LD C,0
        0xC3, 0x05, 0x00,       # JP 0005h
    ))
    result = bytearray(image)
    result[:len(prefix)] = prefix
    return bytes(result)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    text = SOURCE.read_text(encoding="ascii")
    text = text.replace("CPXBASE         EQU     08000H",
                        "CPXBASE         EQU     00100H")
    text = text.replace("        CSEG\n        .PHASE  ",
                        "        ASEG\n        ORG     ").replace(
                            "        .DEPHASE\n", "")
    listing = BUILD / "basic-transient.lst"
    base = assemble(args.assembler, text, BUILD / "basic-transient.bin",
                    listing, ORIGIN)
    for command, entry_name in COMMANDS.items():
        data = transient(base, symbol(listing, entry_name))
        output = BUILD / f"{command}.COM"
        output.write_bytes(data)
        print(f"{hashlib.sha256(data).hexdigest()}  {output.relative_to(ROOT)}")
        print(f"{command} transient bytes: {len(data)}")


if __name__ == "__main__":
    main()
