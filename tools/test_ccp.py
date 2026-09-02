#!/usr/bin/env python3
"""Execute focused CCP parsing contracts from the assembled resident binary."""
from __future__ import annotations

import re
import struct
from pathlib import Path

from test_bios import Z80, require

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "build/ccp/ccp.bin"
MODULE = ROOT / "build/ccp/ccp.rlm"
LISTING = ROOT / "build/ccp/ccp.lst"
LINK_BASE = 0xBB00
# Keep the focused image below both its C100h BDOS stand-in and the BE00h
# persistent-history fixture as the relocatable CCP grows during development.
BASE = 0xB300
CALLER = 0x7000


def symbol(name: str) -> int:
    matches = re.findall(rf"^([0-9a-f]{{4}})\s+.*\b{name}:?\s*$",
                         LISTING.read_text(encoding="ascii"),
                         re.MULTILINE | re.IGNORECASE)
    require(matches, f"CCP listing lacks {name}")
    linked = int(matches[-1], 16)
    # The CCP is relocatable and has legitimately grown across C000h at its
    # arbitrary link origin. Focused tests must use a real safe runtime base.
    return (linked + BASE - LINK_BASE) & 0xFFFF


def cpu() -> Z80:
    machine = Z80(b"")
    module = MODULE.read_bytes()
    _magic, _version, _header_sectors, link, size, _allocation, _entry, count = (
        struct.unpack_from("<4sBBHHHHH", module))
    data = bytearray(module[512:512 + size])
    delta = BASE - link
    for index in range(count):
        offset = struct.unpack_from("<H", module, 16 + index * 2)[0]
        value = int.from_bytes(data[offset:offset + 2], "little")
        data[offset:offset + 2] = ((value + delta) & 0xFFFF).to_bytes(2, "little")
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
    for command, drive, expected in (
        (b"HELLO WORLD", 0, b"HELLO   COM"),
        (b"MINRET22 X", 0, b"MINRET22COM"),
        (b"A:CPX LIST", 1, b"CPX     COM"),
    ):
        machine = cpu()
        machine.mem[0xC100:0xC103] = bytes((0x3E, 0xFF, 0xC9))
        machine.mem[symbol("CCP_COUNT")] = len(command)
        start = symbol("CCP_DATA")
        machine.mem[start:start + len(command)] = command
        call(machine, symbol("CCP_LOAD"))
        fcb = symbol("CCP_FCB")
        require(machine.mem[fcb] == drive and
                bytes(machine.mem[fcb + 1:fcb + 12]) == expected,
                f"lookup FCB is wrong for {command!r}")

    # A combined DU prefix temporarily selects its user for the file lookup,
    # encodes its drive in the loader FCB, and restores the caller's user even
    # when Open reports that the transient is absent.
    machine = cpu()
    du_bdos = bytes((
        0x79, 0xFE, 32, 0x28, 0x03, 0x3E, 0xFF, 0xC9,
        0x7B, 0xFE, 0xFF, 0x28, 0x05,
        0x32, 0x01, 0x75, 0xAF, 0xC9,
        0x3A, 0x01, 0x75, 0xC9,
    ))
    machine.mem[0xC100:0xC100 + len(du_bdos)] = du_bdos
    machine.mem[0x7501] = 7
    command = b"A0:CPX LIST"
    machine.mem[symbol("CCP_COUNT")] = len(command)
    start = symbol("CCP_DATA")
    machine.mem[start:start + len(command)] = command
    call(machine, symbol("CCP_LOAD"))
    fcb = symbol("CCP_FCB")
    require(machine.mem[fcb] == 1 and
            bytes(machine.mem[fcb + 1:fcb + 12]) == b"CPX     COM" and
            machine.mem[0x7501] == 7,
            "combined DU command lookup did not encode drive and restore user")

    # History belongs to protected persistent DATA, not the reloadable CCP.
    # Store several complete variable-length commands, then retrieve both an
    # interior and newest record through the CCP's public history helpers.
    machine = cpu()
    for command in (b"DIR", b"TYPE README.TXT", b"B:", b"HELLO WORLD"):
        machine.mem[symbol("CCP_COUNT")] = len(command)
        start = symbol("CCP_DATA")
        machine.mem[start:start + len(command)] = command
        call(machine, symbol("CCP_HADD"))
    require(bytes(machine.mem[0xBE00:0xBE04]) == b"BH\x01\x04",
            "persistent history header or record count is wrong")
    for index, expected in ((1, b"TYPE README.TXT"), (3, b"HELLO WORLD")):
        machine.a = index
        call(machine, symbol("CCP_HGET"))
        count = machine.mem[symbol("CCP_COUNT")]
        require(bytes(machine.mem[symbol("CCP_DATA"):symbol("CCP_DATA") + count]) == expected,
                f"persistent history retrieval failed for record {index}")

    # Invoke editing actions with an Enter-returning direct-console stub. Each
    # action flows through the real redraw/finalization path before returning.
    editor_bdos = bytes((
        0x79, 0xFE, 6, 0x28, 0x02, 0xAF, 0xC9,
        0x3A, 0x00, 0x75, 0xC9,
    ))
    for routine, text, cursor, expected, expected_cursor in (
        ("CCP_EDWLEFT", b"ONE TWO", 7, b"ONE TWO", 4),
        ("CCP_EDWRIGHT", b"ONE TWO", 0, b"ONE TWO", 4),
        ("CCP_EDDEL", b"ABC", 1, b"AC", 1),
        ("CCP_EDBS", b"ABC", 2, b"AC", 1),
        ("CCP_EDDWORD", b"ONE  TWO X", 0, b"TWO X", 0),
        ("CCP_EDNEW", b"KEEP", 2, b"KEEP", 2),
        ("CCP_EDCLEAR", b"DISCARD", 4, b"", 0),
    ):
        machine = cpu()
        machine.mem[0xC100:0xC100 + len(editor_bdos)] = editor_bdos
        machine.mem[0x7500] = 13
        machine.mem[symbol("CCP_COUNT")] = len(text)
        machine.mem[symbol("CCP_EDCUR")] = cursor
        start = symbol("CCP_DATA")
        machine.mem[start:start + len(text)] = text
        call(machine, symbol(routine))
        count = machine.mem[symbol("CCP_COUNT")]
        require(bytes(machine.mem[start:start + count]) == expected and
                machine.mem[symbol("CCP_EDCUR")] == expected_cursor,
                f"editor action {routine} produced the wrong line or cursor")

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

    # A bare drive operand is how tools such as Montezuma Micro MDIR request
    # another disk. A file-qualified prefix uses the same CP/M encoding.
    for text, expected in (
        (b"B:", b"\x02           "),
        (b"D:FILE.DAT", b"\x04FILE    DAT"),
        (b"P:LAST.BIN", b"\x10LAST    BIN"),
        (b"B:*.COM", b"\x02????????COM"),
        (b"AB*.D*", b"\x00AB??????D??"),
        (b"Q?.BIN", b"\x00Q?      BIN"),
    ):
        machine = cpu()
        source = 0x7200
        machine.mem[source:source + len(text)] = text
        machine.hl, machine.b, machine.de = source, len(text), 0x005C
        call(machine, symbol("CCP_PFCB"))
        require(bytes(machine.mem[0x005C:0x0068]) == expected,
                f"drive-qualified default FCB is wrong for {text!r}")

    # Model 4 LF preserves the current column. DIR must issue CR/LF or its
    # one-name-per-row display becomes a diagonal staircase across the screen.
    dir_nl = symbol("CCP_DIRNL")
    require(bytes(machine.mem[dir_nl:dir_nl + 3]) == b"\r\n$",
            "resident DIR line separator is not CP/M CR/LF")

    # The initial image has an empty CPX chain. Install two synthetic headers:
    # the first declines and the second claims the command. This verifies the
    # public ordering and carry contract without making a test CPX resident.
    machine = cpu()
    head, second = 0xBFC0, 0xBFC4
    decline, accept = 0x7300, 0x7310
    machine.mem[0xC086:0xC088] = head.to_bytes(2, "little")
    machine.mem[head:head + 4] = (second.to_bytes(2, "little")
                                  + decline.to_bytes(2, "little"))
    machine.mem[second:second + 4] = (bytes(2)
                                      + accept.to_bytes(2, "little"))
    machine.mem[decline:decline + 2] = bytes((0xB7, 0xC9))  # OR A; RET
    machine.mem[accept:accept + 5] = bytes((0x3E, 0xA5, 0x32, 0x00, 0x74))
    machine.mem[accept + 5:accept + 7] = bytes((0x37, 0xC9))  # SCF; RET
    command = b"IF EXIST TEST"
    machine.mem[symbol("CCP_COUNT")] = len(command)
    data = symbol("CCP_DATA")
    machine.mem[data:data + len(command)] = command
    call(machine, symbol("CPX_DISPATCH"))
    require(machine.mem[0x7400] == 0xA5,
            "CPX chain did not pass a declined command to its successor")

    # Navigation syntax is owned by the CCP but its state is owned by BDOS.
    # This tiny BDOS stand-in exposes four physical drives and records current
    # drive/user state, allowing the three public forms to be checked without
    # involving a disk image.
    nav_bdos = bytes((
        0x79,                   # LD A,C
        0xFE, 14, 0x28, 0x06,  # CP 14 / JR Z,select
        0xFE, 32, 0x28, 0x0F,  # CP 32 / JR Z,user
        0xAF, 0xC9,             # XOR A / RET
        0x7B, 0xFE, 4,          # select: LD A,E / CP 4
        0x30, 0x05,             # JR NC,bad
        0x32, 0x00, 0x75,       # LD (7500h),A
        0xAF, 0xC9,             # XOR A / RET
        0x3E, 0xFF, 0xC9,       # bad: LD A,FFh / RET
        0x7B, 0xFE, 0xFF,       # user: LD A,E / CP FFh
        0x28, 0x05,             # JR Z,get-user
        0x32, 0x01, 0x75,       # LD (7501h),A
        0xAF, 0xC9,             # XOR A / RET
        0x3A, 0x01, 0x75, 0xC9  # get-user: LD A,(7501h) / RET
    ))
    machine = cpu()
    machine.mem[0xC100:0xC100 + len(nav_bdos)] = nav_bdos
    machine.mem[0x7500], machine.mem[0x7501] = 0, 0
    for command, drive, user in (
        (b"B:", 1, 0),
        (b"5:", 1, 5),
        (b"C31:", 2, 31),
        (b"E3:", 2, 31),       # unavailable drive must not alter either
    ):
        machine.mem[symbol("CCP_COUNT")] = len(command)
        start = symbol("CCP_DATA")
        machine.mem[start:start + len(command)] = command
        call(machine, symbol("CCP_NAVIGATE"))
        require((machine.mem[0x7500], machine.mem[0x7501]) == (drive, user),
                f"navigation state is wrong after {command!r}")

    print("CCP parsing, DU execution, navigation, resident DIR, and CPX dispatch passed")


if __name__ == "__main__":
    main()
