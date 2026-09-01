#!/usr/bin/env python3
"""Build the page-zero gateway and compose the provisional resident image."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/system/gateway.mac"
BUILD = ROOT / "build/system"
COMPONENTS = (
    (0xC000, "gateway.bin"),
    (0xC100, "../bdos/bdos.bin"),
    (0xD800, "../bdos/directory.bin"),
    (0xEA40, "../ccp/ccp.bin"),
    (0xEF00, "../bios/bios.bin"),
)
RESIDENT_BASE = 0xBF00       # includes the reserved 128-byte DIRBUF workspace
LIMITS = (0xC100, 0xD800, 0xEA40, 0xED00, 0x10000)


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
    gateway = BUILD / "gateway.bin"
    with tempfile.TemporaryDirectory(prefix="bettercpm-system-") as temporary:
        staged = Path(temporary) / SOURCE.name
        staged.write_text(text, encoding="ascii")
        subprocess.run([str(args.assembler), "-fb", f"-o{gateway}",
                        f"-l{BUILD / 'gateway.lst'}", staged.name],
                       check=True, cwd=staged.parent)
    data = gateway.read_bytes()
    if len(data) > 0xC000 and data[:0xC000] == bytes(0xC000):
        data = data[0xC000:]
        gateway.write_bytes(data)
    if not data:
        raise SystemExit("empty system-gateway output")

    base = RESIDENT_BASE
    end = base
    loaded = []
    for index, (address, relative) in enumerate(COMPONENTS):
        path = (BUILD / relative).resolve()
        if not path.is_file():
            raise SystemExit(f"missing resident component: {path}")
        component = path.read_bytes()
        if address < end:
            raise SystemExit(f"resident component overlap at {address:04X}h")
        if address + len(component) > LIMITS[index]:
            raise SystemExit(f"resident component exceeds region ending {LIMITS[index]:04X}h")
        loaded.append((address, component))
        end = address + len(component)
    image = bytearray(end - base)
    for address, component in loaded:
        image[address - base:address - base + len(component)] = component
    resident = BUILD / "resident.bin"
    resident.write_bytes(image)
    print(f"{hashlib.sha256(data).hexdigest()}  {gateway.relative_to(ROOT)}")
    print(f"gateway bytes: {len(data)}")
    print(f"resident span: {base:04X}h..{end - 1:04X}h ({len(image)} bytes)")


if __name__ == "__main__":
    main()
