#!/usr/bin/env python3
"""Execute the initial directory reader against the real BIOS vectors."""
from pathlib import Path

from test_bios import BASE as BIOS_BASE, Z80, require

ROOT = Path(__file__).resolve().parents[1]
BIOS = ROOT / "build/bios/bios.bin"
DIRECTORY = ROOT / "build/bdos/directory.bin"
DIR_BASE = 0xE800
DIR_BUFFER = 0xE900
FIXTURE = 0x7500


def main() -> None:
    cpu = Z80(BIOS.read_bytes())
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
        0x32, 0x00, 0x73,                         # cylinder
        0x78, 0x32, 0x01, 0x73,                   # side
        0x79, 0x32, 0x02, 0x73,                   # sector ID
        0x21, FIXTURE & 0xFF, FIXTURE >> 8,        # LD HL,FIXTURE
        0x11, 0x00, 0xEE,                          # LD DE,physical scratch
        0x01, 0x00, 0x02,                          # LD BC,512
        0xED, 0xB0, 0xAF, 0xC9,                    # LDIR / success
    ))
    cpu.mem[platform_read:platform_read + len(read_success)] = read_success

    # Empty CP/M record: four deleted entries and no match.
    cpu.mem[FIXTURE:FIXTURE + 128] = bytes((0xE5,)) * 128
    cpu.run(DIR_BASE)
    require(cpu.a == 0 and cpu.hl == DIR_BUFFER, "directory record did not load")
    require(bytes(cpu.mem[0x7300:0x7303]) == bytes((2, 0, 1)),
            "directory reader did not map track 2, sector 0 correctly")
    cpu.run(DIR_BASE + 3)
    require(cpu.a == 0xFF, "empty directory produced an ordinary entry")

    # Reserved metadata in slot zero must be skipped; slot two is user 7.
    cpu.mem[FIXTURE:FIXTURE + 128] = bytes((0xE5,)) * 128
    cpu.mem[FIXTURE] = 0x21
    cpu.mem[FIXTURE + 64:FIXTURE + 76] = bytes((7,)) + b"TEST    COM"
    cpu.run(DIR_BASE + 3)
    require(cpu.a == 0 and cpu.hl == DIR_BUFFER + 64,
            "first ordinary directory entry was not selected")
    require(cpu.mem[cpu.hl] == 7 and bytes(cpu.mem[cpu.hl + 1:cpu.hl + 12]) == b"TEST    COM",
            "directory entry fields were not preserved")

    cpu.mem[platform_read:platform_read + 4] = bytes((0x3E, 0x05, 0xB7, 0xC9))
    cpu.run(DIR_BASE)
    require(cpu.a == 5, "directory reader did not propagate the BIOS error")

    print("first directory record loaded through BIOS")
    print("deleted, reserved-metadata, and ordinary entries classified")


if __name__ == "__main__":
    main()
