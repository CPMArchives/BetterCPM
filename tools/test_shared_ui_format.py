#!/usr/bin/env python3
"""Exercise actual choice formatter bytes without terminal I/O."""
import json
from build_shared_ui_fixtures import BUILD,ROOT,fixture_source
from build_ccp import assemble
from shared_ui import UI
from test_bios import Z80
from test_utility_versions import address


def main():
    source=fixture_source('choice').replace('LIB_END:',(UI/'format.inc').read_text()+'\nLIB_END:')
    source=source.replace('        END\n', '''UF_LABEL: DW LABEL
UF_WIDTH: DB 79
FMTLEFT: DB 90
UF_BUF:
        REPT 256
        DB 165
        ENDM
FMTRIGHT: DB 90
        END
''')
    BUILD.mkdir(parents=True,exist_ok=True)
    (BUILD/'format.mac').write_text(source)
    image=assemble(__import__('pathlib').Path.home()/'bin/z80asm',source,BUILD/'format.bin',BUILD/'format.lst',0x100)
    listing=(BUILD/'format.lst').read_text();at=lambda name:address(listing,name)
    cases=0
    for label in (b'',b'Erase? ',b'X'*30,b'X'*240,b'X'*246,b'X'*255,b'Bad\r'):
        for choices in (b'yn',b'RSA?',b'N'):
            for default in (0,choices[0]):
                expected=label+b'('+b'/'.join(bytes([c]).upper() for c in choices)+b')'
                if default:expected+=b' ['+bytes([default]).upper()+b']'
                for width in (0,39,79,255,min(255,max(0,len(expected)-1)),min(255,len(expected))):
                    c=Z80(b'');c.mem[256:256+len(image)]=image
                    c.setword(at('UF_LABEL'),0x8000);c.mem[0x8000:0x8000+len(label)+1]=label+b'\0'
                    c.setword(at('UC_LIST'),0x8200);c.mem[0x8200:0x8200+len(choices)]=choices
                    c.mem[at('UC_COUNT')]=len(choices);c.mem[at('UC_DEF')]=default
                    c.mem[at('UF_WIDTH')]=width
                    before=bytes(c.mem[at('UC_LIST'):at('UC_VALUE')+1]);sp=c.sp
                    c.run(at('UF_PICK'),limit=100000)
                    good=b'\r' not in label and len(expected)<=width
                    assert bool(c.carry)==(not good),(label,width,expected,c.a)
                    if good:
                        assert c.a==0 and c.hl==at('UF_BUF') and c.b==len(expected)
                        assert bytes(c.mem[c.hl:c.hl+c.b+1])==expected+b'\0'
                    else:
                        assert c.a==7 and bytes(c.mem[at('UF_BUF'):at('UF_BUF')+256])==bytes([165])*256
                    assert c.sp==sp and before==bytes(c.mem[at('UC_LIST'):at('UC_VALUE')+1])
                    assert c.mem[at('FMTLEFT')]==90 and c.mem[at('FMTRIGHT')]==90
                    cases+=1
    report={'cases':cases,'formatter_bytes':at('LIB_END')-at('UF_PICK'),'result':'pass','scope':'compiled formatting only; no terminal rendering claim'}
    (BUILD/'format-results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
