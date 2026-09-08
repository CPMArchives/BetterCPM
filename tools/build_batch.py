#!/usr/bin/env python3
"""Build native SUBMIT/XSUB utilities and the protected BATCHIO BRSX."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from build_ccp import assemble
from build_cpx_module import relocation_offsets
from build_rsx_module import make_module

ROOT = Path(__file__).resolve().parents[1]
UTIL = ROOT / "build/utilities"
RSX = ROOT / "build/rsx"
LINK_BASE = 0x8000
ALTERNATE_BASE = 0x8101


def normalized(text: str) -> str:
    return text.replace("        CSEG\n        .PHASE  ",
                        "        ASEG\n        ORG     ").replace(
                            "        .DEPHASE\n", "")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    UTIL.mkdir(parents=True, exist_ok=True)
    RSX.mkdir(parents=True, exist_ok=True)

    for stem in ("submit", "xsub"):
        text = normalized((ROOT / f"src/utilities/{stem}.mac").read_text(
            encoding="ascii"))
        output = UTIL / f"{stem.upper()}.COM"
        data = assemble(args.assembler, text, output,
                        UTIL / f"{stem}.lst", 0x100)
        print(f"{hashlib.sha256(data).hexdigest()}  {output.relative_to(ROOT)}")
        print(f"{stem.upper()}.COM: {len(data)} bytes")

    source = (ROOT / "src/rsx/batchio.mac").read_text(encoding="ascii")
    text = normalized(source)
    code = assemble(args.assembler, text, RSX / "batchio.bin",
                    RSX / "batchio.lst", LINK_BASE)
    alternate = assemble(
        args.assembler,
        text.replace("RSXBASE         EQU     08000H",
                     "RSXBASE         EQU     08101H"),
        RSX / "batchio-alt.bin", RSX / "batchio-alt.lst", ALTERNATE_BASE)
    offsets = relocation_offsets(code, alternate, ALTERNATE_BASE - LINK_BASE)
    carrier = make_module(name="BATCHIO", version=(1, 0), services=[10],
                          linked_base=LINK_BASE, code=code,
                          relocations=offsets)
    output = RSX / "BATCHIO.RSX"
    output.write_bytes(carrier)
    print(f"{hashlib.sha256(code).hexdigest()}  build/rsx/batchio.bin")
    print(f"BATCHIO.RSX code: {len(code)} bytes; allocation: "
          f"{(len(code) + 255) & ~255} bytes; relocations: {len(offsets)}")


if __name__ == "__main__":
    main()
