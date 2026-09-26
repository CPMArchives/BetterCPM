#!/usr/bin/env python3
"""Exercise final private-selector routing and P2DOS absence behavior."""
from __future__ import annotations

from pathlib import Path

from system_layout import LAYOUT
from test_bios import Z80, require

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    cpu = Z80(b"")
    bdos = (ROOT / "build/bdos/bdos.bin").read_bytes()
    extension = (ROOT / "build/system/extensions.bin").read_bytes()
    cpu.mem[LAYOUT["BDOS"]:LAYOUT["BDOS"] + len(bdos)] = bdos
    cpu.mem[LAYOUT["EXTENSIONS"]:LAYOUT["EXTENSIONS"] + len(extension)] = extension
    initial_sp = 0xA800

    def call(selector: int) -> None:
        cpu.sp, cpu.c, cpu.de, cpu.ix = initial_sp, selector, 0x73A0, 0xA55A
        cpu.run(LAYOUT["BDOS"], limit=5000)
        require(cpu.sp == initial_sp and cpu.de == 0x73A0 and cpu.ix == 0xA55A,
                f"Function {selector} damaged preserved state")

    for selector in (200, 201):
        call(selector)
        require(cpu.a == 0xFF and cpu.hl == 0x00FF,
                f"absent P2DOS Function {selector} fallback is incorrect")

    for selector in (41, 175, 184, 197, 202, 220, 255):
        call(selector)
        require(cpu.a == 0 and cpu.hl == 0,
                f"unassigned selector {selector} entered private dispatch")

    print("Final selector routing and absent P2DOS fallback passed")


if __name__ == "__main__":
    main()
