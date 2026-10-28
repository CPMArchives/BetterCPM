#!/usr/bin/env python3
"""Execute compiled PATCH against a fault-injecting CP/M 2.2 BDOS model."""
from pathlib import Path
import re
from test_bios import Z80
from test_crc import name83, records
ROOT=Path(__file__).resolve().parents[1]

def execute(files=None, tail='', *, caller=(2, 7), keys=b'Y', fault=None,
            cancel_at=None, size_override=None, limit=30000000, program='PATCH', attrs=None, mutate=None):
    c = Z80(b'')
    image = (ROOT/('build/utilities/'+program+'.COM')).read_bytes()
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
        for off in (attrs or {}).get(key,[]): c.mem[dma+off] |= 128
        c.a = 0

    def bdos(port, value):
        nonlocal drive, user, dma, keypos, polls, search, searchpos
        fn = c.c
        services.append(fn)
        counts[fn] = counts.get(fn, 0)+1
        fail = ((fn, counts[fn]) in fault if isinstance(fault, set)
                else fault == (fn, counts[fn]))
        addr = c.de
        if mutate: mutate(fn, counts[fn], disk, c, dma)
        if fn == 2:
            output.append(c.e)
        elif fn == 1:
            c.a = keys[keypos] if keypos < len(keys) else 13
            keypos += 1
        elif fn == 6:
            if c.e != 255:
                output.append(c.e)
            elif cancel_at is not None and polls >= cancel_at:
                c.a = 3
            else:
                c.a = keys[keypos] if keypos < len(keys) else 13
                keypos += 1
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
        elif fn == 33:
            key = identity(addr)
            pos = int.from_bytes(c.mem[addr+33:addr+36], 'little')
            reads.append((key,pos))
            if fail: c.a=2
            elif key not in disk or pos*128>=len(disk[key]): c.a=1
            else:
                c.mem[dma:dma+128]=disk[key][pos*128:pos*128+128]
                c.a=0
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
    listing=(ROOT/'build/utilities/patch.lst').read_text().splitlines()
    top=int(next(x[:4] for x in listing if re.search(r'\bSTKTOP:',x)),16)
    assert bytes(c.mem[top-512:top-448]) == b'\xff'*64,'private stack guard touched'
    return dict(text=output.decode('ascii'), files={k: bytes(v) for k, v in disk.items()},
                services=services, reads=reads, writes=writes,
                complete='full verification passed.' in output.decode('ascii'))


def fixture(text,data=None,old=None):
    f={(2,7,'FIX.PAT'):text.encode(),(2,7,'IN.DAT'):bytes(range(128)) if data is None else data}
    if old is not None:f[2,7,'OUT.DAT']=old
    return f


def main():
    import json,hashlib
    count=0
    def run(*args,**kwargs):
        nonlocal count
        count+=1
        return execute(*args,**kwargs)
    def out(r,name='OUT.DAT',du=(2,7)):
        return r['files'].get((*du,name83(name)))
    def unchanged(r,f):
        for (d,u,n),b in f.items():assert r['files'].get((d,u,name83(n)))==records(b),(n,r['text'])
    p='INPUT IN.DAT\r\nOUTPUT OUT.DAT\r\n00: 00 01 02 -> FF FE\r\n02: 02 03 -> FD\r\n'
    expected=bytes([255,254,253])+bytes(range(3,128))
    f=fixture(p)
    for tail in ('/HELP /VER BAD','/VER /HELP /BOGUS','/help\t/WHAT','/VER'):
        r=run(f,tail);assert not set(r['services'])&{14,15,17,25,26,32,35};unchanged(r,f)
    for tail in ('','/BOGUS','FIX.PAT EXTRA.PAT','FIX.PAT /INPUT=',
                 'FIX.PAT /OUTPUT=*.*','B[1-3]:FIX.PAT','FIX.PAT /INPUT=Q:FOO',
                 'FIX.PAT /OUTPUT=OUT.DAT /OUTPUT=OTHER.DAT','/VERIFY'):
        r=run(f,tail);assert not r['complete'] and not r['writes'],(tail,r['text']);unchanged(r,f)
    for text in (p,p.lower(),p.replace('00:', '00h :'),p.replace('\r\n','\n'),p.replace('\r\n','\r'),p.rstrip(),'; header\r\n\r\n'+p,p.replace('->',' -> '),p+'; comment'):
        r=run(fixture(text),'FIX.PAT');assert r['complete'] and out(r)==expected,r['text']
    r=run(f,'FIX.PAT /INPUT=IN.DAT /OUTPUT=B3:NEW.DAT')
    assert r['complete'] and out(r,'NEW.DAT',(1,3))==expected,r['text']
    for output in ('IN.DAT','C7:IN.DAT','FIX.PAT','C7:FIX.PAT'):
        r=run(f,'FIX.PAT /OUTPUT='+output);assert not r['writes'] and not r['complete'];unchanged(r,f)
    base='INPUT IN.DAT\nOUTPUT OUT.DAT\n'
    bads=['00: 00 ->','00: -> 01','00: 0 -> 01','00: 00 -> 0',
          '00: 00 -> 01 02','00: 00 -> GG','00: 00 -> 01 extra',
          '00: 00 01 -> 02\n01: 01 -> 03\n00: 00 -> 04',
          '00: 00 -> 01\n00: 00 -> 01','80: 00 -> 01',
          'FFFFFFFF: 00 -> 01','100000000: 00 -> 01',
          '00: 01 -> 02','INPUT IN.DAT\n00: 00 -> 01',
          '00: 00 -> 01\x00','00: 00 -> 01\x1aX',';'+('x'*255)]
    for body in bads:
        fbad=fixture(base+body)
        r=run(fbad,'FIX.PAT');assert not r['complete'] and not r['writes'] and 22 not in r['services'],(body,r['text']);unchanged(r,fbad)
        if 'line' not in r['text']:raise AssertionError(r['text'])
    for text in ('',base,base+'; nothing'):
        r=run(fixture(text),'FIX.PAT');assert not r['complete'] and 22 not in r['services'],r['text']
    r=run(fixture(base+';'+('x'*254)+'\n00: 00 -> 01'),'FIX.PAT')
    assert r['complete'],r['text']
    for body in ('00: 00 01 02 03 -> FF FE\n02: 02 03 -> FD',
                 '02: 02 03 -> FD\n00: 00 01 02 03 -> FF FE'):
        r=run(fixture(base+body),'FIX.PAT');assert r['complete'] and out(r)==expected,r['text']
    r=run(fixture(base+'00: 00 01 -> 00'),'FIX.PAT')
    assert r['complete'] and 'replacement bytes: 1; changed bytes: 0' in r['text'],r['text']
    raw=bytes(range(256))
    r=run(fixture(base+'7F: 7F 80 81 -> FE FD FC',raw),'FIX.PAT')
    assert r['complete'] and out(r)==raw[:127]+bytes([254,253,252])+raw[130:],r['text']
    # Known original record bytes, including padding, must survive unchanged.
    raw=records(b'abc')
    r=run(fixture(base+'02: 63 1A -> 64',raw),'FIX.PAT')
    assert r['complete'] and out(r)==b'abd'+raw[3:],r['text']
    bad=fixture(base+'00: FF -> 01\n01: FF -> 02')
    r=run(bad,'FIX.PAT');assert r['text'].count('Expected-byte mismatch')==1
    r=run(bad,'FIX.PAT /VERBOSE');assert r['text'].count('Expected-byte mismatch')==2 and 22 not in r['services'],r['text']
    old=records(b'old output')
    for keys in (b'N',b'n',b'\r',b'?N',b'??n',b'XN'):
        fo=fixture(p,old=old);r=run(fo,'FIX.PAT',keys=keys)
        assert not r['complete'] and out(r)==old and 22 not in r['services'],r['text'];unchanged(r,fo)
    for keys in (b'Y',b'y',b'?Y',b'??y'):
        r=run(fixture(p,old=old),'FIX.PAT',keys=keys)
        assert r['complete'] and out(r)==expected and len(r['files'])==3,r['text']
        if b'?' in keys:assert r['text'].count('C7:OUT.DAT exists.')==keys.count(b'?')+1,r['text']
    r=run(fixture(p,old=old),'FIX.PAT',keys=b'RB3:NEW.DAT\r')
    assert r['complete'] and out(r)==old and out(r,'NEW.DAT',(1,3))==expected,r['text']
    for attr in ([9],[10],[9,10]):
        fo=fixture(p,old=old)
        r=run(fo,'FIX.PAT',attrs={(2,7,name83('OUT.DAT')):attr})
        assert not r['complete'] and out(r)==old and 22 not in r['services'],r['text']
    for fault in ((22,1),(21,1),(16,1),(33,1),(23,1),(23,2)):
        fo=fixture(p,old=old);r=run(fo,'FIX.PAT',fault=fault)
        assert not r['complete'] and out(r)==old,(fault,r['text']);unchanged(r,fo)
    r=run(fixture(p,old=old),'FIX.PAT',fault={(23,2),(23,3)})
    assert not r['complete'] and 'Restore failed' in r['text'] and 'Verified staged file retained' in r['text'],r['text']
    assert old in r['files'].values() and expected in r['files'].values(),r['files']
    r=run(fixture(p,old=old),'FIX.PAT',fault=(19,1))
    assert r['complete'] and out(r)==expected and 'backup retained' in r['text'] and old in r['files'].values(),r['text']
    # Deliberately occupy transaction slots; none may be overwritten.
    occupied={**fixture(p),(2,7,'PAT00000.TMP'):old,(2,7,'PAT00001.TMP'):old}
    r=run(occupied,'FIX.PAT');assert r['complete'] and out(r)==expected;unchanged(r,occupied)
    for point in (1,3,10,25):
        fo=fixture(p,old=old);r=run(fo,'FIX.PAT',cancel_at=point)
        assert not r['complete'] and out(r)==old and 'Cancelled' in r['text'],(point,r['text']);unchanged(r,fo)
    # Corrupt the staged record as it is read for mandatory verification.
    flipped=[False]
    def corrupt_stage(fn,n,disk,c,dma):
        if fn==33:
            name=bytes(x&127 for x in c.mem[c.de+1:c.de+12])
            if name.endswith(b'TMP') and not flipped[0]:
                key=next(k for k in disk if k[2]==name)
                disk[key][0]^=1;flipped[0]=True
    fo=fixture(p,old=old);r=run(fo,'FIX.PAT',mutate=corrupt_stage)
    assert not r['complete'] and out(r)==old and 'Full-output verification failed' in r['text'],r['text']
    changed=[False]
    def alter_patch(fn,n,disk,c,dma):
        if fn==35 and n==3 and not changed[0]:
            key=(2,7,name83('FIX.PAT'))
            disk[key][:]=disk[key].replace(b'FF FE',b'EE FE');changed[0]=True
    r=run(fixture(p),'FIX.PAT',mutate=alter_patch)
    assert not r['complete'] and 'changed between passes' in r['text'] and 22 not in r['services'],r['text']
    def alter_input(fn,n,disk,c,dma):
        if fn==22:disk[2,7,name83('IN.DAT')][0]^=1
    r=run(fixture(p,old=old),'FIX.PAT',mutate=alter_input)
    assert not r['complete'] and out(r)==old and 'Expected-byte mismatch' in r['text'],r['text']
    # Cleanup failure must name an incomplete stage; no final output is installed.
    r=run(fixture(p),'FIX.PAT',fault={(21,1),(19,1)})
    assert not r['complete'] and out(r) is None and 'Cleanup failed; retained' in r['text'],r['text']
    # Text EOF accepts zero/1Ah record padding but never hidden statement text.
    r=run(fixture(p+'\x1a'+('\x00'*13)),'FIX.PAT')
    assert r['complete'],r['text']
    report={'status':'PASS','cases':count,'binary_sha256':hashlib.sha256((ROOT/'build/utilities/PATCH.COM').read_bytes()).hexdigest()}
    dest=ROOT/'build/patch-development';dest.mkdir(parents=True,exist_ok=True)
    (dest/'model-evidence.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PATCH: {count} compiled BDOS scenarios PASS')

if __name__=='__main__':main()
