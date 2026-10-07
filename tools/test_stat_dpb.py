#!/usr/bin/env python3
"""Execute STAT's DPB capacity calculation, including word carry."""
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
    for dsm, shift, expected in [(165, 4, 2656), (165, 1, 332),
                                 (399, 4, 6400), (399, 1, 800),
                                 (4095, 5, 131072), (65535, 0, 65536)]:
        cpu = Z80(b'')
        cpu.mem[0x100:0x100 + len(binary)] = binary
        cpu.setword(address('DPB'), 0x8000)
        cpu.setword(0x8005, dsm)
        cpu.a = shift
        cpu.run(address('CAPVALUE'), limit=10000)
        start = address('SIZEVAL')
        actual = int.from_bytes(cpu.mem[start:start + 3], 'little')
        assert actual == expected, (dsm, shift, actual)
    print('STAT 332K/800K DPB capacities and 16-bit carry boundaries passed')


if __name__ == '__main__':
    main()
