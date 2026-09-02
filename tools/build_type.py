#!/usr/bin/env python3
"""Build the portable TYPE.COM utility."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/utilities/type.mac"
BUILD = ROOT / "build/utilities"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    text = SOURCE.read_text(encoding="ascii")
    text = text.replace("        CSEG\n", "        ASEG\n")
    text = text.replace("        .PHASE  0103H\n", "        ORG     0103H\n")
    text = text.replace("        .DEPHASE\n", "")
    output = BUILD / "TYPE.COM"
    with tempfile.TemporaryDirectory(prefix="bettercpm-type-") as temporary:
        staged = Path(temporary) / SOURCE.name
        staged.write_text(text, encoding="ascii")
        raw = Path(temporary) / "type.bin"
        subprocess.run([str(args.assembler), "-fb", f"-o{raw}",
                        f"-l{BUILD / 'type.lst'}", staged.name],
                       check=True, cwd=staged.parent)
        data = raw.read_bytes()
    data = bytes((0xC3, 0x03, 0x01)) + data
    if len(data) == 3:
        raise SystemExit("empty TYPE output")
    output.write_bytes(data)
    print(f"{hashlib.sha256(data).hexdigest()}  {output.relative_to(ROOT)}")
    print(f"TYPE bytes: {len(data)}")


if __name__ == "__main__":
    main()
