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
        cpu.run(BASE, limit=50000)
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
    require(call(16) == 0xFF, "unfinished file call was not rejected")

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
    cpu.mem[FIXTURE + 13:FIXTURE + 16] = bytes((0x55, 2, 0x22))
    cpu.mem[FIXTURE + 16:FIXTURE + 32] = bytes(range(1, 17))
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

    # Open uses the same iterator in exact-name mode, filters EX/S2 with the
    # live DPB's EXM, and activates bytes 1..31 without changing drive or CR.
    cpu.mem[FCB:FCB + 33] = bytes((0xA5,)) * 33
    cpu.mem[FCB] = 0
    cpu.mem[FCB + 1:FCB + 12] = b"ONE     COM"
    cpu.mem[FCB + 12] = 0
    cpu.mem[FCB + 14] = 2
    cpu.mem[FCB + 32] = 9
    require(call(15, FCB) == 0, "Open missed an exact existing extent")
    require(cpu.mem[FCB] == 0 and cpu.mem[FCB + 32] == 9,
            "Open changed the caller's drive byte or current record")
    require(cpu.mem[FCB + 1:FCB + 32] == cpu.mem[FIXTURE + 1:FIXTURE + 32],
            "Open did not activate directory bytes 1..31")

    # Make is the first mutation client. Replace only the BIOS WRITE vector
    # with a success/count stub; mapping and cache selection remain real.
    cpu.mem[BIOS_BASE + 14 * 3:BIOS_BASE + 14 * 3 + 3] = bytes((0xC3, 0x00, 0x74))
    cpu.mem[0x7400:0x7409] = bytes((
        0x3A, 0x04, 0x73, 0x3C, 0x32, 0x04, 0x73, 0xAF, 0xC9))
    cpu.mem[FCB:FCB + 36] = bytes(36)
    cpu.mem[FCB + 1:FCB + 12] = b"NEW     COM"
    made = call(22, FCB)
    require(made == 2,
            f"Make did not select the first free slot: A={made:02X} writes={cpu.mem[0x7304]} "
            f"mode={cpu.mem[state['UB_ITMODE']]} rec={cpu.mem[state['UB_ITREC']]} "
            f"slot={cpu.mem[state['UB_ITSLOT']]} dirty={cpu.mem[state['UB_DIRTY']]}")
    require(cpu.mem[0x7304] == 1, "Make did not flush exactly one directory sector")
    require(bytes(cpu.mem[0xEC80 + 64:0xEC80 + 76]) ==
            bytes((7,)) + b"NEW     COM",
            "Make did not initialize the cached directory entry")
    require(call(22, FCB) == 0xFF and cpu.mem[0x7304] == 1,
            "Make accepted a duplicate or wrote during duplicate rejection")
    cpu.mem[FCB + 1:FCB + 12] = b"RO      COM"
    call(28)
    require(call(22, FCB) == 0xFF and cpu.mem[0x7304] == 1,
            "Make mutated a software write-protected drive")

    # Constrain the fixture to one directory record and verify Delete's
    # preflight/mutation passes through the same cache and iterator.
    require(call(37, 2) == 0, "could not clear drive-B write protection")
    dpb = 0xC9E8
    cpu.mem[dpb + 7] = 3          # DRM=3: four entries, one directory record
    cpu.mem[FCB:FCB + 36] = bytes(36)
    cpu.mem[FCB + 1:FCB + 12] = b"ONE     COM"
    writes = cpu.mem[0x7304]
    require(call(19, FCB) == 0, "Delete missed an exact existing file")
    require(cpu.mem[0xEC80] == 0xE5 and cpu.mem[0xEC80 + 32] == 7,
            "Delete changed the wrong cached directory entries")
    require(cpu.mem[0x7304] == writes + 1,
            "Delete did not flush its dirty directory sector exactly once")
    require(call(19, FCB) == 0xFF,
            "Delete reported success when no matching entry remained")

    # A read-only extent found during preflight must prevent every mutation.
    cpu.mem[0xEC80] = 7
    cpu.mem[0xEC80 + 9] |= 0x80
    cpu.mem[FCB + 1:FCB + 12] = b"???????????"
    snapshot = bytes(cpu.mem[0xEC80:0xED00])
    writes = cpu.mem[0x7304]
    require(call(19, FCB) == 0xFF,
            "Delete accepted a set containing a read-only extent")
    require(bytes(cpu.mem[0xEC80:0xED00]) == snapshot and
            cpu.mem[0x7304] == writes,
            "Delete partially mutated a set rejected during preflight")

    # Rename changes all matching source extents through the same two-pass
    # path, retaining the directory attribute bits on each name/type byte.
    cpu.mem[0xEC80 + 9] &= 0x7F
    cpu.mem[0xEC80 + 33] |= 0x80
    cpu.mem[FCB:FCB + 36] = bytes(36)
    cpu.mem[FCB + 1:FCB + 12] = b"TWO     COM"
    cpu.mem[FCB + 17:FCB + 28] = b"SECOND  COM"
    writes = cpu.mem[0x7304]
    require(call(23, FCB) == 0, "Rename missed an exact existing source")
    require(bytes(value & 0x7F for value in cpu.mem[0xEC80 + 33:0xEC80 + 44]) ==
            b"SECOND  COM" and cpu.mem[0xEC80 + 33] & 0x80,
            "Rename did not replace the name while preserving attributes")
    require(cpu.mem[0x7304] == writes + 1,
            "Rename did not flush its dirty directory sector exactly once")

    cpu.mem[FCB + 1:FCB + 12] = b"SECOND  COM"
    cpu.mem[FCB + 17:FCB + 28] = b"ONE     COM"
    snapshot = bytes(cpu.mem[0xEC80:0xED00])
    writes = cpu.mem[0x7304]
    require(call(23, FCB) == 0xFF,
            "Rename accepted an already-existing target")
    require(bytes(cpu.mem[0xEC80:0xED00]) == snapshot and
            cpu.mem[0x7304] == writes,
            "Rename mutated the directory while rejecting its target")

    # Set Attributes copies only high bits from the FCB name/type fields.
    cpu.mem[FCB:FCB + 36] = bytes(36)
    cpu.mem[FCB + 1:FCB + 12] = b"SECOND  COM"
    cpu.mem[FCB + 9] |= 0x80    # T1 read-only on; first-name high bit off
    tail = bytes(cpu.mem[0xEC80 + 44:0xEC80 + 64])
    writes = cpu.mem[0x7304]
    require(call(30, FCB) == 0, "Set Attributes missed an existing file")
    require(not cpu.mem[0xEC80 + 33] & 0x80 and
            cpu.mem[0xEC80 + 41] & 0x80,
            "Set Attributes did not copy the requested high bits")
    require(bytes(cpu.mem[0xEC80 + 44:0xEC80 + 64]) == tail,
            "Set Attributes changed extent or allocation fields")
    require(cpu.mem[0x7304] == writes + 1,
            "Set Attributes did not flush exactly one dirty sector")
    cpu.mem[FCB + 1:FCB + 12] = b"ABSENT  COM"
    writes = cpu.mem[0x7304]
    require(call(30, FCB) == 0xFF and cpu.mem[0x7304] == writes,
            "Set Attributes wrote while reporting no matching file")

    print(f"unified BDOS U01-U06 foundation passed ({len(image)} bytes)")
    print("disk state, FCB drive view, shared iterator, and one-sector cache passed")


if __name__ == "__main__":
    main()
