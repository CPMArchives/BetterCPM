#!/usr/bin/env python3
"""Execute the initial directory reader against the real BIOS vectors."""
from pathlib import Path

from test_bios import BASE as BIOS_BASE, Z80, install_drive_tables, require

ROOT = Path(__file__).resolve().parents[1]
BIOS = ROOT / "build/bios/bios.bin"
DIRECTORY = ROOT / "build/bdos/directory.bin"
DIR_BASE = 0xD600
DIR_BUFFER = 0xD500
FIXTURE = 0x7500
QUERY = 0x7600
FCB = 0x7700


def main() -> None:
    cpu = Z80(BIOS.read_bytes())
    install_drive_tables(cpu)
    cpu.sp = 0xBC00          # below resident memory and BIOS workspaces
    component = DIRECTORY.read_bytes()
    cpu.mem[DIR_BASE:DIR_BASE + len(component)] = component

    # Replace the physical reader below the assembled production BIOS. This
    # retains the real BIOS state, mapping, 512-byte transfer, and DMA copy.
    read_impl = cpu.word(BIOS_BASE + 13 * 3 + 1)
    read_calls = [address for address in range(read_impl, read_impl + 48)
                  if cpu.mem[address] == 0xCD]
    require(len(read_calls) >= 2, "BIOS physical-read call was not found")
    platform_read = cpu.word(read_calls[1] + 1)
    read_success = bytes((
        0xF5,
        0x3A, 0x03, 0x73,                         # count physical reads
        0x3C,
        0x32, 0x03, 0x73,
        0xF1,
        0x32, 0x00, 0x73,                         # cylinder
        0x78, 0x32, 0x01, 0x73,                   # side
        0x79, 0x32, 0x02, 0x73,                   # sector ID
        0x21, FIXTURE & 0xFF, FIXTURE >> 8,        # LD HL,FIXTURE
        0x11, 0x00, 0xED,                          # LD DE,physical scratch
        0x01, 0x00, 0x02,                          # LD BC,512
        0xED, 0xB0, 0xAF, 0xC9,                    # LDIR / success
    ))
    cpu.mem[platform_read:platform_read + len(read_success)] = read_success

    cpu.c = 0
    cpu.run(BIOS_BASE + 9 * 3)
    dph = cpu.hl
    dpb = cpu.word(dph + 10)
    alv = cpu.word(dph + 14)
    cpu.mem[alv:alv + 50] = bytes((0xA5,)) * 50

    # Login reconstructs live 16-bit blocks. Duplicate block 5 is idempotent;
    # impossible blocks in deleted/metadata entries must be ignored.
    cpu.mem[FIXTURE:FIXTURE + 512] = bytes((0xE5,)) * 512
    cpu.mem[FIXTURE] = 3
    cpu.mem[FIXTURE + 16:FIXTURE + 32] = bytes(16)
    cpu.mem[FIXTURE + 16:FIXTURE + 22] = bytes((5, 0, 1, 1, 5, 0))
    cpu.mem[FIXTURE + 32] = 0x21
    cpu.mem[FIXTURE + 48:FIXTURE + 50] = bytes((0xFF, 0xFF))
    cpu.mem[FIXTURE + 80:FIXTURE + 82] = bytes((0xFF, 0xFF))
    cpu.c = 0
    cpu.run(DIR_BASE + 12, limit=50000)
    require(cpu.a == 0 and cpu.mem[0x7303] == 32,
            f"drive login scan failed: A={cpu.a:02X} reads={cpu.mem[0x7303]}")
    require(cpu.mem[alv] == 0xC4 and cpu.mem[alv + 32] == 0x40,
            "live 16-bit allocation blocks were not reconstructed")
    require(cpu.mem[alv + 1:alv + 32] == bytes(31) and
            cpu.mem[alv + 33:alv + 50] == bytes(17),
            "allocation scan marked an unexpected block")

    # Empty CP/M record: four deleted entries and no match.
    cpu.mem[FIXTURE:FIXTURE + 512] = bytes((0xE5,)) * 512
    cpu.mem[0x7303] = 0
    cpu.run(DIR_BASE, limit=2000)
    require(cpu.a == 0 and cpu.hl == DIR_BUFFER,
            f"directory record did not load: A={cpu.a:02X} HL={cpu.hl:04X}")
    require(bytes(cpu.mem[0x7300:0x7303]) == bytes((2, 0, 1)),
            "directory reader did not map track 2, sector 0 correctly")
    cpu.run(DIR_BASE + 3)
    require(cpu.a == 0xFF, "empty directory produced an ordinary entry")

    # Reserved metadata in slot zero must be skipped; slot two is user 7.
    cpu.mem[FIXTURE:FIXTURE + 512] = bytes((0xE5,)) * 512
    cpu.mem[FIXTURE] = 0x21
    cpu.mem[FIXTURE + 64:FIXTURE + 76] = bytes((7,)) + b"TEST    COM"
    cpu.run(DIR_BASE + 3)
    require(cpu.a == 0 and cpu.hl == DIR_BUFFER + 64,
            "first ordinary directory entry was not selected")
    require(cpu.mem[cpu.hl] == 7 and bytes(cpu.mem[cpu.hl + 1:cpu.hl + 12]) == b"TEST    COM",
            "directory entry fields were not preserved")

    # Exact search masks CP/M attribute bits but requires both user and name.
    cpu.mem[FIXTURE + 65] |= 0x80
    cpu.mem[FIXTURE + 72] |= 0x80
    cpu.mem[QUERY:QUERY + 11] = b"TEST    COM"
    cpu.a, cpu.de = 7, QUERY
    cpu.run(DIR_BASE + 9, limit=20000)
    require(cpu.a == 0 and cpu.hl == DIR_BUFFER + 64,
            "exact user/name search did not find the entry")

    cpu.mem[0x7303] = 0
    cpu.mem[QUERY:QUERY + 11] = b"OTHER   COM"
    cpu.a, cpu.de = 7, QUERY
    cpu.run(DIR_BASE + 9, limit=20000)
    require(cpu.a == 0xFF, "nonmatching name was falsely found")
    require(cpu.mem[0x7303] == 32, "search did not examine all 32 directory records")
    require(bytes(cpu.mem[0x7300:0x7303]) == bytes((2, 0, 6)),
            "last directory record mapped to the wrong physical sector")

    cpu.mem[QUERY:QUERY + 11] = b"TEST    COM"
    cpu.a, cpu.de = 6, QUERY
    cpu.run(DIR_BASE + 9, limit=20000)
    require(cpu.a == 0xFF, "wrong user number was falsely matched")

    # Read-only FCB Open selects the requested EX/S2 extent, activates bytes
    # 1..31 from its directory entry, and preserves drive and caller CR.
    cpu.mem[FIXTURE + 76:FIXTURE + 80] = bytes((3, 0x55, 2, 0x22))
    cpu.mem[FIXTURE + 80:FIXTURE + 96] = bytes(range(1, 17))
    cpu.mem[FCB:FCB + 33] = bytes((0xA5,)) * 33
    cpu.mem[FCB] = 0
    cpu.mem[FCB + 1:FCB + 12] = b"TEST    COM"
    cpu.mem[FCB + 12] = 3
    cpu.mem[FCB + 14] = 2
    cpu.mem[FCB + 32] = 9
    cpu.a, cpu.de = 7, FCB
    cpu.run(DIR_BASE + 18, limit=20000)
    require(cpu.a == 2, "FCB Open did not return directory slot 2")
    require(cpu.mem[FCB] == 0 and cpu.mem[FCB + 32] == 9,
            "FCB Open changed the drive byte or caller CR")
    require(cpu.mem[FCB + 1:FCB + 32] == cpu.mem[FIXTURE + 65:FIXTURE + 96],
            "FCB Open did not activate directory bytes 1..31")

    cpu.mem[FIXTURE + 79] = 129
    cpu.a, cpu.de = 7, FCB
    cpu.run(DIR_BASE + 18, limit=30000)
    require(cpu.a == 0xFF, "FCB Open accepted an impossible RC value")
    cpu.mem[FIXTURE + 79] = 0x22

    cpu.mem[FCB:FCB + 33] = bytes((0xA5,)) * 33
    cpu.mem[FCB] = 0
    cpu.mem[FCB + 1:FCB + 12] = b"TEST    COM"
    cpu.mem[FCB + 12] = 4
    cpu.mem[FCB + 14] = 2
    cpu.mem[FCB + 32] = 11
    unopened = bytes(cpu.mem[FCB:FCB + 33])
    cpu.a, cpu.de = 7, FCB
    cpu.run(DIR_BASE + 18, limit=30000)
    require(cpu.a == 0xFF, "FCB Open accepted the wrong extent")
    require(cpu.mem[FCB:FCB + 33] == unopened,
            "failed exact FCB Open modified the caller FCB")

    cpu.mem[FCB:FCB + 33] = bytes(33)
    cpu.mem[FCB + 1:FCB + 12] = b"TE?T    ?OM"
    cpu.mem[FCB + 12] = 3
    cpu.mem[FCB + 14] = 2
    cpu.a, cpu.de = 7, FCB
    cpu.run(DIR_BASE + 18, limit=20000)
    require(cpu.a == 2 and bytes(cpu.mem[FCB + 1:FCB + 12]) ==
            bytes(cpu.mem[FIXTURE + 65:FIXTURE + 76]),
            "wildcard FCB Open did not activate the matching real identity")

    # EXM=3 groups four logical extents in one directory entry. Directory EX=3
    # means requested EX 0..2 are full (RC=128), while EX=3 uses stored RC.
    cpu.mem[FIXTURE:FIXTURE + 512] = bytes((0xE5,)) * 512
    for offset, name, rc in ((0, b"ALPHA   TXT", 10),
                             (32, b"APPLE   TXT", 11),
                             (64, b"GROUP   DAT", 37)):
        cpu.mem[FIXTURE + offset:FIXTURE + offset + 12] = bytes((4,)) + name
        cpu.mem[FIXTURE + offset + 12:FIXTURE + offset + 16] = bytes((3, 0, 1, rc))
        cpu.mem[FIXTURE + offset + 16:FIXTURE + offset + 32] = bytes(16)
    cpu.mem[dpb + 4] = 3
    cpu.run(DIR_BASE + 15)
    cpu.c = 0
    cpu.run(DIR_BASE + 12, limit=50000)
    require(cpu.a == 0, "EXM=3 drive login failed")

    cpu.mem[FCB:FCB + 33] = bytes(33)
    cpu.mem[FCB + 1:FCB + 12] = b"A???????TXT"
    cpu.mem[FCB + 12] = 3
    cpu.mem[FCB + 14] = 1
    cpu.a, cpu.de = 4, FCB
    cpu.run(DIR_BASE + 18, limit=20000)
    require(cpu.a == 0 and bytes(cpu.mem[FCB + 1:FCB + 12]) == b"ALPHA   TXT",
            "wildcard Open did not activate the first matching entry")

    for requested, expected_rc in ((1, 128), (3, 37)):
        cpu.mem[FCB:FCB + 33] = bytes(33)
        cpu.mem[FCB + 1:FCB + 12] = b"GROUP   DAT"
        cpu.mem[FCB + 12] = requested
        cpu.mem[FCB + 14] = 1
        cpu.mem[FCB + 32] = 7
        cpu.a, cpu.de = 4, FCB
        cpu.run(DIR_BASE + 18, limit=20000)
        require(cpu.a == 2 and cpu.mem[FCB + 12] == requested and
                cpu.mem[FCB + 15] == expected_rc and cpu.mem[FCB + 32] == 7,
                f"EXM grouped Open returned wrong state for EX={requested}")

    cpu.mem[FCB:FCB + 33] = bytes(33)
    cpu.mem[FCB + 1:FCB + 12] = b"GROUP   DAT"
    cpu.mem[FCB + 12] = 4
    cpu.mem[FCB + 14] = 1
    cpu.a, cpu.de = 4, FCB
    cpu.run(DIR_BASE + 18, limit=30000)
    require(cpu.a == 0xFF, "EXM grouped Open crossed into the wrong group")

    # Invalidation forces a fresh DPH/DPB login. Altered test DPB values prove
    # that directory bounds and OFF are derived state rather than constants.
    cpu.mem[FIXTURE:FIXTURE + 512] = bytes((0xE5,)) * 512
    cpu.run(DIR_BASE + 15)
    cpu.mem[dpb + 4] = 0
    cpu.setword(dpb + 5, 127)    # small DPB: sixteen 8-bit block slots
    cpu.setword(dpb + 7, 7)      # DRM=7: eight entries, two records
    cpu.setword(dpb + 13, 3)     # directory begins at logical track 3
    cpu.mem[FIXTURE] = 2
    cpu.mem[FIXTURE + 16:FIXTURE + 32] = bytes((5,)) + bytes(15)
    cpu.c = 0
    cpu.run(DIR_BASE + 12, limit=2000)
    require(cpu.a == 0, "explicit drive re-login failed")
    require(cpu.mem[alv] == 0xC4,
            "8-bit allocation entries were not reconstructed")
    cpu.mem[0x7303] = 0
    cpu.mem[QUERY:QUERY + 11] = b"ABSENT  COM"
    cpu.a, cpu.de = 7, QUERY
    cpu.run(DIR_BASE + 9, limit=5000)
    require(cpu.a == 0xFF and cpu.mem[0x7303] == 2,
            "search did not use the reloaded DRM-derived bound")
    require(bytes(cpu.mem[0x7300:0x7303]) == bytes((3, 0, 1)),
            "directory reader did not use the reloaded DPB OFF value")

    cpu.mem[FIXTURE:FIXTURE + 512] = bytes((0xE5,)) * 512
    cpu.mem[FIXTURE] = 1
    cpu.mem[FIXTURE + 16:FIXTURE + 18] = bytes((0xFF, 0xFF))
    cpu.run(DIR_BASE + 15)
    cpu.c = 0
    cpu.run(DIR_BASE + 12, limit=5000)
    require(cpu.a == 1, "out-of-range live allocation block did not fail login")

    cpu.mem[FIXTURE:FIXTURE + 512] = bytes((0xE5,)) * 512
    cpu.mem[platform_read:platform_read + 4] = bytes((0x3E, 0x05, 0xB7, 0xC9))
    cpu.run(DIR_BASE, limit=2000)
    require(cpu.a == 5, "directory reader did not propagate the BIOS error")

    print("DPH/DPB login and complete allocation reconstruction passed")
    print("all 128 directory entries searched through BIOS")
    print("EXM-grouped and wildcard-first FCB Open activation passed")
    print("invalidation, exact user/8.3 matching, and attribute masking passed")


if __name__ == "__main__":
    main()
