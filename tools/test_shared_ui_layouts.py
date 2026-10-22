#!/usr/bin/env python3
"""Compiled standard default and choice-error formatting contracts."""
import json
from pathlib import Path
from build_shared_ui_fixtures import BUILD,fixture_source
from shared_ui import UI
from build_ccp import assemble
from test_bios import Z80
from test_utility_versions import address


def main():
    modules='\n'.join((UI/n).read_text() for n in ('format.inc','default.inc','choiceerror.inc'))
    source=fixture_source('combined').replace('LIB_END:',modules+'\nLIB_END:')
    source=source.replace('        END\n','''UF_LABEL: DW LABEL
UF_WIDTH: DB 79
LAYLEFT: DB 90
UF_BUF:
        REPT 256
        DB 165
        ENDM
LAYRIGHT: DB 90
        END
''')
    BUILD.mkdir(parents=True,exist_ok=True);(BUILD/'layouts.mac').write_text(source)
    image=assemble(Path.home()/'bin/z80asm',source,BUILD/'layouts.bin',BUILD/'layouts.lst',0x100)
    listing=(BUILD/'layouts.lst').read_text();at=lambda n:address(listing,n)
    count=0
    def new(label,width):
        c=Z80(b'');c.mem[256:256+len(image)]=image
        c.setword(at('UF_LABEL'),0x8000);c.mem[0x8000:0x8000+len(label)+1]=label+b'\0'
        c.mem[at('UF_WIDTH')]=width
        c.setword(at('UP_DPTR'),0x8200);c.mem[0x8200:0x8207]=b'DEFAULT'
        c.mem[at('UP_DLEN')]=7;c.mem[at('EDITLEN')]=0;c.mem[at('UP_MODE')]=3
        c.setword(at('UC_LIST'),at('CHOICES'));c.mem[at('UC_COUNT')]=2;c.mem[at('UC_DEF')]=ord('N')
        return c
    def call(c,name):
        nonlocal count
        state=bytes(c.mem[at('EDITLEN'):at('UF_LABEL')+3]);sp=c.sp
        c.run(at(name),limit=100000)
        assert c.sp==sp and state==bytes(c.mem[at('EDITLEN'):at('UF_LABEL')+3])
        assert c.mem[at('LAYLEFT')]==90 and c.mem[at('LAYRIGHT')]==90
        count+=1
    for label in (b'',b'Value: ',b'X'*30,b'X'*245,b'Bad\t'):
        for width in (0,1,39,40,79,80,255):
            for mode,length in ((3,0),(3,1),(0,0),(1,0),(2,0)):
                c=new(label,width);c.mem[at('UP_MODE')]=mode;c.mem[at('EDITLEN')]=length
                expected=label+(b'[DEFAULT] ' if mode==3 and not length else b'')
                call(c,'UT_TEXT');good=b'\t' not in label and len(expected)<width
                assert bool(c.carry)==(not good),(label,width,mode,length)
                if good:
                    assert c.a==0 and c.b==len(expected) and c.hl==at('UF_BUF')
                    assert bytes(c.mem[c.hl:c.hl+c.b+1])==expected+b'\0'
                else:assert c.a==7 and bytes(c.mem[at('UF_BUF'):at('UF_BUF')+256])==bytes([165])*256
    for label in (b'',b'Erase? ',b'X'*30):
        for width in (0,9,10,11,19,39,79,255):
            for msg in (b'',b'Invalid.',b'X'*255,b'Bad\t'):
                c=new(label,width);c.hl=0x8400;c.mem[c.hl:c.hl+len(msg)+1]=msg+b'\0'
                prompt=label+b'(Y/N) [N]';room=width-len(prompt)-1
                shown=msg[:max(0,room)]
                if len(msg)>room and room>0:shown=shown[:-1]+b'~'
                expected=prompt+b' '+shown
                call(c,'UE_ERROR');good=room>=1 and b'\t' not in msg[:max(0,room)]
                assert bool(c.carry)==(not good),(label,width,msg,c.a)
                if good:
                    assert c.a==0 and c.hl==at('UF_BUF') and c.b==len(expected)
                    assert bytes(c.mem[c.hl:c.hl+c.b+1])==expected+b'\0'
                else:assert c.a==7
    report={'cases':count,'result':'pass','scope':'compiled layout only, no terminal transport'}
    (BUILD/'layouts-results.json').write_text(json.dumps(report,indent=2)+'\n');print(report)


if __name__=='__main__':main()
