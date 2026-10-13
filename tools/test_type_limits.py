#!/usr/bin/env python3
"""Qualify TYPE selection-counter bounds and its private stack workspace."""
import re
from pathlib import Path
from test_bios import Z80
from test_resident_type import execute
ROOT=Path(__file__).resolve().parents[1]

def main():
    binary=(ROOT/'build/utilities/TYPE.COM').read_bytes();listing=(ROOT/'build/utilities/type.lst').read_text()
    def addr(name):return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
    index=addr('T_FIDX')
    for before in (0,254,255,65534,65535):
        c=Z80(b'');c.mem[0x100:0x100+len(binary)]=binary;c.setword(index,before)
        c.run(addr('T_BUMP'),limit=10000)
        assert c.carry==(before==65535) and c.word(index)==min(65535,before+1),before
    a=(1,3,b'A       TXT');b=(1,3,b'B       TXT')
    injected=[False]
    def exhaust(c,service):
        if service==17 and not injected[0]:c.setword(index,65535);injected[0]=True
    out,calls=execute('/P B3:*.TXT',{a:(b'DATA',0)},transient=True,observe=exhaust)
    assert 'Too many selected files.' in out and not any(f in calls for f in (15,20)),out
    top=addr('T_STACK');bottom=top-128;low=[top]
    def stack(c,service):
        low[0]=min(low[0],c.sp)
        assert bytes(c.mem[bottom:bottom+16])==b'\xff'*16,'TYPE stack guard overwritten'
    data=(b'A\tB\r\n'+bytes(i for i in range(32) if i!=26)+b'\x9aEND\r\n')*50+b'\x1a'
    execute('/P /7 /CTL /T B3:*.TXT',{a:(data,0),b:(data,7)},responses='.< >\x11'.replace(' ',''),transient=True,observe=stack)
    used=top-low[0];assert used<=112,used
    print(f'PASS: TYPE 65,535-file capacity guard and private stack ({used}/128 bytes observed)')
if __name__=='__main__':main()
