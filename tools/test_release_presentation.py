#!/usr/bin/env python3
"""Execute changed DIR report and RSX LIST paths with a fixture BDOS."""
from pathlib import Path
import re
from test_bios import Z80
ROOT=Path(__file__).resolve().parents[1]

def program(name, listing):
    c=Z80(b'')
    data=(ROOT/'build/utilities'/name).read_bytes()
    c.mem[256:256+len(data)]=data
    c.mem[5:8]=b'\xd3\x00\xc9'
    text=(ROOT/'build/utilities'/listing).read_text()
    def addr(label):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+label+':',text,re.M|re.I)[1],16)
    return c,addr

for unit in 'KSE':
    for attrs in (0,1):
        for user in (0,12):
            c,a=program('DIR.COM','dir-transient.lst');out=bytearray()
            dpb,alv=0x7000,0x7100
            c.mem[dpb+2]=3;c.setword(dpb+5,99)
            def bdos(port,value):
                if c.c==2:out.append(c.e)
                elif c.c==25:c.a=0
                elif c.c==31:c.hl=dpb
                elif c.c==27:c.hl=alv
                else:raise AssertionError(c.c)
            c.port_write=bdos
            c.mem[a('RD_NEXT')]=0xc9
            c.mem[a('RD_USER')]=user
            c.mem[a('DT_UNIT')]=ord(unit)
            c.mem[a('DT_SHOWATTR')]=attrs
            records=[]
            for n,size in (('SMALL   COM',8),('LARGE   COM',800)):
                records.append(n.encode()+bytes([0])+size.to_bytes(4,'little')+size.to_bytes(4,'little')+(1).to_bytes(4,'little'))
            start=a('DT_BUFFER');c.mem[start:start+48]=b''.join(records)
            c.setword(a('DT_FILES'),2);c.setword(a('DT_END'),start+48)
            c.mem[a('DT_TOTAL'):a('DT_TOTAL')+12]=(808).to_bytes(4,'little')*2+(2).to_bytes(4,'little')
            c.run(a('DT_REPORT'),limit=500000)
            text=out.decode();lines=text.splitlines()
            row=next(x for x in lines if 'LARGE' in x)
            cells=row.split(' : ')
            assert len(cells[0])==len(cells[1]),row
            assert all(re.search(r'COM +[0-9]+['+unit+r'](?:  ---)?$',cell) for cell in cells),row
            assert max(map(len,lines))<=80,text
            total={'K':'101K','S':'808S','E':'2E'}[unit]
            assert f'---- 2 FILES, {total} TOTAL, 100K FREE ----' in text,text
            assert text.count('FREE')==1 and f'A{user}:\r\n' in text,text
# Empty DU still reports its free space.
c,a=program('DIR.COM','dir-transient.lst');out=bytearray()
def empty_bdos(port,value):
    if c.c==2:out.append(c.e)
    elif c.c==25:c.a=3
    elif c.c==31:c.hl=0x7000
    elif c.c==27:c.hl=0x7100
    else:raise AssertionError(c.c)
c.port_write=empty_bdos;c.mem[a('RD_NEXT')]=0xc9
c.mem[0x7002]=3;c.setword(0x7005,99)
c.run(a('DT_REPORT'),limit=100000)
assert 'NO FILE' in out.decode() and '100K FREE' in out.decode(),out
# RSX LIST: zero, one and two profile entries; TPA starts on its own line.
for names in ((),('ADM3A',),('M4SCRN','ADM3A')):
    c,a=program('RSX.COM','rsx.lst');out=bytearray()
    c.mem[5]=0xc3;c.setword(6,0xd000)
    c.mem[0xd000:0xd003]=b'\xd3\x00\xc9'
    c.mem[0x80]=4;c.mem[0x81:0x85]=b'LIST'
    def rsx_bdos(port,value):
        if c.c==9:
            p=c.de
            while c.mem[p]!=36:out.append(c.mem[p]);p+=1
        elif c.c==2:out.append(c.e)
        elif c.c==177:
            p=c.de;i=c.mem[p+2]
            c.a=int(i<len(names))
            if c.a:c.mem[p+4:p+12]=names[i].ljust(8).encode();c.mem[p+12]=255
        else:raise AssertionError(c.c)
    c.port_write=rsx_bdos
    c.run(0x100,limit=100000)
    assert b'\r\nTPA available: ' in out,out
    assert b'255TPA' not in out,out
print('DIR populated/empty DU, units, alignment and RSX LIST presentation: PASS')

# Execute the release-identification paths, rather than trusting binary hashes
# or the legacy TSV projection as evidence that revisions reached the binaries.
from component_registry import utility_identities
from test_utility_versions import runner, output
from test_crc import execute
expected_revisions={'DIR':10,'RSX':6,'CRCKSUM':7,'COMPARE':3}
for name,revision in expected_revisions.items():
    assert utility_identities()[name]==('1.0',revision)
    if name in ('DIR','RSX'):
        c=runner((ROOT/'build/utilities'/(name+'.COM')).read_bytes())
        c.mem[128]=4;c.mem[129:133]=b'/VER'
        c.run(256,limit=100000)
        text=output(c)
    elif name=='COMPARE':
        from test_compare import execute as compare_query
        text=compare_query(tail='/VER')['text']
    else:
        text=execute(tail='/VER',program=name)['text']
    assert text.startswith(f'{name} 1.0 ({revision:03}-dev)\r\n'),(name,text)
    print(text.splitlines()[0])
print('Packaged-component revision query paths: PASS')
