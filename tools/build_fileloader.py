#!/usr/bin/env python3
"""Build the protected CPX/RSX filename stream reader."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/system/fileloader.mac"
BUILD = ROOT / "build/system"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    text = SOURCE.read_text(encoding="ascii").replace(
        "        CSEG\n        .PHASE  ", "        ASEG\n        ORG     ").replace(
            "        .DEPHASE\n", "")
    output = BUILD / "fileloader.bin"
    with tempfile.TemporaryDirectory(prefix="bettercpm-fileloader-") as temporary:
        staged = Path(temporary) / SOURCE.name
        staged.write_text(text, encoding="ascii")
        subprocess.run([str(args.assembler), "-fb", f"-o{output}",
                        f"-l{BUILD / 'fileloader.lst'}", staged.name],
                       check=True, cwd=staged.parent)
    data = output.read_bytes()
    if len(data) > 0xD000 and data[:0xD000] == bytes(0xD000):
        data = data[0xD000:]
        output.write_bytes(data)
    print(f"{hashlib.sha256(data).hexdigest()}  build/system/fileloader.bin")
    print(f"file-loader bytes: {len(data)}")


if __name__ == "__main__":
    main()
