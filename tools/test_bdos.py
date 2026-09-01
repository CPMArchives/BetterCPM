#!/usr/bin/env python3
"""Execute the initial BDOS function dispatcher and function-15 boundary."""
from pathlib import Path
import re

from test_bios import BASE as BIOS_BASE, Z80, require

ROOT = Path(__file__).resolve().parents[1]
BIOS = ROOT / "build/bios/bios.bin"
DIRECTORY = ROOT / "build/bdos/directory.bin"
BDOS = ROOT / "build/bdos/bdos.bin"
BDOS_BASE = 0xE600
DIR_BASE = 0xE800
DIR_BUFFER = 0xED00
FIXTURE = 0x7500
FCB = 0x7700


def symbol(name: str) -> int:
    listing = (ROOT / "build/bdos/bdos.lst").read_text(encoding="ascii")
    match = re.search(rf"^([0-9a-f]{{4}})\s+.*\b{name}:?\s*$",
                      listing, re.MULTILINE | re.IGNORECASE)
    require(match is not None, f"BDOS listing lacks {name}")
    return int(match.group(1), 16)


def main() -> None:
    cpu = Z80(BIOS.read_bytes())
    directory = DIRECTORY.read_bytes()
    bdos = BDOS.read_bytes()
    cpu.mem[DIR_BASE:DIR_BASE + len(directory)] = directory
    cpu.mem[BDOS_BASE:BDOS_BASE + len(bdos)] = bdos
    dma_state = symbol("BDOS_DMA")
    login_state = symbol("STATE_LV")
    readonly_state = symbol("STATE_RO")

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
    dph = cpu.hl
    expected_dpb = cpu.word(dph + 10)
    expected_alv = cpu.word(dph + 14)

    cpu.mem[FIXTURE:FIXTURE + 512] = bytes((0xE5,)) * 512
    cpu.mem[FIXTURE:FIXTURE + 12] = bytes((0,)) + b"FIRST   DAT"
    cpu.mem[FIXTURE + 12:FIXTURE + 16] = bytes((0, 0, 0, 1))
    cpu.mem[FIXTURE + 16:FIXTURE + 32] = bytes(16)
    entry = FIXTURE + 32
    cpu.mem[entry:entry + 12] = bytes((0,)) + b"OPEN    DAT"
    cpu.mem[entry + 12:entry + 16] = bytes((0, 0x55, 0, 1))
    cpu.mem[entry + 16:entry + 32] = bytes(16)
    other = FIXTURE + 64
    cpu.mem[other:other + 12] = bytes((5,)) + b"OTHER   DAT"
    cpu.mem[other + 12:other + 16] = bytes((0, 0, 0, 1))
    cpu.mem[other + 16:other + 32] = bytes(16)

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
    opened_fcb = bytes(cpu.mem[FCB:FCB + 33])
    media_before_close = bytes(cpu.mem[FIXTURE:FIXTURE + 512])
    cpu.c, cpu.de = 16, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 1 and bytes(cpu.mem[FCB:FCB + 33]) == opened_fcb and
            bytes(cpu.mem[FIXTURE:FIXTURE + 512]) == media_before_close,
            "unchanged Close did not return slot 1 without modifying state")
    cpu.mem[FCB + 15] = 2
    dirty_fcb = bytes(cpu.mem[FCB:FCB + 33])
    cpu.c, cpu.de = 16, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0xFF and bytes(cpu.mem[FCB:FCB + 33]) == dirty_fcb and
            bytes(cpu.mem[FIXTURE:FIXTURE + 512]) == media_before_close,
            "provisional dirty Close did not reject without media mutation")
    cpu.mem[FCB:FCB + 33] = opened_fcb

    cpu.mem[FCB + 1:FCB + 12] = b"MISSING DAT"
    cpu.mem[FCB + 14] = 0xA5
    cpu.c, cpu.de = 15, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0xFF and cpu.l == 0xFF and cpu.b == cpu.h == 0,
            "missing BDOS Open did not return FFh aliases")
    require(cpu.mem[FCB + 14] == 0, "BDOS Open did not clear caller S2")
    cpu.c, cpu.de = 16, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0xFF, "Close of a missing filename did not return FFh")

    cpu.c, cpu.de = 12, FCB
    cpu.run(BDOS_BASE)
    require(cpu.hl == 0x0022 and cpu.a == 0x22 and cpu.b == 0,
            "BDOS version did not return CP/M 2.2 aliases")
    cpu.c, cpu.e = 14, 0
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0, "selecting drive A did not complete login")
    cpu.c = 25
    cpu.run(BDOS_BASE)
    require(cpu.a == cpu.l == 0 and cpu.b == cpu.h == 0,
            "current-drive query did not return drive A")
    cpu.c, cpu.e = 14, 1
    cpu.run(BDOS_BASE)
    require(cpu.a == 0xFF, "unsupported drive B was not rejected")
    cpu.c = 25
    cpu.run(BDOS_BASE)
    require(cpu.a == 0, "failed drive selection changed the current drive")
    cpu.c = 24
    cpu.run(BDOS_BASE)
    require(cpu.hl == 1 and cpu.a == 1 and cpu.b == 0,
            "login vector did not report drive A only")
    cpu.c, cpu.de = 26, 0x7345
    cpu.run(BDOS_BASE)
    require(cpu.word(dma_state) == 0x7345,
            "set-DMA state did not retain DE")
    cpu.c = 27
    cpu.run(BDOS_BASE)
    require(cpu.hl == expected_alv and cpu.mem[cpu.hl] == 0xC0,
            "allocation-vector pointer or reserved bits are wrong")
    cpu.c = 31
    cpu.run(BDOS_BASE)
    require(cpu.hl == expected_dpb and bytes(cpu.mem[cpu.hl:cpu.hl + 15]) ==
            bytes((80, 0, 4, 15, 0, 0x8A, 1, 0x7F, 0, 0xC0, 0, 32, 0, 2, 0)),
            "DPB pointer or 15-byte MM 790K layout is wrong")
    cpu.mem[FCB:FCB + 33] = bytes(33)
    cpu.mem[FCB + 1:FCB + 13] = b"????????????"
    cpu.mem[FCB + 14] = 0xA5
    cpu.c, cpu.de = 26, 0x7200
    cpu.run(BDOS_BASE)
    cpu.c, cpu.de = 17, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0 and cpu.mem[FCB + 14] == 0 and
            bytes(cpu.mem[0x7200:0x7280]) == bytes(cpu.mem[FIXTURE:FIXTURE + 128]),
            "Search First did not return slot 0 and the complete DMA record")
    cpu.c, cpu.de = 26, 0x7280
    cpu.run(BDOS_BASE)
    cpu.c, cpu.de = 18, 0xA55A
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 1 and
            bytes(cpu.mem[0x7280:0x7300]) == bytes(cpu.mem[FIXTURE:FIXTURE + 128]),
            "Search Next did not continue at slot 1 using the changed DMA")
    saved_record = bytes(cpu.mem[FIXTURE:FIXTURE + 128])
    cpu.mem[FIXTURE:FIXTURE + 128] = bytes((0xE5,)) * 128
    cpu.c, cpu.de = 18, 0x5AA5
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0xFF, "Search Next did not exhaust user-0 matches")
    cpu.mem[FIXTURE:FIXTURE + 128] = saved_record
    cpu.mem[FCB] = ord('?')
    cpu.mem[FCB + 14] = 0xA5
    cpu.c, cpu.de = 17, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0 and cpu.mem[FCB + 14] == 0xA5,
            "all-user Search First did not preserve special S2 state")
    cpu.c, cpu.e = 32, 0x25
    cpu.run(BDOS_BASE)
    cpu.c, cpu.e = 32, 0xFF
    cpu.run(BDOS_BASE)
    require(cpu.a == cpu.l == 5 and cpu.word(dma_state) == 0x7280,
            "user modulo-32 selection/query or DMA independence failed")
    cpu.c = 29
    cpu.run(BDOS_BASE)
    require(cpu.hl == 0, "read-only vector was not initially clear")
    media_before_protect = bytes(cpu.mem[FIXTURE:FIXTURE + 512])
    cpu.c = 28
    cpu.run(BDOS_BASE)
    cpu.c = 29
    cpu.run(BDOS_BASE)
    require(cpu.hl == 1 and cpu.word(readonly_state) == 1,
            "write protect did not set drive A in the read-only vector")
    require(bytes(cpu.mem[FIXTURE:FIXTURE + 512]) == media_before_protect,
            "software write protection modified the disk image")
    cpu.c = 13
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0 and cpu.word(dma_state) == 0x0080 and
            cpu.word(login_state) == 1 and cpu.word(readonly_state) == 0,
            "disk reset did not restore DMA, drive A, login, and protection")
    cpu.c, cpu.e = 32, 0xFF
    cpu.run(BDOS_BASE)
    require(cpu.a == 5, "disk reset did not preserve current user")
    cpu.c = 40
    cpu.run(BDOS_BASE)
    require(cpu.a == 0xFF and cpu.l == 0xFF,
            "unsupported BDOS function did not fail explicitly")

    cpu.run(DIR_BASE + 15)       # invalidate, forcing storage on next Open
    cpu.mem[platform_read:platform_read + 4] = bytes((0x3E, 0x05, 0xB7, 0xC9))
    cpu.c, cpu.e = 14, 0
    cpu.run(BDOS_BASE, limit=5000)
    require(cpu.a == 0xFF, "drive login storage failure was not reported")
    cpu.c = 25
    cpu.run(BDOS_BASE)
    require(cpu.a == 0, "failed drive-A relogin changed current-drive state")
    cpu.mem[FCB + 1:FCB + 12] = b"OPEN    DAT"
    cpu.c, cpu.de = 15, FCB
    cpu.run(BDOS_BASE, limit=5000)
    require(cpu.a == 0xFF and cpu.l == 0xFF,
            f"provisional BDOS storage failure was confused with slot success: "
            f"A={cpu.a:02X} L={cpu.l:02X}")

    print("BDOS functions 12-18, 24-29, 31, and 32 passed")
    print("state persistence, aliases, stack, Open, and failure paths passed")


if __name__ == "__main__":
    main()
