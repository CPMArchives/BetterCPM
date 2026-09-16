#!/usr/bin/env python3
"""Validate the Phase-3 qualification carrier and its pointer classes."""
from __future__ import annotations

import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 0x8000


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def symbols(path: Path) -> dict[str, int]:
    return {name.upper(): int(address, 16) for address, name in re.findall(
        r"^([0-9a-f]{4})\s+.*?\b([A-Z][A-Z0-9_]*):",
        path.read_text(encoding="ascii"), re.M | re.I)}


def main() -> None:
    module = (ROOT / "build/rsx/STATEFUL.RSX").read_bytes()
    names = symbols(ROOT / "build/rsx/stateful.lst")
    flags = struct.unpack_from("<H", module, 8)[0]
    size, allocation, entry = struct.unpack_from("<HHH", module, 12)
    relocations = struct.unpack_from("<H", module, 22)[0]
    relocation_table = struct.unpack_from("<H", module, 28)[0]
    metadata = struct.unpack_from("<H", module, 30)[0]
    require(module[:8] == b"BRSX\x02\x02\x01\x00", "BRSX-v2 identity/ABI")
    require(flags & 3 == 1 and flags & ~3 == 0,
            "qualification provider is not STATEFUL")
    require(entry == 8 and size < allocation and allocation & 0xFF == 0,
            "live allocation contract")
    offsets = struct.unpack_from(f"<{relocations}H", module, relocation_table)
    linked = names["SR_LINKED"] - BASE
    runtime = names["SR_RUNTIME"] - BASE
    require(linked in offsets, "ordinary linked pointer lacks relocation")
    require(runtime not in offsets, "runtime pointer was treated as static")
    code = module[512:512 + size]
    require(struct.unpack_from("<H", code, linked)[0] == names["SR_BUFFER"],
            "linked pointer target")
    require(struct.unpack_from("<H", code, runtime)[0] == 0,
            "runtime pointer must begin null")
    require(struct.unpack_from("<H", code, names["SR_FIXED"] - BASE)[0] == 5,
            "fixed address fixture")
    require(struct.unpack_from("<H", code, names["SR_NULL"] - BASE)[0] == 0,
            "null fixture")
    require(struct.unpack_from("<H", code, names["SR_SENTINEL"] - BASE)[0] == 0xFFFF,
            "sentinel fixture")
    require(module[metadata:metadata + 12] ==
            b"BMET\x01\x00\x0c\x02\x1c\x00\x00\x00", "metadata envelope")
    cursor = metadata + 12
    require(module[cursor:cursor + 2] == bytes((2, 10)),
            "callable record framing")
    service_id, major, minor, service_entry, capabilities = struct.unpack_from(
        "<4sBBHH", module, cursor + 2)
    require((service_id, major, minor, service_entry, capabilities) ==
            (b"STAT", 1, 0, names["SR_SERVICE"] - BASE, 0),
            "STAT advertisement")
    cursor += 12
    require(module[cursor:cursor + 4] == bytes((3, 2, runtime & 0xFF,
                                               runtime >> 8)),
            "runtime-pointer metadata")
    print("STATEFUL qualification carrier covers mutable, linked, runtime, "
          "fixed, null, and sentinel state")


if __name__ == "__main__":
    main()
