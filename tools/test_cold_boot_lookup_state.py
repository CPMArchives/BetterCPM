#!/usr/bin/env python3
"""Execute both disk cold loaders with poisoned interrupted-lookup state."""
import argparse
import re
from pathlib import Path

from test_bios import SENTINEL, Z80, require
from system_layout import LAYOUT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--z80pack-build', type=Path, required=True)
    parser.add_argument('--model4-build', type=Path, required=True)
    args = parser.parse_args()
    boot = (args.z80pack_build / 'boot.bin').read_bytes()
    require(len(boot) == 128, 'cpmsim first-record budget changed')
    for poison in (1, 0xA5, 0xFF):
        cpu = Z80(b'')
        cpu.mem[:] = bytes((poison,)) * 65536
        cpu.mem[:128] = boot
        # 0048h contains live bootstrap code until the last read completes.
        # Do not poison it separately: this is the real overlap that caused A32.
        cpu.mem[LAYOUT['BIOS']:LAYOUT['BIOS'] + 3] = bytes((0xC3, 0xFF, 0xFF))
        reads = []
        ports = {}

        def output(port, data):
            port &= 0xFF
            ports[port] = data
            if port == 13:
                require(data == 0, 'bootstrap requested a write')
                address = ports[15] | ports[16] << 8
                reads.append((ports[11], ports[12], address))

        cpu.port_write = output
        cpu.port_read = lambda port: 0
        cpu.run(0, limit=10000)
        require(cpu.pc == SENTINEL and cpu.mem[0x48] == 0,
                'cpmsim cold loader left lookup recovery active')
        require(len(reads) == 52 and
                [r[2] for r in reads] == [LAYOUT['SYSTEM'] + i * 128 for i in range(52)],
                'bootstrap did not read all 52 resident records in order')
        # Mapping bytes are emitted at the end of the first record. Compare
        # every physical request, including track crossing after record 35.
        mapping = boot[-36:]
        expected = [(record // 36, mapping[record % 36] + 1)
                    for record in range(8, 60)]
        require([(track, sector) for track, sector, _ in reads] == expected,
                'bootstrap zero-register optimization changed physical mapping')

    stage = (args.model4_build / 'stage1.bin').read_bytes()
    listing = (args.model4_build / 'stage1.lst').read_text()
    match = re.search(r'^([0-9a-fA-F]{4})\s+.*\bM4_READ:', listing, re.M)
    require(match is not None, 'Model 4 read entry absent from listing')
    read_entry = int(match.group(1), 16)
    for poison in (1, 0xA5, 0xFF):
        cpu = Z80(b'')
        cpu.mem[:] = bytes((poison,)) * 65536
        cpu.mem[0x5000:0x5000 + len(stage)] = stage
        # Controlled physical transport: advance one sector and return success.
        # The real cold-loader instructions and loop still execute unchanged.
        cpu.mem[read_entry:read_entry + 7] = b'\x11\x00\x02\x19\xaf\xc9\x00'
        cpu.mem[LAYOUT['BIOS']:LAYOUT['BIOS'] + 3] = b'\xc3\xff\xff'
        cpu.run(0x5000, limit=10000)
        require(cpu.mem[0x48] == 0 and cpu.mem[0x46] == poison,
                'Model 4 cold loader failed to invalidate poisoned lookup state')
    print('PASS: both emitted cold loaders clear lookup recovery for three RAM patterns; cpmsim reads all 52 mapped records and fits 128 bytes')


if __name__ == '__main__':
    main()
