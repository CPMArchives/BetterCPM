#!/usr/bin/env python3
"""Validate the self-hosted system build kit and its complete-source companion."""
from __future__ import annotations

import subprocess
import re
import tempfile
import shutil
from pathlib import Path

from build_source_disk import BUILD_INCLUDES, extract_files, z80pack_logical
from system_layout import LAYOUT

ROOT = Path(__file__).resolve().parents[1]
BUILD_IMAGE = ROOT / "build/trs80/BetterCPM-Build-80T-DS-800K.img"
BUILD_Z80PACK = ROOT / "build/trs80/BetterCPM-Build-80T-DS-800K.dsk"
WORK_IMAGE = ROOT / "build/trs80/BetterCPM-Work-80T-DS-800K.img"
WORK_Z80PACK = ROOT / "build/trs80/BetterCPM-Work-80T-DS-800K.dsk"

PRODUCTS = (
    "BOOT.BIN", "STAGE1.BIN", "RESIDENT.BIN", "CCPRELOD.BIN",
    "RSXSEL.BIN", "CONFIG.BIN", "RSXLOAD.BIN", "RSXRESOL.BIN", "CCP.RLM",
)


def main() -> None:
    subprocess.run(["python3", str(ROOT / "tools/build_source_disk.py")],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    build = extract_files(BUILD_IMAGE.read_bytes())
    if z80pack_logical(BUILD_Z80PACK.read_bytes()) != BUILD_IMAGE.read_bytes():
        raise SystemExit("z80pack build disk does not decode to the logical image")
    work = extract_files(WORK_IMAGE.read_bytes())
    if z80pack_logical(WORK_Z80PACK.read_bytes()) != WORK_IMAGE.read_bytes():
        raise SystemExit("z80pack work disk does not decode to the logical image")
    includes = {name for name, _relative in BUILD_INCLUDES}
    work_names = {name for _user, name in work}
    if work_names != includes:
        raise SystemExit("native work disk is not the exact generated-include set")
    source_images = sorted((ROOT / "build/trs80").glob(
        "BetterCPM-Sources-[0-9]*-80T-DS-800K.img"))
    if not source_images:
        raise SystemExit("no source archive volumes were generated")
    for image in source_images:
        if z80pack_logical(image.with_suffix(".dsk").read_bytes()) != image.read_bytes():
            raise SystemExit(f"z80pack source disk does not decode: {image.name}")
    # Qualify the published cpmtools view itself.  A conventional 160-track
    # raw definition lets libdsk infer side ordering and silently reads files
    # beyond the first side from the wrong offsets.
    with tempfile.TemporaryDirectory(prefix="bettercpm-build-disk-") as tmp:
        work = Path(tmp)
        shutil.copy2(ROOT / "build/trs80/diskdefs-build", work / "diskdefs")
        shutil.copy2(BUILD_IMAGE, work / "build.img")
        subprocess.run(["cpmcp", "-f", "bettercpm-build", "build.img",
                        "0:ZSM4.COM", "ZSM4.COM"], cwd=work, check=True)
        expected = build[(0, "ZSM4.COM")]
        actual = (work / "ZSM4.COM").read_bytes()[:len(expected)]
        if actual != expected:
            raise SystemExit("cpmtools flat-image definition reordered build-disk data")
    required = {
        "BUILD.SUB", "ZSM4.COM", "LINK.COM", "SUBMIT.COM", "BATCHIO.RSX",
        "RESPACK.COM", "RLMBUILD.COM", "SYSBUILD.COM", "SYSGEN.COM", "CORE.INC",
        "BIOSLINK.INC", "DISKLINK.INC", "CPXLINK.INC",
        "BOOT.MAC", "STAGE1.MAC", "GATEWAY.MAC", "BDOS.MAC", "EXTENS.MAC",
        "DISK.MAC", "BIOS.MAC", "FILELOAD.MAC", "TABLES.MAC", "CCPRELOD.MAC",
        "RSXSEL.MAC", "CONFIG.MAC", "RSXLOAD.MAC", "RSXRESOL.MAC",
        "CCP.MAC", "CCPALT.MAC", "CCPCHK.MAC",
        "R3PLAN.RSX", "R3SLOTS.RSX", "R3SNAP.RSX", "R3CARR.RSX",
        "R3META.RSX", "R3COORD.RSX", "R3PROF.RSX", "R3KCTX.RSX",
        "R3KEEP.RSX", "R3KPRE.RSX", "R3FINAL.RSX", "R3DROP.RSX",
        "R3MOVE.RSX", "R3COMIT.RSX", "R3RESOL.RSX",
    }
    names = {name for _user, name in build}
    missing = sorted(required - names)
    if missing:
        raise SystemExit(f"native build disk lacks {missing}")
    script = build[(0, "BUILD.SUB")].decode("ascii").replace("\r", "")
    lines = script.rstrip("\x1a\n").splitlines()
    if any(not line.strip() or line.lstrip().startswith(";") or len(line) > 126
           for line in lines):
        raise SystemExit("native BUILD.SUB is not a bounded command-only stream")
    for product in PRODUCTS:
        if product not in script and product not in ("RESIDENT.BIN", "CCP.RLM"):
            raise SystemExit(f"BUILD.SUB does not produce {product}")
    for command in ("C:\n", "B:RESPACK\n", "B:RLMBUILD\n", "B:SYSBUILD\n"):
        if command not in script:
            raise SystemExit(f"BUILD.SUB lacks {command.strip()}")

    if "REN CCPBASE.BIN=CCP.COM" not in script:
        raise SystemExit("BUILD.SUB does not supply RLMBUILD's canonical base input")
    for name in ("STAGE1.MAC", "CCPRELOD.MAC", "RSXSEL.MAC"):
        if b"-sector-table@" in build[(0, name)]:
            raise SystemExit(f"native source retains an unexpanded table: {name}")
    if b"-sector-table@" in extract_files(WORK_IMAGE.read_bytes())[(0, "RELOAD.INC")]:
        raise SystemExit("native work disk retains unexpanded overlay tables")
    listing = (ROOT / "build/utilities/sysbuild.lst").read_text()
    symbols = {name: int(address, 16) for address, name in re.findall(
        r"^([0-9a-f]{4})\s+.*?\b(OUTFCB|HEADER):", listing, re.M | re.I)}
    if symbols["HEADER"] - symbols["OUTFCB"] != 36:
        raise SystemExit("SYSBUILD reopen reset can overwrite its expected header")

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

    archived: set[tuple[int, str]] = set()
    manifests: set[bytes] = set()
    for image in source_images:
        source = extract_files(image.read_bytes())
        manifests.add(source[(0, "SOURCES.DOC")].rstrip(b"\x1a"))
        files = set(source) - {(0, "README.DOC"), (0, "SOURCES.DOC")}
        if archived & files:
            raise SystemExit(f"source names repeat across archive volumes: {image.name}")
        archived |= files
    if len(manifests) != 1:
        raise SystemExit("source archive volumes disagree on SOURCES.DOC")
    source_count = sum(1 for path in (ROOT / "src").rglob("*")
                       if path.is_file() and not path.name.startswith("."))
    if len(archived) != source_count:
        raise SystemExit("source archive volumes do not cover the current src tree")
    print("native build disk contains the complete BUILD.SUB toolchain; RESPACK "
          "matches resident.bin and the companion volumes preserve every source")


if __name__ == "__main__":
    main()
