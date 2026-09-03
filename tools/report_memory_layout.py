#!/usr/bin/env python3
"""Report occupied and theoretically packed BetterCP/M resident memory."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TPA_ORIGIN = 0x0100
MODEL4_CEILING = 0xF400

COMPONENTS = (
    ("System gateway and ECB", "build/system/gateway.bin", None),
    ("BDOS core and private data", "build/bdos/bdos.bin", None),
    ("Protected file loader", "build/system/fileloader.bin", None),
    ("RSX manager", "build/system/rsxloader.bin", None),
    ("Directory/filesystem services", "build/bdos/directory.bin", None),
    ("Command-environment reloader", "build/trs80/ccpreload.bin", None),
    ("BIOS", "build/bios/bios.bin", None),
    ("Persistent command history", None, 512),
    ("Directory transfer buffer", None, 128),
    ("Protected module buffer", None, 512),
)


def main() -> None:
    total = 0
    print("Protected component                         Bytes")
    print("----------------------------------------  -----")
    for name, relative, fixed in COMPONENTS:
        size = fixed if fixed is not None else (ROOT / relative).stat().st_size
        total += size
        print(f"{name:40}  {size:5}")
    packed_base = MODEL4_CEILING - total
    packed_tpa = packed_base - TPA_ORIGIN
    print(f"{'Total occupied/protected':40}  {total:5}")
    print()
    print(f"Model 4 protected ceiling: {MODEL4_CEILING:04X}h")
    print(f"Theoretical byte-packed base: {packed_base:04X}h")
    print(f"Theoretical byte-packed TPA:  {packed_tpa // 1024}K + {packed_tpa % 1024} bytes")
    print("Current published TPA:        47K")
    required = max(0, total - (MODEL4_CEILING - (TPA_ORIGIN + 56 * 1024)))
    print(f"Reduction required for 56K:   {required} bytes")


if __name__ == "__main__":
    main()
