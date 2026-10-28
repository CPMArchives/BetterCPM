#!/usr/bin/env python3
"""Execute compiled MD5SUM against independent hashlib and hostile BDOS fixtures."""
from pathlib import Path
import hashlib
import json
import re
from test_bios import Z80
from test_crc import execute, name83, records

ROOT=Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.md5(data).hexdigest()


def entry(name,data,mode='*'):
    return (digest(data)+' '+mode+name+'\r\n').encode()


def main():
    count=0
    def run(*args,**kwargs):
        nonlocal count
        count+=1
        return execute(*args,program='MD5SUM',**kwargs)
    image=(ROOT/'build/utilities/MD5SUM.COM').read_bytes()
    listing=(ROOT/'build/utilities/md5sum.lst').read_text().splitlines()
    sym={n:int(next(x[:4] for x in listing if re.search(r'\b'+n+':',x)),16)
         for n in ('CINIT','CUPDATE','CFINISH','CVALUES','MDLENGTH')}
    vectors=[b'',b'a',b'abc',b'123456789',records(b'123456789'),bytes(range(256))]
    vectors += [bytes((i*73+19)&255 for i in range(n)) for n in (55,56,63,64,65,127,128,129,255,513)]
    for raw in vectors:
        c=Z80(b'');c.mem[256:256+len(image)]=image
        c.run(sym['CINIT'],limit=10000)
        for byte in raw:c.a=byte;c.run(sym['CUPDATE'],limit=200000)
        c.run(sym['CFINISH'],limit=200000)
        assert bytes(c.mem[sym['CVALUES']:sym['CVALUES']+16]).hex()==digest(raw)
        count+=1
    # Carry into high MD5 length words without generating a multi-gigabyte file.
    c=Z80(b'');c.mem[256:256+len(image)]=image;c.run(sym['CINIT'],limit=10000)
    c.mem[sym['MDLENGTH']:sym['MDLENGTH']+8]=(0xfffffff8).to_bytes(8,'little')
    c.a=0;c.run(sym['CUPDATE'],limit=10000)
    assert int.from_bytes(c.mem[sym['MDLENGTH']:sym['MDLENGTH']+8],'little')==0x100000000
    data=records(b'123456789');f={(2,7,'TEST.DAT'):data,(2,7,'NOEXT'):b''}
    for tail in ('/VER','/HELP /VER BAD','/VER /HELP /MD5','/help\t/WHAT'):
        r=run(f,tail);assert not set(r['services']) & {14,15,17,25,26,32,35},r['text']
    for tail in ('/MD5','/CRCK','/LEGACY','/UNKNOWN','/HELPER','/VERIFY',
                 '/CHECK=B:MD5SUM.LST','/LOCAL=C3:MD5SUM.LST','/FILE=*.*','/FILE=',
                 '/LOCAL=','/CHECK=','/FILE=B[1-2]:LST','/CHECK /FILE=MD5SUM.LST',
                 '/CHECK /LOCAL=LST','Q:FILE','A32:','TOOLONGNM.TXT',
                 'TEST.DAT /FILE=TEST.DAT','TEST.DAT /LOCAL=TEST.DAT',
                 '/LOCAL=B:LST /LOCAL=LST'):
        r=run(f,tail);assert 'invalid command' in r['text'] and not set(r['services']) & {15,17,19,21,22,23},(tail,r['text'])
    expected=entry('NOEXT',b'')+entry('TEST.DAT',data)
    for tail in ('/FILE=MD5SUM.LST','/FILE=MD5SUM.LST /40','/LOCAL=MD5SUM.LST'):
        r=run(f,tail);saved=r['files'][2,7,name83('MD5SUM.LST')].split(b'\x1a')[0]
        assert saved==expected,(tail,saved,r['text'])
        assert '; BetterCP/M' not in r['text'] and 'RECS' not in r['text'],r['text']
        if '/40' in tail:assert all(len(line)<=40 for line in r['text'].splitlines()),r['text']
        else:assert expected.decode() in r['text'],r['text']
        checked=run({**f,(2,7,'MD5SUM.LST'):saved},'/CHECK')
        assert checked['complete'] and '2 verified.' in checked['text'],checked['text']
    for text in (expected,expected.replace(b' *',b'  '),expected.upper(),expected.lower(),
                 expected.replace(b'\r\n',b'\n'),expected.rstrip(b'\r\n'),b'\r\n'+expected):
        r=run({**f,(2,7,'REF.LST'):text},'/CHECK=REF.LST')
        assert r['complete'] and '2 verified.' in r['text'],r['text']
    for bad in (b'garbage',b'',b'; comment',b'0'*31+b' *TEST.DAT',b'g'*32+b' *TEST.DAT',
                b'0'*32+b'  *TEST.DAT',b'0'*32+b' *B:TEST.DAT',b'0'*32+b' *dir/TEST.DAT',
                b'0'*32+b' *dir\\TEST.DAT',b'0'*32+b' *TEST.DAT extra',
                b'0'*32+b' *TEST.DAT\x00garbage',b'0'*32+b' *TEST.DAT\x80',
                entry('TEST.DAT',data).replace(b'*TEST',b'*TE\rST'),
                b'0'*32+b' *',b'0'*32+b' *TOOLONGNM.COM',b'x'*300):
        r=run({**f,(2,7,'MD5SUM.LST'):bad},'/CHECK TEST.DAT')
        assert not r['complete'] and 'LIST ERROR' in r['text'],(bad,r['text'])
    wrong=entry('TEST.DAT',b'wrong')
    for text in (wrong+entry('TEST.DAT',data),entry('TEST.DAT',data)+wrong):
        r=run({**f,(2,7,'MD5SUM.LST'):text},'/CHECK TEST.DAT')
        assert r['complete'] and '1 verified.' in r['text'] and 'Differing alternative' in r['text'],r['text']
    r=run({**f,(2,7,'MD5SUM.LST'):wrong},'/CHECK TEST.DAT')
    assert not r['complete'] and 'MD5 MISMATCH' in r['text'],r['text']
    r=run({**f,(2,7,'MD5SUM.LST'):entry('MISSING.COM',b'')},'/CHECK')
    assert not r['complete'] and 'FILE NOT FOUND' in r['text'] and 'FILE NOT LISTED' in r['text'],r['text']
    r=run({**f,(0,0,'MD5SUM.LST'):expected},'/CHECK TEST.DAT')
    assert 'No MD5 list found' in r['text'] and not r['reads'],r['text']
    many={(1,3,'Z.DAT'):data,(1,3,'A.DAT'):b'',(1,1,'A.DAT'):data,(2,7,'C.DAT'):data}
    r=run(many,'B[3,1]: B3:*.DAT C7: /FILE=C7:MD5SUM.LST /LOCAL=MD5SUM.LST')
    master=r['files'][2,7,name83('MD5SUM.LST')].split(b'\x1a')[0]
    assert master==entry('A.DAT',data)+entry('A.DAT',b'')+entry('Z.DAT',data)+entry('C.DAT',data),master
    assert r['text'].endswith('4 files calculated; 3 lists written.\r\n'),r['text']
    for key,payload in many.items():
        assert sum(k==(key[0],key[1],name83(key[2])) for k,pos in r['reads'])==len(payload)//128+1
    old=b'old list'+b'\x1a'*120
    for keys in (b'N',b'n'):
        r=run({**f,(2,7,'MD5SUM.LST'):old},'/FILE=MD5SUM.LST',keys=keys)
        assert r['files'][2,7,name83('MD5SUM.LST')]==old and '1 list declined' in r['text']
    for keys in (b'Y',b'\r',b'A'):
        r=run({**f,(2,7,'MD5SUM.LST'):old},'/FILE=MD5SUM.LST',keys=keys)
        assert r['files'][2,7,name83('MD5SUM.LST')].startswith(expected),r['text']
    for fault in ((22,1),(21,1),(23,1),(16,2)):
        r=run({**f,(2,7,'MD5SUM.LST'):old},'/FILE=MD5SUM.LST',fault=fault)
        assert r['files'].get((2,7,name83('MD5SUM.LST')))==old,(fault,r['text'])
    r=run({**f,(2,7,'MD5SUM.LST'):old},'/FILE=MD5SUM.LST',cancel_at=8)
    assert r['files'][2,7,name83('MD5SUM.LST')]==old and 'cancelled' in r['text'],r['text']
    # The actual command stream crosses 64 KiB; no 16-bit byte-count truncation.
    large=bytes(range(256))*257
    r=run({(2,7,'LARGE.BIN'):large},'/FILE=MD5SUM.LST',limit=100000000)
    assert r['files'][2,7,name83('MD5SUM.LST')].startswith(entry('LARGE.BIN',large)),r['text']
    report={'status':'PASS','fixtures':count,'binary_bytes':len(image),'sha256':hashlib.sha256(image).hexdigest()}
    out=ROOT/'build/md5sum-development';out.mkdir(parents=True,exist_ok=True)
    (out/'HOST-MD5SUM-CHECKS.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'MD5SUM: {count} compiled command/routine fixtures passed')


if __name__=='__main__':main()
