#!/usr/bin/env python3
"""Build the portable BetterCP/M STAT.COM utility."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path

from system_layout import expand_layout

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/utilities/stat.mac"
BUILD = ROOT / "build/utilities"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    text = expand_layout(SOURCE.read_text(encoding="ascii"))
    text = text.replace("        CSEG\n", "        ASEG\n")
    text = text.replace("        .PHASE  0103H\n", "        ORG     0103H\n")
    text = text.replace("        .DEPHASE\n", "")
    with tempfile.TemporaryDirectory(prefix="bettercpm-stat-") as temporary:
        staged = Path(temporary) / "stat.mac"
        staged.write_text(text, encoding="ascii")
        raw = Path(temporary) / "stat.bin"
        listing = BUILD / "stat.lst"
        subprocess.run([str(args.assembler), "-fb", f"-o{raw}",
                        f"-l{listing}", staged.name], cwd=staged.parent,
                       check=True)
        data = raw.read_bytes()
    if len(data) > 0x0103 and data[:0x0103] == bytes(0x0103):
        data = data[0x0103:]
    data = bytes((0xC3, 0x03, 0x01)) + data
    if len(data) <= 3:
        raise SystemExit("empty STAT output")
    output = BUILD / "STAT.COM"
    output.write_bytes(data)
    print(f"{hashlib.sha256(data).hexdigest()}  {output.relative_to(ROOT)}")
    print(f"STAT bytes: {len(data)}")


if __name__ == "__main__":
    main()
