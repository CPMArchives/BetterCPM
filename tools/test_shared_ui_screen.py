#!/usr/bin/env python3
"""Compile and exercise screen fields at real 40/80 and byte-limit widths."""
import json
from pathlib import Path
from build_shared_ui_fixtures import BUILD,fixture_source
from shared_ui import UI
from build_ccp import assemble
from test_bios import Z80
from test_utility_versions import address


def main():
    source=fixture_source('engine').replace('LIB_END:',(UI/'screen.inc').read_text()+'''
LIB_END:
UR_PUT: IN A,(120)
        RET
UR_POS: IN A,(121)
        RET
UR_MARK: IN A,(122)
        RET
''')
    BUILD.mkdir(parents=True,exist_ok=True)
    (BUILD/'screen.mac').write_text(source)
    image=assemble(Path.home()/'bin/z80asm',source,BUILD/'screen.bin',BUILD/'screen.lst',0x100)
    listing=(BUILD/'screen.lst').read_text();at=lambda n:address(listing,n)
    count=0
    for width,prefix in ((40,6),(80,14),(255,0),(1,0),(0,0),(40,40),(40,41)):
        for length in (0,9,64,255):
            for cursor in (0,length//2,length):
                for start in (0,cursor,length):
                    c=Z80(b'');c.mem[256:256+len(image)]=image
                    for n,v in [('EDITLEN',length),('EDITCUR',cursor),('EDITSTART',start),('EDITMAX',255)]:c.mem[at(n)]=v
                    data=bytes(33+i%90 for i in range(length));c.mem[at('EDITBUF'):at('EDITBUF')+length]=data
                    cells=bytearray(b' '*max(1,width));pos=prefix;events=[]
                    def io(port):
                        nonlocal pos
                        p=port&255;events.append((p,c.a,c.c))
                        if p==121:pos=c.c
                        else:
                            assert 0<=pos<width,(width,prefix,length,cursor,start,pos)
                            cells[pos]=c.a;pos+=1
                        return c.a
                    c.port_read=io;c.a=width;c.d=prefix;sp=c.sp
                    c.run(at('UR_DRAW'),limit=100000)
                    good=width>prefix
                    assert bool(c.carry)==(not good)
                    if good:
                        first=c.mem[at('EDITSTART')];capacity=width-prefix-1
                        expected_start=min(start,cursor)
                        if cursor-expected_start>capacity:expected_start=cursor-capacity
                        assert first==expected_start
                        expected=bytearray(b' '*width)
                        shown=data[first:first+capacity];expected[prefix:prefix+len(shown)]=shown
                        caret=prefix+cursor-first;expected[caret]=data[cursor] if cursor<length else ord('_')
                        assert cells==expected and pos==caret
                    else:assert not events and c.mem[at('EDITSTART')]==start
                    assert c.sp==sp and c.mem[at('EDITCUR')]==cursor and c.mem[at('EDITLEN')]==length
                    assert bytes(c.mem[at('EDITBUF'):at('EDITBUF')+length])==data
                    count+=1
    result={'cases':count,'result':'pass','scope':'compiled cell renderer, no terminal transport'}
    (BUILD/'screen-results.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':main()
