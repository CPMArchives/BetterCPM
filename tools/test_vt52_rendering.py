#!/usr/bin/env python3
"""Independently render actual provider ANSI output at 80x24 and 100x40."""
import argparse
import pyte
from test_vt52_foundation import ROOT,OUT,symbols
from test_bios import Z80


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bios',type=type(ROOT),default=ROOT/'build/z80pack')
    args=parser.parse_args()
    syms=symbols(OUT/'vt52.lst');bios=symbols(args.bios/'bios.lst')
    base_bios=bios['MONRAW']-69
    code=(OUT/'vt52.bin').read_bytes();carrier=(OUT/'VT52.RSX').read_bytes()
    slots=[int.from_bytes(carrier[48+2*i:50+2*i],'little') for i in range(int.from_bytes(carrier[22:24],'little'))]
    for width,height in [(80,24),(100,40)]:
        cpu=Z80(b'');data=(args.bios/'bios.bin').read_bytes()
        cpu.mem[base_bios:base_bios+len(data)]=data;cpu.setword(1,base_bios+3)
        base=0x6000;relocated=bytearray(code)
        for slot in slots:
            value=int.from_bytes(code[slot:slot+2],'little')+base-0x8000
            relocated[slot:slot+2]=value.to_bytes(2,'little')
        cpu.mem[base:base+len(code)]=relocated
        screen=pyte.Screen(width,height);stream=pyte.Stream(screen)
        cpu.port_write=lambda port,value:stream.feed(chr(value))
        entry=syms['VT_ENTRY']+base-0x8000
        def call(op,char=0):cpu.a,cpu.c=op,char;cpu.run(entry,limit=20000)
        def send(data):
            for char in data:call(0,char)
        def address(row,col):send(bytes([27,ord('Y'),row+32,col+32]))
        call(4)
        address(5,78);send(b'ABC')
        assert screen.display[5][78:80]=='AC' and screen.cursor.x==79
        # Partial addressing must not move the terminal or committed cursor.
        address(8,20);send(b'\x1bY!');call(5);send(b'X')
        assert screen.display[8][20]=='X'
        assert cpu.mem[syms['VT_ROW']+base-0x8000]==8
        for row in range(24):address(row,0);send(bytes([65+row])*80)
        address(23,17);send(b'\x1bB')
        assert screen.display[0][:80]=='A'*80
        send(b'\n')
        assert screen.display[0][:80]=='B'*80
        assert screen.display[23][:80]==' '*80
        assert (screen.cursor.y,screen.cursor.x)==(23,17)
        assert screen.margins is None
        address(0,19);send(b'\x1bI')
        assert screen.display[0][:80]==' '*80
        assert screen.display[1][:80]=='B'*80
        assert (screen.cursor.y,screen.cursor.x)==(0,19)
        assert screen.margins is None
        address(4,0);send(b'KEEP remove');address(4,4);send(b'\x1bK')
        assert screen.display[4][:80]=='KEEP'+' '*76
        address(6,10);send(b'\x1bJ')
        assert all(line[:80]==' '*80 for line in screen.display[7:24])
        assert (screen.cursor.y,screen.cursor.x)==(6,10)
    print('PASS: independent ANSI rendering at 80x24 and 100x40, bounded scrolling, margin replacement, erase and partial reset')


if __name__=='__main__':main()
