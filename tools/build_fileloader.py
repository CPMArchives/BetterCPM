#!/usr/bin/env python3
"""Build the protected CPX/RSX filename stream reader."""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import tempfile
from pathlib import Path
from system_layout import LAYOUT, expand_layout

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
        staged.write_text(expand_layout(text), encoding="ascii")
        subprocess.run([str(args.assembler), "-fb", f"-o{output}",
                        f"-l{BUILD / 'fileloader.lst'}", staged.name],
                       check=True, cwd=staged.parent)
    data = output.read_bytes()
    if len(data) > LAYOUT["FILE"] and data[:LAYOUT["FILE"]] == bytes(LAYOUT["FILE"]):
        data = data[LAYOUT["FILE"]:]
        output.write_bytes(data)
    match = re.search(r"^([0-9a-f]{4})\s+.*\bFL_FCB:", (BUILD/'fileloader.lst').read_text(), re.M|re.I)
    if not match or int(match[1],16) != LAYOUT['FILE']+109:
        raise SystemExit('protected COM loader FCB address changed; update its ABI')
    print(f"{hashlib.sha256(data).hexdigest()}  build/system/fileloader.bin")
    print(f"file-loader bytes: {len(data)}")


if __name__ == "__main__":
    main()
