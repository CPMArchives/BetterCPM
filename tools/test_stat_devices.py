#!/usr/bin/env python3
"""Execute assembled STAT device matching, bit updates and assignment lists."""
import re
import subprocess
import tempfile
from pathlib import Path
from build_ccp import assemble
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
    source = '''        ORG 7000H
        LD A,C
        CP 2
        JR Z,CHAR
        CP 9
        RET NZ
STRING: LD A,(DE)
        CP '$'
        RET Z
        CALL PUT
        INC DE
        JR STRING
CHAR:   LD A,E
PUT:    PUSH HL
        LD HL,(7F00H)
        LD (HL),A
        INC HL
        LD (7F00H),HL
        POP HL
        RET
        END
'''
    with tempfile.TemporaryDirectory() as folder:
        folder = Path(folder)
        stub = assemble(Path.home() / 'bin/z80asm', source, folder / 'query.bin', folder / 'query.lst', 0x7000)
    for initial in range(256):
        cpu = cpu_for('')
        cpu.mem[3] = initial
        for device, (_, values) in enumerate(MATRIX):
            cpu.mem[address('DEVNO')] = device
            cpu.run(address('DEVTARGET'), limit=10000)
            assert cpu.mem[cpu.hl:cpu.hl + 4].decode() == values[(initial >> (2 * device)) & 3]
    targets = sorted({value for _, values in MATRIX for value in values})
    for initial in (0, 0x95, 0x55, 0xff):
        for target in targets:
            cpu = cpu_for(target + '  ')
            cpu.mem[3] = initial
            cpu.mem[0x7000:0x7000 + len(stub)] = stub
            cpu.mem[5:8] = bytes((0xc3, 0, 0x70))
            cpu.setword(0x7f00, 0x8000)
            cpu.run(address('DEVICEQUERY'), limit=30000)
            matches = [name for device, (name, values) in enumerate(MATRIX)
                       if values[(initial >> (2 * device)) & 3] == target]
            expected = ''.join('\r\n' + target + ' assigned to ' + name for name in matches)
            if not matches:
                expected = '\r\n' + target + ' not assigned'
            expected += '\r\n'
            actual = cpu.mem[0x8000:cpu.word(0x7f00)].decode()
            assert cpu.carry and actual == expected, (initial, target, actual, expected)
            assert cpu.mem[3] == initial
    for text in ('B:', 'B31:*.COM', 'C7:FOO.DAT', '31:*.COM', 'FOO.DAT',
                 'CON:=CRT:', 'CON: = CRT: RDR:=PTR:'):
        cpu = cpu_for(text)
        cpu.run(address('DEVICEQUERY'), limit=10000)
        assert not cpu.carry and cpu.hl == 0x9000 and cpu.b == len(text), text
    for text, message in [('XYZ:', 'Unknown device target'),
                          ('PTP:X', 'Invalid STAT command'),
                          ('CRT: EXTRA', 'Invalid STAT command')]:
        cpu = cpu_for(text)
        cpu.mem[3] = 0x95
        cpu.mem[0x7000:0x7000 + len(stub)] = stub
        cpu.mem[5:8] = bytes((0xc3, 0, 0x70))
        cpu.setword(0x7f00, 0x8000)
        cpu.run(address('DEVICEQUERY'), limit=30000)
        assert cpu.carry and message in cpu.mem[0x8000:cpu.word(0x7f00)].decode(), text
        assert cpu.mem[3] == 0x95
    print('STAT all 16 device values, unrelated-bit preservation and assignment lists passed')
    print('STAT inverse queries, all 256 IOBYTE decodes, shared/unused targets and DU passthrough passed')


if __name__ == '__main__':
    main()
