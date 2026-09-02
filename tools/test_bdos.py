#!/usr/bin/env python3
"""Execute the initial BDOS function dispatcher and function-15 boundary."""
from pathlib import Path
import re

from test_bios import BASE as BIOS_BASE, Z80, install_drive_tables, require

ROOT = Path(__file__).resolve().parents[1]
BIOS = ROOT / "build/bios/bios.bin"
DIRECTORY = ROOT / "build/bdos/directory.bin"
BDOS = ROOT / "build/bdos/bdos.bin"
BDOS_BASE = 0xC100
DIR_BASE = 0xD600
DIR_BUFFER = 0xF300
FIXTURE = 0x7500
FCB = 0x7700
DATA = 0x7900


def symbol(name: str) -> int:
    listing = (ROOT / "build/bdos/bdos.lst").read_text(encoding="ascii")
    matches = re.findall(rf"^([0-9a-f]{{4}})\s+.*\b{name}:?\s*$",
                         listing, re.MULTILINE | re.IGNORECASE)
    require(matches, f"BDOS listing lacks {name}")
    # The defining label follows its forward references in this source. Taking
    # the last exact-line match avoids mistaking `LD HL,SYMBOL` for the label.
    return int(matches[-1], 16)


def main() -> None:
    cpu = Z80(BIOS.read_bytes())
    install_drive_tables(cpu)
    cpu.sp = 0xBC00          # below resident memory and BIOS workspaces
    directory = DIRECTORY.read_bytes()
    bdos = BDOS.read_bytes()
    cpu.mem[DIR_BASE:DIR_BASE + len(directory)] = directory
    cpu.mem[BDOS_BASE:BDOS_BASE + len(bdos)] = bdos
    dma_state = symbol("BDOS_DMA")
    login_state = symbol("STATE_LV")
    readonly_state = symbol("STATE_RO")
    old_stack = symbol("BDOS_OLDSP")

    # WBOOT is intentionally non-returning in the provisional BIOS. Replace
    # only its vector during this unit test with an observable recovery shim.
    warm_vector = bytes(cpu.mem[BIOS_BASE + 3:BIOS_BASE + 6])
    cpu.mem[0x7060:0x706A] = bytes((
        0x3E, 0x5A,             # LD A,5Ah
        0x32, 0x4F, 0x70,       # LD (704Fh),A
        0xED, 0x7B, old_stack & 0xFF, old_stack >> 8,
        0xC9,                   # RET using the restored caller stack
    ))
    cpu.mem[BIOS_BASE + 3:BIOS_BASE + 6] = bytes((0xC3, 0x60, 0x70))
    cpu.mem[0x704F] = 0
    cpu.c = 0
    cpu.run(BDOS_BASE)
    require(cpu.mem[0x704F] == 0x5A,
            "System Reset did not transfer through the BIOS WBOOT vector")
    cpu.mem[BIOS_BASE + 3:BIOS_BASE + 6] = warm_vector

    const_impl = cpu.word(BIOS_BASE + 2 * 3 + 1)
    platform_const = cpu.word(const_impl + 1)
    cpu.mem[platform_const:platform_const + 2] = bytes((0xAF, 0xC9))
    cpu.c = 11
    cpu.run(BDOS_BASE)
    require(cpu.a == cpu.l == 0, "BDOS console status reported a false key")
    cpu.mem[platform_const:platform_const + 3] = bytes((0x3E, 0x01, 0xC9))
    cpu.c = 11
    cpu.run(BDOS_BASE)
    require(cpu.a == cpu.l == 0xFF,
            "BDOS console status did not normalize ready to FFh")
    cpu.c = 11
    cpu.run(BDOS_BASE)
    require(cpu.a == 0xFF, "BDOS console status consumed the pending key")
    cpu.mem[platform_const:platform_const + 2] = bytes((0xAF, 0xC9))

    conin_impl = cpu.word(BIOS_BASE + 3 * 3 + 1)
    platform_conin = cpu.word(conin_impl + 1)
    cpu.mem[platform_conin:platform_conin + 3] = bytes((0x3E, 0xC1, 0xC9))
    conout_impl = cpu.word(BIOS_BASE + 4 * 3 + 1)
    platform_conout = cpu.word(conout_impl + 1)
    cpu.mem[platform_conout:platform_conout + 5] = bytes(
        (0x79, 0x32, 0x00, 0x70, 0xC9))
    cpu.mem[0x7000] = 0
    cpu.c, cpu.e = 6, 0xFF
    cpu.run(BDOS_BASE)
    require(cpu.a == 0 and cpu.mem[0x7000] == 0,
            "Direct Console I/O empty poll blocked or produced output")
    cpu.mem[platform_const:platform_const + 3] = bytes((0x3E, 0x01, 0xC9))
    cpu.c, cpu.e = 6, 0xFF
    cpu.run(BDOS_BASE)
    require(cpu.a == cpu.l == 0x41 and cpu.mem[0x7000] == 0,
            "Direct Console I/O input was echoed or retained parity")
    cpu.c, cpu.e = 6, 0xC2
    cpu.run(BDOS_BASE)
    require(cpu.a == 0 and cpu.mem[0x7000] == 0xC2,
            "Direct Console I/O did not pass output byte unchanged")
    cpu.mem[platform_const:platform_const + 2] = bytes((0xAF, 0xC9))

    console_column = symbol("BDOS_COLUMN")
    cpu.mem[platform_conin:platform_conin + 3] = bytes((0x3E, 0x41, 0xC9))
    cpu.mem[0x7000] = 0
    cpu.c = 1
    cpu.run(BDOS_BASE)
    require(cpu.a == cpu.l == 0x41 and cpu.mem[0x7000] == 0x41 and
            cpu.mem[console_column] == 1,
            f"Console Input graphic failed: A={cpu.a:02X} L={cpu.l:02X} "
            f"out={cpu.mem[0x7000]:02X} col={cpu.mem[console_column]:02X}")
    cpu.mem[platform_conin:platform_conin + 3] = bytes((0x3E, 0x01, 0xC9))
    cpu.mem[0x7000] = 0
    cpu.c = 1
    cpu.run(BDOS_BASE)
    require(cpu.a == 1 and cpu.mem[0x7000] == 0 and
            cpu.mem[console_column] == 1,
            "Console Input echoed an ordinary control character")
    cpu.mem[platform_conin:platform_conin + 3] = bytes((0x3E, 0x09, 0xC9))
    cpu.c = 1
    cpu.run(BDOS_BASE, limit=100000)
    require(cpu.a == 9 and cpu.mem[0x7000] == 0x20 and
            cpu.mem[console_column] == 8,
            "Console Input did not expand tab to the next eight-column stop")
    cpu.mem[platform_conin:platform_conin + 3] = bytes((0x3E, 0x0D, 0xC9))
    cpu.c = 1
    cpu.run(BDOS_BASE)
    require(cpu.a == 13 and cpu.mem[console_column] == 0,
            "Console Input carriage return did not reset the column")

    cpu.mem[platform_const:platform_const + 2] = bytes((0xAF, 0xC9))
    cpu.mem[0x7000] = 0
    cpu.c, cpu.e = 2, 0x42
    cpu.run(BDOS_BASE)
    require(cpu.a == 0 and cpu.mem[0x7000] == 0x42 and
            cpu.mem[console_column] == 1,
            "Console Output did not emit and count a graphic character")
    cpu.c, cpu.e = 2, 9
    cpu.run(BDOS_BASE, limit=100000)
    require(cpu.mem[0x7000] == 0x20 and cpu.mem[console_column] == 8,
            "Console Output did not expand tab to column eight")
    cpu.mem[platform_const:platform_const + 3] = bytes((0x3E, 0x01, 0xC9))
    cpu.mem[platform_conin:platform_conin + 3] = bytes((0x3E, 0x4B, 0xC9))
    cpu.c, cpu.e = 2, 0x5A
    cpu.run(BDOS_BASE)
    cpu.c = 11
    cpu.run(BDOS_BASE)
    require(cpu.a == 0xFF and cpu.mem[0x7000] == 0x5A,
            "Console Output lost an ordinary key encountered while polling")
    cpu.mem[platform_const:platform_const + 2] = bytes((0xAF, 0xC9))
    cpu.c = 1
    cpu.run(BDOS_BASE)
    require(cpu.a == 0x4B and cpu.mem[0x7000] == 0x4B,
            "Console Input did not recover the output-poll lookahead key")

    reader_vector = bytes(cpu.mem[BIOS_BASE + 21:BIOS_BASE + 24])
    punch_vector = bytes(cpu.mem[BIOS_BASE + 18:BIOS_BASE + 21])
    list_vector = bytes(cpu.mem[BIOS_BASE + 15:BIOS_BASE + 18])
    cpu.mem[0x7040:0x7043] = bytes((0x3E, 0x5A, 0xC9))
    cpu.mem[BIOS_BASE + 21:BIOS_BASE + 24] = bytes((0xC3, 0x40, 0x70))
    cpu.c = 3
    cpu.run(BDOS_BASE)
    require(cpu.a == cpu.l == 0x5A, "Reader Input did not return the BIOS byte")
    cpu.mem[0x7040:0x7045] = bytes((0x79, 0x32, 0x48, 0x70, 0xC9))
    cpu.mem[0x7048] = 0
    cpu.mem[BIOS_BASE + 18:BIOS_BASE + 21] = bytes((0xC3, 0x40, 0x70))
    cpu.c, cpu.e = 4, 0xB3
    cpu.run(BDOS_BASE)
    require(cpu.a == 0 and cpu.mem[0x7048] == 0xB3,
            "Punch Output did not pass its byte to BIOS")
    cpu.mem[0x7048] = 0
    cpu.mem[BIOS_BASE + 15:BIOS_BASE + 18] = bytes((0xC3, 0x40, 0x70))
    cpu.c, cpu.e = 5, 0xC4
    cpu.run(BDOS_BASE)
    require(cpu.a == 0 and cpu.mem[0x7048] == 0xC4,
            "List Output did not pass its byte to BIOS")
    cpu.mem[BIOS_BASE + 21:BIOS_BASE + 24] = reader_vector
    cpu.mem[BIOS_BASE + 18:BIOS_BASE + 21] = punch_vector
    cpu.mem[BIOS_BASE + 15:BIOS_BASE + 18] = list_vector
    cpu.mem[3] = 0xA5
    cpu.c = 7
    cpu.run(BDOS_BASE)
    require(cpu.a == cpu.l == 0xA5 and cpu.mem[3] == 0xA5,
            "Get I/O Byte did not return page-zero address 0003h unchanged")
    cpu.c, cpu.e = 8, 0x5A
    cpu.run(BDOS_BASE)
    require(cpu.a == cpu.l == 0 and cpu.mem[3] == 0x5A,
            "Set I/O Byte did not update page-zero address 0003h")
    cpu.c = 7
    cpu.run(BDOS_BASE)
    require(cpu.a == cpu.l == 0x5A,
            "Get I/O Byte did not observe the value written by Set I/O Byte")
    cpu.mem[0x7050:0x7055] = b"A\tB$Z"
    cpu.mem[0x7000] = 0
    cpu.mem[console_column] = 0
    cpu.c, cpu.de = 9, 0x7050
    cpu.run(BDOS_BASE, limit=100000)
    require(cpu.a == cpu.l == 0 and cpu.mem[0x7000] == ord("B") and
            cpu.mem[console_column] == 9 and
            bytes(cpu.mem[0x7050:0x7055]) == b"A\tB$Z",
            f"Print String failed: A={cpu.a:02X} L={cpu.l:02X} "
            f"out={cpu.mem[0x7000]:02X} col={cpu.mem[console_column]:02X} "
            f"source={bytes(cpu.mem[0x7050:0x7055])!r}")

    # A tiny scripted CONIN implementation advances a pointer through input.
    cpu.mem[0x7060:0x706A] = bytes((
        0x2A, 0x70, 0x70,       # LD HL,(7070h)
        0x7E, 0x23,             # LD A,(HL); INC HL
        0x22, 0x70, 0x70,       # LD (7070h),HL
        0xC9, 0x00,
    ))
    cpu.mem[BIOS_BASE + 9:BIOS_BASE + 12] = bytes((0xC3, 0x60, 0x70))

    def read_line(script: bytes, maximum: int, address: int = 0x7200):
        queue = 0x8000
        cpu.mem[queue:queue + len(script)] = script
        cpu.mem[0x7070:0x7072] = bytes((queue & 0xFF, queue >> 8))
        cpu.mem[address:address + maximum + 2] = bytes((0xCC,)) * (maximum + 2)
        cpu.mem[address] = maximum
        cpu.c, cpu.de = 10, address
        cpu.run(BDOS_BASE, limit=500000)
        return bytes(cpu.mem[address + 2:address + 2 + cpu.mem[address + 1]])

    require(read_line(bytes((0xC1, ord("B"), 13)), 8) == b"AB",
            "Read Console Buffer did not mask, store, count, and CR-terminate")
    require(read_line(bytes((ord("A"), ord("B"), 8, ord("C"), 127,
                             ord("D"), 13)), 8) == b"AD",
            "Read Console Buffer backspace/DEL editing failed")
    require(read_line(bytes((ord("A"), 5, ord("B"), 18, ord("C"), 13)), 8)
            == b"ABC", "Read Console Buffer continuation/redisplay failed")
    require(read_line(bytes((ord("A"), ord("B"), 21, ord("C"), 13)), 8)
            == b"C", "Read Console Buffer Ctrl-U deletion failed")
    require(read_line(bytes((ord("A"), ord("B"), 24, ord("C"), 10)), 8)
            == b"C", "Read Console Buffer Ctrl-X/LF behavior failed")
    require(read_line(b"QZ", 1) == b"Q" and cpu.word(0x7070) == 0x8001,
            "Read Console Buffer capacity required an extra input byte")
    require(read_line(bytes((ord("X"),)) * 255, 255, 0x7200) ==
            bytes((ord("X"),)) * 255,
            "Read Console Buffer did not support the 255-byte maximum")
    cpu.mem[BIOS_BASE + 9:BIOS_BASE + 12] = bytes((0xC3,
                                                  conin_impl & 0xFF,
                                                  conin_impl >> 8))

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
    read_entry = FIXTURE + 96
    cpu.mem[read_entry:read_entry + 12] = bytes((0,)) + b"READ    DAT"
    cpu.mem[read_entry + 12:read_entry + 16] = bytes((0, 0, 0, 2))
    cpu.mem[read_entry + 16:read_entry + 32] = bytes((2, 0)) + bytes(14)
    cpu.mem[DATA:DATA + 128] = bytes((0xA0,)) * 128
    cpu.mem[DATA + 128:DATA + 256] = bytes((0xA1,)) * 128
    cpu.mem[DATA + 256:DATA + 512] = bytes((0xEE,)) * 256

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
    require(cpu.a == 1 and bytes(cpu.mem[FCB:FCB + 33]) == dirty_fcb and
            cpu.mem[entry + 15] == 2,
            "dirty Close did not commit RC while preserving the caller FCB")

    # Function 19 wildcard-deletes every matching extent and releases blocks
    # when the invalidated allocation vector is rebuilt.
    delete0 = FIXTURE + 128
    delete1 = FIXTURE + 160
    cpu.mem[delete0:delete0 + 32] = (bytes((0,)) + b"DELONE  DAT" +
                                     bytes((0, 0, 0, 1)) +
                                     bytes((5, 0)) + bytes(14))
    cpu.mem[delete1:delete1 + 32] = (bytes((0,)) + b"DELTWO  DAT" +
                                     bytes((1, 0, 0, 1)) +
                                     bytes((6, 0)) + bytes(14))
    cpu.run(DIR_BASE + 15)
    cpu.c = 13
    cpu.run(BDOS_BASE, limit=50000)
    cpu.mem[FCB:FCB + 33] = bytes(33)
    cpu.mem[FCB + 1:FCB + 12] = b"DEL?????DAT"
    cpu.c, cpu.de = 19, FCB
    cpu.run(BDOS_BASE, limit=200000)
    require(cpu.a == 0 and cpu.mem[delete0] == 0xE5 and
            cpu.mem[delete1] == 0xE5,
            "wildcard Delete did not remove every matching extent")
    cpu.c = 27
    cpu.run(BDOS_BASE, limit=100000)
    require(cpu.mem[cpu.hl] == 0xE0,
            "Delete did not release extent blocks during ALV reconstruction")

    # One read-only matching extent rejects the whole multi-extent operation.
    cpu.mem[delete0:delete0 + 32] = (bytes((0,)) + b"PROTECT DAT" +
                                     bytes((0, 0, 0, 1)) + bytes(16))
    cpu.mem[delete1:delete1 + 32] = (bytes((0,)) + b"PROTECT DAT" +
                                     bytes((1, 0, 0, 1)) + bytes(16))
    cpu.mem[delete1 + 9] |= 0x80
    cpu.run(DIR_BASE + 15)
    protected_extents = bytes(cpu.mem[delete0:delete1 + 32])
    cpu.mem[FCB:FCB + 33] = bytes(33)
    cpu.mem[FCB + 1:FCB + 12] = b"PROTECT DAT"
    cpu.c, cpu.de = 19, FCB
    cpu.run(BDOS_BASE, limit=200000)
    require(cpu.a == 0xFF and
            bytes(cpu.mem[delete0:delete1 + 32]) == protected_extents,
            "read-only preflight allowed partial multi-extent deletion")
    cpu.mem[delete0:delete1 + 32] = bytes((0xE5,)) * 64
    cpu.run(DIR_BASE + 15)

    # Function 35 returns the maximum S2:EX/RC boundary in 24-bit R0..R2.
    cpu.mem[delete0:delete0 + 32] = (bytes((0,)) + b"SIZE    DAT" +
                                     bytes((0, 0, 0, 128)) + bytes(16))
    cpu.mem[delete1:delete1 + 32] = (bytes((0,)) + b"SIZE    DAT" +
                                     bytes((2, 0, 0, 5)) + bytes(16))
    size2 = FIXTURE + 192
    cpu.mem[size2:size2 + 32] = (bytes((0,)) + b"SIZE    DAT" +
                                 bytes((0, 0, 1, 1)) + bytes(16))
    cpu.run(DIR_BASE + 15)
    cpu.mem[FCB:FCB + 36] = bytes(36)
    cpu.mem[FCB + 1:FCB + 12] = b"SIZE    DAT"
    cpu.c, cpu.de = 35, FCB
    cpu.run(BDOS_BASE, limit=200000)
    require(cpu.a == 0 and bytes(cpu.mem[FCB + 33:FCB + 36]) ==
            bytes((0x01, 0x10, 0x00)),
            f"Compute File Size result A={cpu.a:02X} "
            f"R={bytes(cpu.mem[FCB + 33:FCB + 36]).hex()}")
    cpu.mem[FCB + 1:FCB + 12] = b"ABSENT  DAT"
    cpu.mem[FCB + 33:FCB + 36] = bytes((0xA5,)) * 3
    cpu.c, cpu.de = 35, FCB
    cpu.run(BDOS_BASE, limit=200000)
    require(cpu.a == 0xFF and
            bytes(cpu.mem[FCB + 33:FCB + 36]) == bytes((0xA5,)) * 3,
            "missing Compute File Size changed the random-record field")

    # Function 36 converts the current sequential position without disk I/O.
    cpu.mem[FCB + 12] = 2
    cpu.mem[FCB + 14] = 1
    cpu.mem[FCB + 32] = 5
    sequential = bytes(cpu.mem[FCB + 12:FCB + 33])
    cpu.c, cpu.de = 36, FCB
    cpu.run(BDOS_BASE)
    require(cpu.a == 0 and bytes(cpu.mem[FCB + 33:FCB + 36]) ==
            bytes((0x05, 0x11, 0x00)) and
            bytes(cpu.mem[FCB + 12:FCB + 33]) == sequential,
            "Set Random Record mishandled S2=1 EX=2 CR=5")
    cpu.mem[FCB + 12] = 31
    cpu.mem[FCB + 14] = 0
    cpu.mem[FCB + 32] = 128
    cpu.c, cpu.de = 36, FCB
    cpu.run(BDOS_BASE)
    require(bytes(cpu.mem[FCB + 33:FCB + 36]) == bytes((0x00, 0x10, 0x00)),
            "Set Random Record mishandled the EX=31 CR=128 carry")
    # RANDTEST 0319: the last CP/M 2.2 record is S2=15, EX=31, CR=127.
    cpu.mem[FCB + 12] = 31
    cpu.mem[FCB + 14] = 15
    cpu.mem[FCB + 32] = 127
    cpu.c, cpu.de = 36, FCB
    cpu.run(BDOS_BASE)
    require(bytes(cpu.mem[FCB + 33:FCB + 36]) == bytes((0xFF, 0xFF, 0x00)),
            "Set Random Record mishandled CP/M 2.2 record 65535")
    cpu.mem[delete0:size2 + 32] = bytes((0xE5,)) * 96
    cpu.run(DIR_BASE + 15)

    # Function 30 applies and clears high attribute bits on wildcard matches.
    cpu.mem[delete0:delete0 + 32] = (bytes((0,)) + b"ATTRIB  DAT" +
                                     bytes((0, 0, 0, 1)) + bytes(16))
    cpu.mem[delete1:delete1 + 32] = (bytes((0,)) + b"ATTRIX  DAT" +
                                     bytes((1, 0, 0, 1)) + bytes(16))
    cpu.run(DIR_BASE + 15)
    cpu.mem[FCB:FCB + 33] = bytes(33)
    cpu.mem[FCB + 1:FCB + 12] = b"ATTRI?  DAT"
    cpu.mem[FCB + 2] |= 0x80
    cpu.mem[FCB + 9] |= 0x80
    cpu.mem[FCB + 10] |= 0x80
    cpu.c, cpu.de = 30, FCB
    cpu.run(BDOS_BASE, limit=200000)
    require(cpu.a == 0 and all(cpu.mem[base + 2] & 0x80 and
                               cpu.mem[base + 9] & 0x80 and
                               cpu.mem[base + 10] & 0x80 and
                               not (cpu.mem[base + 11] & 0x80)
                               for base in (delete0, delete1)) and
            bytes((value & 0x7F for value in
                   cpu.mem[delete0 + 1:delete0 + 12])) == b"ATTRIB  DAT" and
            bytes((value & 0x7F for value in
                   cpu.mem[delete1 + 1:delete1 + 12])) == b"ATTRIX  DAT",
            "Set Attributes did not preserve names and apply wildcard matches")
    for index in range(1, 12):
        cpu.mem[FCB + index] &= 0x7F
    cpu.c, cpu.de = 30, FCB
    cpu.run(BDOS_BASE, limit=200000)
    require(cpu.a == 0 and all(not (cpu.mem[base + index] & 0x80)
                               for base in (delete0, delete1)
                               for index in range(1, 12)),
            "Set Attributes could not clear existing attribute bits")
    cpu.mem[delete0:delete1 + 32] = bytes((0xE5,)) * 64
    cpu.run(DIR_BASE + 15)

    # Function 23 renames every exact-name extent while preserving attributes.
    cpu.mem[delete0:delete0 + 32] = (bytes((0,)) + b"OLDNAME DAT" +
                                     bytes((0, 0, 0, 1)) + bytes(16))
    cpu.mem[delete1:delete1 + 32] = (bytes((0,)) + b"OLDNAME DAT" +
                                     bytes((1, 0, 0, 1)) + bytes(16))
    cpu.mem[delete0 + 10] |= 0x80
    cpu.run(DIR_BASE + 15)
    cpu.mem[FCB:FCB + 33] = bytes(33)
    cpu.mem[FCB + 1:FCB + 12] = b"OLDNAME DAT"
    cpu.mem[FCB + 16] = 0
    cpu.mem[FCB + 17:FCB + 28] = b"NEWNAME DAT"
    cpu.c, cpu.de = 23, FCB
    cpu.run(BDOS_BASE, limit=200000)
    require(cpu.a == 0 and
            bytes(cpu.mem[delete0 + 1:delete0 + 12]) ==
            b"NEWNAME D" + bytes((ord('A') | 0x80,)) + b"T" and
            bytes(cpu.mem[delete1 + 1:delete1 + 12]) == b"NEWNAME DAT",
            "Rename did not update all extents while preserving attributes")

    # Existing target and a read-only source extent both reject before writes.
    cpu.mem[delete0:delete0 + 32] = (bytes((0,)) + b"SOURCE  DAT" +
                                     bytes((0, 0, 0, 1)) + bytes(16))
    cpu.mem[delete1:delete1 + 32] = (bytes((0,)) + b"TARGET  DAT" +
                                     bytes((0, 0, 0, 1)) + bytes(16))
    cpu.run(DIR_BASE + 15)
    rename_media = bytes(cpu.mem[FIXTURE:FIXTURE + 512])
    cpu.mem[FCB + 1:FCB + 12] = b"SOURCE  DAT"
    cpu.mem[FCB + 17:FCB + 28] = b"TARGET  DAT"
    cpu.c, cpu.de = 23, FCB
    cpu.run(BDOS_BASE, limit=200000)
    require(cpu.a == 0xFF and bytes(cpu.mem[FIXTURE:FIXTURE + 512]) == rename_media,
            "Rename overwrote an existing target")
    cpu.mem[delete1:delete1 + 32] = (bytes((0,)) + b"SOURCE  DAT" +
                                     bytes((1, 0, 0, 1)) + bytes(16))
    cpu.mem[delete1 + 9] |= 0x80
    cpu.run(DIR_BASE + 15)
    rename_media = bytes(cpu.mem[FIXTURE:FIXTURE + 512])
    cpu.mem[FCB + 17:FCB + 28] = b"RENAMED DAT"
    cpu.c, cpu.de = 23, FCB
    cpu.run(BDOS_BASE, limit=200000)
    require(cpu.a == 0xFF and bytes(cpu.mem[FIXTURE:FIXTURE + 512]) == rename_media,
            "read-only preflight allowed partial multi-extent Rename")
    cpu.mem[delete0:delete1 + 32] = bytes((0xE5,)) * 64
    cpu.run(DIR_BASE + 15)

    # Function 22 creates one canonical empty first extent and activates it.
    post_close_fcb = bytes(cpu.mem[FCB:FCB + 33])
    cpu.mem[FCB:FCB + 33] = bytes((0,)) + b"MAKE    DAT" + bytes((0xA5,)) * 21
    cpu.c, cpu.de = 22, FCB
    cpu.run(BDOS_BASE, limit=100000)
    require(cpu.a == 0 and bytes(cpu.mem[FCB + 12:FCB + 33]) == bytes(21) and
            bytes(cpu.mem[FIXTURE + 128:FIXTURE + 140]) ==
            bytes((0,)) + b"MAKE    DAT",
            f"BDOS Make result A={cpu.a:02X} "
            f"FCB={bytes(cpu.mem[FCB + 12:FCB + 33]).hex()} "
            f"DIR={bytes(cpu.mem[FIXTURE + 128:FIXTURE + 140]).hex()}")
    made_fcb = bytes(cpu.mem[FCB:FCB + 33])
    made_media = bytes(cpu.mem[FIXTURE:FIXTURE + 512])
    cpu.c, cpu.de = 22, FCB
    cpu.run(BDOS_BASE, limit=100000)
    require(cpu.a == 0xFF and bytes(cpu.mem[FCB:FCB + 33]) == made_fcb and
            bytes(cpu.mem[FIXTURE:FIXTURE + 512]) == made_media,
            "duplicate Make changed the FCB or directory")
    cpu.mem[FIXTURE + 128:FIXTURE + 160] = bytes((0xE5,)) * 32
    cpu.run(DIR_BASE + 15)       # isolate later wildcard fixtures from Make
    cpu.mem[FCB:FCB + 33] = post_close_fcb
    cpu.c = 28
    cpu.run(BDOS_BASE)
    cpu.mem[FCB + 15] = 3
    protected_fcb = bytes(cpu.mem[FCB:FCB + 33])
    protected_media = bytes(cpu.mem[FIXTURE:FIXTURE + 512])
    cpu.mem[FCB:FCB + 33] = bytes((0,)) + b"DENIED  DAT" + bytes(21)
    denied_fcb = bytes(cpu.mem[FCB:FCB + 33])
    cpu.c, cpu.de = 22, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0xFF and bytes(cpu.mem[FCB:FCB + 33]) == denied_fcb and
            bytes(cpu.mem[FIXTURE:FIXTURE + 512]) == protected_media,
            "software-protected Make changed the FCB or directory")
    cpu.mem[FCB:FCB + 33] = protected_fcb
    cpu.c, cpu.de = 16, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0xFF and bytes(cpu.mem[FCB:FCB + 33]) == protected_fcb and
            bytes(cpu.mem[FIXTURE:FIXTURE + 512]) == protected_media,
            "write-protected dirty Close changed FCB or media")
    cpu.c = 13
    cpu.run(BDOS_BASE, limit=50000)
    cpu.mem[FCB:FCB + 33] = opened_fcb
    cpu.mem[FCB + 15] = 2
    cpu.mem[FCB + 16] = 1
    unsupported_fcb = bytes(cpu.mem[FCB:FCB + 33])
    unsupported_media = bytes(cpu.mem[FIXTURE:FIXTURE + 512])
    cpu.c, cpu.de = 16, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0xFF and bytes(cpu.mem[FCB:FCB + 33]) == unsupported_fcb and
            bytes(cpu.mem[FIXTURE:FIXTURE + 512]) == unsupported_media,
            "Close accepted an allocation-map mutation it cannot validate")
    cpu.mem[FCB + 16] = 0
    cpu.mem[FCB + 15] = 3
    failed_fcb = bytes(cpu.mem[FCB:FCB + 33])
    failed_media = bytes(cpu.mem[FIXTURE:FIXTURE + 512])
    cpu.mem[platform_write:platform_write + 4] = bytes((0x3E, 0x06, 0xB7, 0xC9))
    cpu.c, cpu.de = 16, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0xFF and bytes(cpu.mem[FCB:FCB + 33]) == failed_fcb and
            bytes(cpu.mem[FIXTURE:FIXTURE + 512]) == failed_media,
            "failed dirty Close did not preserve caller and media fixtures")
    cpu.mem[platform_write:platform_write + len(write_success)] = write_success
    cpu.mem[FCB + 15] = 2

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
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0, "selecting configured drive B failed")
    cpu.c = 25
    cpu.run(BDOS_BASE)
    require(cpu.a == 1, "drive B selection did not change the current drive")
    cpu.c = 24
    cpu.run(BDOS_BASE)
    require(cpu.hl == 3 and cpu.a == 3 and cpu.b == 0,
            "login vector did not accumulate A and B")
    cpu.c, cpu.e = 14, 0
    cpu.run(BDOS_BASE, limit=50000)
    cpu.c, cpu.de = 26, 0x7345
    cpu.run(BDOS_BASE)
    require(cpu.word(dma_state) == 0x7345,
            "set-DMA state did not retain DE")
    cpu.c = 27
    cpu.run(BDOS_BASE)
    require(cpu.hl == expected_alv and cpu.mem[cpu.hl] == 0xE0,
            "allocation-vector pointer or fixture-owned block bits are wrong")
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
    cpu.mem[FCB:FCB + 33] = bytes(33)
    cpu.mem[FCB + 1:FCB + 12] = b"READ    DAT"
    cpu.c, cpu.de = 15, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 3 and cpu.mem[FCB + 15] == 2,
            "sequential-read fixture did not Open in slot 3")
    cpu.c, cpu.de = 26, 0x7100
    cpu.run(BDOS_BASE)
    cpu.c, cpu.de = 20, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0 and cpu.mem[FCB + 32] == 1 and
            bytes(cpu.mem[0x7100:0x7180]) == bytes((0xA0,)) * 128,
            "first sequential record or CR advancement is wrong")
    cpu.c, cpu.de = 26, 0x7180
    cpu.run(BDOS_BASE)
    cpu.c, cpu.de = 20, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0 and cpu.mem[FCB + 32] == 2 and
            bytes(cpu.mem[0x7180:0x7200]) == bytes((0xA1,)) * 128,
            "second sequential record or changed DMA transfer is wrong")
    cpu.c, cpu.de = 20, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a != 0 and cpu.mem[FCB + 32] == 2,
            "partial-final-extent EOF was not stable")
    cpu.c, cpu.de = 20, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a != 0, "repeated sequential EOF fabricated a record")

    # Function 33 decodes the CP/M 2.2 16-bit random-record field, activates
    # that extent, and leaves the sequential position at the record just read.
    cpu.mem[FCB + 33:FCB + 36] = bytes((1, 0, 0))
    cpu.mem[0x7200:0x7280] = bytes((0xCC,)) * 128
    cpu.c, cpu.de = 26, 0x7200
    cpu.run(BDOS_BASE)
    cpu.c, cpu.de = 33, FCB
    cpu.run(BDOS_BASE, limit=100000)
    require(cpu.a == 0 and cpu.mem[FCB + 12] == 0 and
            cpu.mem[FCB + 14] == 0 and cpu.mem[FCB + 32] == 1 and
            bytes(cpu.mem[FCB + 33:FCB + 36]) == bytes((1, 0, 0)) and
            bytes(cpu.mem[0x7200:0x7280]) == bytes((0xA1,)) * 128,
            "Read Random record 1 data, position, or R0-R2 is wrong")
    cpu.mem[FCB + 33:FCB + 36] = bytes((2, 0, 0))
    cpu.c, cpu.de = 33, FCB
    cpu.run(BDOS_BASE, limit=100000)
    require(cpu.a == 1 and cpu.mem[FCB + 32] == 2,
            "Read Random did not report unwritten data in an existing extent")
    cpu.mem[FCB + 33:FCB + 36] = bytes((0x80, 0, 0))
    cpu.c, cpu.de = 33, FCB
    cpu.run(BDOS_BASE, limit=100000)
    require(cpu.a == 4 and cpu.mem[FCB + 12] == 1 and
            cpu.mem[FCB + 32] == 0,
            "Read Random did not report an unwritten extent")
    cpu.mem[FCB + 33:FCB + 36] = bytes((0, 0, 1))
    stable_random_fcb = bytes(cpu.mem[FCB:FCB + 36])
    cpu.c, cpu.de = 33, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 6 and bytes(cpu.mem[FCB:FCB + 36]) == stable_random_fcb,
            "Read Random accepted nonzero R2 or changed the FCB")
    cpu.mem[FCB + 1] = ord('?')
    cpu.mem[FCB + 35] = 0
    cpu.c, cpu.de = 33, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 9, "Read Random accepted a wildcard FCB")

    # Function 34 writes both an allocated record and a newly created extent,
    # while preserving the random field and positioning sequential I/O on the
    # record just written.
    random_media = bytes(cpu.mem[FIXTURE:FIXTURE + 512])
    random_data = bytes(cpu.mem[DATA:DATA + 512])
    cpu.mem[FCB + 1:FCB + 12] = b"READ    DAT"
    cpu.mem[FCB + 33:FCB + 36] = bytes((1, 0, 0))
    cpu.mem[0x7000:0x7080] = bytes((0xB4,)) * 128
    cpu.c, cpu.de = 26, 0x7000
    cpu.run(BDOS_BASE)
    cpu.c, cpu.de = 34, FCB
    cpu.run(BDOS_BASE, limit=150000)
    require(cpu.a == 0 and cpu.mem[FCB + 12] == 0 and
            cpu.mem[FCB + 14] == 0 and cpu.mem[FCB + 32] == 1 and
            bytes(cpu.mem[FCB + 33:FCB + 36]) == bytes((1, 0, 0)) and
            bytes(cpu.mem[DATA + 128:DATA + 256]) == bytes((0xB4,)) * 128,
            "Write Random existing-record data or FCB semantics failed")
    cpu.mem[expected_alv:expected_alv + 50] = bytes((0xFF,)) * 50
    cpu.mem[FCB + 33:FCB + 36] = bytes((16, 0, 0))
    cpu.c, cpu.de = 34, FCB
    cpu.run(BDOS_BASE, limit=100000)
    require(cpu.a == 2, "Write Random did not distinguish data-block exhaustion")
    cpu.run(DIR_BASE + 15)
    cpu.c = 13
    cpu.run(BDOS_BASE, limit=50000)
    cpu.mem[FCB + 33:FCB + 36] = bytes((0x80, 0, 0))
    cpu.mem[0x7000:0x7080] = bytes((0xB5,)) * 128
    cpu.c, cpu.de = 34, FCB
    cpu.run(BDOS_BASE, limit=200000)
    require(cpu.a == 0 and cpu.mem[FCB + 12] == 1 and
            cpu.mem[FCB + 15] == 1 and cpu.mem[FCB + 32] == 0 and
            bytes(cpu.mem[FCB + 33:FCB + 36]) == bytes((0x80, 0, 0)),
            "Write Random did not create and write a missing extent")
    cpu.mem[FCB + 35] = 1
    stable_random_fcb = bytes(cpu.mem[FCB:FCB + 36])
    cpu.c, cpu.de = 34, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 6 and bytes(cpu.mem[FCB:FCB + 36]) == stable_random_fcb,
            "Write Random accepted nonzero R2 or changed the FCB")
    cpu.mem[FIXTURE:FIXTURE + 512] = random_media
    for offset in range(0, 512, 32):
        if cpu.mem[FIXTURE + offset] == 0xE5:
            cpu.mem[FIXTURE + offset:FIXTURE + offset + 32] = (
                bytes((0,)) + b"FULL    DAT" + bytes(20))
    cpu.run(DIR_BASE + 15)
    cpu.c = 13
    cpu.run(BDOS_BASE, limit=50000)

    cpu.mem[FCB + 1:FCB + 12] = b"READ    DAT"
    cpu.mem[FCB + 33:FCB + 36] = bytes((0x80, 0, 0))
    cpu.c, cpu.de = 34, FCB
    cpu.run(BDOS_BASE, limit=200000)
    require(cpu.a == 5,
            f"Write Random did not distinguish directory overflow: A={cpu.a:02X}")
    cpu.mem[FIXTURE:FIXTURE + 512] = random_media
    cpu.mem[DATA:DATA + 512] = random_data
    cpu.run(DIR_BASE + 15)
    cpu.c = 13
    cpu.run(BDOS_BASE, limit=50000)

    # Function 40 must clear every record of a newly allocated CP/M block
    # before installing the caller's record. Record 16 selects the empty
    # second allocation slot of READ.DAT's first extent.
    cpu.mem[DATA:DATA + 512] = bytes((0xCC,)) * 512
    cpu.mem[0x7000:0x7080] = bytes((0xB7,)) * 128
    cpu.mem[FCB + 1:FCB + 12] = b"READ    DAT"
    cpu.mem[FCB + 33:FCB + 36] = bytes((16, 0, 0))
    cpu.c, cpu.de = 26, 0x7000
    cpu.run(BDOS_BASE)
    cpu.c, cpu.de = 40, FCB
    cpu.run(BDOS_BASE, limit=400000)
    require(cpu.a == 0 and cpu.mem[FCB + 12] == 0 and
            cpu.mem[FCB + 32] == 16 and
            bytes(cpu.mem[FCB + 33:FCB + 36]) == bytes((16, 0, 0)) and
            bytes(cpu.mem[DATA:DATA + 128]) == bytes((0xB7,)) * 128 and
            bytes(cpu.mem[DATA + 128:DATA + 512]) == bytes(384),
            "Write Random with Zero Fill did not initialize the new block")
    cpu.mem[FIXTURE:FIXTURE + 512] = random_media
    cpu.mem[DATA:DATA + 512] = random_data
    cpu.run(DIR_BASE + 15)
    cpu.c = 13
    cpu.run(BDOS_BASE, limit=50000)

    # Reproduce ENTRYTST's exact Function 40 lifecycle: Make an empty file,
    # write record 2, then read zero-filled records 0 and 1 without Close.
    for cycle in range(2):
        cpu.mem[FCB:FCB + 36] = bytes(36)
        cpu.mem[FCB + 1:FCB + 12] = b"ENT40   $$$"
        cpu.c, cpu.de = 22, FCB
        cpu.run(BDOS_BASE, limit=100000)
        require(cpu.a != 0xFF, f"Function 40 fixture Make failed in cycle {cycle}")
        cpu.mem[0x7000:0x7080] = bytes((0xA5,)) * 128
        cpu.c, cpu.de = 26, 0x7000
        cpu.run(BDOS_BASE)
        cpu.mem[FCB + 33:FCB + 36] = bytes((2, 0, 0))
        cpu.c, cpu.de = 40, FCB
        cpu.run(BDOS_BASE, limit=400000)
        require(cpu.a == 0,
                f"Function 40 rejected record 2 in cycle {cycle}")
        for record, expected in ((0, bytes(128)), (1, bytes(128)),
                                 (2, bytes((0xA5,)) * 128)):
            cpu.mem[0x7180:0x7200] = bytes((0xCC,)) * 128
            cpu.c, cpu.de = 26, 0x7180
            cpu.run(BDOS_BASE)
            cpu.mem[FCB + 33:FCB + 36] = bytes((record, 0, 0))
            cpu.c, cpu.de = 33, FCB
            cpu.run(BDOS_BASE, limit=200000)
            require(cpu.a == 0 and bytes(cpu.mem[0x7180:0x7200]) == expected,
                    f"Function 40 cycle {cycle} failed record {record}")
        cpu.c, cpu.de = 19, FCB
        cpu.run(BDOS_BASE, limit=200000)
        require(cpu.a == 0,
                f"Delete did not retire Function 40 cycle {cycle} journal")
    cpu.mem[FIXTURE:FIXTURE + 512] = random_media
    cpu.mem[DATA:DATA + 512] = random_data
    cpu.run(DIR_BASE + 15)
    cpu.c = 13
    cpu.run(BDOS_BASE, limit=50000)

    cpu.mem[FCB + 1:FCB + 12] = b"READ    DAT"
    cpu.mem[FCB + 12] = cpu.mem[FCB + 14] = 0
    cpu.mem[FCB + 33:FCB + 36] = bytes(3)
    cpu.c, cpu.de = 26, 0x7180
    cpu.run(BDOS_BASE)
    cpu.mem[FIXTURE:FIXTURE + 12] = bytes((0,)) + b"READ    DAT"
    cpu.mem[FIXTURE + 12:FIXTURE + 16] = bytes((1, 0, 0, 1))
    cpu.mem[FIXTURE + 16:FIXTURE + 32] = bytes((2, 0)) + bytes(14)
    cpu.mem[FCB + 32] = 128
    cpu.c, cpu.de = 20, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0 and cpu.mem[FCB + 12] == 1 and
            cpu.mem[FCB + 32] == 1 and
            bytes(cpu.mem[0x7180:0x7200]) == bytes((0xA0,)) * 128,
            f"automatic sequential extent transition failed: A={cpu.a:02X} "
            f"EX={cpu.mem[FCB + 12]:02X} S2={cpu.mem[FCB + 14]:02X} "
            f"RC={cpu.mem[FCB + 15]:02X} CR={cpu.mem[FCB + 32]:02X}")

    # Return to extent zero and verify Function 21 through the BDOS boundary.
    cpu.mem[FCB + 12] = cpu.mem[FCB + 14] = cpu.mem[FCB + 32] = 0
    cpu.mem[FCB + 15] = 2
    cpu.mem[FCB + 16:FCB + 32] = bytes((2, 0)) + bytes(14)
    cpu.mem[0x7000:0x7080] = bytes((0xB0,)) * 128
    cpu.c, cpu.de = 26, 0x7000
    cpu.run(BDOS_BASE)
    cpu.c, cpu.de = 21, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0 and cpu.mem[FCB + 32] == 1 and
            cpu.mem[FCB + 15] == 2 and
            bytes(cpu.mem[DATA:DATA + 128]) == bytes((0xB0,)) * 128,
            "sequential overwrite or FCB position advancement failed")

    # An empty allocation entry receives the first genuinely free block.
    cpu.mem[FIXTURE:FIXTURE + 32] = bytes((0,)) + b"NEW     DAT" + bytes(20)
    cpu.run(DIR_BASE + 15)
    cpu.c = 13
    cpu.run(BDOS_BASE, limit=50000)
    cpu.mem[FCB:FCB + 33] = bytes(33)
    cpu.mem[FCB + 1:FCB + 12] = b"NEW     DAT"
    cpu.c, cpu.de = 15, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0, "empty sequential-write fixture did not Open")
    alv_before = bytes(cpu.mem[expected_alv:expected_alv + 50])
    cpu.mem[0x7000:0x7080] = bytes((0xB1,)) * 128
    cpu.c, cpu.de = 26, 0x7000
    cpu.run(BDOS_BASE)
    cpu.c, cpu.de = 21, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0 and cpu.mem[FCB + 16] == 3 and
            cpu.mem[FCB + 17] == 0 and cpu.mem[FCB + 15] == 1 and
            cpu.mem[FCB + 32] == 1 and
            cpu.mem[expected_alv] == (alv_before[0] | 0x10),
            "first sequential write did not allocate block 3 transactionally")
    require(bytes(cpu.mem[FIXTURE + 1:FIXTURE + 12]) == b"NEW     DAT",
            f"data write reached directory fixture: C={cpu.c:02X}")
    written_fcb = bytes(cpu.mem[FCB:FCB + 33])
    pending_media = bytes(cpu.mem[FIXTURE:FIXTURE + 512])
    cpu.mem[FCB:FCB + 33] = bytes(33)
    cpu.mem[FCB + 1:FCB + 12] = b"FIRST   DAT"
    cpu.c, cpu.de = 19, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0xFF and
            bytes(cpu.mem[FIXTURE:FIXTURE + 512]) == pending_media,
            "Delete invalidated a live pending-allocation journal")
    cpu.mem[FCB:FCB + 33] = written_fcb
    cpu.c, cpu.de = 16, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0 and bytes(cpu.mem[FCB:FCB + 33]) == written_fcb and
            cpu.mem[FIXTURE + 15] == 1 and
            bytes(cpu.mem[FIXTURE + 16:FIXTURE + 18]) == bytes((3, 0)),
            f"Close did not atomically commit trusted allocation: A={cpu.a:02X} "
            f"RC={cpu.mem[FIXTURE + 15]:02X} "
            f"AL={bytes(cpu.mem[FIXTURE + 16:FIXTURE + 18]).hex()}")

    # A full extent is closed, followed by creation and use of the next one.
    cpu.mem[FIXTURE:FIXTURE + 32] = (bytes((0,)) + b"CROSS   DAT" +
                                            bytes((0, 0, 0, 128)) +
                                            bytes((3, 0)) + bytes(14))
    cpu.mem[FIXTURE + 64:FIXTURE + 96] = bytes((0xE5,)) * 32
    cpu.run(DIR_BASE + 15)
    cpu.c = 13
    cpu.run(BDOS_BASE, limit=50000)
    cpu.mem[FCB:FCB + 33] = bytes(33)
    cpu.mem[FCB + 1:FCB + 12] = b"CROSS   DAT"
    cpu.mem[FCB + 32] = 128
    cpu.c, cpu.de = 15, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0 and cpu.mem[FCB + 15] == 128 and
            cpu.mem[FCB + 32] == 128, "full-extent fixture did not Open")
    cpu.mem[0x7000:0x7080] = bytes((0xB2,)) * 128
    cpu.c, cpu.de = 26, 0x7000
    cpu.run(BDOS_BASE)
    cpu.c, cpu.de = 21, FCB
    cpu.run(BDOS_BASE, limit=100000)
    require(cpu.a == 0 and cpu.mem[FCB + 12] == 1 and
            cpu.mem[FCB + 15] == 1 and cpu.mem[FCB + 32] == 1 and
            bytes(cpu.mem[FCB + 16:FCB + 18]) == bytes((4, 0)) and
            bytes(cpu.mem[FIXTURE + 65:FIXTURE + 76]) == b"CROSS   DAT" and
            cpu.mem[FIXTURE + 76] == 1 and cpu.mem[FIXTURE + 79] == 0,
            "Write Sequential did not create and enter the next extent")
    next_fcb = bytes(cpu.mem[FCB:FCB + 33])
    cpu.c, cpu.de = 16, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 2 and bytes(cpu.mem[FCB:FCB + 33]) == next_fcb and
            cpu.mem[FIXTURE + 79] == 1 and
            bytes(cpu.mem[FIXTURE + 80:FIXTURE + 82]) == bytes((4, 0)),
            "Close did not commit the automatically created extent")

    # With every repeated fixture slot occupied, transition reports directory
    # full and restores the stable completed-extent FCB.
    for offset in range(32, 512, 32):
        cpu.mem[FIXTURE + offset:FIXTURE + offset + 32] = (
            bytes((0,)) + b"FULL    DAT" + bytes((0, 0, 0, 1)) + bytes(16))
    cpu.run(DIR_BASE + 15)
    cpu.c = 13
    cpu.run(BDOS_BASE, limit=50000)
    cpu.mem[FCB:FCB + 33] = bytes(33)
    cpu.mem[FCB + 1:FCB + 12] = b"CROSS   DAT"
    cpu.mem[FCB + 32] = 128
    cpu.c, cpu.de = 15, FCB
    cpu.run(BDOS_BASE, limit=50000)
    full_fcb = bytes(cpu.mem[FCB:FCB + 33])
    full_media = bytes(cpu.mem[FIXTURE:FIXTURE + 512])
    cpu.c, cpu.de = 21, FCB
    cpu.run(BDOS_BASE, limit=200000)
    require(cpu.a == 1 and bytes(cpu.mem[FCB:FCB + 33]) == full_fcb and
            bytes(cpu.mem[FIXTURE:FIXTURE + 512]) == full_media,
            f"directory-full transition state: A={cpu.a:02X} "
            f"EX={cpu.mem[FCB + 12]:02X} RC={cpu.mem[FCB + 15]:02X} "
            f"CR={cpu.mem[FCB + 32]:02X}")
    cpu.mem[FCB:FCB + 33] = bytes((0,)) + b"NOSPACE DAT" + bytes((0xA5,)) * 21
    make_full_fcb = bytes(cpu.mem[FCB:FCB + 33])
    cpu.c, cpu.de = 22, FCB
    cpu.run(BDOS_BASE, limit=200000)
    require(cpu.a == 0xFF and bytes(cpu.mem[FCB:FCB + 33]) == make_full_fcb,
            "directory-full Make did not restore the caller FCB")

    # Software and FCB attribute protection must precede all mutation.
    cpu.c = 28
    cpu.run(BDOS_BASE)
    protected_fcb = bytes(cpu.mem[FCB:FCB + 33])
    protected_alv = bytes(cpu.mem[expected_alv:expected_alv + 50])
    protected_data = bytes(cpu.mem[DATA:DATA + 512])
    cpu.c, cpu.de = 21, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0xFF and bytes(cpu.mem[FCB:FCB + 33]) == protected_fcb and
            bytes(cpu.mem[expected_alv:expected_alv + 50]) == protected_alv and
            bytes(cpu.mem[DATA:DATA + 512]) == protected_data,
            "software-protected sequential write changed state")
    cpu.c = 13
    cpu.run(BDOS_BASE, limit=50000)
    cpu.mem[FCB + 9] |= 0x80
    protected_fcb = bytes(cpu.mem[FCB:FCB + 33])
    # File R/O is a terminal CP/M path, not an FFh-returning call. Replace
    # WBOOT with the same observable recovery shim used for Function 0.
    warm_vector = bytes(cpu.mem[BIOS_BASE + 3:BIOS_BASE + 6])
    cpu.mem[0x7060:0x706A] = bytes((
        0x3E, 0x5A, 0x32, 0x4F, 0x70,
        0xED, 0x7B, old_stack & 0xFF, old_stack >> 8, 0xC9,
    ))
    cpu.mem[BIOS_BASE + 3:BIOS_BASE + 6] = bytes((0xC3, 0x60, 0x70))
    cpu.mem[0x704F] = 0
    cpu.c, cpu.de = 21, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.mem[0x704F] == 0x5A and
            bytes(cpu.mem[FCB:FCB + 33]) == protected_fcb,
            "file read-only attribute did not take terminal WBOOT path")
    cpu.mem[BIOS_BASE + 3:BIOS_BASE + 6] = warm_vector
    cpu.mem[FCB + 9] &= 0x7F

    # A failed BIOS write cannot publish a newly selected block or position.
    cpu.mem[FCB + 15:FCB + 33] = bytes(18)
    failed_fcb = bytes(cpu.mem[FCB:FCB + 33])
    failed_alv = bytes(cpu.mem[expected_alv:expected_alv + 50])
    cpu.mem[platform_write:platform_write + 4] = bytes((0x3E, 0x06, 0xB7, 0xC9))
    cpu.c, cpu.de = 21, FCB
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0xFF and bytes(cpu.mem[FCB:FCB + 33]) == failed_fcb and
            bytes(cpu.mem[expected_alv:expected_alv + 50]) == failed_alv,
            "failed sequential write published allocation or FCB metadata")
    cpu.mem[platform_write:platform_write + len(write_success)] = write_success
    cpu.c, cpu.e = 32, 0x25
    cpu.run(BDOS_BASE)
    cpu.c, cpu.e = 32, 0xFF
    cpu.run(BDOS_BASE)
    require(cpu.a == cpu.l == 5 and cpu.word(dma_state) == 0x0080,
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
    cpu.c, cpu.de = 37, 0x0002
    cpu.run(BDOS_BASE)
    require(cpu.a == 0 and cpu.word(login_state) == 1 and
            cpu.word(readonly_state) == 1,
            "Reset Drive changed A for an unsupported-drive-only mask")
    cpu.c, cpu.de = 37, 0x0001
    cpu.run(BDOS_BASE)
    require(cpu.a == 0 and cpu.word(login_state) == 0 and
            cpu.word(readonly_state) == 0,
            "Reset Drive did not log off and make drive A read/write")
    cpu.c = 25
    cpu.run(BDOS_BASE)
    require(cpu.a == 0, "Reset Drive changed the current drive")
    cpu.c, cpu.e = 14, 0
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0 and cpu.word(login_state) == 1,
            "drive A did not rebuild cleanly after selective reset")
    cpu.c = 13
    cpu.run(BDOS_BASE, limit=50000)
    require(cpu.a == 0 and cpu.word(dma_state) == 0x0080 and
            cpu.word(login_state) == 1 and cpu.word(readonly_state) == 0,
            "disk reset did not restore DMA, drive A, login, and protection")
    cpu.c, cpu.e = 32, 0xFF
    cpu.run(BDOS_BASE)
    require(cpu.a == 5, "disk reset did not preserve current user")
    cpu.c = 41
    cpu.run(BDOS_BASE)
    require(cpu.a == cpu.l == 0 and cpu.b == cpu.h == 0,
            "unsupported BDOS selector did not return conventional zero")

    # BetterCP/M's provisional Function 200 owns active CPX-profile mutation.
    cpu.mem[0xC094], cpu.mem[0xC096] = 1, 4
    cpu.c, cpu.e = 200, 0
    cpu.run(BDOS_BASE)
    require(cpu.a == 1, "CPX control did not report BASIC.CPX loaded")
    cpu.c, cpu.e = 200, 2
    cpu.run(BDOS_BASE)
    require(cpu.a == 0 and cpu.mem[0xC094] == 0,
            "CPX control did not unload the active BASIC profile")
    cpu.c, cpu.e = 200, 1
    cpu.run(BDOS_BASE)
    require(cpu.a == 0 and cpu.mem[0xC094] == 1 and cpu.mem[0xC096] == 4,
            "CPX control did not restore the active BASIC profile")
    cpu.c, cpu.e = 200, 3
    cpu.run(BDOS_BASE)
    require(cpu.a == 0xFF, "CPX control accepted an unknown operation")

    cpu.run(DIR_BASE + 15)       # invalidate, forcing storage on next Open
    cpu.mem[platform_read:platform_read + 4] = bytes((0x3E, 0x05, 0xB7, 0xC9))
    cpu.c, cpu.e = 14, 0
    cpu.run(BDOS_BASE, limit=5000)
    require(cpu.a == 0xFF, "drive login storage failure was not reported")
    cpu.c = 25
    cpu.run(BDOS_BASE)
    require(cpu.a == 0, "failed drive-A relogin changed current-drive state")
    cpu.c, cpu.de = 20, FCB
    cpu.run(BDOS_BASE, limit=5000)
    require(cpu.a == 0xFF,
            "sequential-read storage failure was confused with ordinary EOF")
    cpu.mem[FCB + 1:FCB + 12] = b"OPEN    DAT"
    cpu.c, cpu.de = 15, FCB
    cpu.run(BDOS_BASE, limit=5000)
    require(cpu.a == 0xFF and cpu.l == 0xFF,
            f"provisional BDOS storage failure was confused with slot success: "
            f"A={cpu.a:02X} L={cpu.l:02X}")

    print("all 39 defined CP/M 2.2 BDOS functions passed")
    print("state persistence, aliases, stack, Open, and failure paths passed")


if __name__ == "__main__":
    main()
