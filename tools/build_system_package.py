#!/usr/bin/env python3
"""Compose the host reference for SYSBUILD's version-1 SYSTEM.SYS package."""
from __future__ import annotations

import argparse
import shutil
import struct
from pathlib import Path

from add_cpm_file_to_dmk import extract_raw
from system_layout import LAYOUT

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "build/trs80/system-package"
PAYLOAD_SIZE = 20 * 1024

COMPONENTS = (
    ("BOOT.BIN", "build/trs80/boot.bin", 0, 512),
    ("STAGE1.BIN", "build/trs80/stage1.bin", 512, 512),
    ("RESIDENT.BIN", "build/system/resident.bin", 1024, 52 * 128),
    ("CCPRELOD.BIN", "build/trs80/ccpreload.bin", 7680, 896),
    ("RSXSEL.BIN", "build/trs80/rsxselect.bin", 8576, 128),
    ("CONFIG.BIN", "build/system/config.bin", 8704, 1024),
    ("RSXLOAD.BIN", "build/system/rsxloader.bin", 9728, 1021),
    ("RSXVALID.BIN", "build/system/rsxvalidator.bin", 10752, 1021),
    ("RSXPUBL.BIN", "build/system/rsxpublish.bin", 11776, 1021),
    ("RSXRESOL.BIN", "build/system/rsxresolver.bin", 12800, 1021),
    ("CCP.RLM", "build/ccp/ccp.rlm", 13824, 52 * 128),
)


def compose() -> tuple[bytes, dict[str, bytes]]:
    payload = bytearray(PAYLOAD_SIZE)
    exported = {}
    for name, relative, offset, capacity in COMPONENTS:
        data = (ROOT / relative).read_bytes()
        if not data or len(data) > capacity:
            raise ValueError(f"{name}: {len(data)} bytes exceeds {capacity}")
        payload[offset:offset + len(data)] = data
        exported[name] = data
    gateway = bytes((0xC3, LAYOUT["BDOS"] & 0xFF, LAYOUT["BDOS"] >> 8))
    for offset in (9728, 10752, 11776, 12800):
        payload[offset + 1021:offset + 1024] = gateway

    resident = bytes(payload[1024:1024 + 52 * 128])
    signature = b"BDCF" + bytes((5, 4, 4, 64))
    at = resident.index(signature)
    logical = struct.unpack_from("<H", resident, at + 10)[0]
    binding_at = logical - LAYOUT["SYSTEM"] + 16
    if not 0 <= binding_at <= len(resident) - 64:
        raise ValueError("built A: binding lies outside the resident image")
    header = bytearray(128)
    header[:6] = b"BCSY" + bytes((1, 1))
    struct.pack_into("<HH", header, 6, 160, LAYOUT["SYSTEM"])
    header[16:80] = resident[binding_at:binding_at + 64]
    return bytes(header) + bytes(payload), exported


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    package, components = compose()
    for name, data in components.items():
        (output / name).write_bytes(data)
    (output / "SYSTEM.SYS").write_bytes(package)

    boot_disk = ROOT / "build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk"
    if boot_disk.is_file():
        installed = extract_raw(boot_disk.read_bytes())[:PAYLOAD_SIZE]
        if package[128:] != installed:
            raise ValueError("SYSTEM.SYS payload differs from the installed boot image")
    print(f"Created {output / 'SYSTEM.SYS'} ({len(package)} bytes, 161 records)")


if __name__ == "__main__":
    main()
