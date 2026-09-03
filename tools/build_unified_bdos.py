#!/usr/bin/env python3
"""Build the compact replacement BDOS alongside the active implementation."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/bdos/unified.mac"
BUILD = ROOT / "build/bdos"
BASE = 0xC100
LIMIT = 3584


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    text = SOURCE.read_text(encoding="ascii")
    text = text.replace("        CSEG\n        .PHASE  ",
                        "        ASEG\n        ORG     ")
    text = text.replace("        .DEPHASE\n", "")
    output = BUILD / "unified-bdos.bin"
    with tempfile.TemporaryDirectory(prefix="bettercpm-unified-bdos-") as temporary:
        staged = Path(temporary) / SOURCE.name
        staged.write_text(text, encoding="ascii")
        subprocess.run([str(args.assembler), "-fb", f"-o{output}",
                        f"-l{BUILD / 'unified-bdos.lst'}", staged.name],
                       check=True, cwd=staged.parent)
    data = output.read_bytes()
    if len(data) > BASE and data[:BASE] == bytes(BASE):
        data = data[BASE:]
        output.write_bytes(data)
    if not data or len(data) > LIMIT:
        raise SystemExit(f"unified BDOS size {len(data)} exceeds {LIMIT}")
    print(f"{hashlib.sha256(data).hexdigest()}  {output.relative_to(ROOT)}")
    print(f"unified BDOS slice: {len(data)} / {LIMIT} bytes")


if __name__ == "__main__":
    main()
