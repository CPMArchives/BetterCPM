#!/usr/bin/env python3
"""Build the hardware-independent BetterCP/M TIME.COM utility."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/utilities/time.mac"
BUILD = ROOT / "build/utilities"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    text = SOURCE.read_text(encoding="ascii").replace(
        "        CSEG\n", "        ASEG\n").replace(
        "        .PHASE  0103H\n", "        ORG     0103H\n").replace(
        "        .DEPHASE\n", "")
    with tempfile.TemporaryDirectory(prefix="bettercpm-time-") as temporary:
        staged = Path(temporary) / SOURCE.name
        staged.write_text(text, encoding="ascii")
        raw = Path(temporary) / "time.bin"
        subprocess.run([str(args.assembler), "-fb", f"-o{raw}",
                        f"-l{BUILD / 'time.lst'}", staged.name],
                       check=True, cwd=staged.parent)
        data = bytes((0xC3, 0x03, 0x01)) + raw.read_bytes()
    output = BUILD / "TIME.COM"
    output.write_bytes(data)
    print(f"{hashlib.sha256(data).hexdigest()}  {output.relative_to(ROOT)}")
    print(f"TIME bytes: {len(data)}")


if __name__ == "__main__":
    main()
