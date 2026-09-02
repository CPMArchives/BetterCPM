#!/usr/bin/env python3
"""Build the Model 4 relocatable command-image reloader."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/platform/trs80m4/commandreload.mac"
BUILD = ROOT / "build/trs80"
BASE = 0xE900


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
    output = BUILD / "ccpreload.bin"
    with tempfile.TemporaryDirectory(prefix="bettercpm-ccpreload-") as temporary:
        staged = Path(temporary) / SOURCE.name
        staged.write_text(text, encoding="ascii")
        subprocess.run([str(args.assembler), "-fb", f"-o{output}",
                        f"-l{BUILD / 'ccpreload.lst'}", staged.name],
                       check=True, cwd=staged.parent)
    data = output.read_bytes()
    if len(data) > BASE and data[:BASE] == bytes(BASE):
        data = data[BASE:]
        output.write_bytes(data)
    if not data or len(data) > 0x400:
        raise SystemExit(f"CCP reloader exceeds E900h..ECFFh: {len(data)} bytes")
    print(f"{hashlib.sha256(data).hexdigest()}  {output.relative_to(ROOT)}")
    print(f"CCP reloader bytes: {len(data)}")


if __name__ == "__main__":
    main()
