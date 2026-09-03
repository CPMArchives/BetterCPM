#!/usr/bin/env python3
"""Build RSX.COM and RSXTEST.COM."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from build_ccp import assemble

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build/utilities"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    for stem, output_name in (("rsx", "RSX.COM"),
                              ("rsxtest", "RSXTEST.COM"),
                              ("rsx2test", "RSX2TST.COM")):
        source = (ROOT / f"src/utilities/{stem}.mac").read_text(encoding="ascii")
        text = source.replace("        CSEG\n        .PHASE  ",
                              "        ASEG\n        ORG     ").replace(
                                  "        .DEPHASE\n", "")
        output = BUILD / output_name
        linked = assemble(args.assembler, text, output,
                          BUILD / f"{stem}.lst", 0x103)
        data = bytes((0xC3, 0x03, 0x01)) + linked
        output.write_bytes(data)
        print(f"{hashlib.sha256(data).hexdigest()}  build/utilities/{output_name}")


if __name__ == "__main__":
    main()
