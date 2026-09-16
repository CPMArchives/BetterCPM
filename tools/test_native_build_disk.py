#!/usr/bin/env python3
"""Validate the self-hosted system build kit and its complete-source companion."""
from __future__ import annotations

import subprocess
from pathlib import Path

from build_source_disk import extract_files, z80pack_logical
from system_layout import LAYOUT

ROOT = Path(__file__).resolve().parents[1]
BUILD_IMAGE = ROOT / "build/trs80/BetterCPM-Build-80T-DS-800K.img"
SOURCE_IMAGE = ROOT / "build/trs80/BetterCPM-Sources-80T-DS-800K.img"
BUILD_Z80PACK = ROOT / "build/trs80/BetterCPM-Build-80T-DS-800K.dsk"
SOURCE_Z80PACK = ROOT / "build/trs80/BetterCPM-Sources-80T-DS-800K.dsk"

PRODUCTS = (
    "BOOT.BIN", "STAGE1.BIN", "RESIDENT.BIN", "CCPRELOD.BIN",
    "RSXSEL.BIN", "CONFIG.BIN", "RSXLOAD.BIN", "RSXVALID.BIN",
    "RSXPUBL.BIN", "RSXRESOL.BIN", "CCP.RLM",
)


def main() -> None:
    subprocess.run(["python3", str(ROOT / "tools/build_source_disk.py")],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    build = extract_files(BUILD_IMAGE.read_bytes())
    if z80pack_logical(BUILD_Z80PACK.read_bytes()) != BUILD_IMAGE.read_bytes():
        raise SystemExit("z80pack build disk does not decode to the logical image")
    if z80pack_logical(SOURCE_Z80PACK.read_bytes()) != SOURCE_IMAGE.read_bytes():
        raise SystemExit("z80pack source disk does not decode to the logical image")
    required = {
        "BUILD.SUB", "ZSM4.COM", "LINK.COM", "SUBMIT.COM", "BATCHIO.RSX",
        "RESPACK.COM", "RLMBUILD.COM", "SYSBUILD.COM", "SYSGEN.COM", "CORE.INC",
        "BIOSLINK.INC", "DISKLINK.INC", "CPXLINK.INC",
        "BOOT.MAC", "STAGE1.MAC", "GATEWAY.MAC", "BDOS.MAC", "EXTENS.MAC",
        "DISK.MAC", "BIOS.MAC", "FILELOAD.MAC", "TABLES.MAC", "CCPRELOD.MAC",
        "RSXSEL.MAC", "CONFIG.MAC", "RSXLOAD.MAC", "RSXVALID.MAC",
        "RSXPUBL.MAC", "RSXRESOL.MAC", "CCP.MAC", "CCPALT.MAC", "CCPCHK.MAC",
    }
    names = {name for _user, name in build}
    missing = sorted(required - names)
    if missing:
        raise SystemExit(f"native build disk lacks {missing}")
    script = build[(0, "BUILD.SUB")].decode("ascii").replace("\r", "")
    for product in PRODUCTS:
        if product not in script and product not in ("RESIDENT.BIN", "CCP.RLM"):
            raise SystemExit(f"BUILD.SUB does not produce {product}")
    for command in ("B:\n", "RESPACK\n", "RLMBUILD\n", "SYSBUILD\n"):
        if command not in script:
            raise SystemExit(f"BUILD.SUB lacks {command.strip()}")

    # RESPACK's declared inputs must reproduce the host resident image exactly
    # after CP/M record padding.
    components = (
        (LAYOUT["SYSTEM"], ROOT / "build/system/gateway.bin"),
        (LAYOUT["BDOS"], ROOT / "build/bdos/bdos.bin"),
        (LAYOUT["EXTENSIONS"], ROOT / "build/system/extensions.bin"),
        (LAYOUT["DISK"], ROOT / "build/system/disk.bin"),
        (LAYOUT["BIOS"], ROOT / "build/bios/bios.bin"),
        (LAYOUT["FILE"], ROOT / "build/system/fileloader.bin"),
        (LAYOUT["TABLES"], ROOT / "build/system/tables.bin"),
    )
    packed = bytearray(52 * 128)
    for address, path in components:
        data = path.read_bytes()
        offset = address - LAYOUT["SYSTEM"]
        packed[offset:offset + len(data)] = data
    resident = (ROOT / "build/system/resident.bin").read_bytes()
    if packed != resident.ljust(52 * 128, b"\0"):
        raise SystemExit("RESPACK component map differs from resident.bin")

    source = extract_files(SOURCE_IMAGE.read_bytes())
    archived = {(user, name) for user, name in source}
    source_count = sum(1 for path in (ROOT / "src").rglob("*")
                       if path.is_file() and not path.name.startswith("."))
    if len(archived) != source_count + 2:
        raise SystemExit("complete-source image does not cover the current src tree")
    print("native build disk contains the complete BUILD.SUB toolchain; RESPACK "
          "matches resident.bin and the companion disk preserves every source")


if __name__ == "__main__":
    main()
