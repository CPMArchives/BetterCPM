#!/usr/bin/env python3
"""Execute COPY's exact-filespec validator in CPX and transient builds."""
import re
from pathlib import Path
from test_bios import Z80
from test_disk_utilities import ROOT


def main():
    valid = ['A', 'FILE', 'FILE.', 'FILE.COM', 'ABCDEFGH.COM', '12345678.123']
    invalid = ['', '.COM', 'ABCDEFGHI.COM', 'FILE.ABCD', 'FILE..COM',
               'F*X.DAT', 'F?.DAT', 'FILE:COM', 'FILE=COM', 'FILE COM',
               'FILE.COM EXTRA', 'FILE.\x01', 'FILE.\x7f']
    for binary_path, listing_path, origin in [
            ('build/cpx/rcp.bin', 'build/cpx/rcp.lst', 0x8000),
            ('build/utilities/COPY.COM', 'build/utilities/rcp-transient.lst', 0x100)]:
        binary = (ROOT / binary_path).read_bytes()
        listing = (ROOT / listing_path).read_text()
        entry = int(re.search(r'^([0-9a-f]{4})\s+.*?\bBC_CVALID:', listing, re.M | re.I)[1], 16)
        for text in valid + invalid:
            cpu = Z80(b'')
            cpu.mem[origin:origin + len(binary)] = binary
            cpu.mem[0x7000:0x7000 + len(text)] = text.encode('ascii')
            cpu.hl, cpu.b = 0x7000, len(text)
            before = bytes(cpu.mem)
            cpu.run(entry, limit=10000)
            assert cpu.carry == (text in invalid), (binary_path, text)
            # The routine only reads its operand; no FCB or code writes.
            assert cpu.mem[origin:origin + len(binary)] == before[origin:origin + len(binary)]
        def address(name):
            return int(re.search(r'^([0-9a-f]{4})\s+.*?\b' + name + ':', listing, re.M | re.I)[1], 16)
        for text, accepted in [('*.DAT', True), ('F?*.DAT', True), ('F***.D**', True),
                               ('?*.?*', True), ('F*X.DAT', False), ('F**?.DAT', False),
                               ('F*.DAT*', False), ('ABCDEFGH*.DAT', False)]:
            cpu = Z80(b'')
            cpu.mem[origin:origin + len(binary)] = binary
            cpu.setword(address('BC_COFCP'), address('BC_FCB'))
            cpu.mem[0x7000:0x7000 + len(text)] = text.encode('ascii')
            cpu.hl, cpu.b = 0x7000, len(text)
            cpu.run(entry, limit=10000)
            assert cpu.carry == (not accepted), (binary_path, text)
            if accepted:
                assert cpu.mem[address('BC_CWILD')] == 1
        # Stop after normalization: inspect operand boundaries without file I/O.
        for text, move, destination, source in [
                ('B:OUT.DAT=A:IN.DAT', 0, 'B:OUT.DAT', 'A:IN.DAT'),
                ('B4:=A1:*.COM', 0, 'B4:', 'A1:*.COM'),
                ('B:OUT.DAT:=A:IN.DAT', 1, 'B:OUT.DAT', 'A:IN.DAT'),
                ('A:IN.DAT B:OUT.DAT', 0, 'B:OUT.DAT', 'A:IN.DAT')]:
            cpu = Z80(b'')
            cpu.mem[origin:origin + len(binary)] = binary
            cpu.mem[5] = 0xc9  # BDOS return; no media operations in this check.
            cpu.mem[address('BC_CPARSE')] = 0xc9
            cpu.mem[address('BC_MVFLAG')] = move
            cpu.mem[0x7000:0x7000 + len(text)] = text.encode('ascii')
            cpu.hl, cpu.b = 0x7000, len(text)
            cpu.run(address('BC_COPY'), limit=10000)
            for pointer, length, expected in [('BC_CDPTR', 'BC_CDLEN', destination),
                                               ('BC_CSPTR', 'BC_CSLEN', source)]:
                start = cpu.word(address(pointer))
                count = cpu.mem[address(length)]
                assert bytes(cpu.mem[start:start + count]).decode() == expected, (text, pointer)
        option_entry = address('BC_COPT')
        for text, expected, overwrite, move, rejected in [
                ('B1:F.DAT B3:', 'B1:F.DAT B3:', 0, 0, False),
                ('B1:F.DAT B3:   ', 'B1:F.DAT B3:', 0, 0, False),
                ('B1:F.DAT B3: /O', 'B1:F.DAT B3:', 1, 0, False),
                ('B3:=B1:F.DAT   /O  ', 'B3:=B1:F.DAT', 1, 0, False),
                ('B1:F.DAT B3: /O', '', 0, 1, True),
                ('    ', '', 0, 0, True)]:
            cpu = Z80(b'')
            cpu.mem[origin:origin + len(binary)] = binary
            cpu.mem[address('BC_MVFLAG')] = move
            cpu.mem[0x7000:0x7000 + len(text)] = text.encode('ascii')
            cpu.hl, cpu.b = 0x7000, len(text)
            cpu.run(option_entry, limit=10000)
            assert cpu.carry == rejected, (binary_path, text)
            assert cpu.hl == 0x7000
            if not rejected:
                assert bytes(cpu.mem[cpu.hl:cpu.hl + cpu.b]).decode() == expected, text
                assert cpu.mem[address('BC_OVER')] == overwrite
    print('COPY CPX/transient exact 8.3, bounded wildcards and trailing /O parsing passed')


if __name__ == '__main__':
    main()
