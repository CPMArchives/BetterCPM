#!/usr/bin/env python3
"""Execute the U01-U06 foundation of the compact replacement BDOS."""
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
FIXTURE = 0x7500


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

    # Keep the production BIOS mapping and replace only its platform reader
    # with a deterministic 512-byte physical-sector fixture.
    read_impl = cpu.word(BIOS_BASE + 13 * 3 + 1)
    read_calls = [address for address in range(read_impl, read_impl + 48)
                  if cpu.mem[address] == 0xCD]
    require(len(read_calls) >= 2, "BIOS physical-read call was not found")
    platform_read = cpu.word(read_calls[1] + 1)
    read_success = bytes((
        0xF5, 0x3A, 0x03, 0x73, 0x3C, 0x32, 0x03, 0x73, 0xF1,
        0x32, 0x00, 0x73, 0x78, 0x32, 0x01, 0x73,
        0x79, 0x32, 0x02, 0x73,
        0x21, FIXTURE & 0xFF, FIXTURE >> 8,
        0x11, 0x00, 0xED, 0x01, 0x00, 0x02,
        0xED, 0xB0, 0xAF, 0xC9,
    ))
    cpu.mem[platform_read:platform_read + len(read_success)] = read_success
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

    # Shared U05 iterator and U06 DPH-backed cache: wildcard Search First/Next
    # must retain one cursor, return containing records, and avoid rereading a
    # cached directory sector between adjacent slots.
    cpu.mem[FIXTURE:FIXTURE + 512] = bytes((0xE5,)) * 512
    cpu.mem[FIXTURE:FIXTURE + 12] = bytes((7,)) + b"ONE     COM"
    cpu.mem[FIXTURE + 32:FIXTURE + 44] = bytes((7,)) + b"TWO     COM"
    cpu.mem[FIXTURE + 12] = cpu.mem[FIXTURE + 44] = 0
    cpu.mem[FCB:FCB + 36] = bytes(36)
    cpu.mem[FCB] = 0
    cpu.mem[FCB + 1:FCB + 12] = b"???????????"
    call(32, 7)
    cpu.mem[0x7303] = 0
    state = symbols()
    cpu.run(state["UB_DIRCOUNT"])
    require(cpu.b == 32, f"directory geometry returned {cpu.b} records")
    cpu.a = 0
    cpu.run(state["UB_DIRLOAD"], limit=10000)
    require(cpu.a == 0, f"directory cache load failed with {cpu.a:02X}")
    search_first = call(17, FCB)
    require(search_first == 0,
            f"Search First missed slot zero: A={search_first:02X} "
            f"reads={cpu.mem[0x7303]} mapped={bytes(cpu.mem[0x7300:0x7303]).hex()} "
            f"buffer={bytes(cpu.mem[0xEC80:0xEC8D]).hex()} "
            f"live={cpu.mem[state['UB_ITLIVE']]} rec={cpu.mem[state['UB_ITREC']]} "
            f"cache={cpu.mem[state['UBS_COK']]} dph={cpu.word(state['UB_DPH']):04X}")
    dma = cpu.word(symbols()["UB_DMA"])
    require(bytes(cpu.mem[dma:dma + 12]) == bytes((7,)) + b"ONE     COM",
            "Search First did not copy the containing directory record")
    reads = cpu.mem[0x7303]
    require(call(18) == 1, "Search Next did not retain slot continuation")
    require(cpu.mem[0x7303] == reads,
            "Search Next reread an already cached directory sector")

    print(f"unified BDOS U01-U06 foundation passed ({len(image)} bytes)")
    print("disk state, FCB drive view, shared iterator, and one-sector cache passed")


if __name__ == "__main__":
    main()
