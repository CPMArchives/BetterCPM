#!/usr/bin/env python3
"""Build the real-emulator STATEFUL reconstruction qualification command."""
from pathlib import Path
import argparse

from build_ccp import assemble

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    source = (ROOT / "src/utilities/stattst.mac").read_text(encoding="ascii")
    text = source.replace("        CSEG\n        .PHASE  ",
                          "        ASEG\n        ORG     ").replace(
                              "        .DEPHASE\n", "")
    output = ROOT / "build/utilities/STATTST.COM"
    output.parent.mkdir(parents=True, exist_ok=True)
    data = assemble(args.assembler, text, output, output.with_suffix(".lst"),
                    0x103)
    data = bytes((0xC3, 0x03, 0x01)) + data
    output.write_bytes(data)
    print(f"STATTST.COM bytes: {len(data)}")


if __name__ == "__main__":
    main()
