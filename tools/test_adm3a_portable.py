#!/usr/bin/env python3
"""Execute the same MM-style ADM3A personality through both screen backends."""
import argparse
from pathlib import Path
from test_screen_backends import ROOT, fixture, load


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cpmsim-bios',type=Path,default=ROOT/'build/z80pack')
    args=parser.parse_args()
    for name in ('M4SCRN','ANSISCRN'):
        for backbase in (0x6000,0x8101):
            cpu,backcall,cells,wire=fixture(name,backbase,cpmsim_bios=args.cpmsim_bios)
            base=0x7000
            syms=load(cpu,ROOT/'build/monitor-development','adm3a',base)
            cpu.setword(base+12,cpu.backend_entry)
            entry=syms['AM_ENTRY']+base-0x8000
            def call(op,char=0):
                sp=cpu.sp;cpu.a,cpu.c=op,char
                cpu.run(entry,limit=200000)
                assert cpu.sp==sp
                return cpu.a
            def send(data):
                for char in data:call(0,char)
            def position(row,col):send(bytes([27,ord('='),row+32,col+32]))
            def cursor():return tuple(cpu.mem[syms[label]+base-0x8000] for label in ['AM_ROWPOS','AM_COLPOS'])
            call(4)
            position(5,78);send(b'XYZ')
            assert cells()[478:481]==b'XYZ' and cursor()==(6,1)
            position(6,0);send(b'\x08')
            assert cursor()==(5,79)
            position(0,0);send(b'\x08');assert cursor()==(0,0)
            send(b'\x0f');call(4)
            assert cells()==b'\xa0'*1920
            position(23,79);send(b'Q')
            assert cells()[1839]==ord('Q')|128 and cells()[1840:]==b'\xa0'*80
            assert cursor()==(23,0)
            send(b'\x0e');call(4)
            for row in range(23):
                position(row,0);send(bytes([65+row])*80)
            position(8,19);before=cells();send(b'\x0f\x1c')
            assert cells()==before[:640]+b'\xa0'*80+before[640:-80]
            assert cursor()==(8,19)
            before=cells();send(b'\x1d')
            assert cells()==before[:640]+before[720:]+b'\xa0'*80
            assert cursor()==(8,19)
            before=cursor();send(b'\x1b=!');call(5)
            assert cursor()==before
            send(b'\x1b0');assert call(3)==0
            call(5);assert call(3)==0
            send(b'\x1b1');assert call(3)==1
            # MM's ordinary output includes every byte >= 20h, including
            # high-bit glyphs. Backend glyph fallback must still advance once.
            for reverse in (0,128):
                send(b'\x0f' if reverse else b'\x0e')
                for value in range(32,256):
                    position(1,2);send(bytes([value]))
                    display=value|reverse;glyph=display&127
                    expected=display if name=='M4SCRN' or 32<=glyph<127 else (display&128)|ord('?')
                    assert cells()[82]==expected,(name,reverse,value)
                    assert cursor()==(1,3)
            send(b'\x0e')
            position(5,10)
            cpu.de=ord('X')
            assert call(3,ord('X'))==1 and cpu.de==ord('X')
            assert cursor()==(5,11) and cells()[410]==ord('X')|128
            position(23,79)
            assert call(3,ord('R'))==1
            assert cursor()==(23,0) and cells()[1839]==ord('R')|128
            assert call(6)==255
            print(f'PASS {name} at {backbase:04X}: portable MM wrap, scroll, reverse fills, lines, reset and visibility')


if __name__=='__main__':main()
