#!/usr/bin/env python3
"""Execute the quote-aware SEARCH parser and production shared selectors."""
from pathlib import Path
import re
from build_ccp import assemble
from search_source import development_source, ROOT
from test_bios import Z80


def main():
    out = ROOT/'build/search-parser'
    out.mkdir(parents=True, exist_ok=True)
    image = assemble(Path.home()/'bin/z80asm', '        ORG 0200H\n'+development_source()+'\nRHOOK: RET\n        END\n',
                     out/'parser.bin', out/'parser.lst', 0x200)
    listing = (out/'parser.lst').read_text()
    def address(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':', listing, re.M | re.I)[1], 16)
    def parse(tail, caller=(1, 2)):
        tail = tail.encode('ascii') if isinstance(tail, str) else tail
        c = Z80(b'')
        c.mem[0x200:0x200+len(image)] = image
        c.mem[0x7000:0x7000+len(tail)] = tail
        c.hl = 0x7000
        c.b = len(tail)
        c.d, c.e = caller
        sp = c.sp
        c.run(address('PCOMMAND'), limit=1000000)
        assert c.sp == sp
        assert bytes(c.mem[0x7000:0x7000+len(tail)]) == tail
        return c
    def field(c, name, n=1):
        start = address(name)
        return bytes(c.mem[start:start+n])
    def expect(tail, error):
        c = parse(tail)
        assert c.carry and c.a == error, (tail, c.a, c.carry)
        assert field(c, 'DU_MAP', 64) == bytes(64)
        assert field(c, 'FS_FCB', 36) == bytes(36)
        assert field(c, 'STLEN') == field(c, 'SHLEN') == b'\0'
    for tail, error in [('', 11), ('FOO.TXT "hello"', 11), ('hello FOO.TXT', 11),
                        ('"hello"', 11), ('"" FOO.TXT', 13),
                        ('"hello" /P FOO.TXT', 11), ('"hello" A.TXT B.TXT', 11),
                        ('"hello" "FOO.TXT"', 11), ('"hello" FOO.TXT /X', 12),
                        ('"hello" FOO.TXT /NOTEXT', 13),
                        ('"41" FOO.TXT /NOTEXT /NOHEX', 13),
                        ('"hello" B32:*.TXT', 14), ('"hello" B[3,]:*.TXT', 14),
                        ('"hello" B[-]:', 14), ('"hello" F*A.TXT', 14),
                        ('"hello" FOO.TXT[$WHL]', 14),
                        ('"hello FOO.TXT', 10), ('"hello"x FOO.TXT', 10),
                        ('"hello" FOO.TXT"', 10), ('"'+'x'*65+'" F.T', 13),
                        ('x'*128, 10), (b'"x" F.T\0 /HELP', 10)]:
        expect(tail, error)
    c = parse('/nohex /nocase "Hello World" [A0,B[3-7],5]:*.TXT /p /NOCASE')
    assert not c.carry and c.a == 0
    assert field(c, 'STPAT', 11) == b'HELLO WORLD'
    assert field(c, 'PFLAGS') == b'\5' and field(c, 'PPAGED') == b'\1'
    expected = bytearray(64)
    for drive, user in [(0,0), (1,5)]+[(1,u) for u in range(3,8)]:
        expected[drive*4+user//8] |= 1 << (user%8)
    assert field(c, 'DU_MAP', 64) == expected
    assert field(c, 'FS_FCB', 12) == b'\0????????TXT'
    c = parse('"Error" *.TXT[$RO+!$SYS]')
    assert not c.carry and field(c, 'STPAT', 5) == b'Error'
    assert field(c, 'FS_MASK') == bytes([0x22])
    for tail in ['"/VER" FOO.TXT', '"/HELP" FOO.TXT', '"a\tB" FOO.TXT',
                 '\t/NOTEXT\t"41 42"\tB7:*.COM\t/P']:
        c = parse(tail)
        assert not c.carry and c.a == 0, (tail, c.a)
    for tail, result in [('/VER', 2), ('/HELP', 1), ('/VER /HELP', 1),
                         ('/help /ver', 1), ('/BOGUS /VER x', 2),
                         ('"/HELP" FOO.TXT /VER', 2),
                         ('"/VER" FOO.TXT /HELP', 1), ('/HELP "" B32:', 1),
                         ('"x"glue /HELP', 1)]:
        c = parse(tail, caller=(255,255))
        assert not c.carry and c.a == result, (tail, c.a, c.carry)
        assert field(c, 'DU_MAP', 64) == bytes(64)
        assert field(c, 'FS_FCB', 36) == bytes(36)
        assert field(c, 'STLEN') == field(c, 'SHLEN') == b'\0'
    expect('/HELPER', 12)
    expect('"x" FOO.TXT /VERIFY', 12)
    # Every byte of the tail counts, including spaces, quoting and selectors.
    c = parse('"x" F.T'+' '*120)
    assert not c.carry and c.a == 0
    expect('"x" F.T'+' '*121, 10)
    print(f'SEARCH parser: quoted pattern-first grammar, queries, flags, shared DU/attribute/8.3 selection and 127-byte boundary pass ({len(image)} bytes including modules/state)')


if __name__ == '__main__':
    main()
