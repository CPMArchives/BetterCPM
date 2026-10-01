#!/usr/bin/env python3
"""Build the transient TRS-80 system-track RSX overlay selector."""
from pathlib import Path
import argparse
from build_ccp import assemble
from system_layout import LAYOUT, expand_layout

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/platform/trs80m4/rsxsel.mac"
OUTPUT = ROOT / "build/trs80/rsxselect.bin"

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    text = expand_layout(SOURCE.read_text(encoding="ascii")).replace(
        "        CSEG\n        .PHASE  ", "        ASEG\n        ORG     ").replace(
        "        .DEPHASE\n", "")
    data = assemble(args.assembler, text, OUTPUT,
                    OUTPUT.with_suffix(".lst"), LAYOUT["RSX_SELECTOR"])
    capacity = 1024 - LAYOUT["RELOADER_CAPACITY"]
    if not 0 < len(data) <= capacity:
        raise SystemExit(f"RSX selector exceeds its {capacity}-byte tail: {len(data)}")
    print(f"RSX selector bytes: {len(data)}")

if __name__ == "__main__":
    main()
