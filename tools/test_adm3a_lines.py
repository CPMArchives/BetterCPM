#!/usr/bin/env python3
"""Compare assembled provider line operations with the selected original MM binary."""
import argparse
from test_mm_adm3a_reference import reference, DEFAULT
from test_adm3a_foundation import ROOT, OUT, symbols
from system_layout import LAYOUT
from test_bios import Z80


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',type=type(DEFAULT),default=DEFAULT)
    args=parser.parse_args()
    code=(OUT/'adm3a.bin').read_bytes()
    blob=(OUT/'ADM3A.RSX').read_bytes()
    count=int.from_bytes(blob[22:24],'little')
    slots=[int.from_bytes(blob[48+2*i:50+2*i],'little') for i in range(count)]
    syms=symbols(OUT/'adm3a.lst')
    bios=symbols(ROOT/'build/bios/bios.lst')
    original=reference(args.image)
    pattern=bytes(33+(i//80)%90 for i in range(1920))
    cases=0
    for base in [0x6000,0x8101]:
        cpu=Z80((ROOT/'build/bios/bios.bin').read_bytes())
        cpu.setword(1,LAYOUT['BIOS']+3)
        relocated=bytearray(code)
        for slot in slots:
            value=int.from_bytes(code[slot:slot+2],'little')+base-0x8000
            relocated[slot:slot+2]=value.to_bytes(2,'little')
        cpu.mem[base:base+len(code)]=relocated
        entry=syms['AM_ENTRY']+base-0x8000
        reverse_address=syms['AM_REVERSE']+base-0x8000
        for old in [0,128]:
            cpu.mem[reverse_address]=old
            for _ in range(2):
                cpu.a,cpu.c=0,15
                cpu.run(entry)
                assert cpu.mem[reverse_address]==128
        for row in range(24):
            for col in range(80):
                for reverse in [0,128]:
                    for char in [28,29]:
                        for machine in [cpu,original]:
                            machine.mem[0xF800:0xFF80]=pattern
                            machine.mem[0xF7FF]=165
                            machine.mem[0xFF80]=90
                        original.setword(0xF0C9,row+256*col)
                        original.mem[0xF0CB]=reverse
                        original.c=char
                        original.run(0xEFD9,limit=20000)
                        cpu.setword(bios['M4CURSOR'],0xF800+80*row+col)
                        cpu.mem[bios['M4COLUMN']]=col
                        cpu.mem[reverse_address]=reverse
                        cpu.a,cpu.c=0,char
                        cpu.run(entry,limit=20000)
                        assert cpu.mem[0xF800:0xFF80]==original.mem[0xF800:0xFF80],(base,row,col,reverse,char)
                        assert cpu.word(bios['M4CURSOR'])==0xF800+80*row+col
                        assert cpu.mem[bios['M4COLUMN']]==col
                        assert cpu.mem[0xF7FF]==165 and cpu.mem[0xFF80]==90
                        cases+=1
    print(f'PASS: 0Fh reverse ON and {cases} relocated line operations match original MM 2.32')


if __name__=='__main__':main()
