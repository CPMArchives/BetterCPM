#!/usr/bin/env python3
"""Validate BRSX-v2 typed metadata and runtime descriptor capacity."""
from __future__ import annotations

import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    module = (ROOT / "build/rsx/TEST.RSX").read_bytes()
    require(module[:8] == b"BRSX\x02\x02\x01\x00", "BRSX-v2 identity/ABI")
    flags, size, allocation, entry, metadata = struct.unpack_from(
        "<HxxHHH12xH", module, 8)
    require(flags & 3 == 0, "TEST provider is not STATELESS")
    require(entry >= 8 and size + 10 <= allocation,
            "runtime header or service-descriptor capacity")
    require(module[metadata:metadata + 4] == b"BMET", "metadata signature")
    major, minor, header_size, count, total, reserved = struct.unpack_from(
        "<BBBBHH", module, metadata + 4)
    require((major, minor, header_size, count, reserved) == (1, 0, 12, 1, 0),
            "metadata envelope")
    require(metadata + total == len(module), "metadata length/trailing data")
    record_type, length = module[metadata + 12:metadata + 14]
    require((record_type, length) == (2, 10), "callable-service record")
    service_id, abi_major, abi_minor, service_entry, capabilities = \
        struct.unpack_from("<4sBBHH", module, metadata + 14)
    require((service_id, abi_major, abi_minor, capabilities) ==
            (b"TEST", 1, 0, 1), "TEST service identity")
    require(8 <= service_entry < size, "TEST service entry")
    print("BRSX v2 envelope, typed TEST advertisement, and capacity passed")


if __name__ == "__main__":
    main()
