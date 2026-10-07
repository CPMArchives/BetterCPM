#!/usr/bin/env python3
"""Execute STAT's full-width logical record-count formatting."""
import re
import subprocess
import tempfile
from pathlib import Path
from build_ccp import assemble
from test_bios import Z80
from test_z80pack_submit_xsub import ROOT


def main():
    subprocess.run(['python3', str(ROOT / 'tools/build_stat.py')], check=True)
    listing = (ROOT / 'build/utilities/stat.lst').read_text()
    def address(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b' + name + ':', listing, re.M | re.I)[1], 16)
    source = '''        ORG 7000H
        LD HL,(7200H)
        LD (HL),E
        INC HL
        LD (7200H),HL
        RET
        END
'''
    with tempfile.TemporaryDirectory() as name:
        work = Path(name)
        stub = assemble(Path.home() / 'bin/z80asm', source, work / 'stub.bin', work / 'stub.lst', 0x7000)
    binary = (ROOT / 'build/utilities/STAT.COM').read_bytes()
    for value in [0, 1, 161, 513, 65535, 65536, 262144, 1000000, 16777215]:
        cpu = Z80(b'')
        cpu.mem[0x100:0x100 + len(binary)] = binary
        cpu.mem[5:8] = bytes((0xc3, 0, 0x70))
        cpu.mem[0x7000:0x7000 + len(stub)] = stub
        cpu.setword(0x7200, 0x7300)
        start = address('SIZEVAL')
        cpu.mem[start:start + 3] = value.to_bytes(3, 'little')
        cpu.run(address('P24'), limit=20000)
        actual = cpu.mem[0x7300:cpu.word(0x7200)].decode()
        assert actual == str(value).zfill(5), (value, actual)
    print('STAT logical-size formatting preserves all 24 bits, including 65536 records')


if __name__ == '__main__':
    main()
