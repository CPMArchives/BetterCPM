#!/usr/bin/env python3
"""Execute initialization and a real CP/M CALL 0005h function-15 path."""
from pathlib import Path

from test_bios import BASE as BIOS_BASE, Z80, require

ROOT = Path(__file__).resolve().parents[1]
RESIDENT = ROOT / "build/system/resident.bin"
RESIDENT_BASE = 0xBF00
SYSTEM_INIT = 0xC000
FIXTURE = 0x7500
FCB = 0x7700
CALLER = 0x7800
DATA = 0x7900


def main() -> None:
    resident = RESIDENT.read_bytes()
    bios_offset = BIOS_BASE - RESIDENT_BASE
    cpu = Z80(resident[bios_offset:])
    cpu.sp = 0xED00          # clear of D800h..ECFFh System Services growth
    cpu.mem[RESIDENT_BASE:RESIDENT_BASE + len(resident)] = resident

    read_impl = cpu.word(BIOS_BASE + 13 * 3 + 1)
    calls = [address for address in range(read_impl, read_impl + 48)
             if cpu.mem[address] == 0xCD]
    require(len(calls) >= 2, "BIOS physical-read call was not found")
    platform_read = cpu.word(calls[1] + 1)
    read_success = bytes((
        0x79, 0xFE, 0x08, 0x20, 0x05,
        0x21, DATA & 0xFF, DATA >> 8,
        0x18, 0x03,
        0x21, FIXTURE & 0xFF, FIXTURE >> 8,
        0x11, 0x00, 0xEE,
        0x01, 0x00, 0x02,
        0xED, 0xB0, 0xAF, 0xC9,
    ))
    cpu.mem[platform_read:platform_read + len(read_success)] = read_success
    write_impl = cpu.word(BIOS_BASE + 14 * 3 + 1)
    write_jumps = [address for address in range(write_impl, write_impl + 90)
                   if cpu.mem[address] == 0xC3]
    require(write_jumps, "BIOS physical-write jump was not found")
    platform_write = cpu.word(write_jumps[-1] + 1)
    cpu.mem[platform_write:platform_write + 13] = bytes((
        0x21, 0x00, 0xEE,
        0x11, FIXTURE & 0xFF, FIXTURE >> 8,
        0x01, 0x00, 0x02,
        0xED, 0xB0, 0xAF, 0xC9,
    ))

    cpu.mem[FIXTURE:FIXTURE + 512] = bytes((0xE5,)) * 512
    entry = FIXTURE + 32
    cpu.mem[entry:entry + 12] = bytes((0,)) + b"GATEWAY DAT"
    cpu.mem[entry + 12:entry + 16] = bytes((0, 0, 0, 1))
    cpu.mem[entry + 16:entry + 32] = bytes(16)
    read_entry = FIXTURE + 64
    cpu.mem[read_entry:read_entry + 12] = bytes((0,)) + b"READ    DAT"
    cpu.mem[read_entry + 12:read_entry + 16] = bytes((0, 0, 0, 2))
    cpu.mem[read_entry + 16:read_entry + 32] = bytes((2, 0)) + bytes(14)
    cpu.mem[DATA:DATA + 128] = bytes((0xA0,)) * 128
    cpu.mem[DATA + 128:DATA + 256] = bytes((0xA1,)) * 128
    cpu.mem[DATA + 256:DATA + 512] = bytes((0xEE,)) * 256

    cpu.run(SYSTEM_INIT, limit=60000)
    require(cpu.a == 0, "resident initialization failed")
    require(bytes(cpu.mem[0:3]) == bytes((0xC3, 0x03, 0xF0)),
            "warm-boot page-zero vector is wrong")
    require(bytes(cpu.mem[5:8]) == bytes((0xC3, 0x00, 0xC1)),
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
    opened_fcb = bytes(cpu.mem[FCB:FCB + 33])
    media_before_close = bytes(cpu.mem[FIXTURE:FIXTURE + 512])
    cpu.c, cpu.de = 16, FCB
    cpu.run(CALLER, limit=50000)
    require(cpu.a == 1 and bytes(cpu.mem[FCB:FCB + 33]) == opened_fcb and
            bytes(cpu.mem[FIXTURE:FIXTURE + 512]) == media_before_close,
            "CALL 0005h unchanged Close modified FCB or media")
    cpu.mem[FCB + 15] = 2
    dirty_fcb = bytes(cpu.mem[FCB:FCB + 33])
    cpu.c, cpu.de = 16, FCB
    cpu.run(CALLER, limit=50000)
    require(cpu.a == 1 and bytes(cpu.mem[FCB:FCB + 33]) == dirty_fcb and
            cpu.mem[entry + 15] == 2,
            "CALL 0005h dirty Close did not commit RC")

    cpu.mem[FCB:FCB + 33] = bytes(33)
    cpu.mem[FCB + 1:FCB + 13] = b"????????????"
    cpu.c, cpu.de = 26, 0x7200
    cpu.run(CALLER)
    cpu.c, cpu.de = 17, FCB
    cpu.run(CALLER, limit=50000)
    require(cpu.a == 1 and
            bytes(cpu.mem[0x7200:0x7280]) == bytes(cpu.mem[FIXTURE:FIXTURE + 128]),
            "CALL 0005h Search First did not transfer its directory record")
    saved_record = bytes(cpu.mem[FIXTURE:FIXTURE + 128])
    cpu.mem[FIXTURE:FIXTURE + 128] = bytes((0xE5,)) * 128
    cpu.c, cpu.de = 26, 0x7280
    cpu.run(CALLER)
    cpu.c, cpu.de = 18, 0xA55A
    cpu.run(CALLER, limit=50000)
    require(cpu.a == 0xFF, "CALL 0005h Search Next did not reach exhaustion")
    cpu.mem[FIXTURE:FIXTURE + 128] = saved_record

    cpu.mem[FCB:FCB + 33] = bytes(33)
    cpu.mem[FCB + 1:FCB + 12] = b"READ    DAT"
    cpu.c, cpu.de = 15, FCB
    cpu.run(CALLER, limit=50000)
    require(cpu.a == 2, "CALL 0005h could not Open sequential-read fixture")
    cpu.c, cpu.de = 26, 0x7100
    cpu.run(CALLER)
    cpu.c, cpu.de = 20, FCB
    cpu.run(CALLER, limit=50000)
    require(cpu.a == 0 and cpu.mem[FCB + 32] == 1 and
            bytes(cpu.mem[0x7100:0x7180]) == bytes((0xA0,)) * 128,
            "CALL 0005h first sequential read failed")
    cpu.c, cpu.de = 20, FCB
    cpu.run(CALLER, limit=50000)
    require(cpu.a == 0 and cpu.mem[FCB + 32] == 2 and
            bytes(cpu.mem[0x7100:0x7180]) == bytes((0xA1,)) * 128,
            "CALL 0005h second sequential read failed")
    cpu.c, cpu.de = 20, FCB
    cpu.run(CALLER, limit=50000)
    require(cpu.a != 0, "CALL 0005h sequential read did not report EOF")
    cpu.mem[FIXTURE:FIXTURE + 12] = bytes((0,)) + b"READ    DAT"
    cpu.mem[FIXTURE + 12:FIXTURE + 16] = bytes((1, 0, 0, 1))
    cpu.mem[FIXTURE + 16:FIXTURE + 32] = bytes((2, 0)) + bytes(14)
    cpu.mem[FCB + 32] = 128
    cpu.c, cpu.de = 20, FCB
    cpu.run(CALLER, limit=50000)
    require(cpu.a == 0 and cpu.mem[FCB + 12] == 1 and cpu.mem[FCB + 32] == 1,
            "CALL 0005h did not transition to the next sequential extent")
    cpu.mem[FCB + 9] |= 0x80
    protected_fcb = bytes(cpu.mem[FCB:FCB + 33])
    cpu.c, cpu.de = 21, FCB
    cpu.run(CALLER, limit=50000)
    require(cpu.a == 0xFF and bytes(cpu.mem[FCB:FCB + 33]) == protected_fcb,
            "CALL 0005h did not enforce file protection on sequential write")
    cpu.mem[FCB + 9] &= 0x7F

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
    cpu.c = 24
    cpu.run(CALLER)
    require(cpu.hl == 1, "CALL 0005h login vector did not contain drive A")
    cpu.c = 28
    cpu.run(CALLER)
    saved_fcb = bytes(cpu.mem[FCB:FCB + 33])
    cpu.mem[FCB:FCB + 33] = bytes((0,)) + b"DENIED  DAT" + bytes(21)
    cpu.c, cpu.de = 19, FCB
    cpu.run(CALLER, limit=50000)
    require(cpu.a == 0xFF,
            "CALL 0005h Delete ignored current-drive write protection")
    cpu.mem[FCB + 16] = 0
    cpu.mem[FCB + 17:FCB + 28] = b"RENAMED DAT"
    cpu.c, cpu.de = 23, FCB
    cpu.run(CALLER, limit=50000)
    require(cpu.a == 0xFF,
            "CALL 0005h Rename ignored current-drive write protection")
    cpu.c, cpu.de = 30, FCB
    cpu.run(CALLER, limit=50000)
    require(cpu.a == 0xFF,
            "CALL 0005h Set Attributes ignored current-drive write protection")
    cpu.c, cpu.de = 22, FCB
    cpu.run(CALLER, limit=50000)
    require(cpu.a == 0xFF,
            "CALL 0005h Make ignored current-drive write protection")
    cpu.mem[FCB:FCB + 33] = saved_fcb
    cpu.c = 29
    cpu.run(CALLER)
    require(cpu.hl == 1, "CALL 0005h did not protect current drive A")
    cpu.mem[FCB:FCB + 36] = bytes(36)
    cpu.mem[FCB + 1:FCB + 12] = b"ABSENT  DAT"
    cpu.mem[FCB + 33:FCB + 36] = bytes((0xA5,)) * 3
    cpu.c, cpu.de = 35, FCB
    cpu.run(CALLER, limit=100000)
    require(cpu.a == 0xFF and
            bytes(cpu.mem[FCB + 33:FCB + 36]) == bytes((0xA5,)) * 3,
            "CALL 0005h missing Compute File Size changed R0-R2")
    cpu.c = 27
    cpu.run(CALLER)
    alv = cpu.hl
    require(cpu.mem[alv] == 0xE0,
            "CALL 0005h allocation vector lacks directory/read-fixture blocks")
    cpu.c = 31
    cpu.run(CALLER)
    require(bytes(cpu.mem[cpu.hl:cpu.hl + 5]) == bytes((80, 0, 4, 15, 0)),
            "CALL 0005h DPB does not begin with the MM 790K parameters")
    cpu.c = 13
    cpu.run(CALLER, limit=50000)
    cpu.c = 29
    cpu.run(CALLER)
    require(cpu.hl == 0, "disk reset did not clear software protection")
    cpu.c = 25
    cpu.run(CALLER)
    require(cpu.a == 0, "disk reset did not restore current drive A")
    cpu.c, cpu.e = 32, 0xFF
    cpu.run(CALLER)
    require(cpu.a == 31, "disk reset did not preserve current user")

    # Initialization failure must not expose either conventional vector.
    failed = Z80(resident[bios_offset:])
    failed.sp = 0xED00
    failed.mem[RESIDENT_BASE:RESIDENT_BASE + len(resident)] = resident
    failed_read = failed.word(calls[1] + 1)
    failed.mem[failed_read:failed_read + 4] = bytes((0x3E, 0x05, 0xB7, 0xC9))
    failed.run(SYSTEM_INIT, limit=5000)
    require(failed.a == 5 and bytes(failed.mem[0:8]) == bytes(8),
            "failed initialization published page-zero vectors")

    print("resident initialization installed WBOOT and BDOS page-zero vectors")
    print("application CALL 0005h reached functions 12-32 and 35")


if __name__ == "__main__":
    main()
