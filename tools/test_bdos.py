#!/usr/bin/env python3
"""Execute the initial BDOS function dispatcher and function-15 boundary."""
from pathlib import Path

from test_bios import BASE as BIOS_BASE, Z80, require

ROOT = Path(__file__).resolve().parents[1]
BIOS = ROOT / "build/bios/bios.bin"
DIRECTORY = ROOT / "build/bdos/directory.bin"
BDOS = ROOT / "build/bdos/bdos.bin"
BDOS_BASE = 0xE600
DIR_BASE = 0xE800
DIR_BUFFER = 0xEC00
FIXTURE = 0x7500
FCB = 0x7700


def main() -> None:
    cpu = Z80(BIOS.read_bytes())
    directory = DIRECTORY.read_bytes()
    bdos = BDOS.read_bytes()
    cpu.mem[DIR_BASE:DIR_BASE + len(directory)] = directory
    cpu.mem[BDOS_BASE:BDOS_BASE + len(bdos)] = bdos

    read_impl = cpu.word(BIOS_BASE + 13 * 3 + 1)
    calls = [address for address in range(read_impl, read_impl + 48)
             if cpu.mem[address] == 0xCD]
    require(len(calls) >= 2, "BIOS physical-read call was not found")
    platform_read = cpu.word(calls[1] + 1)
    read_success = bytes((
        0x21, FIXTURE & 0xFF, FIXTURE >> 8,
        0x11, 0x00, 0xEE,
        0x01, 0x00, 0x02,
        0xED, 0xB0, 0xAF, 0xC9,
    ))
    cpu.mem[platform_read:platform_read + len(read_success)] = read_success

    # Establish the BIOS drive state before exercising the higher-level entry.
    # A real cold boot does this before BDOS receives calls.
    cpu.c = 0
    cpu.run(BIOS_BASE + 9 * 3)

    cpu.mem[FIXTURE:FIXTURE + 512] = bytes((0xE5,)) * 512
    entry = FIXTURE + 32
    cpu.mem[entry:entry + 12] = bytes((0,)) + b"OPEN    DAT"
    cpu.mem[entry + 12:entry + 16] = bytes((0, 0x55, 0, 1))
    cpu.mem[entry + 16:entry + 32] = bytes(16)

    cpu.mem[FCB:FCB + 33] = bytes((0xA5,)) * 33
    cpu.mem[FCB] = 0
    cpu.mem[FCB + 1:FCB + 12] = b"OPEN    DAT"
    cpu.mem[FCB + 12] = 0
    cpu.mem[FCB + 14] = 0xA5
    cpu.mem[FCB + 32] = 7
    cpu.mem[FCB + 14] = 0
    cpu.c = 0
    cpu.run(DIR_BASE + 12, limit=50000)
    require(cpu.a == 0,
            f"dispatcher fixture drive login failed with {cpu.a:02X}")
    cpu.a, cpu.de = 0, FCB
    cpu.run(DIR_BASE + 18, limit=50000)
    require(cpu.a == 1,
            f"direct Open fixture failed with {cpu.a:02X}; "
            f"dir={bytes(cpu.mem[DIR_BUFFER + 32:DIR_BUFFER + 48]).hex()} "
            f"src={bytes(cpu.mem[FIXTURE + 32:FIXTURE + 48]).hex()} "
            f"fcb={bytes(cpu.mem[FCB:FCB + 16]).hex()}")
    cpu.mem[FCB + 1:FCB + 12] = b"OPEN    DAT"
    cpu.mem[FCB + 12:FCB + 32] = bytes((0, 0xA5, 0xA5, 0xA5)) + bytes((0xA5,)) * 16
    cpu.mem[FCB + 32] = 7
    original_sp = cpu.sp
    cpu.c, cpu.de = 15, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 1 and cpu.l == 1 and cpu.b == 0 and cpu.h == 0,
            f"BDOS Open aliases wrong: A={cpu.a:02X} L={cpu.l:02X} "
            f"B={cpu.b:02X} H={cpu.h:02X} S2={cpu.mem[FCB + 14]:02X} "
            f"RC={cpu.mem[FCB + 15]:02X}")
    require(cpu.sp == original_sp, "BDOS did not restore the caller stack")
    require(cpu.mem[FCB + 14] == 0 and cpu.mem[FCB + 15] == 1 and
            cpu.mem[FCB + 32] == 7,
            "BDOS Open did not clear S2 and activate RC while preserving CR")

    cpu.mem[FCB + 1:FCB + 12] = b"MISSING DAT"
    cpu.mem[FCB + 14] = 0xA5
    cpu.c, cpu.de = 15, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0xFF and cpu.l == 0xFF and cpu.b == cpu.h == 0,
            "missing BDOS Open did not return FFh aliases")
    require(cpu.mem[FCB + 14] == 0, "BDOS Open did not clear caller S2")

    cpu.c, cpu.de = 12, FCB
    cpu.run(BDOS_BASE)
    require(cpu.a == 0xFF and cpu.l == 0xFF,
            "unsupported BDOS function did not fail explicitly")

    cpu.run(DIR_BASE + 15)       # invalidate, forcing storage on next Open
    cpu.mem[platform_read:platform_read + 4] = bytes((0x3E, 0x05, 0xB7, 0xC9))
    cpu.mem[FCB + 1:FCB + 12] = b"OPEN    DAT"
    cpu.c, cpu.de = 15, FCB
    cpu.run(BDOS_BASE, limit=5000)
    require(cpu.a == 0xFF and cpu.l == 0xFF,
            "provisional BDOS storage failure was confused with slot success")

    print("BDOS function 15 returned CP/M A/L and B/H aliases")
    print("private stack restoration, S2 clearing, Open, and failure paths passed")


if __name__ == "__main__":
    main()
