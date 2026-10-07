#!/usr/bin/env python3
"""Execute assembled STAT device matching, bit updates and assignment lists."""
import re
import subprocess
from test_bios import Z80
from test_z80pack_submit_xsub import ROOT

MATRIX = [('CON:', ['TTY:', 'CRT:', 'BAT:', 'UC1:']),
          ('RDR:', ['TTY:', 'PTR:', 'UR1:', 'UR2:']),
          ('PUN:', ['TTY:', 'PTP:', 'UP1:', 'UP2:']),
          ('LST:', ['TTY:', 'CRT:', 'LPT:', 'UL1:'])]


def main():
    subprocess.run(['python3', str(ROOT / 'tools/build_stat.py')], check=True)
    listing = (ROOT / 'build/utilities/stat.lst').read_text()
    def address(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b' + name + ':', listing, re.M | re.I)[1], 16)
    binary = (ROOT / 'build/utilities/STAT.COM').read_bytes()
    def cpu_for(text):
        cpu = Z80(b'')
        cpu.mem[0x100:0x100 + len(binary)] = binary
        cpu.mem[0x9000:0x9000 + len(text)] = text.encode()
        cpu.hl, cpu.b = 0x9000, len(text)
        return cpu
    for device, (_, values) in enumerate(MATRIX):
        for selection, value in enumerate(values):
            cpu = cpu_for(value)
            cpu.mem[address('DEVNO')] = device
            cpu.run(address('DEVVALUE'), limit=10000)
            assert not cpu.carry and cpu.a == selection, (device, value)
            assert cpu.b == 0 and cpu.hl == 0x9004
            for initial in [0, 0x95, 0xff]:
                cpu.a = selection
                cpu.mem[3] = initial
                # BDOS Function 8 stores E; other calls simply return.
                cpu.mem[5:8] = bytes((0xc3, 0, 0x70))
                cpu.mem[0x7000:0x700b] = bytes.fromhex('79 fe 08 c0 7b 32 03 00 c9 00 00')
                cpu.run(address('SETIO'), limit=10000)
                expected = (initial & ~(3 << (device * 2))) | selection << (device * 2)
                assert cpu.mem[3] == expected, (device, value, initial)
        for value in ['CRT:X', 'TTY:EXTRA', 'TTY:CON:=CRT:', 'XXX:', 'TTY', '']:
            cpu = cpu_for(value)
            cpu.mem[address('DEVNO')] = device
            cpu.run(address('DEVVALUE'), limit=10000)
            assert cpu.carry, (device, value)
    for text, expected in [
        ('CON:=CRT: RDR:=PTR: PUN:=PTP: LST:=LPT:', 0x95),
        ('CON: = UC1:   RDR:=UR2: PUN:=UP2: LST:=UL1:  ', 0xff),
        ('CON:=BAT: CON:=TTY:', 0),
    ]:
        cpu = cpu_for(text)
        cpu.mem[5:8] = bytes((0xc3, 0, 0x70))
        cpu.mem[0x7000:0x7009] = bytes.fromhex('79 fe 08 c0 7b 32 03 00 c9')
        cpu.run(address('DEVICEASSIGN'), limit=30000)
        assert cpu.carry and cpu.mem[3] == expected, text
    print('STAT all 16 device values, unrelated-bit preservation and assignment lists passed')


if __name__ == '__main__':
    main()
