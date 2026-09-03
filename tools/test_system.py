#!/usr/bin/env python3
"""Execute initialization and a real CP/M CALL 0005h function-15 path."""
from pathlib import Path

from test_bios import BASE as BIOS_BASE, Z80, require
from test_ccpreload import relocated

ROOT = Path(__file__).resolve().parents[1]
RESIDENT = ROOT / "build/system/resident.bin"
CCP = ROOT / "build/ccp/ccp.bin"
CCP_MODULE = ROOT / "build/ccp/ccp.rlm"
RESIDENT_BASE = 0xC000
SYSTEM_INIT = 0xC000
HISTORY_BASE = 0xBE00
DEFAULT_GATEWAY = 0xBDFD
FIXTURE = 0x7500
FCB = 0x7700
CALLER = 0x7800
DATA = 0x7900


def bdos_symbol(name: str) -> int:
    import re
    listing = (ROOT / "build/bdos/bdos.lst").read_text(encoding="ascii")
    matches = re.findall(rf"^([0-9a-f]{{4}})\s+.*\b{name}:?\s*$",
                         listing, re.MULTILINE | re.IGNORECASE)
    require(matches, f"BDOS listing lacks {name}")
    return int(matches[-1], 16)


def main() -> None:
    resident = RESIDENT.read_bytes()
    bios_offset = BIOS_BASE - RESIDENT_BASE
    cpu = Z80(resident[bios_offset:])
    cpu.sp = 0xA800          # below resident memory and BIOS workspaces
    cpu.mem[RESIDENT_BASE:RESIDENT_BASE + len(resident)] = resident

    const_impl = cpu.word(BIOS_BASE + 2 * 3 + 1)
    platform_const = cpu.word(const_impl + 1)
    cpu.mem[platform_const:platform_const + 2] = bytes((0xAF, 0xC9))

    read_impl = cpu.word(BIOS_BASE + 13 * 3 + 1)
    calls = [address for address in range(read_impl, read_impl + 48)
             if cpu.mem[address] == 0xCD]
    require(len(calls) >= 2, "BIOS physical-read call was not found")
    platform_read = cpu.word(calls[1] + 1)
    read_success = bytes((
        0x78, 0xB7, 0x20, 0x07,
        0x79, 0xFE, 0x08, 0x30, 0x02,
        0x18, 0x05,
        0x21, DATA & 0xFF, DATA >> 8,
        0x18, 0x03,
        0x21, FIXTURE & 0xFF, FIXTURE >> 8,
        0x11, 0x00, 0xED,
        0x01, 0x00, 0x02,
        0xED, 0xB0, 0xAF, 0xC9,
    ))
    cpu.mem[platform_read:platform_read + len(read_success)] = read_success
    write_impl = cpu.word(BIOS_BASE + 14 * 3 + 1)
    write_jumps = [address for address in range(write_impl, write_impl + 90)
                   if cpu.mem[address] == 0xC3]
    require(write_jumps, "BIOS physical-write jump was not found")
    platform_write = cpu.word(write_jumps[-1] + 1)
    write_success = bytes((
        0x78, 0xB7, 0x20, 0x07,
        0x79, 0xFE, 0x08, 0x30, 0x02,
        0x18, 0x05,
        0x11, DATA & 0xFF, DATA >> 8,
        0x18, 0x03,
        0x11, FIXTURE & 0xFF, FIXTURE >> 8,
        0x21, 0x00, 0xED,
        0x01, 0x00, 0x02,
        0xED, 0xB0, 0xAF, 0xC9,
    ))
    cpu.mem[platform_write:platform_write + len(write_success)] = write_success

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
    cpu.mem[3] = 0xA5

    cpu.run(SYSTEM_INIT, limit=60000)
    require(cpu.a == 0, "resident initialization failed")
    require(bytes(cpu.mem[0:3]) == bytes((0xC3, 0x03, 0xEF)),
            "warm-boot page-zero vector is wrong")
    require(bytes(cpu.mem[5:8]) == bytes((0xC3, 0xFD, 0xBD)) and
            bytes(cpu.mem[DEFAULT_GATEWAY:HISTORY_BASE]) == bytes((0xC3, 0x00, 0xC1)),
            "BDOS page-zero vector is wrong")
    cpu.mem[CALLER:CALLER + 4] = bytes((0xCD, 0x05, 0x00, 0xC9))
    old_stack = bdos_symbol("BDOS_OLDSP")
    warm_vector = bytes(cpu.mem[BIOS_BASE + 3:BIOS_BASE + 6])
    cpu.mem[0x7060:0x706A] = bytes((0x3E, 0x5A, 0x32, 0x4F, 0x70,
                                    0xED, 0x7B, old_stack & 0xFF,
                                    old_stack >> 8, 0xC9))
    cpu.mem[BIOS_BASE + 3:BIOS_BASE + 6] = bytes((0xC3, 0x60, 0x70))
    cpu.mem[0x704F] = 0
    cpu.c = 0
    cpu.run(CALLER)
    require(cpu.mem[0x704F] == 0x5A,
            "CALL 0005h System Reset did not enter the BIOS WBOOT vector")
    cpu.mem[BIOS_BASE + 3:BIOS_BASE + 6] = warm_vector
    cpu.c = 7
    cpu.run(CALLER)
    require(cpu.a == cpu.l == 0xA5 and cpu.mem[3] == 0xA5,
            "CALL 0005h Get I/O Byte lost the page-zero value")
    cpu.c, cpu.e = 8, 0x5A
    cpu.run(CALLER)
    require(cpu.a == cpu.l == 0 and cpu.mem[3] == 0x5A,
            "CALL 0005h Set I/O Byte did not update page-zero address 0003h")
    cpu.c = 7
    cpu.run(CALLER)
    require(cpu.a == cpu.l == 0x5A,
            "CALL 0005h Get I/O Byte did not observe Set I/O Byte")
    conout_impl = cpu.word(BIOS_BASE + 4 * 3 + 1)
    platform_conout = cpu.word(conout_impl + 1)
    cpu.mem[platform_conout:platform_conout + 5] = bytes(
        (0x79, 0x32, 0x00, 0x70, 0xC9))
    cpu.mem[0x7040:0x7045] = b"A\tB$Z"
    cpu.mem[0x7000] = 0
    cpu.c, cpu.de = 9, 0x7040
    cpu.run(CALLER, limit=100000)
    require(cpu.a == cpu.l == 0 and cpu.mem[0x7000] == ord("B") and
            bytes(cpu.mem[0x7040:0x7045]) == b"A\tB$Z",
            "CALL 0005h Print String did not stop at dollar after cooked output")

    cpu.c = 11
    cpu.run(CALLER)
    require(cpu.a == 0, "CALL 0005h console status reported a false key")
    cpu.mem[platform_const:platform_const + 3] = bytes((0x3E, 0x01, 0xC9))
    cpu.c = 11
    cpu.run(CALLER)
    require(cpu.a == cpu.l == 0xFF,
            "CALL 0005h console status did not report a pending key")
    cpu.c = 11
    cpu.run(CALLER)
    require(cpu.a == 0xFF, "CALL 0005h console status consumed the key")
    cpu.mem[platform_const:platform_const + 2] = bytes((0xAF, 0xC9))

    conin_impl = cpu.word(BIOS_BASE + 3 * 3 + 1)
    platform_conin = cpu.word(conin_impl + 1)
    cpu.mem[platform_conin:platform_conin + 3] = bytes((0x3E, 0xC1, 0xC9))
    conout_impl = cpu.word(BIOS_BASE + 4 * 3 + 1)
    platform_conout = cpu.word(conout_impl + 1)
    cpu.mem[platform_conout:platform_conout + 5] = bytes(
        (0x79, 0x32, 0x00, 0x70, 0xC9))
    cpu.mem[0x7060:0x7069] = bytes((0x2A, 0x70, 0x70, 0x7E, 0x23,
                                    0x22, 0x70, 0x70, 0xC9))
    cpu.mem[0x7070:0x7072] = bytes((0x80, 0x70))
    cpu.mem[0x7080:0x7084] = b"ABC\r"
    cpu.mem[BIOS_BASE + 9:BIOS_BASE + 12] = bytes((0xC3, 0x60, 0x70))
    cpu.mem[0x7200:0x720A] = bytes((8, 0)) + bytes((0xCC,)) * 8
    cpu.c, cpu.de = 10, 0x7200
    cpu.run(CALLER, limit=100000)
    require(cpu.mem[0x7201] == 3 and bytes(cpu.mem[0x7202:0x7205]) == b"ABC",
            "CALL 0005h Read Console Buffer returned the wrong counted line")
    cpu.mem[BIOS_BASE + 9:BIOS_BASE + 12] = bytes((0xC3,
                                                  conin_impl & 0xFF,
                                                  conin_impl >> 8))
    cpu.mem[0x7000] = 0
    cpu.c, cpu.e = 6, 0xFF
    cpu.run(CALLER)
    require(cpu.a == 0 and cpu.mem[0x7000] == 0,
            "CALL 0005h Direct Console I/O empty poll failed")
    cpu.mem[platform_const:platform_const + 3] = bytes((0x3E, 0x01, 0xC9))
    cpu.c, cpu.e = 6, 0xFF
    cpu.run(CALLER)
    require(cpu.a == 0x41 and cpu.mem[0x7000] == 0,
            "CALL 0005h Direct Console I/O input echoed or retained parity")
    cpu.c, cpu.e = 6, 0xC2
    cpu.run(CALLER)
    require(cpu.a == 0 and cpu.mem[0x7000] == 0xC2,
            "CALL 0005h Direct Console I/O output changed the byte")
    cpu.mem[platform_const:platform_const + 2] = bytes((0xAF, 0xC9))

    cpu.mem[platform_conin:platform_conin + 3] = bytes((0x3E, 0x41, 0xC9))
    cpu.mem[0x7000] = 0
    cpu.c = 1
    cpu.run(CALLER)
    require(cpu.a == cpu.l == 0x41 and cpu.mem[0x7000] == 0x41,
            "CALL 0005h Console Input did not echo and return its character")
    cpu.mem[platform_conin:platform_conin + 3] = bytes((0x3E, 0x01, 0xC9))
    cpu.mem[0x7000] = 0
    cpu.c = 1
    cpu.run(CALLER)
    require(cpu.a == 1 and cpu.mem[0x7000] == 0,
            "CALL 0005h Console Input echoed an ordinary control byte")

    cpu.mem[platform_const:platform_const + 2] = bytes((0xAF, 0xC9))
    cpu.c, cpu.e = 2, 0x42
    cpu.run(CALLER)
    require(cpu.a == 0 and cpu.mem[0x7000] == 0x42,
            "CALL 0005h Console Output did not emit its character")
    cpu.mem[platform_const:platform_const + 3] = bytes((0x3E, 0x01, 0xC9))
    cpu.mem[platform_conin:platform_conin + 3] = bytes((0x3E, 0x4B, 0xC9))
    cpu.c, cpu.e = 2, 0x5A
    cpu.run(CALLER)
    cpu.mem[platform_const:platform_const + 2] = bytes((0xAF, 0xC9))
    cpu.c = 1
    cpu.run(CALLER)
    require(cpu.a == 0x4B and cpu.mem[0x7000] == 0x4B,
            "CALL 0005h did not retain output-polled ordinary input")

    reader_vector = bytes(cpu.mem[BIOS_BASE + 21:BIOS_BASE + 24])
    punch_vector = bytes(cpu.mem[BIOS_BASE + 18:BIOS_BASE + 21])
    list_vector = bytes(cpu.mem[BIOS_BASE + 15:BIOS_BASE + 18])
    cpu.mem[0x7040:0x7043] = bytes((0x3E, 0x5A, 0xC9))
    cpu.mem[BIOS_BASE + 21:BIOS_BASE + 24] = bytes((0xC3, 0x40, 0x70))
    cpu.c = 3
    cpu.run(CALLER)
    require(cpu.a == 0x5A, "CALL 0005h Reader Input missed the BIOS byte")
    cpu.mem[0x7040:0x7045] = bytes((0x79, 0x32, 0x48, 0x70, 0xC9))
    cpu.mem[BIOS_BASE + 18:BIOS_BASE + 21] = bytes((0xC3, 0x40, 0x70))
    cpu.mem[0x7048] = 0
    cpu.c, cpu.e = 4, 0xB3
    cpu.run(CALLER)
    require(cpu.mem[0x7048] == 0xB3, "CALL 0005h Punch Output changed its byte")
    cpu.mem[BIOS_BASE + 15:BIOS_BASE + 18] = bytes((0xC3, 0x40, 0x70))
    cpu.mem[0x7048] = 0
    cpu.c, cpu.e = 5, 0xC4
    cpu.run(CALLER)
    require(cpu.mem[0x7048] == 0xC4, "CALL 0005h List Output changed its byte")
    cpu.mem[BIOS_BASE + 21:BIOS_BASE + 24] = reader_vector
    cpu.mem[BIOS_BASE + 18:BIOS_BASE + 21] = punch_vector
    cpu.mem[BIOS_BASE + 15:BIOS_BASE + 18] = list_vector

    cpu.mem[FCB:FCB + 33] = bytes(33)
    cpu.mem[FCB + 1:FCB + 12] = b"GATEWAY DAT"
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
    cpu.mem[FCB + 33:FCB + 36] = bytes((1, 0, 0))
    cpu.c, cpu.de = 33, FCB
    cpu.run(CALLER, limit=100000)
    require(cpu.a == 0 and cpu.mem[FCB + 12] == 0 and
            cpu.mem[FCB + 14] == 0 and cpu.mem[FCB + 32] == 1 and
            bytes(cpu.mem[FCB + 33:FCB + 36]) == bytes((1, 0, 0)) and
            bytes(cpu.mem[0x7100:0x7180]) == bytes((0xA1,)) * 128,
            "CALL 0005h Read Random did not preserve CP/M FCB semantics")
    cpu.mem[0x7100:0x7180] = bytes((0xB6,)) * 128
    cpu.c, cpu.de = 34, FCB
    cpu.run(CALLER, limit=150000)
    require(cpu.a == 0 and cpu.mem[FCB + 32] == 1 and
            bytes(cpu.mem[FCB + 33:FCB + 36]) == bytes((1, 0, 0)) and
            bytes(cpu.mem[DATA + 128:DATA + 256]) == bytes((0xB6,)) * 128,
            "CALL 0005h Write Random did not preserve CP/M FCB semantics")
    cpu.mem[DATA + 128:DATA + 256] = bytes((0xA1,)) * 128
    zero_media = bytes(cpu.mem[FIXTURE:FIXTURE + 512])
    zero_data = bytes(cpu.mem[DATA:DATA + 512])
    cpu.mem[DATA:DATA + 512] = bytes((0xCC,)) * 512
    cpu.mem[0x7100:0x7180] = bytes((0xB8,)) * 128
    cpu.mem[FCB + 33:FCB + 36] = bytes((16, 0, 0))
    cpu.c, cpu.de = 40, FCB
    cpu.run(CALLER, limit=400000)
    require(cpu.a == 0 and cpu.mem[FCB + 32] == 16 and
            bytes(cpu.mem[DATA:DATA + 128]) == bytes((0xB8,)) * 128 and
            bytes(cpu.mem[DATA + 128:DATA + 512]) == bytes(384),
            f"CALL 0005h Write Random with Zero Fill failed: A={cpu.a:02X} "
            f"CR={cpu.mem[FCB + 32]:02X} data="
            f"{bytes(cpu.mem[DATA:DATA + 8]).hex()}")
    cpu.mem[FIXTURE:FIXTURE + 512] = zero_media
    cpu.mem[DATA:DATA + 512] = zero_data
    cpu.c = 13
    cpu.run(CALLER, limit=50000)
    cpu.mem[FCB:FCB + 36] = bytes(36)
    cpu.mem[FCB + 1:FCB + 12] = b"READ    DAT"
    cpu.c, cpu.de = 15, FCB
    cpu.run(CALLER, limit=50000)
    cpu.c, cpu.de = 26, 0x7100
    cpu.run(CALLER)
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
    warm_vector = bytes(cpu.mem[BIOS_BASE + 3:BIOS_BASE + 6])
    cpu.mem[0x7060:0x706A] = bytes((0x3E, 0x5A, 0x32, 0x4F, 0x70,
                                    0xED, 0x7B, old_stack & 0xFF,
                                    old_stack >> 8, 0xC9))
    cpu.mem[BIOS_BASE + 3:BIOS_BASE + 6] = bytes((0xC3, 0x60, 0x70))
    cpu.mem[0x704F] = 0
    cpu.c, cpu.de = 21, FCB
    cpu.run(CALLER, limit=50000)
    require(cpu.mem[0x704F] == 0x5A and
            bytes(cpu.mem[FCB:FCB + 33]) == protected_fcb,
            "CALL 0005h file protection did not take terminal WBOOT path")
    cpu.mem[BIOS_BASE + 3:BIOS_BASE + 6] = warm_vector
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
    cpu.run(CALLER, limit=50000)
    require(cpu.a == 0, "CALL 0005h could not select configured drive B")
    cpu.c = 25
    cpu.run(CALLER)
    require(cpu.a == 1, "CALL 0005h drive B selection was not persistent")
    cpu.c, cpu.e = 14, 0
    cpu.run(CALLER, limit=50000)
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
    require(cpu.hl == 3, "CALL 0005h login vector did not contain A and B")
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
    cpu.c, cpu.de = 37, 0x0002
    cpu.run(CALLER)
    cpu.c = 29
    cpu.run(CALLER)
    require(cpu.hl == 1, "CALL 0005h Reset Drive changed unselected A")
    cpu.c, cpu.de = 37, 0x0001
    cpu.run(CALLER)
    cpu.c = 24
    cpu.run(CALLER)
    require(cpu.a == 0 and cpu.hl == 0,
            "CALL 0005h Reset Drive did not remove A from the login vector")
    cpu.c = 29
    cpu.run(CALLER)
    require(cpu.hl == 0, "CALL 0005h Reset Drive left A write-protected")
    cpu.c = 25
    cpu.run(CALLER)
    require(cpu.a == 0, "CALL 0005h Reset Drive changed current drive A")
    cpu.c, cpu.e = 14, 0
    cpu.run(CALLER, limit=50000)
    cpu.c = 24
    cpu.run(CALLER)
    require(cpu.hl == 1, "CALL 0005h could not relog A after Reset Drive")
    cpu.mem[FCB:FCB + 36] = bytes(36)
    cpu.mem[FCB + 1:FCB + 12] = b"ABSENT  DAT"
    cpu.mem[FCB + 33:FCB + 36] = bytes((0xA5,)) * 3
    cpu.c, cpu.de = 35, FCB
    cpu.run(CALLER, limit=100000)
    require(cpu.a == 0xFF and
            bytes(cpu.mem[FCB + 33:FCB + 36]) == bytes((0xA5,)) * 3,
            "CALL 0005h missing Compute File Size changed R0-R2")
    cpu.mem[FCB + 12] = 2
    cpu.mem[FCB + 14] = 1
    cpu.mem[FCB + 32] = 5
    cpu.c, cpu.de = 36, FCB
    cpu.run(CALLER)
    require(bytes(cpu.mem[FCB + 33:FCB + 36]) == bytes((0x05, 0x11, 0x00)),
            "CALL 0005h Set Random Record returned the wrong position")
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
    failed.sp = 0xA800
    failed.mem[RESIDENT_BASE:RESIDENT_BASE + len(resident)] = resident
    failed_read = failed.word(calls[1] + 1)
    failed.mem[failed_read:failed_read + 4] = bytes((0x3E, 0x05, 0xB7, 0xC9))
    failed.run(SYSTEM_INIT, limit=5000)
    require(failed.a == 5 and bytes(failed.mem[0:8]) == bytes(8),
            "failed initialization published page-zero vectors")

    # Exercise the real WBOOT -> CCP path. WARM invokes Function 0, after which
    # the reconstructed CCP accepts VER and prints its version banner.
    cpu.mem[0x7060:0x7069] = bytes((0x2A, 0x80, 0x70, 0x7E, 0x23,
                                    0x22, 0x80, 0x70, 0xC9))
    # The enhanced CCP reads through nonblocking BDOS Function 6, which checks
    # CONST before consuming CONIN. This scripted fixture always has another
    # byte until its final intentional execution-limit wait.
    cpu.mem[0x7050:0x7053] = bytes((0x3E, 0xFF, 0xC9))
    cpu.mem[0x7070:0x7079] = bytes((0x2A, 0x90, 0x70, 0x71, 0x23,
                                    0x22, 0x90, 0x70, 0xC9))
    cpu.mem[0x7080:0x7082] = bytes((0x00, 0x71))
    cpu.mem[0x7090:0x7092] = bytes((0x00, 0x90))
    cpu.mem[0x7100:0x7109] = b"WARM\rVER\r"
    cpu.mem[BIOS_BASE + 6:BIOS_BASE + 9] = bytes((0xC3, 0x50, 0x70))
    cpu.mem[BIOS_BASE + 9:BIOS_BASE + 12] = bytes((0xC3, 0x60, 0x70))
    cpu.mem[BIOS_BASE + 12:BIOS_BASE + 15] = bytes((0xC3, 0x70, 0x70))
    # The platform reloader has its own raw-sector test. This resident-core
    # test bypasses only disk restoration so it can exercise portable WBOOT.
    ccp = CCP.read_bytes()
    allocation = (len(ccp) + 0xFF) & ~0xFF
    ccp_base = DEFAULT_GATEWAY - allocation
    ccp = relocated(CCP_MODULE.read_bytes(), ccp_base)
    cpu.mem[ccp_base:ccp_base + len(ccp)] = ccp
    cpu.mem[0xC08C:0xC08E] = ccp_base.to_bytes(2, "little")
    cpu.mem[0xC08E:0xC090] = allocation.to_bytes(2, "little")
    # This portable-core fixture intentionally exercises the no-CPX layout;
    # the platform reloader and production disk tests cover BASIC.CPX.  Keep
    # its saved reconstruction profile explicitly empty rather than allowing
    # the production default to interpret the fixture's dummy sectors.
    cpu.mem[0xC094] = 0
    cpu.mem[0xE900:0xE903] = bytes((0xC3, 0x23, 0xC0))
    cpu.c, cpu.de = 26, 0x7345
    cpu.run(CALLER)
    cpu.mem[0:8] = bytes((0xCC,)) * 8
    try:
        cpu.run(0xC023, limit=200000)
    except AssertionError as error:
        require("execution limit reached" in str(error),
                f"CCP execution failed unexpectedly: {error}")
    transcript = bytes(cpu.mem[0x9000:cpu.word(0x7090)])
    # Earlier BDOS coverage deliberately leaves user 31 selected. WBOOT must
    # preserve it, and the reconstructed CCP must derive that live state for
    # every prompt rather than silently reverting its display to user zero.
    require(transcript.count(b"A31>") >= 3 and b"BetterCP/M 0.3" in transcript,
            f"WBOOT/Function-0 CCP transcript is incomplete at PC={cpu.pc:04X}: "
            f"in={cpu.word(0x7080):04X} out={cpu.word(0x7090):04X} "
            f"ccp={bytes(cpu.mem[ccp_base:ccp_base + 0x2A]).hex()} {transcript[:160]!r}")
    require(bytes(cpu.mem[0:3]) == bytes((0xC3, 0x03, 0xEF)) and
            bytes(cpu.mem[5:8]) == bytes((0xC3, 0xFD, 0xBD)) and
            bytes(cpu.mem[DEFAULT_GATEWAY:HISTORY_BASE]) == bytes((0xC3, 0x00, 0xC1)) and
            cpu.word(bdos_symbol("BDOS_DMA")) == 0x0080,
            "WBOOT did not reconstruct gateways and default DMA state")
    require(bytes(cpu.mem[0xC080:0xC084]) == b"BM\x01\x00" and
            cpu.word(0xC084) == 0 and cpu.word(0xC086) == 0 and
            cpu.word(0xC088) == HISTORY_BASE and cpu.word(0xC08A) == DEFAULT_GATEWAY and
            cpu.word(0xC08C) == ccp_base and cpu.word(0xC08E) == allocation and
            cpu.word(0xC090) == DEFAULT_GATEWAY,
            "extension control block does not publish the default layout")

    print("resident initialization installed WBOOT and BDOS page-zero vectors")
    print("application CALL 0005h reached all 39 defined BDOS functions")
    print("WBOOT entered CCP; WARM returned through Function 0; VER responded")


if __name__ == "__main__":
    main()
