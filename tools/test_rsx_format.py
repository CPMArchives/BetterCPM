#!/usr/bin/env python3
"""Validate every public BRSX-v2 carrier and its service metadata."""
from __future__ import annotations

import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def check(path: Path, name: bytes, services: tuple[int, ...], allocation: int) -> None:
    module = path.read_bytes()
    require(module[:8] == b"BRSX\x02\x02\x01\x00", f"{path.name}: identity/ABI")
    (flags, linked, size, observed_allocation, entry, init, shutdown,
     relocations, header_size, payload, table, metadata) = struct.unpack_from(
         "<12H", module, 8)
    require(flags == 0 and linked == 0x8000 and size,
            f"{path.name}: flags or linked image")
    require(observed_allocation == allocation and allocation >= size
            and allocation & 0xFF == 0 and entry < size,
            f"{path.name}: allocation or dispatch entry")
    require(init == shutdown == 0xFFFF, f"{path.name}: lifecycle entry")
    require(header_size == payload == 512 and table == 48,
            f"{path.name}: noncanonical section layout")
    require(table + relocations * 2 <= header_size,
            f"{path.name}: relocation directory crosses header")
    require(module[32:40] == name.ljust(8, b" "), f"{path.name}: name")
    require(module[42] == len(services), f"{path.name}: service count")
    require(struct.unpack_from("<H", module, 46)[0] == services[0],
            f"{path.name}: primary service")
    offsets = struct.unpack_from(f"<{relocations}H", module, table)
    require(len(set(offsets)) == len(offsets)
            and all(offset + 1 < size for offset in offsets),
            f"{path.name}: invalid relocation")
    code = module[payload:payload + size]
    require((sum(code) & 0xFFFF) == struct.unpack_from("<H", module, 44)[0],
            f"{path.name}: payload checksum")
    require(module[metadata:metadata + 4] == b"BMET",
            f"{path.name}: metadata identity")
    require(module[metadata + 4:metadata + 7] == bytes((1, 0, 12)),
            f"{path.name}: metadata ABI or header size")
    record_count = module[metadata + 7]
    metadata_size = struct.unpack_from("<H", module, metadata + 8)[0]
    require(metadata + metadata_size == len(module),
            f"{path.name}: metadata length or trailing data")
    require(record_count == (1 if services else 0),
            f"{path.name}: unexpected metadata records")
    if services:
        require(module[metadata + 12:metadata + 14] == bytes((1, len(services)))
                and tuple(module[metadata + 14:]) == services,
                f"{path.name}: numeric service record")


def main() -> None:
    for stem in ("HELLO", "ECHO", "FDF", "P2DOS", "BATCHIO", "FREHDCLK",
                 "ZPRTC", "TEST"):
        require((ROOT / f"build/rsx/{stem}.RSX").read_bytes()[:5] ==
                b"BRSX\x02", f"{stem}.RSX: public carrier is not BRSX v2")
    check(ROOT / "build/rsx/HELLO.RSX", b"HELLO", (198,), 1024)
    check(ROOT / "build/rsx/ECHO.RSX", b"ECHO", (199,), 256)
    check(ROOT / "build/rsx/FDF.RSX", b"FDF", (183,), 768)
    check(ROOT / "build/rsx/P2DOS.RSX", b"P2DOS", (200, 201), 256)
    check(ROOT / "build/rsx/BATCHIO.RSX", b"BATCHIO", (10,), 512)
    print("All public BRSX carriers use v2 identity, runtime headers, and metadata")


if __name__ == "__main__":
    main()
