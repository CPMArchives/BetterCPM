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
            ('build/utilities/COPY.COM', 'build/utilities/copy-transient.lst', 0x100)]:
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
        for text, accepted in [('*.DOC', True), ('X?***.BAK', True),
                               ('F*A.DAT', False), ('F**?.DAT', False),
                               ('F?.DAT*', False)]:
            cpu = Z80(b'')
            cpu.mem[origin:origin + len(binary)] = binary
            cpu.setword(address('BC_COFCP'), address('BC_NEWFCB'))
            cpu.mem[0x7000:0x7000 + len(text)] = text.encode('ascii')
            cpu.hl, cpu.b = 0x7000, len(text)
            cpu.run(entry, limit=10000)
            assert cpu.carry == (not accepted or origin != 0x100), (binary_path, text)
            assert cpu.mem[address('BC_CWILD')] == 0
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
            if not rejected:
                assert cpu.hl == 0x7000
                assert bytes(cpu.mem[cpu.hl:cpu.hl + cpu.b]).decode() == expected, text
                assert cpu.mem[address('BC_OVER')] == overwrite
        if origin == 0x100:
            for text, overwrite, skip, rejected in [
                    ('B1:F.DAT B3: /S', 0, 1, False),
                    ('B1:F.DAT B3: /S /S   ', 0, 1, False),
                    ('B1:F.DAT B3: /O /O', 1, 0, False),
                    ('B1:F.DAT B3: /B', 0, 0, False),
                    ('B1:F.DAT B3: /B /S /B', 0, 1, False),
                    ('B1:F.DAT B3: /O /B', 1, 0, False),
                    ('B1:F.DAT B3: /O /S', 0, 0, True),
                    ('B1:F.DAT B3: /S /O', 0, 0, True)]:
                cpu = Z80(b'')
                cpu.mem[origin:origin + len(binary)] = binary
                cpu.mem[0x7000:0x7000 + len(text)] = text.encode('ascii')
                cpu.hl, cpu.b = 0x7000, len(text)
                cpu.run(option_entry, limit=10000)
                assert cpu.carry == rejected, text
                if not rejected:
                    assert bytes(cpu.mem[cpu.hl:cpu.hl + cpu.b]) == b'B1:F.DAT B3:'
                    assert cpu.mem[address('BC_OVER')] == overwrite
                    assert cpu.mem[address('CT_SKIP')] == skip
    # Leading and trailing groups share one invocation-wide policy. Check
    # stripped cursor/count and rejection before operand/media processing.
    binary = (ROOT / 'build/utilities/COPY.COM').read_bytes()
    listing = (ROOT / 'build/utilities/copy-transient.lst').read_text()
    def transient_address(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
    for text, expected, flags in [
        ('/V /B B1:F.DAT B3:', 'B1:F.DAT B3:', (0,0,1,1)),
        (' /V   /O B3:=B1:F.DAT /B /V ', 'B3:=B1:F.DAT', (1,0,1,1)),
        ('/S B1:F.DAT B3: /S', 'B1:F.DAT B3:', (0,1,0,0)),
        ('/V B3: = B1:F.DAT /B', 'B3: = B1:F.DAT', (0,0,1,1)),
        ('/O B1:F.DAT B3: /S', None, None),
        ('/S B1:F.DAT B3: /O', None, None),
        ('/V', None, None), ('/V /B', None, None),
        ('/VV B1:F.DAT B3:', None, None),
        ('/X B1:F.DAT B3:', None, None),
        ('/BACKUP B1:F.DAT B3:', None, None),
        ('/V/B B1:F.DAT B3:', None, None)]:
        c=Z80(b''); c.mem[256:256+len(binary)]=binary
        c.mem[0x7000:0x7000+len(text)]=text.encode()
        c.hl,c.b=0x7000,len(text)
        c.run(transient_address('BC_COPT'),limit=10000)
        assert c.carry==(expected is None),text
        if expected is not None:
            assert bytes(c.mem[c.hl:c.hl+c.b]).decode()==expected,text
            assert tuple(c.mem[transient_address(n)] for n in
                         ('BC_OVER','CT_SKIP','CT_BATCH','CTV_ON'))==flags,text
    print('COPY CPX/transient filespec and transient /O-/S option parsing passed')


if __name__ == '__main__':
    main()
