#!/usr/bin/env python3
"""Exercise Function 208 through the fixed resident extension bridge."""
from __future__ import annotations
import struct
from pathlib import Path
from system_layout import LAYOUT
from test_bios import Z80, require

ROOT = Path(__file__).resolve().parents[1]
REQUEST = 0x7000
HEAD = LAYOUT["SYSTEM"] + 0x84

def initialize(cpu: Z80) -> None:
    cpu.mem[REQUEST:REQUEST + 20] = struct.pack(
        "<BBBB4sBBHHBBHBB", 1, 20, 0, 0, b"TEST", 1, 0,
        0, 0xA5A5, 0xA5, 0xA5, 0xA5A5, 0xA5, 0xA5)
    cpu.c = 208
    cpu.de = REQUEST

def main() -> None:
    extension = (ROOT / "build/system/extensions.bin").read_bytes()
    resolver = (ROOT / "build/system/rsxresolver.bin").read_bytes()

    empty = Z80(b"")
    empty.mem[LAYOUT["EXTENSIONS"]:LAYOUT["EXTENSIONS"] + len(extension)] = extension
    initialize(empty)
    empty.run(LAYOUT["EXTENSIONS"], limit=5000)
    require(empty.a == 1 and empty.hl == 0 and empty.de == REQUEST,
            "empty Function 208 gateway result is incorrect")
    require(empty.mem[REQUEST + 12:REQUEST + 19] == bytes(7) and
            empty.mem[REQUEST + 19] == 1,
            "empty Function 208 gateway did not clear outputs")

    live = Z80(b"")
    live.mem[LAYOUT["EXTENSIONS"]:LAYOUT["EXTENSIONS"] + len(extension)] = extension
    live.mem[LAYOUT["RSX"]:LAYOUT["RSX"] + len(resolver)] = resolver
    base = 0xCD04
    struct.pack_into("<HHBBH", live.mem, base, LAYOUT["BDOS"], base + 8,
                     1, 0, 0x80)
    struct.pack_into("<4sBBHH", live.mem, base + 0x80,
                     b"TEST", 1, 0, 0x20, 0)
    live.setword(HEAD, base)
    live.mem[LAYOUT["RSX_STATE"]] = 1
    initialize(live)
    live.run(LAYOUT["EXTENSIONS"], limit=20000)
    require(live.a == 0 and live.hl == base + 0x20 and live.de == REQUEST,
            "resident Function 208 gateway did not return resolver results")
    print("Function 208 fixed gateway handles empty and active registries")

if __name__ == "__main__":
    main()
