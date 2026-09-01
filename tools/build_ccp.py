#!/usr/bin/env python3
"""Cross-assemble the initial resident BetterCP/M CCP."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/ccp/ccp.mac"
BUILD = ROOT / "build/ccp"


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
    output = BUILD / "ccp.bin"
    with tempfile.TemporaryDirectory(prefix="bettercpm-ccp-") as temporary:
        staged = Path(temporary) / SOURCE.name
        staged.write_text(text, encoding="ascii")
        subprocess.run([str(args.assembler), "-fb", f"-o{output}",
                        f"-l{BUILD / 'ccp.lst'}", staged.name],
                       check=True, cwd=staged.parent)
    data = output.read_bytes()
    if len(data) > 0xE8E0 and data[:0xE8E0] == bytes(0xE8E0):
        data = data[0xE8E0:]
        output.write_bytes(data)
    if not data or len(data) > 0x430:
        raise SystemExit(f"CCP size outside E8E0h..ECFFh: {len(data)} bytes")
    print(f"{hashlib.sha256(data).hexdigest()}  {output.relative_to(ROOT)}")
    print(f"CCP bytes: {len(data)}")


if __name__ == "__main__":
    main()
