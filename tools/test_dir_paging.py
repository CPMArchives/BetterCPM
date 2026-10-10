#!/usr/bin/env python3
"""Execute DIR paging boundaries, controls and nonlocal DU restoration."""
import re
from pathlib import Path
from build_ccp import assemble
from test_bios import Z80
ROOT=Path(__file__).resolve().parents[1]
image=(ROOT/'build/utilities/DIR.COM').read_bytes()
listing=(ROOT/'build/utilities/dir-transient.lst').read_text()
def addr(name):
    return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
work=ROOT/'build/compatibility/dir-paging';work.mkdir(parents=True,exist_ok=True)
provider=assemble(Path('/Users/nathanael/bin/z80asm'),'''        ORG 06000H
        LD A,C
        CP 2
        JR Z,CHAR
        CP 9
        JR Z,TEXT
        CP 6
        JR Z,KEY
        CP 14
        JR Z,DRIVE
        CP 32
        JR Z,USER
        HALT
CHAR:   LD HL,(07500H)
        INC HL
        LD (07500H),HL
        RET
TEXT:   LD HL,%d
        OR A
        SBC HL,DE
        RET NZ
        LD HL,07502H
        INC (HL)
        RET
KEY:    LD HL,(07504H)
        LD A,(HL)
        INC HL
        LD (07504H),HL
        RET
DRIVE:  LD A,E
        LD (07506H),A
        RET
USER:   LD A,E
        LD (07507H),A
        RET
        END
'''%addr('DG_MORE'),work/'provider.bin',work/'provider.lst',0x6000)
def machine(keys):
    c=Z80(b'');c.mem[256:256+len(image)]=image
    c.mem[0x6000:0x6000+len(provider)]=provider
    c.mem[5:8]=b'\xc3\x00\x60'
    c.mem[0x7600:0x7600+len(keys)]=keys;c.setword(0x7504,0x7600)
    c.mem[addr('DG_PAGE')]=1
    return c
def emit(c,text):
    c.mem[0x7700:0x7700+len(text)]=text;c.de=0x7700
    c.run(addr('DG_PRINT'),limit=100000)
for keys in (b'\0X ',b'\r'):
    c=machine(keys)
    emit(c,b'L\r\n'*23+b'$')
    assert c.mem[0x7502]==0 and c.mem[addr('DG_LINES')]==23
    emit(c,b'NEXT\r\n$')
    assert c.mem[0x7502]==1 and c.mem[addr('DG_LINES')]==1
    assert c.word(0x7504)==0x7600+len(keys)
    assert c.word(0x7500)==75  # 23 three-character lines + NEXT/CR/LF
c=machine(b'\x03');c.mem[addr('DG_LINES')]=23
c.setword(addr('DG_STACK'),c.sp-2)
c.mem[addr('BC_DSAVE')],c.mem[addr('BC_USAVE')]=2,7
emit(c,b'NO OUTPUT$')
assert c.word(0x7500)==0 and c.mem[0x7502]==1
assert tuple(c.mem[0x7506:0x7508])==(2,7)
assert c.sp==0xe000
c=machine(b'\x03');c.mem[addr('DG_PAGE')]=0
emit(c,b'L\r\n'*60+b'$')
assert c.word(0x7500)==180 and c.mem[0x7502]==0
assert c.word(0x7504)==0x7600
print('Paging line boundaries, no final pause, Space/Enter, ignored keys, off mode and Ctrl-C stack/DU restoration pass')
