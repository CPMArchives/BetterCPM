#!/usr/bin/env python3
"""Version requests are pure; invalid combinations cannot invoke command work."""
from pathlib import Path
import re
from test_bios import Z80
from utility_versions import banner, identities
ROOT=Path(__file__).resolve().parents[1]
def address(listing,name):
    return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
def runner(image,base=256):
    c=Z80(b'');c.mem[base:base+len(image)]=image
    # Record output service; a nonreturning WBOOT ends handled requests.
    c.mem[0:3]=bytes.fromhex("c3ffff")
    c.mem[5:14]=bytes.fromhex('ed530070ed430270c9')
    return c
def output(c):
    assert c.word(0x7002)&255==9,('unexpected BDOS service',c.word(0x7002))
    p=c.word(0x7000);end=c.mem.index(36,p)
    return bytes(c.mem[p:end]).decode()
def main():
    count=0
    for name in identities():
        if name=='RCP':continue
        image=(ROOT/f'build/utilities/{name}.COM').read_bytes()
        for tail in ['/VER',' /ver  ','/VER x','x /VER','/VER /VER','/VER /B']:
            c=runner(image);data=tail.encode();c.mem[128]=len(data);c.mem[129:129+len(data)]=data
            c.run(256,limit=100000)
            expected=banner(name)+'\r\n' if tail.strip().upper()=='/VER' else 'Invalid /VER usage.\r\n'
            assert output(c)==expected,(name,tail,output(c));count+=1
    image=(ROOT/'build/cpx/rcp.bin').read_bytes()
    listing=(ROOT/'build/cpx/rcp.lst').read_text()
    for name in ['DIR','ERA','TYPE','REN','CLS','USER','VER','COPY','MOVE']:
        c=runner(image,0x8000);tail=(name+' /VER').encode();c.mem[0x6000:0x6000+len(tail)]=tail
        c.de=0x6000;c.b=len(tail);c.run(address(listing,'BC_COMMAND'),limit=100000)
        assert output(c)==banner(name,True)+'\r\n' and c.carry,name;count+=1
    for tail in ['', 'A0:*.COM', '/VERIFY', '/VERBOSE','X/VER','/VER=X',' /B A:FOO B: ']:
        c=runner(image,0x8000);data=tail.encode();c.mem[0x6000:0x6000+len(data)]=data
        c.hl=0x6000;c.bc=len(data)*256+77;c.de=0x4567
        before=(c.hl,c.bc,c.de);c.run(address(listing,'UV_QUERY'),limit=100000)
        assert not c.carry and (c.hl,c.bc,c.de)==before and c.word(0x7002)==0,tail;count+=1
    print(f'{count} utility identity, resident dispatch, invalid usage, and pure fall-through checks pass')
if __name__=='__main__':main()
