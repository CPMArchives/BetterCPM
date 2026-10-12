#!/usr/bin/env python3
"""Run existing behavioral campaigns against isolated audit candidates.

No production binary is replaced. This checks emulated semantics, not floppy
controller timing, native assembler parity, or a final packed-system release.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import test_bios as bios
import test_unified_bdos as foundation

ROOT = Path(__file__).resolve().parents[1]


def symbols(path: Path) -> dict[str, int]:
    return {name: int(address, 16) for address, name in re.findall(
        r"^([0-9a-f]{4})\s+.*?\b([A-Z][A-Z0-9_]*):", path.read_text(errors="replace"), re.M | re.I)}


def mapping_checks(candidate: Path) -> None:
    """Compare emitted baseline/candidate mapping across sizes and track modes."""
    variants = (ROOT / "build/system", candidate)
    states = symbols(ROOT / "build/bios/bios.lst")
    images = [(folder / "disk.bin").read_bytes() for folder in variants]
    syms = [symbols(folder / "disk.lst") for folder in variants]
    cases = 0
    for drive in range(5):  # includes unavailable drive
        for size in range(4):
            for flags in (0, 0x20, 0x40, 0x60, 0x80, 0xE0):
                spt = (20 if flags & 0x20 else 10) << size
                sectors = sorted({0, 1, spt // 2 - 1, spt // 2, spt - 1, spt, 65535})
                for track in (0, 1, 23, 79, 80, 159, 160, 255, 256, 65535):
                    for sector in sectors:
                        results = []
                        for image, table in zip(images, syms):
                            cpu = bios.Z80(b"")
                            bios_base = bios.LAYOUT["DISK"]
                            cpu.mem[bios_base:bios_base + len(image)] = image
                            data = (ROOT / "build/system/tables.bin").read_bytes()
                            start = bios.LAYOUT["TABLES"]
                            cpu.mem[start:start + len(data)] = data
                            binding = start + min(drive, 3) * 80 + 16
                            cpu.setword(binding + 1, spt)
                            cpu.mem[binding + 18] = size
                            cpu.mem[binding + 19] = flags
                            cpu.mem[binding + 52] = 0
                            cpu.mem[states["BIO_DRIVE"]] = drive
                            cpu.setword(states["BIO_TRACK"], track)
                            cpu.setword(states["BIO_SECTOR"], sector)
                            cpu.ix, cpu.sp = 0x7788, 0xA000
                            cpu.run(table["DC_MAP"])
                            results.append((cpu.a, cpu.z, cpu.carry, cpu.ix, cpu.sp,
                                tuple(cpu.mem[states[name]] for name in
                                      ("BIO_PCYL", "B_PSide", "B_PDrive", "BIO_PSEC", "BIO_QUART")),
                                cpu.mem[table["DC_SIZE"]], cpu.mem[table["DC_FLAGS"]]))
                        assert results[0] == results[1], (drive, size, flags, track, sector, results)
                        cases += 1
    print(f"{cases} differential geometry cases passed: sizes, track modes, limits and unavailable drive")


def length_checks(candidate: Path) -> None:
    """Execute the real transfer setup through its calculated block-count point."""
    table = symbols(candidate / "disk.lst")
    for size in range(4):
        cpu = bios.Z80(b"")
        data = (candidate / "disk.bin").read_bytes()
        base = bios.LAYOUT["DISK"]
        cpu.mem[base:base + len(data)] = data
        cpu.mem[table["DC_SEEK"]:table["DC_SEEK"] + 2] = bytes((0xAF, 0xC9))
        cpu.mem[table["DC_BSET"]] = 0xC9
        cpu.mem[table["DC_SIZE"]] = size
        cpu.setword(table["DC_BUFFER"], 0x8000)
        cpu.port_write = lambda port, value: None  # sector/command setup only
        cpu.run(table["DC_TRY"])
        assert cpu.a == max(1, (128 << size) // 256), (size, cpu.a)
        assert cpu.hl == 0x8000
    print("4 actual transfer-setup length cases passed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, default=ROOT / "build/audit/monitor-efficiency")
    args = parser.parse_args()
    measurements = json.loads((args.audit / "measurements.json").read_text())
    candidates = {row["component"]: Path(row["directory"]) for row in measurements}
    bdos, disk = candidates["bdos"], candidates["disk"]
    foundation.IMAGE, foundation.LISTING = bdos / "bdos.bin", bdos / "bdos.lst"
    original_install = bios.install_drive_tables

    def install(cpu, *arguments, **keywords):
        original_install(cpu, *arguments, **keywords)
        data = (disk / "disk.bin").read_bytes()
        base = bios.LAYOUT["DISK"]
        cpu.mem[base:base + len(data)] = data

    bios.install_drive_tables = foundation.install_drive_tables = install
    bios.main()
    foundation.main()
    # Import these only after redirecting the image and symbol inputs.
    import test_bdos_grouped_extents as grouped
    import test_bdos_recovery as recovery
    import test_bios_retry as retry
    grouped.main()
    recovery.wrapper_checks()
    # The recovery campaign re-executes the foundation's source. Explicitly
    # redirect its source constants too, otherwise it silently tests baseline.
    source = Path(foundation.__file__).read_text()
    source = source.replace("ROOT = Path(__file__).resolve().parents[1]", f"ROOT = Path({str(ROOT)!r})")
    source = source.replace('IMAGE = ROOT / "build/bdos/bdos.bin"', f"IMAGE = Path({str(foundation.IMAGE)!r})")
    source = source.replace('LISTING = ROOT / "build/bdos/bdos.lst"', f"LISTING = Path({str(foundation.LISTING)!r})")
    test_source = bdos / "test_unified_bdos.py"
    test_source.write_text(source)
    foundation.__file__ = str(test_source)
    recovery.all_paths()

    retry_root = args.audit / "disk-test-root"
    target = retry_root / "build/system"
    target.mkdir(parents=True, exist_ok=True)
    (target / "disk.bin").write_bytes((disk / "disk.bin").read_bytes())
    # The assembler's listing banner can contain non-UTF8 path bytes.
    (target / "disk.lst").write_text((disk / "disk.lst").read_text(errors="replace"))
    retry.ROOT = retry_root
    retry.main()
    mapping_checks(disk)
    length_checks(disk)
    print("PASS isolated monitor-memory candidates; production images unchanged")


if __name__ == "__main__":
    main()
