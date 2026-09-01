#!/usr/bin/env python3
"""Cross-assemble the independently buildable BetterCP/M BIOS scaffold."""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/bios"
BUILD = ROOT / "build/bios"
BIOS_ADDRESS = 0xF000


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    text = (SOURCE / "bios.mac").read_text(encoding="ascii")
    text = text.replace("        CSEG\n        .PHASE  ",
                        "        ASEG\n        ORG     ")
    text = text.replace("        .DEPHASE\n", "")
    output = BUILD / "bios.bin"
    with tempfile.TemporaryDirectory(prefix="bettercpm-bios-") as temporary:
        staged = Path(temporary)
        (staged / "bios.mac").write_text(text, encoding="ascii")
        shutil.copy2(SOURCE / "biosplat.inc", staged / "biosplat.inc")
        subprocess.run([str(args.assembler), "-fb", f"-o{output}", "bios.mac"],
                       check=True, cwd=staged)
    data = output.read_bytes()
    if len(data) > BIOS_ADDRESS and data[:BIOS_ADDRESS] == bytes(BIOS_ADDRESS):
        data = data[BIOS_ADDRESS:]
        output.write_bytes(data)
    if not data:
        raise SystemExit("empty BIOS output")
    print(f"{hashlib.sha256(data).hexdigest()}  {output.relative_to(ROOT)}")
    print(f"BIOS bytes: {len(data)}")


if __name__ == "__main__":
    main()
