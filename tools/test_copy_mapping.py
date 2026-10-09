#!/usr/bin/env python3
"""Execute transient COPY positional substitution and mapping preflight."""
import re
from test_bios import Z80
from test_disk_utilities import ROOT


def main():
    binary = (ROOT / 'build/utilities/COPY.COM').read_bytes()
    listing = (ROOT / 'build/utilities/copy-transient.lst').read_text()
    def address(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b' + name + ':', listing, re.M | re.I)[1], 16)
    def cpu():
        c = Z80(b'')
        c.mem[0x100:0x100 + len(binary)] = binary
        return c
    def field(value):
        name, _, ext = value.partition('.')
        return (name.ljust(8) + ext.ljust(3)).encode()
    for source, template, expected in [
            ('FOOBAR.COM', 'X???????.BAK', 'XOOBAR.BAK'),
            ('FOO.COM', '????????.DOC', 'FOO.DOC'),
            ('A.COM', '????????.???', 'A.COM'),
            ('ABCDEFGH.XYZ', '????????.???', 'ABCDEFGH.XYZ'),
            ('A.COM', '?X??????.BAK', 'AX.BAK'),
            ('A.COM', '??X?????.BAK', None),
            ('A.COM', '        .BAK', None),
            ('FOO.COM', 'BAD/NAME.DOC', None)]:
        c = cpu()
        c.mem[0x7000:0x700b] = field(source)
        c.mem[address('CT_PATTERN'):address('CT_PATTERN') + 11] = field(template)
        c.hl, c.de = 0x7000, 0x7100
        c.run(address('CTGEN'), limit=10000)
        assert c.carry == (expected is None), (source, template)
        if expected is not None:
            assert bytes(c.mem[0x7100:0x710b]) == field(expected), (source, template)
    for sources, template, same_du, rejected in [
            (['FOO.COM', 'BAR.COM'], '????????.DOC', False, False),
            (['FOO.COM', 'BAR.COM'], 'ONE.DOC', False, True),
            (['FOO.COM', 'BAR.DOC'], '????????.DOC', True, True),
            (['FOO.COM', 'BAR.COM'], '????????.DOC', True, False),
            (['FOO.COM'], '????????.???', True, True)]:
        c = cpu()
        c.mem[address('CT_COUNT')] = len(sources)
        start = address('CT_NAMES')
        for i, source in enumerate(sources):
            c.mem[start + 11*i:start + 11*(i+1)] = field(source)
        c.mem[address('CT_PATTERN'):address('CT_PATTERN') + 11] = field(template)
        c.mem[address('BC_CSDRV')] = 1
        c.mem[address('BC_CDDRV')] = 1 if same_du else 2
        c.mem[address('BC_CSUSR')] = c.mem[address('BC_CDUSR')] = 3
        dus = address('CT_DUS')
        for i in range(len(sources)):
            c.mem[dus+2*i:dus+2*i+2] = bytes((1,3))
        c.mem[address('CT_BEGIN')] = 0xc9
        c.mem[address('BC_PRINT')] = 0xc9
        c.mem[address('BC_WEND')] = 0xc9
        c.run(address('CTPREF'), limit=100000)
        assert (c.de == address('CT_MAPMSG')) == rejected, (sources, template)
    c = cpu()
    c.mem[address('BC_PCHAR')] = 0xc9
    c.mem[address('BC_CSDRV')] = 0
    c.mem[address('BC_CDDRV')] = 2
    c.mem[address('BC_CSUSR')] = 31
    c.mem[address('BC_CDUSR')] = 0
    c.mem[address('BC_FCB')+1:address('BC_FCB')+12] = field('FOO$.COM')
    c.mem[address('BC_NEWFCB')+1:address('BC_NEWFCB')+12] = field('NEW.DOC')
    c.run(address('CTPAIR'), limit=10000)
    start = address('CT_LINE')
    assert bytes(c.mem[start:start+40]).split(b'\0')[0] == b'\r\nA31:FOO$.COM -> C0:NEW.DOC'
    print('Transient COPY positional substitution and mapping conflicts pass')


if __name__ == '__main__':
    main()
