#!/usr/bin/env python3
"""Execute STAT's update path with controlled public BDOS results."""
import re
import subprocess
import tempfile
from pathlib import Path
from build_ccp import assemble
from test_bios import Z80
from test_z80pack_submit_xsub import ROOT

STUB = '''        ORG 7000H
        LD A,C
        CP 29
        JR Z,ROVEC
        CP 25
        JR Z,DRIVE
        CP 30
        JR Z,ATTR
        CP 9
        RET NZ
        LD (7200H),DE
        RET
ROVEC:  LD HL,(7202H)
        RET
DRIVE:  LD A,1
        RET
ATTR:   LD HL,7204H
        INC (HL)
        LD A,(7205H)
        RET
        END
'''


def main():
    subprocess.run(['python3', str(ROOT / 'tools/build_stat.py')], check=True)
    listing = (ROOT / 'build/utilities/stat.lst').read_text()
    def address(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b' + name + ':', listing, re.M | re.I)[1], 16)
    with tempfile.TemporaryDirectory() as folder:
        folder = Path(folder)
        stub = assemble(Path.home() / 'bin/z80asm', STUB, folder / 'stub.bin', folder / 'stub.lst', 0x7000)
    binary = (ROOT / 'build/utilities/STAT.COM').read_bytes()
    for readonly, status, expected, calls in [
        (0, 255, 'MATTRFAIL', 1), (2, 0, 'MATTRRO', 0),
        (0, 0, 'MRO', 1), (0, 1, 'MRO', 1), (0, 2, 'MRO', 1), (0, 3, 'MRO', 1),
    ]:
        cpu = Z80(b'')
        cpu.mem[0x100:0x100 + len(binary)] = binary
        cpu.mem[0x7000:0x7000 + len(stub)] = stub
        cpu.mem[5:8] = bytes((0xc3, 0, 0x70))
        cpu.setword(0x7202, readonly)
        cpu.mem[0x7205] = status
        summary = address('SUMMARY')
        cpu.mem[summary:summary + 11] = b'TARGET  DAT'
        cpu.setword(address('SUMCUR'), summary)
        cpu.mem[address('OPTION')] = 1
        cpu.run(address('SETATTR'), limit=20000)
        assert cpu.word(0x7200) == address(expected), (readonly, status)
        assert cpu.mem[0x7204] == calls, (readonly, status)
    print('STAT attribute success, returned failure and read-only preflight passed')


if __name__ == '__main__':
    main()
