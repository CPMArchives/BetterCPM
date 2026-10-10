#!/usr/bin/env python3
"""Execute live allocation-vector arithmetic, including inclusive DSM and padding."""
import random
import re
from pathlib import Path
from test_bios import Z80
ROOT=Path(__file__).resolve().parents[1]
image=(ROOT/'build/utilities/DIR.COM').read_bytes()
listing=(ROOT/'build/utilities/dir-transient.lst').read_text()
def addr(name):
    return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
rng=random.Random(31);cases=0
for dsm in (0,1,7,8,9,15,255,256,1023,8191,65535):
    for bsh in (3,4,5,6,7):
        for mode in ('free','used','mixed'):
            size=(dsm+8)//8
            vector=bytes(size) if mode=='free' else bytes([255])*size if mode=='used' else bytes(rng.randrange(256) for _ in range(size))
            expected=sum(not(vector[n//8]&(128>>(n%8))) for n in range(dsm+1))*(1<<(bsh-3))
            c=Z80(b'');c.mem[256:256+len(image)]=image;c.mem[5]=0x76
            dpb=bytearray(15);dpb[2]=bsh;dpb[5:7]=dsm.to_bytes(2,'little')
            c.mem[0x5000:0x500f]=dpb;c.mem[0x6000:0x6000+size]=vector
            c.hl=0x5000;c.de=0x6000;c.run(addr('DF_COUNT'),limit=10000000)
            result=int.from_bytes(c.mem[addr('DF_VALUE'):addr('DF_VALUE')+4],'little')
            assert result==expected,(dsm,bsh,mode,result,expected)
            assert bytes(c.mem[0x6000:0x6000+size])==vector
            cases+=1
print(f'DIR free KiB: {cases} inclusive DSM/MSB-first/padding/DWORD cases PASS')
