#!/usr/bin/env python3
"""Exercise canonical rendition and delayed-wrap glyphs on both actual backends."""
import pyte
from test_screen_backends import fixture,ROOT
from test_vt52_foundation import symbols


def main():
    m4=symbols(ROOT/'build/bios/bios.lst');cases=0
    for name in ('M4SCRN','ANSISCRN'):
        for base in (0x6000,0x8101):
            cpu,old,cells,wire=fixture(name,base,cpmsim_bios=ROOT/'build/audit/release-090-z80pack')
            screen=pyte.Screen(80,24);stream=pyte.Stream(screen)
            if name=='ANSISCRN':
                def emit(port,value):
                    assert port&255==1
                    wire.append(value);stream.feed(chr(value))
                cpu.port_write=emit
            def call(op,char=0,record=None):
                if record is not None:cpu.mem[0x4000:0x4009]=bytes(record)
                cpu.a,cpu.c,cpu.hl=op,char,0x4000
                sp=cpu.sp;cpu.run(cpu.backend_entry,limit=200000)
                assert cpu.sp==sp
                return cpu.a
            def style(record):assert call(20,record=record)==0
            def glyph(char):assert call(21,char)==0
            def attr_at(row,col):return screen.buffer[row][col]
            for flags in range(256):
                old(6,3,4);style([flags]+[0]*8);glyph(ord('X'))
                if name=='M4SCRN':
                    expected=(32 if flags&64 else ord('X'))|(128 if flags&32 else 0)
                    assert cpu.mem[0xF800+244]==expected,(flags,expected)
                else:
                    cell=attr_at(3,4)
                    for field,bit in [('bold',1),('italics',4),('underscore',8),('blink',16),('reverse',32),('strikethrough',128)]:
                        assert getattr(cell,field)==bool(flags&bit),(flags,field)
                    # pyte does not model faint/conceal: verify their encoded controls.
                    if flags&2:assert b'\x1b[2m' in bytes(wire)
                    if flags&64:assert b'\x1b[8m' in bytes(wire)
                    assert cell.fg==cell.bg=='default'
                cases+=1;wire.clear()
            for slot,selector in [(1,38),(5,48)]:
                for index in range(256):
                    record=bytearray(9);record[slot]=1;record[slot+1]=index
                    old(6,5,6);style(record);glyph(ord('C'))
                    if name=='ANSISCRN':
                        reference=pyte.Screen(80,24);pyte.Stream(reference).feed(f'\x1b[{selector};5;{index}mC')
                        field='fg' if slot==1 else 'bg'
                        assert getattr(attr_at(5,6),field)==getattr(reference.buffer[0][0],field),(slot,index)
                    else:assert cpu.mem[0xF800+406]==ord('C')
                    cases+=1
            record=[33,2,10,128,250,2,240,80,5]
            old(6,1,1);style(record);glyph(ord('R'))
            if name=='ANSISCRN':
                assert attr_at(1,1).fg=='0a80fa' and attr_at(1,1).bg=='f05005'
                assert attr_at(1,1).bold and attr_at(1,1).reverse
                before=len(wire);glyph(ord('S'));assert bytes(wire[before:])==b'S'
                syms=symbols(ROOT/'build/screen-backends/ANSISCRN.lst')
                assert cpu.word(base+syms['BH_PTR']-0x8000)==0
            # Legacy writes override all new rendition; the next styled glyph
            # restores the stored canonical attributes without a new set call.
            old(6,7,8);old(7,col=ord('L'));glyph(ord('N'))
            if name=='ANSISCRN':
                assert not attr_at(7,8).reverse and attr_at(7,8).fg=='default'
                assert attr_at(7,9).reverse and attr_at(7,9).fg=='0a80fa'
            else:assert cpu.mem[0xF800+569]==ord('N')|128
            # Invalid records/glyphs are atomic, including the active style.
            attr=symbols(ROOT/'build/screen-backends'/(name+'.lst'))['SX_ATTR' if name=='M4SCRN' else 'BH_ATTR']+base-0x8000
            for bad in [[0,3,0,0,0,0,0,0,0],[0,0,0,0,0,255,0,0,0]]:
                before=bytes(cpu.mem[attr:attr+9]);video=bytes(cpu.mem[0xF800:0xFF80]);n=len(wire)
                assert call(20,record=bad)==255
                assert bytes(cpu.mem[attr:attr+9])==before and len(wire)==n
                assert bytes(cpu.mem[0xF800:0xFF80])==video
            for bad in (0,31,127,255):
                n=len(wire);video=bytes(cpu.mem[0xF800:0xFF80]);assert call(21,bad)==255
                assert len(wire)==n and bytes(cpu.mem[0xF800:0xFF80])==video
            style([0]*9);old(6,22,79);glyph(ord('A'))
            if name=='M4SCRN':assert cpu.mem[m4['M4COLUMN']]==79
            glyph(ord('B'))
            if name=='M4SCRN':assert cpu.word(m4['M4CURSOR'])==0xFF31
            else:assert (screen.cursor.x,screen.cursor.y)==(1,23)
            # Positioning between right-edge output and another glyph cancels wrap.
            old(6,10,79);glyph(ord('Q'));old(6,4,5);glyph(ord('P'))
            if name=='M4SCRN':assert cpu.mem[0xF800+325]==ord('P')
            else:assert attr_at(4,5).data=='P'
            # Reverse fill while scrolling at the bottom must be physical cells,
            # not merely a cursor mode or cache state.
            style([32]+[0]*8);old(6,23,79);glyph(ord('Z'));glyph(ord('W'))
            if name=='M4SCRN':
                assert cpu.mem[0xFF30]==ord('W')|128
                assert bytes(cpu.mem[0xFF31:0xFF80])==bytes([160])*79
            else:assert attr_at(23,0).data=='W' and attr_at(23,0).reverse
            if name=='ANSISCRN':
                for width,height in [(80,25),(100,40)]:
                    screen=pyte.Screen(width,height);stream=pyte.Stream(screen)
                    style([33,2,10,128,250,1,200,0,0])
                    cpu.a,cpu.hl,cpu.de=18,height,width
                    cpu.run(cpu.backend_entry,limit=200000);assert cpu.a==0
                    glyph(ord('X'));glyph(ord('Y'))
                    assert (screen.cursor.x,screen.cursor.y)==(1,height-1)
                    assert attr_at(height-2,width-1).data=='X'
                    assert attr_at(height-1,0).data=='Y'
                    assert attr_at(height-1,0).reverse and attr_at(height-1,0).fg=='0a80fa'
            print(f'PASS {name} at {base:04X}: attributes/colors, atomic failures, mode switching and delayed wrap')
    print(f'PASS {cases} canonical attribute/palette cases plus directed boundary cases')


if __name__=='__main__':main()
