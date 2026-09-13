#!/usr/bin/env python3
"""Build the Function 208 callable-service qualification utility."""
from pathlib import Path
import argparse
from build_ccp import assemble

ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    source = (ROOT / "src/utilities/svctest.mac").read_text(encoding="ascii")
    text = source.replace("        CSEG\n        .PHASE  ",
                          "        ASEG\n        ORG     ").replace(
                              "        .DEPHASE\n", "")
    output = ROOT / "build/utilities/SVCTEST.COM"
    output.parent.mkdir(parents=True, exist_ok=True)
    data = assemble(args.assembler, text, output, output.with_suffix(".lst"), 0x103)
    print(f"SVCTEST.COM bytes: {len(data)}")

if __name__ == "__main__":
    main()
