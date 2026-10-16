#!/usr/bin/env python3
"""Execute optional SCX motion on both actual relocated screen carriers."""
from pathlib import Path
import pyte
from test_screen_backends import fixture,ROOT
from test_vt52_foundation import symbols


def main():
    cases=0
    m4=symbols(ROOT/'build/bios/bios.lst')
    for name in ('M4SCRN','ANSISCRN'):
        for base in (0x6000,0x8101):
            for width,height in ([(80,24)] if name=='M4SCRN' else [(80,24),(80,25),(100,40)]):
                cpu,old,cells,wire=fixture(name,base,cpmsim_bios=ROOT/'build/audit/release-090-z80pack')
                screen=pyte.Screen(width,height);stream=pyte.Stream(screen)
                if name=='ANSISCRN':
                    def emit(port,value):
                        assert port&255==1
                        wire.append(value);stream.feed(chr(value))
                    cpu.port_write=emit
                def call(op,direction=0,number=0,column=0):
                    cpu.a,cpu.b,cpu.hl,cpu.de=op,direction,number,column
                    sp=cpu.sp;cpu.run(cpu.backend_entry,limit=200000)
                    assert cpu.sp==sp
                    return cpu.a
                assert call(16)==0
                expected=b'SCX\x01\x00\x0c'+(b'\x18\x50' if name=='M4SCRN' else b'\0\0')+(b'\xbf\0\x60\0' if name=='M4SCRN' else b'\xbf\0\xff\x07')
                assert bytes(cpu.mem[cpu.hl:cpu.hl+12])==expected
                for op in range(5):
                    for n in [0,1,9,10,24,25,40,80,100,255,256,9999,10000,65535]:
                        old(6,11,14)
                        if op==4:assert call(18,number=n,column=100)==0
                        else:assert call(17,op,n)==0
                        amount=max(1,n)
                        expected=[(14,max(0,11-amount)),(14,min(height-1,11+amount)),(min(width-1,14+amount),11),(max(0,14-amount),11),(min(width-1,99),min(height-1,amount-1))][op]
                        actual=(cpu.mem[m4['M4COLUMN']],(cpu.word(m4['M4CURSOR'])-0xF800)//80) if name=='M4SCRN' else (screen.cursor.x,screen.cursor.y)
                        assert actual==expected,(name,base,width,height,op,n,actual,expected)
                        cases+=1
                # Invalid controls emit/write nothing; descriptor query is inert.
                before=bytes(cpu.mem[0xF800:0xFF80]);start=len(wire)
                for op,direction in [(17,4),(17,255),(19,2),(255,0)]:
                    assert call(op,direction)==255
                assert call(16)==0
                assert len(wire)==start and bytes(cpu.mem[0xF800:0xFF80])==before
                # Explicit legacy position resynchronizes the fixed-cell tracker
                # after geometry-neutral control operations, as after raw output.
                old(6,2,3);old(7,col=ord('Z'))
                if name=='M4SCRN':assert cpu.mem[0xF800+163]==ord('Z')
                else:assert screen.buffer[2][3].data=='Z' and (screen.cursor.x,screen.cursor.y)==(4,2)
    print(f'PASS {cases} actual-carrier motion/geometry/relocation cases, discovery, invalid calls and legacy resynchronization')


if __name__=='__main__':main()
