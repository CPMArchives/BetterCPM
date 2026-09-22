#!/usr/bin/env python3
"""Build the Phase-3 prospective transaction preparer."""
from pathlib import Path
import argparse

from build_ccp import assemble

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/system/r3prep.mac"
OUTPUT = ROOT / "build/system/rsxprepare.bin"
BASE = 0x7A00


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    text = SOURCE.read_text(encoding="ascii").replace(
        "        CSEG\n        .PHASE  ", "        ASEG\n        ORG     ").replace(
            "        .DEPHASE\n", "")
    data = assemble(args.assembler, text, OUTPUT, OUTPUT.with_suffix(".lst"), BASE)
    if not 0 < len(data) <= 512:
        raise SystemExit(f"RSX transaction preparer exceeds 512 bytes: {len(data)}")
    print(f"RSX transaction preparer bytes: {len(data)}")


if __name__ == "__main__":
    main()
