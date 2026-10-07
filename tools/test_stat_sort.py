#!/usr/bin/env python3
"""Execute STAT sorting and verify complete summaries retain their metadata."""
import re
import subprocess
from test_bios import Z80
from test_z80pack_submit_xsub import ROOT


def main():
    subprocess.run(['python3', str(ROOT / 'tools/build_stat.py')], check=True)
    listing = (ROOT / 'build/utilities/stat.lst').read_text()
    def address(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b' + name + ':', listing, re.M | re.I)[1], 16)
    binary = (ROOT / 'build/utilities/STAT.COM').read_bytes()
    cases = [[], [b'ONE     DAT'],
             [b'ZETA    TXT', b'ALPHA   DAT', b'ALPHA   COM', b'BETA    DAT'],
             [f'F{i:07}DAT'.encode() for i in reversed(range(257))]]
    for names in cases:
        records = []
        for i, name in enumerate(names):
            record = bytearray(name)
            # Attribute bits must neither change ordering nor get separated.
            record[8] |= 0x80 if i % 2 else 0
            record[9] |= 0x80 if i % 3 else 0
            record += bytes((i & 255, i >> 8, (i + 1) & 255, 2, (i + 2) & 255))
            records.append(bytes(record))
        cpu = Z80(b'')
        cpu.mem[0x100:0x100 + len(binary)] = binary
        start = address('SUMMARY')
        cpu.mem[start:start + len(records) * 16] = b''.join(records)
        cpu.setword(address('SUMCOUNT'), len(records))
        cpu.run(address('SORTFILES'), limit=10000000)
        expected = sorted(records, key=lambda row: bytes(value & 0x7f for value in row[:11]))
        assert cpu.mem[start:start + len(records) * 16] == b''.join(expected), len(records)
    print('STAT empty/single, name/type ordering, attribute-bit masking and 257-record metadata sorting passed')


if __name__ == '__main__':
    main()
