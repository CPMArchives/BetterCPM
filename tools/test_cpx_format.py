#!/usr/bin/env python3
"""Validate the public BCPX version-1 carriers and their metadata."""
from __future__ import annotations

import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def check(path: Path, name: bytes, commands: tuple[bytes, ...]) -> None:
    module = path.read_bytes()
    require(module[:8] == b"BCPX\x01\x01\x01\x00", f"{path.name}: identity/ABI")
    (linked, size, allocation, entry, init, shutdown, relocations,
     header_size, payload, table, metadata) = struct.unpack_from("<11H", module, 10)
    require(linked == 0x8000 and size and allocation >= size,
            f"{path.name}: invalid linked image dimensions")
    require(allocation & 0xFF == 0 and entry < size,
            f"{path.name}: invalid allocation or command entry")
    require(init == shutdown == 0xFFFF, f"{path.name}: unexpected lifecycle entry")
    require(header_size == payload == 512 and table == 48,
            f"{path.name}: noncanonical v1 section layout")
    require(table + relocations * 2 <= header_size,
            f"{path.name}: relocation directory crosses header")
    require(module[32:40] == name.ljust(8, b" "), f"{path.name}: module name")
    count = module[42]
    require(count == len(commands), f"{path.name}: command count")
    observed = tuple(module[metadata + n * 8:metadata + (n + 1) * 8].rstrip()
                     for n in range(count))
    require(observed == commands, f"{path.name}: command metadata {observed!r}")
    code = module[payload:payload + size]
    require((sum(code) & 0xFFFF) == struct.unpack_from("<H", module, 44)[0],
            f"{path.name}: payload checksum")
    require(metadata + count * 8 == len(module), f"{path.name}: trailing data")


def main() -> None:
    check(ROOT / "build/cpx/BASIC.CPX", b"BASIC",
          (b"DIR", b"ERA", b"TYPE", b"REN", b"SAVE", b"USER", b"CLR", b"VER"))
    check(ROOT / "build/cpx/HELLO.CPX", b"HELLO", (b"HELLO",))
    print("BCPX v1 identity, ABI, layout, relocation, metadata, and checksum passed")


if __name__ == "__main__":
    main()
