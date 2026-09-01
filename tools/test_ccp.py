#!/usr/bin/env python3
"""Execute focused CCP parsing contracts from the assembled resident binary."""
from __future__ import annotations

import re
from pathlib import Path

from test_bios import Z80, require

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "build/ccp/ccp.bin"
LISTING = ROOT / "build/ccp/ccp.lst"
BASE = 0xB000
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
    head, second = 0xB800, 0xB804
    decline, accept = 0x7300, 0x7310
    machine.mem[0xBFFE:0xC000] = head.to_bytes(2, "little")
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

    print("CCP parsing, resident DIR, and CPX dispatch passed")


if __name__ == "__main__":
    main()
