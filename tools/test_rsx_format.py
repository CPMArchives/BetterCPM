#!/usr/bin/env python3
"""Validate the public BRSX version-1 carriers and service metadata."""
from __future__ import annotations

import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def check(path: Path, name: bytes, services: tuple[int, ...], allocation: int) -> None:
    module = path.read_bytes()
    require(module[:8] == b"BRSX\x01\x02\x01\x00", f"{path.name}: identity/ABI")
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
    require(tuple(module[metadata:]) == services,
            f"{path.name}: service metadata or trailing data")


def main() -> None:
    check(ROOT / "build/rsx/HELLO.RSX", b"HELLO", (201,), 1024)
    check(ROOT / "build/rsx/ECHO.RSX", b"ECHO", (203,), 256)
    print("BRSX v1 identity, ABI, layout, relocation, services, and checksum passed")


if __name__ == "__main__":
    main()
