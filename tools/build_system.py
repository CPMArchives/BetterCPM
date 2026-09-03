#!/usr/bin/env python3
"""Build the gateway and compose the checked, packed resident image."""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import tempfile
from pathlib import Path
from system_layout import LAYOUT, expand_layout

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/system/gateway.mac"
BUILD = ROOT / "build/system"
COMPONENTS = (
    (LAYOUT["SYSTEM"], "gateway.bin"),
    (LAYOUT["BDOS"], "../bdos/bdos.bin"),
    (LAYOUT["FILE"], "fileloader.bin"),
    (LAYOUT["RSX"], "rsxloader.bin"),
    (LAYOUT["EXTENSIONS"], "extensions.bin"),
    (LAYOUT["TABLES"], "tables.bin"),
    (LAYOUT["RELOADER"], "../trs80/ccpreload.bin"),
    (LAYOUT["BIOS"], "../bios/bios.bin"),
)
RESIDENT_BASE = LAYOUT["SYSTEM"]
LIMITS = (LAYOUT["BDOS"], LAYOUT["FILE"], LAYOUT["RSX"], LAYOUT["EXTENSIONS"], LAYOUT["TABLES"], LAYOUT["RELOADER"], LAYOUT["RSX_STATE"], LAYOUT["CEILING"])


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
    for relative, name, base in (("src/system/extensions.mac", "extensions", LAYOUT["EXTENSIONS"]),
                                  ("src/bios/tables.mac", "tables", LAYOUT["TABLES"])):
        source = (ROOT / relative).read_text(encoding="ascii").replace(
            "        CSEG\n        .PHASE  ", "        ASEG\n        ORG     "
        ).replace("        .DEPHASE\n", "")
        with tempfile.TemporaryDirectory(prefix="bettercpm-support-") as temporary:
            staged = Path(temporary)
            (staged / f"{name}.mac").write_text(expand_layout(source), encoding="ascii")
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
        staged.write_text(expand_layout(text), encoding="ascii")
        subprocess.run([str(args.assembler), "-fb", f"-o{gateway}",
                        f"-l{BUILD / 'gateway.lst'}", staged.name],
                       check=True, cwd=staged.parent)
    data = gateway.read_bytes()
    if len(data) > LAYOUT["SYSTEM"] and data[:LAYOUT["SYSTEM"]] == bytes(LAYOUT["SYSTEM"]):
        data = data[LAYOUT["SYSTEM"]:]
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
    # Account for buffers and stacks that do not appear as emitted binaries.
    reservations = [(LAYOUT["TPA"], 3), (LAYOUT["HISTORY"], 512),
                    (LAYOUT["RSX_STATE"], 41),
                    (LAYOUT["STACK_LOW"], LAYOUT["STACK_TOP"] - LAYOUT["STACK_LOW"]),
                    (LAYOUT["DIRBUF"], 128), (LAYOUT["MODULEBUF"], 512)]
    ranges = sorted(reservations + [(address, len(data)) for address, data in loaded])
    previous_end = LAYOUT["TPA"]
    for address, size in ranges:
        if size <= 0 or address < previous_end:
            raise SystemExit(f"protected code/workspace overlap at {address:04X}h")
        previous_end = address + size
    if previous_end > LAYOUT["CEILING"]:
        raise SystemExit("protected image overlaps hardware-mapped memory")
    if (LAYOUT["HISTORY"] != base - 512 or
            LAYOUT["TPA"] != LAYOUT["HISTORY"] - 3):
        raise SystemExit("gateway/history placement disagrees with system initialization")
    load_end = base + LAYOUT["BOOT_SECTORS"] * 512
    if end > load_end or load_end > LAYOUT["CEILING"]:
        raise SystemExit("stage-one sector count does not safely cover the resident image")
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
