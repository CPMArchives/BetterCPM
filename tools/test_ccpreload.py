#!/usr/bin/env python3
"""Verify disk-backed CCP restoration and relocation in the Model 4 reloader."""
from __future__ import annotations

import struct
from pathlib import Path

from test_bios import Z80, require

ROOT = Path(__file__).resolve().parents[1]
RELOADER = ROOT / "build/trs80/ccpreload.bin"
MODULE = ROOT / "build/ccp/ccp.rlm"
CCP = ROOT / "build/ccp/ccp.bin"
BASIC_MODULE = ROOT / "build/cpx/BASIC.CPX"
HELLO_MODULE = ROOT / "build/cpx/HELLO.CPX"
BASE = 0xE900
MODULE_SOURCE = 0x6000
DESCRIPTOR_CCP = 0xC08C
SYSTEM_WBOOT = 0xC023
PHYSICAL_READ = 0xEF33


def relocated(module: bytes, target: int) -> bytes:
    _magic, _version, _header_sectors, link, size, _allocation, _entry, count = (
        struct.unpack_from("<4sBBHHHHH", module))
    image = bytearray(module[512:512 + size])
    delta = target - link
    for index in range(count):
        offset = struct.unpack_from("<H", module, 16 + index * 2)[0]
        value = int.from_bytes(image[offset:offset + 2], "little")
        image[offset:offset + 2] = ((value + delta) & 0xFFFF).to_bytes(2, "little")
    return bytes(image)


def run_at(target: int, with_cpx: bool = False, with_two_cpx: bool = False) -> bytes:
    module = MODULE.read_bytes()
    allocation = struct.unpack_from("<H", module, 10)[0]
    machine = Z80(b"")
    machine.mem[BASE:BASE + len(RELOADER.read_bytes())] = RELOADER.read_bytes()
    sectors = [1, 3, 5, 7, 9, 2, 4, 6, 8, 10]

    def install_slots(first: int, content: bytes) -> None:
        padded = content.ljust(((len(content) + 511) // 512) * 512, b"\x00")
        for offset in range(0, len(padded), 512):
            physical = sectors[first + offset // 512]
            source = MODULE_SOURCE + physical * 512
            machine.mem[source:source + 512] = padded[offset:offset + 512]

    install_slots(0, module)
    cpx_allocation = 0
    if with_two_cpx:
        basic_module = BASIC_MODULE.read_bytes()
        hello_module = HELLO_MODULE.read_bytes()
        install_slots(4, basic_module)
        install_slots(7, hello_module)
        machine.mem[0xC094] = 2
        machine.mem[0xC096] = 4
        machine.mem[0xC09E] = 7
        cpx_allocation = (struct.unpack_from("<H", basic_module, 10)[0] +
                          struct.unpack_from("<H", hello_module, 10)[0])
    elif with_cpx:
        payload = bytes((0, 0, 4, 0x80, 0xC9, 0))
        header = bytearray(512)
        struct.pack_into("<4sBBHHHHH", header, 0, b"BCX1", 1, 1,
                         0x8000, len(payload), 0x100, 0, 1)
        struct.pack_into("<H", header, 16, 2)
        install_slots(4, bytes(header) + payload)
        machine.mem[0xC094] = 1
        machine.mem[0xC096] = 4
        cpx_allocation = 0x100

    gateway = target + allocation + cpx_allocation
    machine.mem[0xC090:0xC092] = gateway.to_bytes(2, "little")
    machine.mem[target:target + allocation] = bytes((0xA5,)) * allocation

    # Source fixtures are indexed by the actual Model 4 sector number in C.
    reader = bytes((
        0xE5,                   # PUSH HL (destination)
        0x79, 0x87, 0x67, 0x2E, 0x00,  # HL=C*512
        0x11, 0x00, 0x60, 0x19,  # HL+=6000h
        0xD1,                   # POP DE (destination)
        0x01, 0x00, 0x02, 0xED, 0xB0,  # LDIR 512 bytes
        0xEB,                   # return HL=destination+512 like M4_READ
        0xAF, 0xC9,             # success
    ))
    machine.mem[PHYSICAL_READ:PHYSICAL_READ + len(reader)] = reader
    machine.mem[SYSTEM_WBOOT:SYSTEM_WBOOT + 2] = bytes((0x18, 0xFE))
    try:
        machine.run(BASE, limit=200000)
    except AssertionError as error:
        require("execution limit reached" in str(error),
                f"reloader failed unexpectedly: {error}")
    expected = relocated(module, target)
    require(bytes(machine.mem[target:target + len(expected)]) == expected,
            f"CCP was not restored and relocated at {target:04X}h")
    if with_two_cpx:
        basic_allocation = struct.unpack_from("<H", BASIC_MODULE.read_bytes(), 10)[0]
        hello_allocation = struct.unpack_from("<H", HELLO_MODULE.read_bytes(), 10)[0]
        basic_base = gateway - basic_allocation
        hello_base = basic_base - hello_allocation
        require(machine.word(0xC086) == basic_base and
                machine.word(basic_base) == hello_base and
                machine.word(hello_base) == 0,
                "two-module CPX chain was not restored in table order")
        require(bytes(machine.mem[basic_base + 4:basic_base + len(relocated(
                    BASIC_MODULE.read_bytes(), basic_base))]) ==
                relocated(BASIC_MODULE.read_bytes(), basic_base)[4:],
                "linking HELLO corrupted relocated BASIC.CPX payload")
        require(bytes(machine.mem[hello_base:hello_base + len(relocated(
                    HELLO_MODULE.read_bytes(), hello_base))]) ==
                relocated(HELLO_MODULE.read_bytes(), hello_base),
                "HELLO.CPX relocation or payload integrity failed")
    elif with_cpx:
        cpx_base = gateway - 0x100
        require(machine.word(0xC086) == cpx_base and
                machine.word(cpx_base) == 0 and
                machine.word(cpx_base + 2) == cpx_base + 4,
                "ordered CPX profile was not restored, relocated, and linked")
    return expected


def main() -> None:
    module = MODULE.read_bytes()
    allocation = struct.unpack_from("<H", module, 10)[0]
    calculated = 0xBFFD - allocation
    require(run_at(calculated) == relocated(module, calculated),
            "calculated-base module payload was not relocated correctly")
    alternate = run_at(0xB900)
    require(alternate != CCP.read_bytes(),
            "alternate-base CCP did not apply relocation records")
    print(f"disk-backed CCP restoration passed at calculated {calculated:04X}h")
    print("relocatable CCP restoration passed at B900h")
    run_at(calculated - 0x100, with_cpx=True)
    print("one-module CPX profile restored before the calculated CCP")
    run_at(calculated - 0x500, with_two_cpx=True)
    print("real BASIC and HELLO modules restored, relocated, and linked")


if __name__ == "__main__":
    main()
