#!/usr/bin/env python3
"""Build the Phase-3 prospective RSX profile planner."""
from pathlib import Path
import argparse

from build_ccp import assemble

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/system/rsxplan.mac"
OUTPUT = ROOT / "build/system/rsxplan.bin"
BASE = 0x7400


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
    if not 0 < len(data) <= 768:
        raise SystemExit(f"RSX profile planner exceeds 768 bytes: {len(data)}")
    print(f"RSX profile planner bytes: {len(data)}")


if __name__ == "__main__":
    main()
