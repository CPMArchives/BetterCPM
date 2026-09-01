#!/usr/bin/env python3
"""Execute focused CCP parsing contracts from the assembled resident binary."""
from __future__ import annotations

import re
from pathlib import Path

from test_bios import Z80, require

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "build/ccp/ccp.bin"
LISTING = ROOT / "build/ccp/ccp.lst"
BASE = 0xE8E0
CALLER = 0x7000


def symbol(name: str) -> int:
    matches = re.findall(rf"^([0-9a-f]{{4}})\s+.*\b{name}:?\s*$",
                         LISTING.read_text(encoding="ascii"),
                         re.MULTILINE | re.IGNORECASE)
    require(matches, f"CCP listing lacks {name}")
    return int(matches[-1], 16)


def cpu() -> Z80:
    machine = Z80(b"")
    data = IMAGE.read_bytes()
    machine.mem[BASE:BASE + len(data)] = data
    machine.sp = 0x7F00
    return machine


def call(machine: Z80, address: int) -> None:
    machine.mem[CALLER:CALLER + 4] = bytes(
        (0xCD, address & 0xFF, address >> 8, 0xC9))
    machine.run(CALLER, limit=20000)


def main() -> None:
    # Stub Open as "not found" so CCP_LOAD returns after constructing its
    # private lookup FCB. This directly guards the 2026-09-01 stale-Z flag bug.
    for command, expected in (
        (b"HELLO WORLD", b"HELLO   COM"),
        (b"MINRET22 X", b"MINRET22COM"),
    ):
        machine = cpu()
        machine.mem[0xC100:0xC103] = bytes((0x3E, 0xFF, 0xC9))
        machine.mem[symbol("CCP_COUNT")] = len(command)
        start = symbol("CCP_DATA")
        machine.mem[start:start + len(command)] = command
        call(machine, symbol("CCP_LOAD"))
        fcb = symbol("CCP_FCB")
        require(bytes(machine.mem[fcb + 1:fcb + 12]) == expected,
                f"lookup FCB is wrong for {command!r}")

    # Exercise the ordinary two-operand default-FCB parser independently of
    # disk access. The second operand is the DRI profile fixture.
    machine = cpu()
    text = b"/0012 SECOND.BIN"
    source = 0x7200
    machine.mem[source:source + len(text)] = text
    machine.hl, machine.b, machine.de = source, len(text), 0x005C
    call(machine, symbol("CCP_PFCB"))
    call(machine, symbol("CCP_PSKIP"))
    machine.de = 0x006C
    call(machine, symbol("CCP_PFCB"))
    require(bytes(machine.mem[0x006C:0x0078]) == b"\x00SECOND  BIN",
            "second default FCB is not drive-zero SECOND.BIN")

    print("CCP lookup names with arguments and two ordinary default FCBs passed")


if __name__ == "__main__":
    main()
