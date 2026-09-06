#!/usr/bin/env python3
"""Cross-assemble the independently buildable BetterCP/M BIOS scaffold."""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path
from system_layout import LAYOUT, expand_layout

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/bios"
PLATFORM = ROOT / "src/platform/trs80m4"
BUILD = ROOT / "build/bios"
BIOS_ADDRESS = LAYOUT["BIOS"]
BIOS_LIMIT = LAYOUT["FILE"] - BIOS_ADDRESS


def validate_bios(data: bytes) -> None:
    if not data:
        raise SystemExit("empty BIOS output")
    if len(data) > BIOS_LIMIT:
        raise SystemExit(
            f"BIOS is {len(data)} bytes; region {BIOS_ADDRESS:04X}h.."
            f"{LAYOUT['FILE'] - 1:04X}h permits {BIOS_LIMIT} bytes "
            f"(exceeds by {len(data) - BIOS_LIMIT} bytes); BIOS not installed")


def build_bios(assembler: Path) -> bytes:
    BUILD.mkdir(parents=True, exist_ok=True)
    text = (SOURCE / "bios.mac").read_text(encoding="ascii")
    text = text.replace("        CSEG\n        .PHASE  ",
                        "        ASEG\n        ORG     ")
    text = text.replace("        .DEPHASE\n", "")
    output = BUILD / "bios.bin"
    listing = BUILD / "bios.lst"
    with tempfile.TemporaryDirectory(prefix="bettercpm-bios-") as temporary:
        staged = Path(temporary)
        (staged / "bios.mac").write_text(expand_layout(text), encoding="ascii")
        shutil.copy2(SOURCE / "biosplat.inc", staged / "biosplat.inc")
        shutil.copy2(PLATFORM / "hardware.inc", staged / "hardware.inc")
        shutil.copy2(PLATFORM / "m4cons.inc", staged / "m4cons.inc")
        shutil.copy2(PLATFORM / "m4scroll.inc", staged / "m4scroll.inc")
        shutil.copy2(PLATFORM / "m4disk.inc", staged / "m4disk.inc")
        (staged / "reload.inc").write_text(expand_layout((PLATFORM / "reload.inc").read_text()))
        staged_output = staged / "bios.bin"
        staged_listing = staged / "bios.lst"
        subprocess.run([str(assembler), "-fb", f"-o{staged_output}",
                        f"-l{staged_listing}", "bios.mac"],
                       check=True, cwd=staged)
        data = staged_output.read_bytes()
        if len(data) > BIOS_ADDRESS and data[:BIOS_ADDRESS] == bytes(BIOS_ADDRESS):
            data = data[BIOS_ADDRESS:]
        validate_bios(data)
        # Publish only a successfully assembled BIOS that fits its region.
        output.write_bytes(data)
        listing.write_bytes(staged_listing.read_bytes())
    print(f"{hashlib.sha256(data).hexdigest()}  {output.relative_to(ROOT)}")
    print(f"BIOS bytes: {len(data)} / {BIOS_LIMIT} ({BIOS_LIMIT - len(data)} free)")
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    build_bios(args.assembler)


if __name__ == "__main__":
    main()
