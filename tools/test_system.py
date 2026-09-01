#!/usr/bin/env python3
"""Execute initialization and a real CP/M CALL 0005h function-15 path."""
from pathlib import Path

from test_bios import BASE as BIOS_BASE, Z80, require

ROOT = Path(__file__).resolve().parents[1]
RESIDENT = ROOT / "build/system/resident.bin"
RESIDENT_BASE = 0xE500
SYSTEM_INIT = 0xE500
FIXTURE = 0x7500
FCB = 0x7700
CALLER = 0x7800


def main() -> None:
    resident = RESIDENT.read_bytes()
    bios_offset = BIOS_BASE - RESIDENT_BASE
    cpu = Z80(resident[bios_offset:])
    cpu.mem[RESIDENT_BASE:RESIDENT_BASE + len(resident)] = resident

    read_impl = cpu.word(BIOS_BASE + 13 * 3 + 1)
    calls = [address for address in range(read_impl, read_impl + 48)
             if cpu.mem[address] == 0xCD]
    require(len(calls) >= 2, "BIOS physical-read call was not found")
    platform_read = cpu.word(calls[1] + 1)
    cpu.mem[platform_read:platform_read + 13] = bytes((
        0x21, FIXTURE & 0xFF, FIXTURE >> 8,
        0x11, 0x00, 0xEE,
        0x01, 0x00, 0x02,
        0xED, 0xB0, 0xAF, 0xC9,
    ))

    cpu.mem[FIXTURE:FIXTURE + 512] = bytes((0xE5,)) * 512
    entry = FIXTURE + 32
    cpu.mem[entry:entry + 12] = bytes((0,)) + b"GATEWAY DAT"
    cpu.mem[entry + 12:entry + 16] = bytes((0, 0, 0, 1))
    cpu.mem[entry + 16:entry + 32] = bytes(16)

    cpu.run(SYSTEM_INIT, limit=60000)
    require(cpu.a == 0, "resident initialization failed")
    require(bytes(cpu.mem[0:3]) == bytes((0xC3, 0x03, 0xF0)),
            "warm-boot page-zero vector is wrong")
    require(bytes(cpu.mem[5:8]) == bytes((0xC3, 0x00, 0xE6)),
            "BDOS page-zero vector is wrong")

    cpu.mem[FCB:FCB + 33] = bytes(33)
    cpu.mem[FCB + 1:FCB + 12] = b"GATEWAY DAT"
    cpu.mem[CALLER:CALLER + 4] = bytes((0xCD, 0x05, 0x00, 0xC9))
    original_sp = cpu.sp
    cpu.c, cpu.de = 15, FCB
    cpu.run(CALLER, limit=50000)
    require(cpu.a == cpu.l == 1 and cpu.b == cpu.h == 0,
            "CALL 0005h did not return function-15 aliases")
    require(cpu.sp == original_sp, "CALL 0005h did not restore caller stack")
    require(cpu.mem[FCB + 15] == 1, "CALL 0005h did not activate the FCB")

    cpu.c = 12
    cpu.run(CALLER)
    require(cpu.hl == 0x0022, "CALL 0005h version query was not CP/M 2.2")
    cpu.c = 25
    cpu.run(CALLER)
    require(cpu.a == cpu.l == 0, "CALL 0005h current drive was not A")
    cpu.c, cpu.e = 14, 0
    cpu.run(CALLER, limit=50000)
    require(cpu.a == 0, "CALL 0005h could not select and log in drive A")
    cpu.c, cpu.e = 14, 1
    cpu.run(CALLER)
    require(cpu.a == 0xFF, "CALL 0005h accepted unavailable drive B")
    cpu.c = 25
    cpu.run(CALLER)
    require(cpu.a == 0, "failed CALL 0005h drive selection changed drive A")
    cpu.c, cpu.de = 26, 0x7345
    cpu.run(CALLER)
    cpu.c, cpu.e = 32, 0x3F
    cpu.run(CALLER)
    cpu.c, cpu.e = 32, 0xFF
    cpu.run(CALLER)
    require(cpu.a == cpu.l == 31,
            "CALL 0005h user selection did not apply modulo 32")

    # Initialization failure must not expose either conventional vector.
    failed = Z80(resident[bios_offset:])
    failed.mem[RESIDENT_BASE:RESIDENT_BASE + len(resident)] = resident
    failed_read = failed.word(calls[1] + 1)
    failed.mem[failed_read:failed_read + 4] = bytes((0x3E, 0x05, 0xB7, 0xC9))
    failed.run(SYSTEM_INIT, limit=5000)
    require(failed.a == 5 and bytes(failed.mem[0:8]) == bytes(8),
            "failed initialization published page-zero vectors")

    print("resident initialization installed WBOOT and BDOS page-zero vectors")
    print("application CALL 0005h reached functions 12, 14, 15, 25, 26, and 32")


if __name__ == "__main__":
    main()
