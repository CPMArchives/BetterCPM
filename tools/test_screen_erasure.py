#!/usr/bin/env python3
"""Check inclusive styled erase ranges, geometry and cursor preservation."""
import pyte
from test_screen_backends import fixture, ROOT
from test_vt52_foundation import symbols


def main():
    m4 = symbols(ROOT/'build/bios/bios.lst'); cases = 0
    for name in ('M4SCRN', 'ANSISCRN'):
        for base in (0x6000, 0x8101):
            for width, height in ([(80,24)] if name=='M4SCRN' else [(80,24),(80,25),(100,40)]):
                cpu, old, cells, wire = fixture(name,base,cpmsim_bios=ROOT/'build/audit/release-090-z80pack')
                screen = pyte.Screen(width,height); stream = pyte.Stream(screen)
                def emit(port,value):
                    assert port&255==1
                    wire.append(value);stream.feed(chr(value))
                if name=='ANSISCRN':cpu.port_write=emit
                def call(op,b=0,c=0,hl=0,de=0):
                    cpu.a,cpu.b,cpu.c,cpu.hl,cpu.de=op,b,c,hl,de
                    sp=cpu.sp;cpu.run(cpu.backend_entry,limit=300000)
                    assert cpu.sp==sp
                    return cpu.a
                for row,col in [(0,0),(height//2,width//2),(height-1,width-1)]:
                    for target in (0,1):
                        for mode in (0,1,2):
                            for reverse in (0,32):
                                if name=='M4SCRN':cpu.mem[0xF800:0xFF80]=b'X'*(80*24)
                                else:
                                    stream.feed('\x1b[0m')
                                    for y in range(height):stream.feed(f'\x1b[{y+1};1H'+'X'*width)
                                cpu.mem[0x4000:0x4009]=bytes([reverse,2,10,128,250,2,240,80,5])
                                assert call(20,hl=0x4000)==0
                                assert call(18,hl=row+1,de=col+1)==0
                                assert call(19,target,mode)==0
                                first,last=(row*width,(row+1)*width) if target==0 else (0,width*height)
                                pos=row*width+col
                                if mode==0:first=pos
                                elif mode==1:last=pos+1
                                for i in range(width*height):
                                    erased=first<=i<last
                                    if name=='M4SCRN':assert cpu.mem[0xF800+i]==((32|(128 if reverse else 0)) if erased else 88),(target,mode,i)
                                    else:
                                        cell=screen.buffer[i//width][i%width]
                                        assert cell.data==(' ' if erased else 'X'),(target,mode,i)
                                        if erased:
                                            assert cell.reverse==bool(reverse)
                                            assert cell.fg=='0a80fa' and cell.bg=='f05005'
                                actual=(cpu.mem[m4['M4COLUMN']],(cpu.word(m4['M4CURSOR'])-0xF800)//80) if name=='M4SCRN' else (screen.cursor.x,screen.cursor.y)
                                assert actual==(col,row)
                                cases+=1
                # Erasure must not consume a deferred right-edge wrap.
                assert call(18,hl=2,de=width)==0
                assert call(21,c=ord('A'))==0
                assert call(19,0,0)==0
                if name=='M4SCRN':assert cpu.mem[0xF800+80+79]&127==ord('A')
                else:assert screen.buffer[1][width-1].data=='A'
                assert call(21,c=ord('B'))==0
                if name=='M4SCRN':assert cpu.word(m4['M4CURSOR'])==0xF800+2*80+1
                else:assert (screen.cursor.x,screen.cursor.y)==(1,2)
                before=bytes(cpu.mem[0xF800:0xFF80]);n=len(wire)
                for b,c in [(2,0),(255,0),(0,3),(1,255)]:assert call(19,b,c)==255
                assert len(wire)==n and bytes(cpu.mem[0xF800:0xFF80])==before
    print(f'PASS {cases} styled erase cases: inclusive ranges, host geometry, cursor and invalid arguments')


if __name__=='__main__':main()
