#!/usr/bin/env python3
"""Check assembled MM screen controls against the frozen cursor/erase contract."""
from test_adm3a_foundation import ROOT, OUT, symbols
from system_layout import LAYOUT
from test_bios import Z80


def main():
    code=(OUT/'adm3a.bin').read_bytes()
    blob=(OUT/'ADM3A.RSX').read_bytes()
    count=int.from_bytes(blob[22:24],'little')
    slots=[int.from_bytes(blob[48+2*i:50+2*i],'little') for i in range(count)]
    syms=symbols(OUT/'adm3a.lst')
    bios=symbols(ROOT/'build/bios/bios.lst')
    cases=0
    pattern=bytes(33+(i//80)%90 for i in range(1920))
    for base in [0x6000,0x8101]:
        cpu=Z80((ROOT/'build/bios/bios.bin').read_bytes())
        cpu.setword(1,LAYOUT['BIOS']+3)
        relocated=bytearray(code)
        for slot in slots:
            value=int.from_bytes(code[slot:slot+2],'little')+base-0x8000
            relocated[slot:slot+2]=value.to_bytes(2,'little')
        cpu.mem[base:base+len(code)]=relocated
        entry=syms['AM_ENTRY']+base-0x8000
        def output(char):
            cpu.a,cpu.c=0,char
            cpu.run(entry,limit=15000)
        for row in range(24):
            for col in range(80):
                for char in [8,9,10,11,12,13,21,23,24,25,30,ord('X')]:
                    offset=row*80+col
                    cpu.mem[0xF800:0xFF80]=pattern
                    cpu.mem[0xF7FF]=0xA5
                    cpu.mem[0xFF80]=0x5A
                    cpu.setword(bios['M4CURSOR'],0xF800+offset)
                    cpu.mem[bios['M4COLUMN']]=col
                    expected=bytearray(pattern)
                    target=offset
                    if char==8:target=max(0,offset-1)
                    elif char==9:target=offset+8-col%8
                    elif char==10:target=offset+80
                    elif char==11:target=offset-80 if row else offset
                    elif char in [12,ord('X')]:
                        target=offset+1
                        if char==ord('X'):expected[offset]=char
                    elif char==13:target=row*80
                    elif char in [21,24]:expected[offset:(row+1)*80]=b' '*(80-col)
                    elif char in [23,25]:expected[offset:]=b' '*(1920-offset)
                    elif char==30:target=0
                    if target>=1920:
                        target-=80
                        expected=expected[80:]+b' '*80
                    output(char)
                    assert cpu.word(bios['M4CURSOR'])==0xF800+target,(base,row,col,char,'cursor')
                    assert cpu.mem[bios['M4COLUMN']]==target%80,(base,row,col,char,'column')
                    assert cpu.mem[0xF800:0xFF80]==expected,(base,row,col,char,'screen')
                    assert cpu.mem[0xF7FF]==0xA5 and cpu.mem[0xFF80]==0x5A
                    cases+=1
        # Ignored controls and deliberately unfinished controls must not leak
        # into the basic renderer or accidentally clear the screen.
        for char in list(range(7))+list(range(16,21))+[7,14,15,22,28,29,31]:
            cpu.mem[0xF800:0xFF80]=pattern
            cpu.setword(bios['M4CURSOR'],0xF864)
            cpu.mem[bios['M4COLUMN']]=20
            output(char)
            assert cpu.mem[0xF800:0xFF80]==pattern
            assert cpu.word(bios['M4CURSOR'])==0xF864
    print(f'PASS: {cases} relocated screen/cursor cases, guarded video boundaries and control containment')


if __name__=='__main__':main()
