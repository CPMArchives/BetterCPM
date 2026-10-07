#!/usr/bin/env python3
"""Execute STAT's actual parser with exact valid and invalid command tails."""
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

    def parse(text):
        cpu = Z80(b'')
        cpu.mem[0x100:0x100 + len(binary)] = binary
        cpu.mem[0x9000:0x9000 + len(text)] = text.encode()
        cpu.hl, cpu.b = 0x9000, len(text)
        cpu.run(address('PARSEFCB'), limit=10000)
        if not cpu.carry:
            cpu.run(address('FILEOPTION'), limit=10000)
        return cpu

    patterns = {
        'F***.DAT': b'F???????DAT', 'F.**': b'F       ???',
        'F?**.DAT': b'F???????DAT', 'F*.D**': b'F???????D??',
        '***.***': b'???????????',
        'F?*.DAT': b'F???????DAT', 'F.??*': b'F       ???',
        '?*.?*': b'???????????', 'F??????*.*': b'F??????????',
        'F*.DAT': b'F???????DAT', '*.COM': b'????????COM',
        '*.*': b'???????????', 'FOO.*': b'FOO     ???',
        'F??.D?T': b'F??     D?T', 'ABCDEFGH.COM': b'ABCDEFGHCOM',
        'FOO': b'FOO        ', '*': b'????????   ',
        'FOO.': b'FOO        ', 'FOO.B*': b'FOO     B??',
    }
    for text, expected in patterns.items():
        cpu = parse(text)
        assert not cpu.carry, text
        offset = address('FCB') + 1
        assert cpu.mem[offset:offset + 11] == expected, text
        assert cpu.mem[address('OPTION')] == 255, text
    for option, value in [('S', 0), ('R/O', 1), ('R/W', 2), ('SYS', 3), ('DIR', 4)]:
        for text in [f'FOO.COM ${option}', f'ABCDEFGH.COM${option}', f'F*.DAT ${option}   ', f'F***.DAT ${option}']:
            cpu = parse(text)
            assert not cpu.carry and cpu.mem[address('OPTION')] == value, text
    for suffix in ['$', '$X', '$SY', '$SYSTEM', '$D', '$DIRX', '$R', '$R/',
                   '$R/OX', '$R/WX', '$S EXTRA', '$SYS $DIR', 'EXTRA', ' $ S']:
        text = 'FOO.COM ' + suffix
        assert parse(text).carry, text
    for text in ['.COM', 'ABCDEFGHI.COM', 'FOO.ABCD', 'F*X.DAT', 'FOO.D*X',
                 'FOO..DAT', 'FOO:BAR', 'FOO.COM EXTRA', 'F?**?.DAT*', 'F**?.DAT',
                 'F.**?', 'F*.DAT*', 'F*X*.DAT', 'F???????*.DAT']:
        assert parse(text).carry, text
    assert not parse('ABCDEFGH   ').carry
    print('STAT wildcard patterns, exact options, trailing spaces and invalid tails passed')


if __name__ == '__main__':
    main()
