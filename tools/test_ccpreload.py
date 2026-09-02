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


def run_at(target: int) -> bytes:
    module = MODULE.read_bytes()
    machine = Z80(b"")
    machine.mem[BASE:BASE + len(RELOADER.read_bytes())] = RELOADER.read_bytes()
    padded = module.ljust(4 * 512, b"\x00")
    machine.mem[MODULE_SOURCE:MODULE_SOURCE + len(padded)] = padded
    machine.mem[DESCRIPTOR_CCP:DESCRIPTOR_CCP + 2] = target.to_bytes(2, "little")
    machine.mem[target:target + 0x500] = bytes((0xA5,)) * 0x500

    # C=1,3,5,7 maps to consecutive 512-byte module sectors at 6000h.
    reader = bytes((
        0xE5,                   # PUSH HL (destination)
        0x79, 0x3D, 0xCB, 0x3F,  # A=(C-1)/2
        0x67, 0x2E, 0x00, 0x29,  # HL=A*512
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
    return expected


def main() -> None:
    require(run_at(0xBB00) == CCP.read_bytes(),
            "default-base module payload differs from canonical CCP")
    alternate = run_at(0xB900)
    require(alternate != CCP.read_bytes(),
            "alternate-base CCP did not apply relocation records")
    print("disk-backed CCP restoration passed at BB00h")
    print("relocatable CCP restoration passed at B900h")


if __name__ == "__main__":
    main()
