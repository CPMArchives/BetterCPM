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
TEST_DPH = 0xD000
TEST_DPB = 0xD040


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
    workspaces = ((0xD050, 0xD070), (0xD0A2, 0xD0C2),
                  (0xD0F4, 0xD114), (0xD146, 0xD166))
    install_drive_tables(cpu, TEST_DPH, TEST_DPB, workspaces)
    # The active BIOS still carries provisional descriptor literals directly
    # after the old BDOS. Relocate those four SELDSK return constants only in
    # this standalone replacement test until generated system layout lands.
    select_impl = cpu.word(BIOS_BASE + 9 * 3 + 1)
    for offset in range(48):
        address = select_impl + offset
        value = cpu.word(address)
        if value in (0xC9A8, 0xC9B8, 0xC9C8, 0xC9D8):
            cpu.setword(address, TEST_DPH + (value - 0xC9A8))
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
    state = symbols()

    def call(function: int, parameter: int = 0) -> int:
        cpu.c, cpu.de = function, parameter
        cpu.run(BASE, limit=50000)
        require(cpu.sp == initial_sp, f"function {function} unbalanced stack")
        return cpu.a

    # U10 character-I/O conformance.  Patch only the platform leaves beneath
    # the BIOS vectors, exactly as the production BDOS test does.
    const_impl = cpu.word(BIOS_BASE + 2 * 3 + 1)
    platform_const = cpu.word(const_impl + 1)
    conin_impl = cpu.word(BIOS_BASE + 3 * 3 + 1)
    platform_conin = cpu.word(conin_impl + 1)
    conout_impl = cpu.word(BIOS_BASE + 4 * 3 + 1)
    platform_conout = cpu.word(conout_impl + 1)
    cpu.mem[platform_const:platform_const + 2] = bytes((0xAF, 0xC9))
    require(call(11) == 0, "function 11 reported a false key")
    cpu.mem[platform_const:platform_const + 3] = bytes((0x3E, 1, 0xC9))
    require(call(11) == 0xFF, "function 11 did not normalize ready to FFh")
    cpu.mem[platform_conin:platform_conin + 3] = bytes((0x3E, 0xC1, 0xC9))
    require(call(6, 0xFF) == 0x41, "function 6 input retained parity")
    cpu.mem[platform_conout:platform_conout + 5] = bytes(
        (0x79, 0x32, 0x00, 0x70, 0xC9))
    cpu.mem[0x7000] = 0
    require(call(6, 0xB2) == 0 and cpu.mem[0x7000] == 0xB2,
            "function 6 output changed its byte")
    cpu.mem[platform_const:platform_const + 2] = bytes((0xAF, 0xC9))
    cpu.mem[state["UB_COLUMN"]] = 0
    require(call(2, ord("A")) == 0 and cpu.mem[0x7000] == ord("A") and
            cpu.mem[state["UB_COLUMN"]] == 1,
            "function 2 did not emit/count a graphic")
    call(2, 9)
    require(cpu.mem[0x7000] == ord(" ") and cpu.mem[state["UB_COLUMN"]] == 8,
            "function 2 did not expand tab")
    cpu.mem[0x7050:0x7055] = b"A\tB$Z"
    cpu.mem[state["UB_COLUMN"]] = 0
    require(call(9, 0x7050) == 0 and cpu.mem[0x7000] == ord("B") and
            cpu.mem[state["UB_COLUMN"]] == 9,
            "function 9 did not use cooked output")
    cpu.mem[3] = 0xA5
    require(call(7) == 0xA5, "function 7 did not return IOBYTE")
    require(call(8, 0x5A) == 0 and cpu.mem[3] == 0x5A,
            "function 8 did not set IOBYTE")

    # Scripted BIOS input verifies the fixed BDOS's bounded counted-line
    # buffer. Rich cursor/history editing intentionally belongs to the CCP.
    cpu.mem[0x7060:0x706A] = bytes((
        0x2A, 0x70, 0x70, 0x7E, 0x23, 0x22, 0x70, 0x70, 0xC9, 0))
    cpu.mem[BIOS_BASE + 9:BIOS_BASE + 12] = bytes((0xC3, 0x60, 0x70))

    def read_line(script: bytes, maximum: int) -> bytes:
        cpu.mem[0x8000:0x8000 + len(script)] = script
        cpu.setword(0x7070, 0x8000)
        cpu.mem[0x7200] = maximum
        call(10, 0x7200)
        return bytes(cpu.mem[0x7202:0x7202 + cpu.mem[0x7201]])

    require(read_line(b"AB\x08C\r", 8) == b"AC",
            "function 10 backspace failed")
    require(read_line(b"AB\x15C\r", 8) == b"C",
            "function 10 Ctrl-U failed")
    require(read_line(b"A\x05B\x12C\r", 8) == b"ABC",
            "function 10 Ctrl-E/Ctrl-R retention failed")
    require(read_line(b"AB\x18C\n", 8) == b"C",
            "function 10 Ctrl-X deletion failed")
    require(read_line(b"A\x03B\r", 8) == b"A\x03B",
            "function 10 noninitial Ctrl-C retention failed")
    cpu.mem[state["UB_LISTE"]] = 0
    require(read_line(b"\x10A\r", 8) == b"A" and
            cpu.mem[state["UB_LISTE"]] == 0xFF,
            "function 10 Ctrl-P printer toggle failed")
    require(read_line(b"QZ", 1) == b"Q" and cpu.word(0x7070) == 0x8001,
            "function 10 consumed beyond a full buffer")
    cpu.mem[BIOS_BASE + 9:BIOS_BASE + 12] = bytes(
        (0xC3, conin_impl & 0xFF, conin_impl >> 8))

    require(call(12) == 0x22 and cpu.hl == 0x22,
            "function 12 did not return CP/M 2.2")
    reset_result = call(13)
    require(reset_result == 0,
            f"disk reset failed: A={reset_result:02X} "
            f"valid={cpu.mem[state['UB_VALID']]} pos={cpu.mem[state['UB_ITPOS']]} "
            f"reads={cpu.mem[0x7303]} cache={cpu.mem[state['UBS_COK']]}")
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
    cpu.mem[FIXTURE + 45:FIXTURE + 64] = bytes(19)
    cpu.mem[FIXTURE + 13:FIXTURE + 16] = bytes((0x55, 2, 0x22))
    cpu.mem[FIXTURE + 16:FIXTURE + 32] = bytes(
        value for block in range(1, 9) for value in (block, 0))
    cpu.mem[FCB:FCB + 36] = bytes(36)
    cpu.mem[FCB] = 0
    cpu.mem[FCB + 1:FCB + 12] = b"???????????"
    call(32, 7)
    cpu.mem[0x7303] = 0
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
            f"pos={cpu.mem[state['UB_ITPOS']]} "
            f"cache={cpu.mem[state['UBS_COK']]} dph={cpu.word(state['UB_DPH']):04X}")
    dma = cpu.word(symbols()["UB_DMA"])
    require(bytes(cpu.mem[dma:dma + 12]) == bytes((7,)) + b"ONE     COM",
            "Search First did not copy the containing directory record")
    reads = cpu.mem[0x7303]
    require(call(18) == 1, "Search Next did not retain slot continuation")
    require(cpu.mem[0x7303] == reads,
            "Search Next reread an already cached directory sector")

    # Drive-B login rebuilt its ALV through the iterator: AL0/AL1 reserve the
    # directory blocks and the live 16-bit allocation entries add blocks 1..8.
    call(27)
    alv = cpu.hl
    require(bytes(cpu.mem[alv:alv + 2]) == bytes((0xFF, 0x80)),
            f"U07 did not reconstruct reserved and file-owned allocation bits: "
            f"{bytes(cpu.mem[alv:alv + 2]).hex()} at {alv:04X}")
    cpu.de = 395                 # one beyond this fixture's DSM=394
    cpu.run(state["UB_ALMARK"])
    require(cpu.a != 0, "U07 accepted an allocation block beyond DSM")
    cpu.run(state["UB_ALFREE"])
    require(cpu.a == 0 and cpu.de == 9,
            "U07 did not find the first free allocation block")
    cpu.run(state["UB_ALMARK"])
    require(cpu.a == 0, "U07 could not reserve the selected free block")
    cpu.run(state["UB_ALFREE"])
    require(cpu.a == 0 and cpu.de == 10,
            "U07 returned a block that had just been reserved")
    cpu.run(state["UB_ALLOGIN"], limit=50000)
    require(cpu.a == 0, "U07 could not reconstruct allocation ownership")
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
    activated = bytearray(cpu.mem[FIXTURE + 1:FIXTURE + 32])
    activated[13] |= 0x80
    require(cpu.mem[FCB + 1:FCB + 32] == activated,
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
            f"mode={cpu.mem[state['UB_ITMODE']]} pos={cpu.mem[state['UB_ITPOS']]} "
            f"dirty={cpu.mem[state['UB_DIRTY']]}")
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
    dpb = TEST_DPB
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

    # Compute File Size reduces multiple exact-name extents to the largest
    # exclusive 128-byte record number and stores it in R0..R2.
    cpu.mem[0xEC80 + 32 + 12] = 3
    cpu.mem[0xEC80 + 32 + 14] = 1
    cpu.mem[0xEC80 + 32 + 15] = 5
    cpu.mem[0xEC80 + 64] = 7
    cpu.mem[0xEC80 + 65:0xEC80 + 76] = b"SECOND  COM"
    cpu.mem[0xEC80 + 64 + 12] = 4
    cpu.mem[0xEC80 + 64 + 14] = 1
    cpu.mem[0xEC80 + 64 + 15] = 10
    cpu.mem[FCB:FCB + 36] = bytes(36)
    cpu.mem[FCB + 1:FCB + 12] = b"SECOND  COM"
    require(call(35, FCB) == 0, "Compute File Size missed existing extents")
    require(bytes(cpu.mem[FCB + 33:FCB + 36]) == bytes((0x0A, 0x12, 0x00)),
            "Compute File Size did not select the largest logical end record")
    cpu.mem[FCB + 1:FCB + 12] = b"ABSENT  COM"
    require(call(35, FCB) == 0xFF,
            "Compute File Size reported success for a missing file")

    # Function 36 must use the identical S2:EX:record conversion, taking CR
    # rather than a directory entry's RC as its low record component.
    cpu.mem[FCB:FCB + 36] = bytes(36)
    cpu.mem[FCB + 12] = 4
    cpu.mem[FCB + 14] = 1
    cpu.mem[FCB + 32] = 10
    require(call(36, FCB) == 0 and
            bytes(cpu.mem[FCB + 33:FCB + 36]) == bytes((0x0A, 0x12, 0x00)),
            "Set Random Record diverged from shared extent arithmetic")

    # Close uses a non-copying canonical lookup and commits a dirty FCB's
    # extent state and allocator-produced map. Conflicting owned blocks fail
    # without changing either the caller or directory.
    cpu.mem[0xEC80 + 41] &= 0x7F
    cpu.mem[FCB:FCB + 36] = bytes(36)
    cpu.mem[FCB + 1:FCB + 12] = b"SECOND  COM"
    cpu.mem[FCB + 12] = 3
    cpu.mem[FCB + 14] = 1
    cpu.mem[FCB + 15] = 6
    cpu.mem[FCB + 32] = 9
    writes = cpu.mem[0x7304]
    require(call(16, FCB) == 1, "Close missed the canonical extent")
    require(cpu.mem[0xEC80 + 32 + 15] == 6 and cpu.mem[FCB + 15] == 6,
            "Close did not commit and preserve the caller's RC")
    require(cpu.mem[0x7304] == writes + 1,
            "Close did not flush one dirty directory sector")
    cpu.mem[0xEC80 + 32 + 16] = 8
    cpu.mem[FCB + 14] &= 0x7F
    cpu.mem[FCB + 15] = 7
    cpu.mem[FCB + 16] = 9
    writes = cpu.mem[0x7304]
    require(call(16, FCB) == 1,
            "base Close rejected an FCB requiring optional SAFEFS validation")
    require(cpu.mem[0xEC80 + 32 + 15] == 7 and
            cpu.mem[0xEC80 + 32 + 16] == 9 and
            cpu.mem[0x7304] == writes + 1,
            "base Close did not publish the caller's active FCB")
    cpu.mem[0xEC80 + 32 + 16] = 8
    cpu.run(state["UB_ALLOGIN"], limit=50000)

    # Sequential Read maps CR through EXM, BSH/BLM, the 16-bit allocation map,
    # SPT/OFF and BIOS translation, transfers one record, then advances CR.
    for quarter, marker in enumerate((0x10, 0x20, 0x30, 0x40)):
        cpu.mem[FIXTURE + quarter * 128:FIXTURE + (quarter + 1) * 128] = \
            bytes((marker,)) * 128
    cpu.mem[FCB:FCB + 36] = bytes(36)
    cpu.mem[FCB + 12] = 0
    cpu.mem[FCB + 15] = 2
    cpu.mem[FCB + 16:FCB + 18] = bytes((1, 0))
    cpu.mem[FCB + 32] = 1
    dma = 0x7800
    call(26, dma)
    require(call(20, FCB) == 0 and cpu.mem[FCB + 32] == 2,
            "Sequential Read failed or did not advance CR")
    require(bytes(cpu.mem[dma:dma + 128]) == bytes((0x20,)) * 128,
            "Sequential Read mapped or transferred the wrong logical record")
    require(call(20, FCB) == 1,
            "Sequential Read did not report EOF when CR reached RC")

    cpu.mem[0xEC80:0xEC80 + 32] = bytes(32)
    cpu.mem[0xEC80:0xEC80 + 12] = bytes((7,)) + b"ONE     COM"
    cpu.mem[0xEC80 + 15] = 2
    cpu.mem[0xEC80 + 16:0xEC80 + 18] = bytes((1, 0))
    cpu.mem[FCB:FCB + 36] = bytes(36)
    cpu.mem[FCB + 1:FCB + 12] = b"ONE     COM"
    cpu.mem[FCB + 33:FCB + 36] = bytes((1, 0, 0))
    cpu.mem[dma:dma + 128] = bytes(128)
    random_result = call(33, FCB)
    require(random_result == 0,
            f"Random Read failed to activate and read the decoded extent: {random_result:02X} "
            f"EX={cpu.mem[FCB+12]} S2={cpu.mem[FCB+14]} RC={cpu.mem[FCB+15]} "
            f"CR={cpu.mem[FCB+32]} AL={bytes(cpu.mem[FCB+16:FCB+20]).hex()}")
    require(cpu.mem[FCB + 12] == 0 and cpu.mem[FCB + 14] == 0x80 and
            cpu.mem[FCB + 32] == 2,
            "Random Read decoded R0..R2 or advanced CR incorrectly")
    require(bytes(cpu.mem[dma:dma + 128]) == bytes((0x20,)) * 128,
            "Random Read did not reuse the sequential record mapper")
    cpu.mem[FCB + 35] = 4
    require(call(33, FCB) == 0xFF,
            "Random Read accepted an out-of-range R2 value")

    # Sequential Write uses the same record mapper, allocating only when its
    # current map element is empty.  It advances CR and grows RC in the FCB;
    # Close is responsible for publishing those authenticated changes.
    cpu.mem[0xEC80 + 64:0xEC80 + 96] = bytes(32)
    cpu.mem[0xEC80 + 64:0xEC80 + 76] = bytes((7,)) + b"NEW     COM"
    cpu.mem[FCB:FCB + 36] = bytes(36)
    cpu.mem[FCB + 1:FCB + 12] = b"NEW     COM"
    cpu.mem[dma:dma + 128] = bytes((0x5A,)) * 128
    writes = cpu.mem[0x7304]
    require(call(21, FCB) == 0,
            "Sequential Write could not allocate and map its first record")
    require(cpu.word(FCB + 16) == 9 and cpu.mem[FCB + 32] == 1 and
            cpu.mem[FCB + 15] == 1,
            "Sequential Write did not install its allocation or advance CR/RC")
    require(cpu.mem[0x7304] == writes + 1,
            "Sequential Write did not issue exactly one physical write")
    writes = cpu.mem[0x7304]
    require(call(21, FCB) == 0 and cpu.word(FCB + 16) == 9 and
            cpu.mem[0x7304] == writes + 1,
            "Sequential Write reallocated an existing block")
    writes = cpu.mem[0x7304]
    close_result = call(16, FCB)
    require(close_result == 2 and cpu.word(0xEC80 + 64 + 16) == 9 and
            cpu.mem[0xEC80 + 64 + 15] == 2,
            f"Close did not publish allocator-produced map and record state: "
            f"A={close_result:02X} dir={bytes(cpu.mem[0xEC80+64:0xEC80+96]).hex()}")
    require(cpu.mem[0x7304] == writes + 1 and cpu.mem[FCB + 14] & 0x80,
            "Close did not flush once and mark the active FCB clean")

    # Random Write shares both the random-record decoder and Sequential
    # Write's transfer core.  Activating record one of the existing extent
    # must reuse block one rather than allocate another block.
    cpu.mem[FCB:FCB + 36] = bytes(36)
    cpu.mem[FCB + 1:FCB + 12] = b"ONE     COM"
    cpu.mem[FCB + 33:FCB + 36] = bytes((1, 0, 0))
    writes = cpu.mem[0x7304]
    require(call(34, FCB) == 0 and cpu.word(FCB + 16) == 1,
            "Random Write did not activate and reuse the decoded extent")
    require(cpu.mem[FCB + 12] == 0 and cpu.mem[FCB + 14] == 0 and
            cpu.mem[FCB + 32] == 2 and cpu.mem[FCB + 15] == 2,
            "Random Write diverged from shared decode/write bookkeeping")
    require(cpu.mem[0x7304] == writes + 1,
            "Random Write did not issue exactly one physical write")

    # A random write to a missing extent creates it through the same free-entry
    # service as Make. A sequential write at CR=128 then closes that dirty
    # extent, advances, creates the next extent, and continues there.
    cpu.mem[0xEC80 + 32] = 0xE5
    cpu.mem[FCB:FCB + 36] = bytes(36)
    cpu.mem[FCB + 1:FCB + 12] = b"NEW     COM"
    cpu.mem[FCB + 33:FCB + 36] = bytes((128, 0, 0))
    writes = cpu.mem[0x7304]
    require(call(34, FCB) == 0 and cpu.mem[FCB + 12] == 1 and
            cpu.mem[FCB + 32] == 1,
            "Random Write did not create and use a missing extent")
    require(cpu.mem[0x7304] == writes + 2,
            "missing-extent Random Write did not create then transfer once")
    extent1 = [offset for offset in range(0, 128, 32)
               if bytes(cpu.mem[0xEC80 + offset + 1:0xEC80 + offset + 12]) ==
               b"NEW     COM" and cpu.mem[0xEC80 + offset + 12] == 1]
    require(len(extent1) == 1, "Random Write did not publish extent one")
    cpu.mem[FCB + 32] = 128
    writes = cpu.mem[0x7304]
    rollover_result = call(21, FCB)
    require(rollover_result == 0 and cpu.mem[FCB + 12] == 2 and
            cpu.mem[FCB + 32] == 1,
            f"Sequential Write did not roll over into a new extent: "
            f"A={rollover_result:02X} EX={cpu.mem[FCB+12]} "
            f"S2={cpu.mem[FCB+14]:02X} CR={cpu.mem[FCB+32]} RC={cpu.mem[FCB+15]} "
            f"RB={cpu.mem[state['UB_RBNO']]} AL={bytes(cpu.mem[FCB+16:FCB+24]).hex()} "
            f"AV={bytes(cpu.mem[alv:alv+8]).hex()}")
    require(cpu.mem[0x7304] == writes + 3,
            "extent rollover did not close, create, and transfer exactly once")
    extent2 = [offset for offset in range(0, 128, 32)
               if bytes(cpu.mem[0xEC80 + offset + 1:0xEC80 + offset + 12]) ==
               b"NEW     COM" and cpu.mem[0xEC80 + offset + 12] == 2]
    require(len(extent2) == 1, "Sequential Write did not publish extent two")

    # Function 40 uses the same Random Write path, but a newly allocated map
    # element first receives a complete zero-filled block.  This fixture has
    # BLM=15, so the initializer performs 16 writes plus the requested one.
    cpu.mem[FCB:FCB + 36] = bytes(36)
    cpu.mem[FCB + 1:FCB + 12] = b"ONE     COM"
    cpu.mem[FCB + 33:FCB + 36] = bytes((16, 0, 0))
    writes = cpu.mem[0x7304]
    zero_result = call(40, FCB)
    require(zero_result == 0 and cpu.word(FCB + 18) == 12,
            f"zero-fill Random Write did not allocate its target block: "
            f"A={zero_result:02X} AL={bytes(cpu.mem[FCB+16:FCB+22]).hex()} "
            f"CR={cpu.mem[FCB+32]} RC={cpu.mem[FCB+15]} writes={cpu.mem[0x7304]-writes}")
    require(cpu.mem[FCB + 32] == 17 and cpu.mem[FCB + 15] == 17,
            "zero-fill Random Write did not restore and advance its target record")
    require(cpu.mem[0x7304] == writes + 17,
            "zero-fill Random Write did not initialize exactly one full block")
    require(cpu.mem[state["UBS_COK"]] == 0,
            "zero-fill scratch use left the directory cache falsely valid")
    call(28)
    writes = cpu.mem[0x7304]
    require(call(21, FCB) == 0xFF and cpu.mem[0x7304] == writes,
            "Sequential Write ignored software write protection")

    print(f"unified BDOS U01-U09 foundation passed ({len(image)} bytes)")
    print("disk, directory, allocation, extent, and record-transfer mapping passed")


if __name__ == "__main__":
    main()
