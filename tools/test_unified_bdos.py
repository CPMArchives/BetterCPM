#!/usr/bin/env python3
"""Execute the first U01-U04 slice of the compact replacement BDOS."""
from __future__ import annotations

import re
from pathlib import Path

from test_bios import BASE as BIOS_BASE, Z80, install_drive_tables, require

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "build/bdos/unified-bdos.bin"
LISTING = ROOT / "build/bdos/unified-bdos.lst"
BIOS = ROOT / "build/bios/bios.bin"
BASE = 0xC100
FCB = 0x7000


def symbols() -> dict[str, int]:
    result: dict[str, int] = {}
    pattern = re.compile(r"^([0-9a-f]{4})\s+.*\s([A-Z][A-Z0-9_]*):", re.I)
    for line in LISTING.read_text(encoding="utf-8", errors="replace").splitlines():
        match = pattern.match(line)
        if match:
            result[match.group(2).upper()] = int(match.group(1), 16)
    return result


def main() -> None:
    cpu = Z80(BIOS.read_bytes())
    install_drive_tables(cpu)
    image = IMAGE.read_bytes()
    cpu.mem[BASE:BASE + len(image)] = image
    initial_sp = cpu.sp

    def call(function: int, parameter: int = 0) -> int:
        cpu.c, cpu.de = function, parameter
        cpu.run(BASE, limit=10000)
        require(cpu.sp == initial_sp, f"function {function} unbalanced stack")
        return cpu.a

    require(call(12) == 0x22 and cpu.hl == 0x22,
            "function 12 did not return CP/M 2.2")
    require(call(13) == 0, "disk reset failed")
    require(call(24) == 1 and cpu.hl == 1, "reset did not log drive A")
    require(call(25) == 0, "reset did not select drive A")

    call(31)
    dpb = cpu.hl
    require(dpb and cpu.word(dpb) == 80, "function 31 returned no live DPB")
    call(27)
    require(cpu.hl != 0 and cpu.hl != dpb, "function 27 returned no live ALV")

    require(call(14, 1) == 0 and call(25) == 1,
            "drive B selection failed")
    require(call(24) == 3, "drive B selection did not extend login vector")
    require(call(28) == 0 and call(29) == 2,
            "drive B software write protection failed")

    require(call(32, 7) == 7 and call(32, 0xFF) == 7,
            "user set/query failed")
    require(call(32, 16) == 0xFF and call(32, 0xFF) == 7,
            "invalid user changed current user")

    require(call(37, 2) == 0, "selective drive reset failed")
    require(call(24) == 1 and call(29) == 0,
            "selective reset did not clear drive B login/protection")
    require(call(14, 4) == 0xFF and call(25) == 1,
            "unavailable drive changed current drive")
    require(call(38) == 0 and call(39) == 0,
            "reserved standard functions did not return zero")
    require(call(15) == 0xFF, "unfinished file call was not rejected")

    fcbdrv = symbols()["UB_FCBDRV"]
    cpu.mem[FCB] = 0
    cpu.de = FCB
    cpu.run(fcbdrv)
    require(not cpu.carry and cpu.c == 1,
            "default FCB drive did not resolve to current drive B")
    cpu.mem[FCB] = 3
    cpu.de = FCB
    cpu.run(fcbdrv)
    require(not cpu.carry and cpu.c == 2, "explicit FCB drive did not resolve")
    cpu.mem[FCB] = 17
    cpu.de = FCB
    cpu.run(fcbdrv)
    require(cpu.carry, "invalid FCB drive was accepted")

    print(f"unified BDOS U01-U04 slice passed ({len(image)} bytes)")
    print("disk/user state, DPH pointers, vectors, reset, and FCB drive view passed")


if __name__ == "__main__":
    main()
