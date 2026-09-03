#!/usr/bin/env python3
"""Verify disk-backed CCP restoration and relocation in the Model 4 reloader."""
from __future__ import annotations

import struct
from pathlib import Path

from test_bios import Z80, require
from build_cpx_module import make_module

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
FILE_LOADER = 0xD000
DIR_LOGIN = 0xD60C


def relocated(module: bytes, target: int) -> bytes:
    if module[:4] == b"BCPX":
        link = struct.unpack_from("<H", module, 10)[0]
        size = struct.unpack_from("<H", module, 12)[0]
        count = struct.unpack_from("<H", module, 22)[0]
        payload = struct.unpack_from("<H", module, 26)[0]
        table = struct.unpack_from("<H", module, 28)[0]
    else:
        _magic, _version, _header_sectors, link, size, _allocation, _entry, count = (
            struct.unpack_from("<4sBBHHHHH", module))
        payload, table = 512, 16
    image = bytearray(module[payload:payload + size])
    delta = target - link
    for index in range(count):
        offset = struct.unpack_from("<H", module, table + index * 2)[0]
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
    # Protected filename-loader test double. OPEN selects BASIC/HELLO from the
    # first stem byte; NEXT copies a 512-byte unit and advances; RESET rewinds.
    vectors = bytes((0xC3, 0x10, 0xD0, 0xC3, 0x30, 0xD0,
                     0xC3, 0x50, 0xD0))
    open_stub = bytes((
        0x7E, 0xFE, 0x42, 0x11, 0x00, 0x90, 0x28, 0x03,
        0x11, 0x00, 0xA0, 0xEB, 0x22, 0x00, 0xD1,
        0x22, 0x02, 0xD1, 0xAF, 0xC9,
    ))
    next_stub = bytes((
        0xE5, 0x2A, 0x00, 0xD1, 0xD1,
        0x01, 0x00, 0x02, 0xED, 0xB0, 0xEB, 0xE5,
        0x2A, 0x00, 0xD1, 0x11, 0x00, 0x02, 0x19,
        0x22, 0x00, 0xD1, 0xE1, 0xAF, 0xC9,
    ))
    reset_stub = bytes((0x2A, 0x02, 0xD1, 0x22, 0x00, 0xD1, 0xAF, 0xC9))
    machine.mem[FILE_LOADER:FILE_LOADER + len(vectors)] = vectors
    machine.mem[0xD010:0xD010 + len(open_stub)] = open_stub
    machine.mem[0xD030:0xD030 + len(next_stub)] = next_stub
    machine.mem[0xD050:0xD050 + len(reset_stub)] = reset_stub
    machine.mem[DIR_LOGIN:DIR_LOGIN + 2] = bytes((0xAF, 0xC9))
    cpx_allocation = 0
    if with_two_cpx:
        basic_module = BASIC_MODULE.read_bytes()
        hello_module = HELLO_MODULE.read_bytes()
        machine.mem[0x9000:0x9000 + len(basic_module)] = basic_module
        machine.mem[0xA000:0xA000 + len(hello_module)] = hello_module
        machine.mem[0xC094] = 2
        machine.mem[0xC096:0xC09E] = b"BASIC   "
        machine.mem[0xC09E:0xC0A6] = b"HELLO   "
        cpx_allocation = (struct.unpack_from("<H", basic_module, 14)[0] +
                          struct.unpack_from("<H", hello_module, 14)[0])
    elif with_cpx:
        payload = bytes((0, 0, 4, 0x80, 0xC9, 0))
        file_module = make_module(name="BASIC", version=(0, 0), commands=[],
                                  linked_base=0x8000, code=payload,
                                  relocations=[2])
        machine.mem[0x9000:0x9000 + len(file_module)] = file_module
        machine.mem[0xC094] = 1
        machine.mem[0xC096:0xC09E] = b"BASIC   "
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
    actual = bytes(machine.mem[target:target + len(expected)])
    mismatch = next((index for index, pair in enumerate(zip(actual, expected))
                     if pair[0] != pair[1]), None)
    require(actual == expected,
            f"CCP was not restored and relocated at {target:04X}h; "
            f"first mismatch={mismatch!r}; "
            f"actual={actual[mismatch:mismatch + 16].hex() if mismatch is not None else ''} "
            f"expected={expected[mismatch:mismatch + 16].hex() if mismatch is not None else ''}")
    if with_two_cpx:
        basic_allocation = struct.unpack_from("<H", BASIC_MODULE.read_bytes(), 14)[0]
        hello_allocation = struct.unpack_from("<H", HELLO_MODULE.read_bytes(), 14)[0]
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
    calculated = 0xBDFD - allocation
    require(run_at(calculated) == relocated(module, calculated),
            "calculated-base module payload was not relocated correctly")
    # Derive a deliberately non-page-aligned alternate below the live base.
    # A fixed B601h target eventually crossed C100h as the CCP grew and tested
    # the loader's bounds rejection rather than relocation.
    alternate_target = calculated - 0x1EC
    alternate = run_at(alternate_target)
    require(alternate != CCP.read_bytes(),
            "alternate-base CCP did not apply relocation records")
    print(f"disk-backed CCP restoration passed at calculated {calculated:04X}h")
    print(f"relocatable CCP restoration passed at {alternate_target:04X}h")
    run_at(calculated - 0x100, with_cpx=True)
    print("one-module CPX profile restored before the calculated CCP")
    cpx_allocation = (
        struct.unpack_from("<H", BASIC_MODULE.read_bytes(), 14)[0] +
        struct.unpack_from("<H", HELLO_MODULE.read_bytes(), 14)[0]
    )
    two_cpx_target = 0xBFFD - allocation - cpx_allocation
    run_at(two_cpx_target, with_two_cpx=True)
    print("real BASIC and HELLO modules restored, relocated, and linked")


if __name__ == "__main__":
    main()
