#!/usr/bin/env python3
"""Focused compiled-CRC tests against a hostile public-BDOS model.

The model clobbers public service scratch registers and reuses the DMA for
directory results. It is not a substitute for native platform qualification.
"""
from pathlib import Path
import re
import zlib
from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]


def name83(name):
    stem, dot, ext = name.upper().partition('.')
    assert 0 < len(stem) <= 8 and len(ext) <= 3
    return (stem.ljust(8)+ext.ljust(3)).encode('ascii')


def records(data):
    return data+b'\x1a'*((-len(data)) % 128)


def oracle(data):
    old = corrected = chek = 0
    for b in data:
        top = old & 0x8000
        shifted = (old << 1) & 0xffff
        old = (shifted & 0xff00) | (((shifted & 255)+b) & 255)
        if top:
            old ^= 0xa097
        for poly, current, which in ((0xa097, corrected, 0), (0x1021, chek, 1)):
            current ^= b << 8
            for _ in range(8):
                current = ((current << 1) ^ (poly if current & 0x8000 else 0)) & 65535
            if which:
                chek = current
            else:
                corrected = current
    return (old, corrected, chek, zlib.crc32(data), sum(data) & 255, sum(data) & 65535, ((sum(data) & 255) + ((sum(data) >> 6) & 3)) & 63, sum(data) & 4095)


def execute(files=None, tail='', *, caller=(2, 7), keys=b'Y', fault=None,
            cancel_at=None, size_override=None, limit=30000000):
    c = Z80(b'')
    image = (ROOT/'build/utilities/CRCKSUM.COM').read_bytes()
    c.mem[0x100:0x100+len(image)] = image
    c.mem[5:8] = b'\xd3\x00\xc9'
    c.mem[0:3] = b'\xc3\xfe\xff'
    data = tail.encode('ascii')
    assert len(data) <= 127
    c.mem[0x80] = len(data)
    c.mem[0x81:0x81+len(data)] = data
    disk = {(d, u, name83(n)): bytearray(records(b))
            for (d, u, n), b in (files or {}).items()}
    output = bytearray()
    services = []
    reads = []
    writes = []
    handles = {}
    counts = {}
    drive, user = caller
    dma = 128
    keypos = polls = 0
    search = []
    searchpos = 0

    def identity(addr):
        dr = c.mem[addr]
        return (dr-1 if dr else drive, user,
                bytes(x & 127 for x in c.mem[addr+1:addr+12]))

    def directory():
        nonlocal searchpos
        if searchpos == len(search):
            c.a = 255
            return
        key = search[searchpos]
        searchpos += 1
        c.mem[dma:dma+128] = bytes(128)
        c.mem[dma] = user
        c.mem[dma+1:dma+12] = key[2]
        c.a = 0

    def bdos(port, value):
        nonlocal drive, user, dma, keypos, polls, search, searchpos
        fn = c.c
        services.append(fn)
        counts[fn] = counts.get(fn, 0)+1
        fail = ((fn, counts[fn]) in fault if isinstance(fault, set)
                else fault == (fn, counts[fn]))
        addr = c.de
        if fn == 2:
            output.append(c.e)
        elif fn == 1:
            c.a = keys[keypos] if keypos < len(keys) else 13
            keypos += 1
        elif fn == 6:
            c.a = 3 if cancel_at is not None and polls >= cancel_at else 0
        elif fn == 11:
            polls += 1
            c.a = 255 if cancel_at is not None and polls >= cancel_at else 0
        elif fn == 25:
            c.a = drive
        elif fn == 14:
            drive = c.e
            c.a = 0
        elif fn == 32:
            if c.e != 255:
                user = c.e
            c.a = user
        elif fn == 26:
            dma = addr
        elif fn == 15:
            key = identity(addr)
            c.a = 0 if key in disk and not fail else 255
            if c.a == 0:
                handles[addr] = [key, 0]
        elif fn == 16:
            handles.pop(addr, None)
            c.a = 255 if fail else 0
        elif fn == 35:
            key = identity(addr)
            n = len(disk[key])//128 if key in disk else 0
            n = (size_override or {}).get(key, n)
            c.mem[addr+33:addr+36] = n.to_bytes(3, 'little')
            c.a = 0 if key in disk else 255
        elif fn == 20:
            key, pos = handles[addr]
            reads.append((key, pos))
            if fail:
                c.a = 2
            elif pos*128 >= len(disk[key]):
                c.a = 1
            else:
                c.mem[dma:dma+128] = disk[key][pos*128:pos*128+128]
                handles[addr][1] += 1
                c.a = 0
        elif fn == 17:
            d, u, pattern = identity(addr)
            search = [k for k in disk if k[:2] == (d, u) and
                      all(a == 63 or a == b for a, b in zip(pattern, k[2]))]
            searchpos = 0
            directory()
        elif fn == 18:
            directory()
        elif fn == 22:
            key = identity(addr)
            if key in disk or fail:
                c.a = 255
            else:
                disk[key] = bytearray()
                handles[addr] = [key, 0]
                c.a = 0
        elif fn == 21:
            key, pos = handles[addr]
            writes.append((key, pos))
            c.a = 1 if fail else 0
            if not fail:
                disk[key][pos*128:pos*128+128] = c.mem[dma:dma+128]
                handles[addr][1] += 1
        elif fn == 19:
            key = identity(addr)
            c.a = 255 if fail or key not in disk else 0
            if c.a == 0:
                del disk[key]
        elif fn == 23:
            old, new = identity(addr), identity(addr+16)
            c.a = 255 if fail or old not in disk or new in disk else 0
            if c.a == 0:
                disk[new] = disk.pop(old)
        else:
            raise AssertionError(('unexpected BDOS', fn))
        c.bc, c.de, c.hl = 0xa5a5, 0x5a5a, 0x1234
    c.port_write = bdos
    sp = c.sp
    c.run(0x100, limit=limit)
    assert c.sp == sp, 'caller stack imbalance'
    assert (drive, user) == caller, ('caller DU changed', drive, user)
    assert dma == 128, 'caller DMA not restored'
    stack = bytes(c.mem[256+len(image)-512:256+len(image)])
    assert stack[:64] == b'\xff'*64, 'private stack guard touched'
    return dict(text=output.decode('ascii'), files={k: bytes(v) for k, v in disk.items()},
                services=services, reads=reads, writes=writes,
                complete=bool(re.search(r'\d+ verified\.\r\n$',output.decode('ascii'))))


def main():
    import json
    count = 0
    def run(*args, **kwargs):
        nonlocal count
        count += 1
        return execute(*args, **kwargs)
    def total(r, label):
        patterns={'Files calculated':r'(\d+) files? calculated',
                  'Files verified':r'(\d+) verified','Files failed':r'(\d+) failed',
                  'Listed files missing':r'(\d+) missing','Files not listed':r'(\d+) unlisted',
                  'Files skipped':r'(\d+) skipped','Malformed/list errors':r'(\d+) list errors?',
                  'DU/reference failures':r'(\d+) DU/reference errors?',
                  'Lists completed':r'(\d+) lists? written','Lists declined':r'(\d+) lists? declined',
                  'Lists failed':r'(\d+) lists? failed','Entries skipped':r'(\d+) entr(?:y|ies) skipped'}
        found=re.search(patterns[label],r['text'].replace('\r\n',' '))
        return int(found[1]) if found else 0
    def native(rows, columns=('CRCK','CRCK5','CHEK','CRC32','SUM8','SUM16','KERM6','KERM12')):
        widths = {'CRCK':4,'CRCK5':5,'CHEK':4,'CRC32':8,'SUM8':4,'SUM16':5,'KERM6':5,'KERM12':6}
        result = ['; BetterCP/M CRC list',
                  'NAME     EXT  RECS  '+'  '.join(x.ljust(widths[x]) for x in columns),
                  '-------- ---  ----  '+'  '.join('-'*widths[x] for x in columns)]
        for name, n, values in rows:
            nm = name83(name).decode()
            result.append(nm[:8]+' '+nm[8:]+'  '+str(n).rjust(4)+'  '+
                          '  '.join(values[x].rjust(widths[x]) for x in columns))
        return ('\r\n'.join(result)+'\r\n').encode()
    def values(data):
        return dict(zip(('CRCK','CRCK5','CHEK','CRC32','SUM8','SUM16','KERM6','KERM12'),
                        (f'{x:0{8 if i==3 else 2 if i in (4,6) else 3 if i==7 else 4}X}' for i,x in enumerate(oracle(data)))))
    # Exercise the actual compiled update routines independently of file logic.
    listing = (ROOT/'build/utilities/crc.lst').read_text()
    symbols = {n:int(next(x[:4] for x in listing.splitlines() if re.search(r'\b'+n+':',x)),16)
               for n in ('CINIT','CUPDATE','CFINISH','CVALUES')}
    image = (ROOT/'build/utilities/CRCKSUM.COM').read_bytes()
    for raw, expected in ((b'',(0,0,0,0,0,0,0,0)),(b'123456789',(0x53c5,0xfb3,0x31c3,0xcbf43926,0xdd,0x1dd,0x20,0x1dd)),
                          (records(b'123456789'),(0xa687,0x5d45,0xe447,0x2f263492,0xf3,0xdf3,0x36,0xdf3)),
                          (bytes(range(256)),oracle(bytes(range(256)))),
                          (b'\xff'*258,oracle(b'\xff'*258))):
        c = Z80(b'');c.mem[256:256+len(image)] = image
        c.run(symbols['CINIT'])
        for byte in raw:
            c.a=byte;c.run(symbols['CUPDATE'])
        c.run(symbols['CFINISH'])
        raw_result=bytes(c.mem[symbols['CVALUES']:symbols['CVALUES']+16])
        actual=tuple(int.from_bytes(raw_result[a:b],'little') for a,b in ((0,2),(2,4),(4,6),(6,10),(10,11),(11,13),(13,14),(14,16)))
        assert actual==expected,(actual,expected)
        count += 1
    data = records(b'123456789');v=values(data)
    f={(2,7,'TEST.DAT'):data,(2,7,'NOEXT'):b''}
    for tail in ('/VER', '/HELP /VER BAD', '/VER /HELP /BOGUS', '/help\t/WHAT'):
        r=run(f,tail);assert not set(r['services']) & {14,15,17,25,26,32,35},r['text']
    bad=('/UNKNOWN','/HELPER','/VERIFY','/CHECK=B:CRC.LST','/LOCAL=C3:CRC.LST',
         '/FILE=*.*','/FILE=','/LOCAL=','/CHECK=','/FILE=B[1-2]:LST',
         '/CHECK /FILE=CRC.LST','/CHECK /LOCAL=LST','Q:FILE','A32:',
         'TOOLONGNM.TXT','/FILE=BAD:NAME','TEST.DAT /FILE=TEST.DAT',
         'TEST.DAT /LOCAL=TEST.DAT','/LOCAL=B:LST /LOCAL=LST')
    for tail in bad:
        r=run(f,tail);assert 'invalid command' in r['text'] and not set(r['services']) & {15,17,19,21,22,23},(tail,r['text'])
    for flags, cols in (('',tuple(v)),('/CRCK',('CRCK',)),('/CHEK /CRCK',('CHEK','CRCK')),
                        ('/CRCK5 /CRCK5',('CRCK5',)),('/CRC32',('CRC32',)),('/SUM8',('SUM8',)),('/SUM16',('SUM16',)),('/KERM6',('KERM6',)),('/KERM12',('KERM12',)),
                        ('/KERM12 /SUM8 /KERM6 /KERM12',('KERM12','SUM8','KERM6')),
                        ('/SUM16 /CRCK /SUM8 /SUM8',('SUM16','CRCK','SUM8')),
                        ('/KERM12 /KERM6 /SUM16 /SUM8 /CRC32 /CHEK /CRCK5 /CRCK',tuple(reversed(v)))):
        r=run(f,'/FILE=CRC.LST '+flags)
        saved=r['files'][2,7,name83('CRC.LST')].split(b'\x1a')[0]
        assert saved==native([('NOEXT',0,values(b'')),('TEST.DAT',1,v)],cols),(flags,saved)
        assert total(r,'Lists completed')==1,r['text']
        checked=run({**f,(2,7,'CRC.LST'):saved},'/CHECK')
        assert total(checked,'Files verified')==2 and checked['complete'],checked['text']
    for flags in ('/LEGACY /CRC32','/CRC32 /LEGACY','/CRCK5 /LEGACY /CHEK','/SUM8 /LEGACY /SUM16','/LEGACY /SUM16 /SUM8','/KERM6 /LEGACY /KERM12'):
        r=run(f,flags+' /FILE=CRC.LST')
        saved=r['files'][2,7,name83('CRC.LST')].split(b'\x1a')[0]
        assert saved==b'\r\n--> FILE:  NOEXT   .   \t\tCRC = 00 00\r\n\r\n--> FILE:  TEST    .DAT\t\tCRC = A6 87\r\n\r\n',saved
        assert total(run({**f,(2,7,'CRCKLIST.CRC'):saved},'/CHECK'),'Files verified')==2
    r=run(f,'/FILE=CRC.LST /40')
    assert all(len(line)<=40 for line in r['text'].splitlines()),r['text']
    assert r['files'][2,7,name83('CRC.LST')].split(b'\x1a')[0]==native([('NOEXT',0,values(b'')),('TEST.DAT',1,v)])
    for narrow in ('',' /40'):
        ordered=run(f,'/FILE=CRC.LST /KERM12 /SUM8 /CRCK'+narrow)
        if narrow:
            row=ordered['text'].split('TEST     DAT')[-1]
            assert row.index('KERM12')<row.index('SUM8')<row.index('CRCK'),row
        saved=ordered['files'][2,7,name83('CRC.LST')]
        checked=run({**f,(2,7,'CRC.LST'):saved},'/CHECK /SUM8 /KERM12'+narrow)
        row=checked['text'].split('TEST     DAT MATCH')[-1]
        assert row.index('SUM8')<row.index('KERM12'),row
    wrong_order=native([('TEST.DAT',1,{**v,'SUM8':'00','KERM12':'000'})])
    result=run({(2,7,'TEST.DAT'):data,(2,7,'CRC.LST'):wrong_order},'/CHECK /KERM12 /SUM8')
    assert 'KERM12=000 SUM8=00' in result['text'],result['text']
    # Operand DU order, selector canonical order, overlap dedup, sorted names,
    # simultaneous output, and a master/local coincident identity.
    many={(1,3,'Z.DAT'):data,(1,3,'A.DAT'):b'',(1,1,'A.DAT'):data,(2,7,'C.DAT'):data}
    r=run(many,'B[3,1]: B3:*.DAT C7: /FILE=C7:CRC.LST /LOCAL=CRC.LST')
    master=r['files'][2,7,name83('CRC.LST')].split(b'\x1a')[0]
    assert master.count(b'; BetterCP/M')==3,master
    assert r['text'].index('B1:')<r['text'].index('B3:')<r['text'].index('C7:')
    for key,payload in many.items():
        identity=(key[0],key[1],name83(key[2]))
        assert sum(1 for k,pos in r['reads'] if k==identity)==len(payload)//128+1
    assert total(r,'Lists completed')==3,r['text']
    assert r['text'].endswith('4 files calculated; 3 lists written.\r\n'),r['text']
    for keys in (b'N',b'Y',b'A',b'\x03'):
        old=records(b'ORIGINAL')
        r=run({**f,(2,7,'CRC.LST'):old},'/FILE=CRC.LST',keys=keys)
        assert (r['files'][2,7,name83('CRC.LST')]==old)==(keys in (b'N',b'\x03'))
        assert len(r['files'])==3
        assert total(r,'Lists declined')==(keys==b'N')
    for name in ('CRC00001.$$$','CRC00001.BAK'):
        r=run(f,'/FILE='+name)
        assert (2,7,name83(name)) in r['files'] and total(r,'Lists completed')==1
        old=records(b'ANOTHER FILE')
        r=run({**f,(2,7,name):old},'/FILE=CRC.LST')
        assert r['files'][2,7,name83(name)]==old
        assert total(r,'Lists completed')==1 and len(r['files'])==4
    for fault in ((21,1),(23,2),(22,1)):
        old=records(b'ORIGINAL')
        r=run({**f,(2,7,'CRC.LST'):old},'/FILE=CRC.LST',fault=fault)
        assert r['files'][2,7,name83('CRC.LST')]==old,(fault,r['text'])
        assert len(r['files'])==3,(fault,r['files'])
        assert total(r,'Lists failed')==1,(fault,r['text'])
    r=run(f,'/FILE=CRC.LST',cancel_at=3)
    assert (2,7,name83('CRC.LST')) not in r['files'] and 'cancelled' in r['text']
    old=records(b'ORIGINAL')
    r=run({**f,(2,7,'CRC.LST'):old},'/FILE=CRC.LST',fault={(23,2),(23,3)})
    assert 'recovery incomplete' in r['text'] and 'CRC00001.BAK' in r['text'],r['text']
    assert r['files'][2,7,name83('CRC00001.BAK')]==old
    assert (2,7,name83('CRC.LST')) not in r['files']
    r=run(f,'/FILE=CRC.LST',size_override={(2,7,name83('TEST.DAT')):10000})
    assert '-------- ---  -----' in r['text'] and 'READ ERROR' in r['text']
    assert (2,7,name83('CRC.LST')) not in r['files']
    # Independent reference fixtures, rather than just writer/reader agreement.
    one={(2,7,'TEST.DAT'):data}
    for ref in (native([('TEST.DAT',1,v)],('KERM12','SUM16','CRC32','KERM6','CHEK','SUM8','CRCK5','CRCK')),
                b'--> FILE:  TEST    .DAT\t\tCRC = A6 87\r\n',
                b'TEST.DAT KERM6 = 36 KERM12 = DF3 SUM8 = F3 SUM16 = 0D F3 CHEK = E447 CRC = A687 CRC32 = 2F263492 CRCK5 = 5D45\n',
                b'Index Name Size CRC Description\r\n310.01\tTEST    .DAT 1K A6 87 fixture\r\n'):
        r=run({**one,(2,7,'CRC.LST'):ref},'/CHECK')
        assert total(r,'Files verified')==1 and r['complete'],r['text']
    # Each new checksum independently rejects a mismatch; old four-column lists remain valid.
    for alg in ('SUM8','SUM16','KERM6','KERM12'):
        ref=native([('TEST.DAT',1,{**v,alg:'00' if alg in ('SUM8','KERM6') else '000' if alg=='KERM12' else '0000'})],(alg,))
        r=run({**one,(2,7,'CRC.LST'):ref},'/CHECK /'+alg)
        assert total(r,'Files failed')==1,r['text']
    ref=native([('TEST.DAT',1,v)],('CRCK','CRCK5','CHEK','CRC32'))
    assert total(run({**one,(2,7,'CRC.LST'):ref},'/CHECK'),'Files verified')==1
    wrong={**v,'CRCK':'FFFF','CRC32':'00000000'}
    ref=native([('TEST.DAT',1,wrong)])+b'\r\n'+native([('TEST.DAT',1,v)])
    r=run({**one,(2,7,'CRC.LST'):ref},'/CHECK')
    assert total(r,'Files verified')==1 and 'alternative' in r['text'],r['text']
    mixed=native([('TEST.DAT',1,{**v,'CRC32':'00000000'}),('TEST.DAT',1,{**v,'CRCK':'FFFF'})])
    r=run({**one,(2,7,'CRC.LST'):mixed},'/CHECK /CRCK /CRC32')
    assert total(r,'Files failed')==1 and 'CHECKSUM MISMATCH' in r['text'],r['text']
    for ref,flag,expect in ((native([('TEST.DAT',2,v)]),'','SIZE MISMATCH'),
                           (native([('TEST.DAT',1,v)],('CHEK',)),'/CRCK','SKIPPED'),
                           (native([('OTHER.DAT',1,v)]),'','FILE NOT LISTED')):
        r=run({**one,(2,7,'CRC.LST'):ref},'/CHECK '+flag)
        assert expect in r['text'] and not r['complete'],r['text']
        if expect=='SIZE MISMATCH':
            assert not [x for x in r['reads'] if x[0][2]==name83('TEST.DAT')],r['reads']
    r=run({**one,(2,7,'CRC.LST'):native([('TEST.DAT',1,v)])},'/CHECK /40')
    assert all(len(line)<=40 for line in r['text'].splitlines()),r['text']
    # Rounded K rejects only incompatible ranges.
    for k,expect in ((0,'SIZE MISMATCH'),(1,' MATCH'),(2,'SIZE MISMATCH')):
        ref=f'INDEX NAME SIZE CRC\n310.1 TEST.DAT {k}K A6 87 comment\n'.encode()
        r=run({**one,(2,7,'CRC.LST'):ref},'/CHECK');assert expect in r['text'],r['text']
    malformed=(native([('TEST.DAT',1,v)]).replace(b'A687',b'G687'),
               native([('TEST.DAT',1,v)]).replace(b'CRCK5',b'CRCK '),
               native([('TEST.DAT',1,v)])+b'junk\r\n',
               b'--> FILE:  TEST    .DAT CRC = A687 CHEK = E447 CHEK = E447\n',
               b'--> FILE:  TEST    .DAT BOGUS = A687\n',
               native([('TEST.DAT',1,v)],('SUM16','SUM16')),
               native([('TEST.DAT',1,v)],('KERM12','KERM12')),
               native([('TEST.DAT',1,v)],('KERM6',)).replace(b'36',b'FF'),
               native([('TEST.DAT',1,v)],('KERM12',)).replace(b'DF3',b'1DF3'),
               native([('TEST.DAT',1,v)],('SUM8',)).replace(b'F3',b'FFF'),
               b'; empty\n',b'NAME     EXT  RECS  CRCK\nBAD SEPARATOR\n')
    for ref in malformed:
        r=run({**one,(2,7,'CRC.LST'):ref},'/CHECK')
        assert total(r,'Malformed/list errors') and not r['complete'],r['text']
    # Summaries keep the checksum rows visible and never repeat per DU.
    simple=run(one,'/LOCAL=CRC.LST')
    assert simple['text'].endswith('1 file calculated; 1 list written.\r\n'),simple['text']
    assert 'totals:' not in simple['text'] and ': 0' not in simple['text'],simple['text']
    checked=run({**one,(2,7,'CRC.LST'):native([('TEST.DAT',1,v)])},'/CHECK')
    assert checked['text'].endswith('1 verified.\r\n') and checked['complete'],checked['text']
    empty=run({},'/CHECK')
    assert empty['text'].endswith('No files verified; 1 DU/reference error; incomplete.\r\n'),empty['text']
    # Priority, no malformed-reference fallback, ambiguity, locality.
    good=native([('TEST.DAT',1,v)])
    r=run({**one,(2,7,'CRC.LST'):good,(2,7,'CRCKLIST.CRC'):b'bad'},'/CHECK')
    assert total(r,'Files verified')==1
    r=run({**one,(2,7,'CRC.LST'):b'bad',(2,7,'CRCKLIST.CRC'):good},'/CHECK')
    assert total(r,'Files verified')==0 and total(r,'Malformed/list errors')
    r=run({**one,(2,7,'CRCKLIST.001'):good,(2,7,'CRCKLIST.002'):good},'/CHECK')
    assert 'Ambiguous' in r['text'] and not r['reads']
    r=run({**one,(1,3,'CRC.LST'):good},'/CHECK C7:')
    assert 'No CRC list found' in r['text']
    r=run({**one,(2,7,'X.LST'):good},'/CHECK=X.LST TEST.DAT')
    assert total(r,'Files verified')==1
    report={'command_fixtures':count,'binary_bytes':len(image),
            'scope':'compiled command and routine fixtures; platform results separate'}
    out=ROOT/'build/crc-development';out.mkdir(exist_ok=True)
    (out/'HOST-CRC-CHECKS.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'CRC: {count} compiled command/routine fixtures passed')


if __name__ == '__main__':
    main()
