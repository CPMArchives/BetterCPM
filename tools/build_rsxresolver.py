#!/usr/bin/env python3
"""Build the disk-free Function 182 resident-service resolver overlay."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from build_ccp import assemble
from system_layout import LAYOUT

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/system/rsxresol.mac"
BUILD = ROOT / "build/system"
BASE = LAYOUT["RSX"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    text = SOURCE.read_text(encoding="ascii").replace(
        "        CSEG\n        .PHASE  ", "        ASEG\n        ORG     ").replace(
        "        .DEPHASE\n", "")
    assemble(args.assembler,text,BUILD/'rsxresolver-plain.bin',
             BUILD/'rsxresolver-plain.lst',BASE)
    from private_rsx_rebase import boot_image
    data = boot_image(args.assembler,text,'RRBASE',BUILD,'rsxresolver')
    if not data or len(data) > 1000:
        raise SystemExit(f"RSX resolver exceeds its packed slot: {len(data)} bytes")
    print(f"{hashlib.sha256(data).hexdigest()}  build/system/rsxresolver.bin")
    print(f"RSX resolver bytes: {len(data)}")


if __name__ == "__main__":
    main()
