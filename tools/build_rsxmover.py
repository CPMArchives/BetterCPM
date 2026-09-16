#!/usr/bin/env python3
"""Build the Phase-3 live RSX allocation mover."""
from pathlib import Path
import argparse

from build_ccp import assemble

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/system/rsxmover.mac"
OUTPUT = ROOT / "build/system/rsxmover.bin"
BASE = 0x7000


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
        raise SystemExit(f"RSX mover exceeds its 512-byte budget: {len(data)}")
    print(f"RSX mover bytes: {len(data)}")


if __name__ == "__main__":
    main()
