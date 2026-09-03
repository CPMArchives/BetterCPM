#!/usr/bin/env python3
"""Build the page-zero gateway and compose the provisional resident image."""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/system/gateway.mac"
BUILD = ROOT / "build/system"
COMPONENTS = (
    (0xC000, "gateway.bin"),
    (0xC100, "../bdos/bdos.bin"),
    (0xD000, "fileloader.bin"),
    (0xD100, "rsxloader.bin"),
    (0xD600, "extensions.bin"),
    (0xDA00, "tables.bin"),
    (0xE900, "../trs80/ccpreload.bin"),
    (0xEF00, "../bios/bios.bin"),
)
RESIDENT_BASE = 0xC000
LIMITS = (0xC100, 0xD000, 0xD100, 0xD500, 0xDA00, 0xE900, 0xED00, 0x10000)


def build_support(assembler: Path) -> None:
    """Link internal adapters against this exact core, never fixed globals."""
    listing = (ROOT / "build/bdos/bdos.lst").read_text(errors="replace")
    symbols = {}
    for name in ("UB_DMA", "UB_DRIVE", "UB_USERNO", "UB_COLUMN", "UB_LISTE"):
        match = re.search(rf"^([0-9a-f]{{4}})\s+.*\b{name}:",
                          listing, re.MULTILINE | re.IGNORECASE)
        if not match:
            raise SystemExit(f"unified core lacks internal symbol {name}")
        symbols[name] = int(match[1], 16)
    core = "".join(f"{name} EQU 0{address:04X}H\n"
                   for name, address in symbols.items())
    (BUILD / "core.inc").write_text(core, encoding="ascii")
    for relative, name, base in (("src/system/extensions.mac", "extensions", 0xD600),
                                  ("src/bios/tables.mac", "tables", 0xDA00)):
        source = (ROOT / relative).read_text(encoding="ascii").replace(
            "        CSEG\n        .PHASE  ", "        ASEG\n        ORG     "
        ).replace("        .DEPHASE\n", "")
        with tempfile.TemporaryDirectory(prefix="bettercpm-support-") as temporary:
            staged = Path(temporary)
            (staged / f"{name}.mac").write_text(source, encoding="ascii")
            (staged / "core.inc").write_text(core, encoding="ascii")
            (staged / "versions.inc").write_bytes(
                (ROOT / "src/bdos/versions.inc").read_bytes())
            output = BUILD / f"{name}.bin"
            subprocess.run([str(assembler), "-fb", f"-o{output}",
                            f"-l{BUILD / (name + '.lst')}", f"{name}.mac"],
                           check=True, cwd=staged)
        data = output.read_bytes()
        if len(data) > base and data[:base] == bytes(base):
            data = data[base:]
            output.write_bytes(data)
        print(f"{name}: {len(data)} protected bytes (outside standard BDOS core)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    build_support(args.assembler)
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
