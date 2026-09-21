#!/usr/bin/env python3
"""Verify that RSX.COM supplies the Function 202 v2 workspace contract."""
from __future__ import annotations

import re
from pathlib import Path

from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = 0x7000


def invoke(command: bytes, ceiling: int = 0xD000) -> tuple[bytes, int]:
    cpu = Z80(b"")
    program = (ROOT / "build/utilities/RSX.COM").read_bytes()
    cpu.mem[0x100:0x100 + len(program)] = program
    cpu.mem[0x80] = len(command)
    cpu.mem[0x81:0x81 + len(command)] = command
    cpu.mem[5:8] = bytes((0xC3, ceiling & 0xFF, ceiling >> 8))
    # Capture the Function 202 request; every other BDOS call returns normally.
    cpu.mem[ceiling:ceiling + 0x12] = bytes((
        0x79, 0xFE, 0xCA, 0x20, 0x0B, 0xEB, 0x11, 0x00, 0x70,
        0x01, 0x12, 0x00, 0xED, 0xB0, 0xAF, 0xC9, 0xAF, 0xC9,
    ))
    cpu.sp = 0xD000
    cpu.run(0x100, limit=20000)
    return bytes(cpu.mem[CAPTURE:CAPTURE + 18]), cpu.sp


def main() -> None:
    listing = (ROOT / "build/utilities/rsx.lst").read_text(encoding="ascii")
    match = re.search(r"^([0-9a-f]{4})\s+.*\bRS_END:", listing,
                      re.MULTILINE | re.IGNORECASE)
    assert match
    low = int(match[1], 16)
    for command, operation in ((b"LOAD HELLO", 1), (b"UNLOAD HELLO", 2)):
        request, final_sp = invoke(command)
        assert request[:4] == bytes((2, operation, 0, 0))
        assert request[4:12] == b"HELLO   "
        assert int.from_bytes(request[12:14], "little") == 0
        assert int.from_bytes(request[14:16], "little") == low
        high = int.from_bytes(request[16:18], "little")
        assert low < high <= 0xD000 and high + 64 < 0xD000
        assert final_sp == 0xD000
    request, _ = invoke(b"LOAD HELLO", ceiling=0xC800)
    assert int.from_bytes(request[16:18], "little") == 0xC800
    print("RSX.COM emits Function 202 v2 load/unload requests with workspace "
          "bounded by its image end and live stack")


if __name__ == "__main__":
    main()
