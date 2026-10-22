#!/usr/bin/env python3
"""Execute CONFIG's shared editor paths with hostile BDOS and a console model."""
from pathlib import Path
import hashlib,json
from test_bios import Z80
from test_utility_versions import address
from startup_record import build,parse
from system_layout import LAYOUT
ROOT=Path(__file__).resolve().parents[1]


def execute(entry,keys,*,reverse=True,old=73):
    image=(ROOT/'build/utilities/CONFIG.COM').read_bytes()
    listing=(ROOT/'build/utilities/config.lst').read_text()
    at=lambda name:address(listing,name)
    cpu=Z80(b'');cpu.mem[256:256+len(image)]=image
    cpu.mem[5:8]=bytes((0xdb,254,0xc9))
    cpu.mem[at('STARTMENU')]=0xc9
    cpu.mem[at('HASREV')]=int(reverse)
    previous=build('OLD STARTUP',system_base=LAYOUT['SYSTEM'])
    base=at('STPEND');cpu.mem[base:base+256]=previous
    cpu.mem[at('STSTATE')]=1;cpu.mem[at('STDIRTY')]=0
    cpu.mem[at('OLDVAL')]=old
    cpu.mem[0xabe6:0xac00]=b'!'*26
    queue=list(keys);out=[];snapshots=[];line=bytearray(b' '*80);column=0
    def io(port):
        nonlocal column,line
        assert port&255==254
        function=cpu.c
        if function==6 and cpu.e==255:
            snapshots.append(bytes(line))
            assert queue,('input exhausted',entry,bytes(out)[-200:])
            value=queue.pop(0)
        else:
            assert function in (6,178),('unexpected service',function)
            value=cpu.e;out.append(value)
            if value==13:column=0
            elif value==10:line=bytearray(b' '*80)
            else:
                assert 0<=column<79,('output wrapped',column)
                line[column]=value|(128 if function==178 else 0);column+=1
            value=0
        cpu.bc=0xbcbc;cpu.de=0xdede;cpu.hl=0xeded
        return value
    cpu.port_read=io;cpu.hl=at('EDVALUE');sp=cpu.sp
    cpu.run(at(entry),limit=1500000)
    assert cpu.sp==sp
    assert cpu.mem[0xabe6:0xac00]==b'!'*26,'editor exceeded private workspace'
    assert not queue,('unused input',queue)
    return cpu,at,bytes(out),snapshots,previous


def main():
    count=0
    def check(*args,**kwargs):
        nonlocal count
        count+=1;return execute(*args,**kwargs)
    # Actual startup commit path, not a stand-in edit routine.
    for reverse in (False,True):
        c,a,out,s,old=check('STEDIT',b'Abc\x13\x07\x08Z\x04!\r',reverse=reverse)
        saved=bytes(c.mem[a('STPEND'):a('STPEND')+256])
        assert parse(saved,system_base=LAYOUT['SYSTEM'])=='AZ!'
        assert c.mem[a('STDIRTY')]==1 and c.mem[a('STSTATE')]==1
        assert any((ord('_')|128) in row if reverse else ord('_') in row for row in s)
    for key in (b'\x1b',b'\x03',b'\r'):
        c,a,out,s,old=check('STEDIT',key)
        assert bytes(c.mem[a('STPEND'):a('STPEND')+256])==old
        assert c.mem[a('STDIRTY')]==0
    c,a,out,s,old=check('STEDIT',b'hello\x7f!\r')
    assert parse(bytes(c.mem[a('STPEND'):a('STPEND')+256]),system_base=LAYOUT['SYSTEM'])=='hell!'
    # Long case-sensitive text scrolls inside one physical line, no CR/LF wraps.
    text=(b'Ab '*42)
    c,a,out,s,old=check('STEDIT',text+b'X\x08Z\r')
    assert b'Input limit reached.' in out
    assert parse(bytes(c.mem[a('STPEND'):a('STPEND')+256]),system_base=LAYOUT['SYSTEM'])==(text[:-1]+b'Z').decode()
    assert c.mem[a('EDITSTART')]>0
    assert any(row[9:20]==text[:11] for row in s)
    for keys,want in [(b'12\x13' + b'0\x04\r',102),(b'123\x13\x07\r',12),
                      (b'123\x08\r',12),(b'65535\r',65535),(b'0\r',0),
                      (b'12X\r\x08\r',12),(b'65536\r\x086\x087\x085\r',65535)]:
        c,a,out,s,old=check('EDNUMBER',keys)
        assert not c.carry and c.de==want,(keys,c.de,out[-150:])
    for keys in (b'\r',b'123\x1b',b'123\x03'):
        c,a,out,s,old=check('EDNUMBER',keys)
        assert c.carry
    c,a,out,s,old=check('EDNUMBER',b'123456\r')
    assert not c.carry and c.de==12345 and b'Input limit reached.' in out
    # Byte fields retain their original empty-Enter default and reject >255.
    c,a,out,s,old=check('NUMBER',b'\r',old=73)
    assert not c.carry and c.a==73
    for keys in (b'\x1b',b'12\x03'):
        c,a,out,s,old=check('NUMBER',keys)
        assert c.carry
    c,a,out,s,old=check('NUMBER',b'256\r\x085\r')
    assert not c.carry and c.a==255 and b'Invalid decimal value.' in out
    c,a,out,s,old=check('NUMBER',b'0\r')
    assert not c.carry and c.a==0
    # Movement/deletion at ends are harmless; DEL is backward, ^G forward.
    c,a,out,s,old=check('STEDIT',b'\x13\x08\x07A\x04\x13B\x04\r')
    assert parse(bytes(c.mem[a('STPEND'):a('STPEND')+256]),system_base=LAYOUT['SYSTEM'])=='BA'
    report={'status':'PASS','cases':count,'bytes':(ROOT/'build/utilities/CONFIG.COM').stat().st_size,
            'sha256':hashlib.sha256((ROOT/'build/utilities/CONFIG.COM').read_bytes()).hexdigest(),
            'scope':'compiled CONFIG paths with destructive BDOS fixture and independent inline console; not native screen qualification'}
    (ROOT/'build/utilities/config-shared-input-tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS: {count} CONFIG shared-input startup/numeric/edit/cancel/scroll/validation cases')


if __name__=='__main__':main()
