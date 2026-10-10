#!/usr/bin/env python3
"""Execute actual field measurement and the automatic/explicit column fit rules."""
import re
from pathlib import Path
from test_bios import Z80
ROOT=Path(__file__).resolve().parents[1]
image=(ROOT/'build/utilities/DIR.COM').read_bytes()
listing=(ROOT/'build/utilities/dir-transient.lst').read_text()
def addr(name):
    return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
cases=0
for unit in 'KSE':
    for attributes in (0,1):
        for records in (0,8,80,800,8000,80000,800000,8000000,80000000,800000000,0xfffffff8):
            value=records//8 if unit=='K' else records
            width=14+len(str(value))+1+5*attributes
            maximum=next(n for n in (4,2,1) if n*width+(n-1)*3<=80)
            for request in (0,1,2,4):
                c=Z80(b'');c.mem[256:256+len(image)]=image;c.mem[5]=0x76
                buffer=addr('DT_BUFFER')
                wide=b'WIDTH   DAT'+bytes([7])+(8 if unit=='E' else records).to_bytes(4,'little')+bytes(4)+records.to_bytes(4,'little')
                narrow=b'EMPTY   DAT'+bytes([0])+bytes(12)
                entries=wide+narrow if cases%2 else narrow+wide
                c.mem[buffer:buffer+48]=entries
                c.setword(addr('DT_FILES'),2)
                c.mem[addr('DG_PAGE')]=1
                c.mem[addr('DT_UNIT')]=ord(unit)
                c.mem[addr('DT_SHOWATTR')]=attributes
                c.mem[addr('DC_REQUEST')]=request
                c.run(addr('DC_LAYOUT'),limit=100000)
                assert c.mem[addr('DC_WIDTH')]==width,(unit,records,attributes,c.mem[addr('DC_WIDTH')],width)
                assert c.carry==(request>maximum),(request,maximum)
                assert c.mem[addr('DC_COLS')]==(request or maximum)
                assert c.mem[addr('DG_MEASURE')]==0
                assert c.mem[addr('DG_LINES')]==0
                assert bytes(c.mem[buffer:buffer+48])==entries
                cases+=1
print(f'DIR actual rendered widths and column fit: {cases} cases PASS')
