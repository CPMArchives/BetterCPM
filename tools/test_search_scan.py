#!/usr/bin/env python3
"""Execute SEARCH parser/traversal/reads with a hostile public-BDOS adapter.

Directory search state is deliberately destroyed by every file operation.
No full utility console/platform qualification is implied.
"""
from pathlib import Path
import re
from build_ccp import assemble
from search_source import development_source, ROOT
from test_bios import Z80


def compile_scan():
    out = ROOT/'build/search-scan'
    out.mkdir(parents=True, exist_ok=True)
    image = assemble(Path.home()/'bin/z80asm', '        ORG 0200H\n'+development_source()+
                     '\nRHOOK: OUT (042H),A\n        RET\n        END\n',
                     out/'scan.bin', out/'scan.lst', 0x200)
    listing = (out/'scan.lst').read_text()
    def address(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':', listing, re.M | re.I)[1], 16)
    return image, address


def entry(name, extent=0, attrs=0):
    stem, _, ext = name.partition('.')
    item = bytearray(32)
    item[1:12] = (stem.ljust(8)+ext.ljust(3)).encode('ascii')
    item[12] = extent & 31
    item[14] = extent >> 5
    for i in range(3):
        if attrs & (1 << i):
            item[9+i] |= 128
    return bytes(item)


def execute(image, address, tail, directories, contents, *, caller=(2,7),
            read_error=None, open_error=None, close_error=None,
            dir_error=None, supported_drives=range(16), max_user=31):
    c = Z80(b'')
    c.mem[0x200:0x200+len(image)] = image
    c.mem[5:8] = b'\xd3\x00\xc9'
    raw = tail.encode('ascii')
    c.mem[0x7000:0x7000+len(raw)] = raw
    c.hl, c.b = 0x7000, len(raw)
    c.d, c.e = caller
    sp = c.sp
    c.run(address('PCOMMAND'), limit=1000000)
    assert not c.carry and c.a == 0, (tail, c.a)
    drive, user = caller
    dma = 0x80
    cursor = None
    events, services, reads, opens, closes = [], [], [], [], []
    handles = {}
    def value(name, size=4):
        p = address(name)
        return int.from_bytes(c.mem[p:p+size], 'little')
    def name_at(pointer):
        return bytes(b & 127 for b in c.mem[pointer+1:pointer+12])
    def key_at(pointer):
        return (c.mem[pointer]-1 if c.mem[pointer] else drive, user, name_at(pointer))
    def directory_result():
        nonlocal cursor
        du, items, pos = cursor
        if dir_error == (du, pos):
            c.a = 4
        elif pos >= len(items):
            c.a = 255
        else:
            slot = pos % 4
            # Distinct nonmatching bytes elsewhere expose a wrong DMA slot.
            c.mem[dma:dma+128] = bytes([0xE5])*128
            c.mem[dma+slot*32:dma+slot*32+32] = items[pos]
            c.a = slot
            cursor = (du, items, pos+1)
    def bdos(port, sent):
        nonlocal drive, user, dma, cursor
        port &= 255
        if port == 0x42:
            kind = value('RWHY', 1)
            events.append(dict(kind=kind, drive=value('RDRIVE', 1), user=value('RUSER', 1),
                               error=value('RERROR', 1), mask=value('SRESULT', 1),
                               name=name_at(address('RFILE')), text=value('STSTART'),
                               line=value('STLINE'), hexx=value('SHSTART')))
            # Hooks cannot corrupt accounting through volatile registers.
            c.bc, c.de, c.hl, c.ix = 0xABCD, 0xBCDE, 0xCDEF, 0x7654
            return
        assert port == 0
        fn = c.c
        services.append(fn)
        if fn == 25:
            c.a = drive
        elif fn == 14:
            if c.e in supported_drives:
                drive = c.e
            c.a = 0
        elif fn == 32:
            if c.e != 255:
                user = c.e & max_user
            c.a = user
        elif fn == 26:
            dma = c.de
        elif fn == 17:
            pattern = name_at(c.de)
            du = (c.mem[c.de]-1 if c.mem[c.de] else drive, user)
            items = [item for item in directories.get(du, [])
                     if all(p == 63 or p == (b & 127) for p, b in zip(pattern, item[1:12]))]
            cursor = (du, items, 0)
            directory_result()
        elif fn == 18:
            assert cursor is not None, 'file I/O invalidated directory state; restart required'
            directory_result()
        elif fn == 15:
            key = key_at(c.de)
            opens.append(key)
            handles[c.de] = key
            c.a = 255 if key == open_error or key not in contents else 0
            cursor = None
        elif fn == 35:
            key = handles[c.de]
            assert (drive, user) == key[:2]
            c.mem[c.de+33:c.de+36] = (len(contents[key])//128).to_bytes(3, 'little')
            c.a = 255  # Function 35 has no defined A status, including on success.
            cursor = None
        elif fn == 33:
            key = handles[c.de]
            assert (drive, user) == key[:2]
            record = int.from_bytes(c.mem[c.de+33:c.de+36], 'little')
            reads.append((key, record))
            if read_error == (key, record):
                c.a = 2
            elif record*128 >= len(contents[key]):
                c.a = 1
            else:
                c.mem[dma:dma+128] = contents[key][record*128:(record+1)*128]
                c.a = 0
            cursor = None
        elif fn == 16:
            key = handles[c.de]
            closes.append(key)
            c.a = 255 if key == close_error else 0
            cursor = None
        else:
            raise AssertionError(('unexpected BDOS operation', fn))
        c.bc, c.de, c.hl, c.ix = 0xA5A5, 0x5A5A, 0x1234, 0x4567
    c.port_write = bdos
    c.run(address('RRUN'), limit=100000000)
    assert c.sp == sp and (drive, user) == caller and dma == 0x80
    assert not set(services) & {19,21,22,23,30,34,40}, 'write operation issued'
    totals = [value(n, 8) for n in ('RFILES', 'RMATCHED', 'RTEXT', 'RHEX', 'RTOTAL')]
    return dict(totals=totals, incomplete=bool(value('RINCOMP', 1)), events=events,
                reads=reads, opens=opens, closes=closes, c=c)


def main():
    image, address = compile_scan()
    a = (0,0,b'ONE     TXT')
    b = (0,0,b'TWO     TXT')
    other = (1,3,b'ONE     TXT')
    directories = {(0,0): [entry('ONE.TXT'), entry('TWO.TXT'), entry('ONE.TXT', 1)],
                   (1,3): [entry('ONE.TXT')]}
    contents = {a: b'4142 AB 4142\r\n'+b'\x1a'*114, b: b'AAAA'+b'.'*124,
                other: b'AB'+b'.'*126}
    result = execute(image, address, '"4142" [B3,A0,A[0]]:*.TXT', directories, contents)
    assert result['totals'] == [3,2,2,2,4], result
    assert result['opens'] == [a,b,other], result['opens']
    assert result['closes'] == [a,b,other] and not result['incomplete']
    observed = [(e['mask'],e['text'],e['line'],e['hexx']) for e in result['events'] if e['kind'] == 2]
    assert observed == [(1,0,1,0), (2,0,1,5), (1,8,1,5), (2,0,0,0)], observed
    result = execute(image, address, '"AAA" A0:*.TXT /NOHEX', directories, contents)
    assert result['totals'] == [2,1,2,0,2] and not result['incomplete']
    result = execute(image, address, '"1a" A0:ONE.TXT /NOTEXT', directories, contents)
    assert result['totals'] == [1,1,0,114,114]
    result = execute(image, address, '"x" A0:*.COM', directories, contents)
    assert result['totals'] == [0]*5 and not result['incomplete']
    for key, expected_files, error in [('open_error',1,3), ('close_error',2,6)]:
        result = execute(image, address, '"4142" A0:*.TXT', directories, contents, **{key:a})
        assert result['incomplete'] and result['totals'][0] == expected_files
        assert any(e['kind'] == 3 and e['error'] == error for e in result['events'])
        assert result['opens'] == [a,b]
    # File larger than one logical record, match spans the boundary. A failed
    # second read contributes neither stale matches nor an invented full scan.
    boundary = {a: b'.'*127+b'A'+b'B'+b'.'*127}
    one_dir = {(0,0): [entry('ONE.TXT'), entry('ONE.TXT', 1)]}
    result = execute(image, address, '"AB" A0:*.TXT /NOHEX', one_dir, boundary)
    assert result['totals'] == [1,1,1,0,1] and len(result['reads']) == 2
    result = execute(image, address, '"AB" A0:*.TXT /NOHEX', one_dir, boundary, read_error=(a,1))
    assert result['incomplete'] and result['totals'] == [1,0,0,0,0]
    assert any(e['kind'] == 3 and e['error'] == 5 for e in result['events'])
    # Empty files count as searched; no file reads are necessary.
    result = execute(image, address, '"x" A0:*.TXT', one_dir, {a:b''})
    assert result['totals'] == [1,0,0,0,0] and not result['reads']
    # Attribute predicates use shared truth masks and physical entry bits.
    d = {(0,0): [entry('ONE.TXT', attrs=1), entry('TWO.TXT', attrs=2)]}
    result = execute(image, address, '"4142" A0:*.TXT[$RO+!$SYS]', d, contents)
    assert result['opens'] == [a]
    # A later matching extent must not be hidden by an earlier extent whose
    # attributes did not satisfy the shared source predicate.
    d = {(0,0): [entry('ONE.TXT'), entry('ONE.TXT', 1, attrs=1), entry('ONE.TXT', 2, attrs=1)]}
    result = execute(image, address, '"4142" A0:*.TXT[$RO]', d, contents)
    assert result['opens'] == [a]
    # A returning user alias is diagnosed before any directory/file operation.
    result = execute(image, address, '"4142" [A0,A31,B3]:*.TXT', directories, contents, max_user=15)
    assert result['incomplete'] and result['opens'] == [a,b,other]
    assert any(e['kind'] == 3 and e['error'] == 1 and e['user'] == 31 for e in result['events'])
    result = execute(image, address, '"4142" [A0,B3]:*.TXT', directories, contents, supported_drives=[0,2])
    assert result['incomplete'] and result['opens'] == [a,b]
    result = execute(image, address, '"4142" [A0,B3]:*.TXT', directories, contents, dir_error=((0,0),0))
    assert result['incomplete'] and result['opens'] == [other]
    # Eight-byte carry and saturation, independently of the traversal fixtures.
    c = result['c']
    p = address('RTEXT')
    c.mem[p:p+8] = (0xFFFFFFFF).to_bytes(8,'little')
    c.hl = p
    c.run(address('RINC8'), limit=10000)
    assert int.from_bytes(c.mem[p:p+8], 'little') == 0x100000000
    c.mem[p:p+8] = bytes([255])*8
    c.hl = p
    c.run(address('RINC8'), limit=10000)
    assert bytes(c.mem[p:p+8]) == bytes([255])*8
    assert c.mem[address('RINCOMP')] == 1
    print(f'SEARCH scan: shared DU/attribute selection, native order/extent dedup, full records, '
          f'hostile cursor invalidation, cross-record matches, errors, wide totals and caller restoration pass ({len(image)} bytes)')


if __name__ == '__main__':
    main()
