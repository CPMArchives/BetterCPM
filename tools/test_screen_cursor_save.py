#!/usr/bin/env python3
"""Check reusable cursor/rendition save slots on actual relocated backends."""
import pyte
from test_screen_backends import fixture,ROOT
from test_vt52_foundation import symbols


def main():
    m4=symbols(ROOT/'build/bios/bios.lst');cases=0
    records=[bytes(9),bytes([33,2,10,128,250,1,200,0,0]),bytes([64,1,9,0,0,2,1,2,3]),bytes([255,2,1,2,3,2,40,50,60])]
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
                syms=symbols(ROOT/'build/screen-backends'/(name+'.lst'))
                attr=base+syms['SX_ATTR' if name=='M4SCRN' else 'BH_ATTR']-0x8000
                def call(op,b=0,c=0,hl=0,de=0):
                    cpu.a,cpu.b,cpu.c,cpu.hl,cpu.de=op,b,c,hl,de
                    sp=cpu.sp;cpu.run(cpu.backend_entry,limit=300000)
                    assert cpu.sp==sp
                    return cpu.a
                def style(record):
                    cpu.mem[0x4000:0x4009]=record
                    assert call(20,hl=0x4000)==0
                def cursor():
                    return (cpu.mem[m4['M4COLUMN']],(cpu.word(m4['M4CURSOR'])-0xF800)//80) if name=='M4SCRN' else (screen.cursor.x,screen.cursor.y)
                before=bytes(cpu.mem[base:base+len((ROOT/'build/screen-backends'/(name+'.bin')).read_bytes())])
                assert call(23,b=1)==255 and not wire
                assert bytes(cpu.mem[base:base+len(before)])==before
                for row,col in [(0,0),(height//2,width//2),(height-1,width-1)]:
                    for record in records:
                        style(record);assert call(18,hl=row+1,de=col+1)==0
                        # Save at a pending right-edge wrap as well as ordinary positions.
                        if col==width-1:assert call(21,c=ord('P'))==0
                        assert call(23,b=0)==0
                        for repeat in range(3):
                            style(bytes(9));assert call(18,hl=2,de=3)==0
                            old(6,2,3);old(7,col=ord('L'))
                            assert call(23,b=1)==0
                            assert cursor()==(col,row),(name,row,col,cursor())
                            assert bytes(cpu.mem[attr:attr+9])==record
                            assert call(21,c=ord('X'))==0
                            if name=='M4SCRN':
                                want=(32 if record[0]&64 else ord('X'))|(128 if record[0]&32 else 0)
                                assert cpu.mem[0xF800+row*80+col]==want
                            else:
                                cell=screen.buffer[row][col]
                                assert cell.data=='X' and cell.reverse==bool(record[0]&32)
                            cases+=1
                # A later save replaces the previous slot, and repeated restore reuses it.
                assert call(18,hl=4,de=5)==0 and call(23,b=0)==0
                for unused in range(3):
                    assert call(18,hl=8,de=9)==0 and call(23,b=1)==0
                    assert cursor()==(4,3)
                # Margins are independent state, not part of the saved cursor slot.
                assert call(22,hl=2,de=height-1)==0
                assert call(18,hl=4,de=5)==0 and call(23,b=0)==0
                assert call(22,hl=3,de=height-2)==0 and call(23,b=1)==0
                if name=='M4SCRN':
                    assert cpu.mem[base+syms['SM_TOPROW']-0x8000]==2
                    assert cpu.mem[base+syms['SM_BOTTOM']-0x8000]==height-3
                else:assert screen.margins==(2,height-3)
                n=len(wire);saved=bytes(cpu.mem[base:base+len(before)])
                for bad in (2,255):assert call(23,b=bad)==255
                assert len(wire)==n and bytes(cpu.mem[base:base+len(before)])==saved
                print(f'PASS {name} {base:04X} {width}x{height}: cursor/style restore, replacement, repeated restore, margins and atomic errors')
    print(f'PASS {cases} saved cursor/rendition continuation cases plus directed slot/boundary checks')


if __name__=='__main__':main()
