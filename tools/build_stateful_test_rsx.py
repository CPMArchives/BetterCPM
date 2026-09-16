#!/usr/bin/env python3
"""Build the Phase-3 STATEFUL movement qualification provider."""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

from build_cpx_module import relocation_offsets
from build_ccp import assemble
from build_rsx_module import make_module

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/rsx/stateful.mac"
BUILD = ROOT / "build/rsx"
LINK_BASE = 0x8000
ALTERNATE_BASE = 0x8101


def symbols(path: Path) -> dict[str, int]:
    return {name.upper(): int(address, 16) for address, name in re.findall(
        r"^([0-9a-f]{4})\s+.*?\b([A-Z][A-Z0-9_]*):",
        path.read_text(encoding="ascii"), re.M | re.I)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    source = SOURCE.read_text(encoding="ascii")
    text = source.replace("        CSEG\n        .PHASE  ",
                          "        ASEG\n        ORG     ").replace(
                              "        .DEPHASE\n", "")
    listing = BUILD / "stateful.lst"
    code = assemble(args.assembler, text, BUILD / "stateful.bin", listing,
                    LINK_BASE)
    alternate = assemble(
        args.assembler,
        text.replace("RSXBASE         EQU     08000H",
                     "RSXBASE         EQU     08101H"),
        BUILD / "stateful-alt.bin", BUILD / "stateful-alt.lst",
        ALTERNATE_BASE)
    relocations = relocation_offsets(code, alternate,
                                      ALTERNATE_BASE - LINK_BASE)
    names = symbols(listing)
    offset = lambda name: names[name] - LINK_BASE
    carrier = make_module(
        name="STATEFUL", version=(0, 1), services=[], linked_base=LINK_BASE,
        code=code, relocations=relocations, entry_offset=8, format_version=2,
        reconstruction_class="STATEFUL",
        callable_services=[(b"STAT", 1, 0, offset("SR_SERVICE"), 0)],
        runtime_pointers=[offset("SR_RUNTIME")])
    (BUILD / "STATEFUL.RSX").write_bytes(carrier)
    print(f"{hashlib.sha256(code).hexdigest()}  build/rsx/stateful.bin")
    print(f"STATEFUL.RSX bytes: {len(code)}; relocations: {len(relocations)}; "
          f"runtime pointers: 1; carrier: {len(carrier)}")


if __name__ == "__main__":
    main()
