#!/usr/bin/env python3
"""Execute the shared screen contract on both production backend candidates."""
import argparse
from pathlib import Path
import pyte
from test_bios import Z80
from test_vt52_foundation import ROOT, symbols

OUT = ROOT/'build/screen-backends'


def load(cpu, directory, stem, base):
    code = (directory/(stem+'.bin')).read_bytes()
    carrier = (directory/(stem.upper()+'.RSX')).read_bytes()
    relocated = bytearray(code)
    for index in range(int.from_bytes(carrier[22:24], 'little')):
        slot = int.from_bytes(carrier[48+index*2:50+index*2], 'little')
        value = int.from_bytes(code[slot:slot+2], 'little')+base-0x8000
        relocated[slot:slot+2] = value.to_bytes(2, 'little')
    cpu.mem[base:base+len(code)] = relocated
    return symbols(directory/(stem+'.lst'))


def fixture(name, base, model4_bios=None, cpmsim_bios=None):
    cpu = Z80(b'')
    model4 = name == 'M4SCRN'
    directory = (model4_bios or ROOT/'build/bios') if model4 else (cpmsim_bios or ROOT/'build/z80pack')
    bios = symbols(directory/'bios.lst')
    origin = bios['MONRAW']-69
    data = (directory/'bios.bin').read_bytes()
    cpu.mem[origin:origin+len(data)] = data
    cpu.setword(1, origin+3)
    syms = load(cpu, OUT, name, base)
    entry = syms['S_ENTRY' if model4 else 'SB_ENTRY']+base-0x8000
    screen = pyte.Screen(80,24)
    stream = pyte.Stream(screen)
    output = []
    def write(port, value):
        if not model4:
            assert port & 255 == 1
            output.append(value)
            stream.feed(chr(value))
    cpu.port_write = write
    def call(op, row=0, col=0):
        sp = cpu.sp
        cpu.a, cpu.b, cpu.c = op, row, col
        cpu.run(entry, limit=200000)
        assert cpu.sp == sp
        return cpu.a
    def cells():
        if model4:
            return bytes(cpu.mem[0xF800:0xFF80])
        return bytes(ord(screen.buffer[r][c].data) | (128 if screen.buffer[r][c].reverse else 0)
                     for r in range(24) for c in range(80))
    cpu.backend_entry = entry
    return cpu, call, cells, output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model4-bios', type=Path, default=ROOT/'build/bios')
    parser.add_argument('--cpmsim-bios', type=Path, default=ROOT/'build/z80pack')
    args = parser.parse_args()
    for name in ('M4SCRN', 'ANSISCRN'):
        for base in (0x6000,0x8101):
            cpu, call, cells, output = fixture(name,base,args.model4_bios,args.cpmsim_bios)
            call(6); call(9,col=32)
            call(12)
            assert bytes(cpu.mem[cpu.hl:cpu.hl+9]) == b'SCR\x01\x00\x18\x50\xff\xff'
            for row in range(24):
                call(6,row,0)
                for col in range(80): call(7,col=65+row)
            assert cells() == b''.join(bytes([65+r])*80 for r in range(24))
            call(6,5,78)
            for char in b'XYZ': call(7,col=char)
            assert cells()[5*80+78:6*80] == b'XZ'
            call(6,7,13); call(7,col=ord('R')|128)
            assert cells()[7*80+13] == ord('R')|128
            for fill in (32,160):
                call(6,5,17); call(8,col=fill)
                assert cells()[5*80+17:6*80] == bytes([fill])*63
                call(6,11,23); before=cells(); call(10,col=fill)
                assert cells() == before[80:]+bytes([fill])*80, (name,base,'scroll up',fill)
                before=cells(); call(11,col=fill)
                assert cells() == bytes([fill])*80+before[:-80], (name,base,'scroll down',fill)
                call(6,8,19); before=cells(); call(13,col=fill)
                assert cells() == before[:640]+bytes([fill])*80+before[640:-80]
                before=cells(); call(14,col=fill)
                assert cells() == before[:640]+before[720:]+bytes([fill])*80
            # Literal display bytes never become terminal controls. Model 4
            # preserves every byte; ASCII hosts substitute unsupported glyphs.
            for value in range(256):
                call(6,2,3);call(7,col=value)
                glyph=value&127
                expected=value if name=='M4SCRN' or 32<=glyph<127 else (value&128)|ord('?')
                assert cells()[163]==expected,(name,value,cells()[163],expected)
            # EOS must fill all subsequent rows in the requested rendition,
            # even on ANSI hosts whose erase command uses default attributes.
            for fill in (160,32):
                call(6,3,11);before=cells();call(9,col=fill)
                assert cells()==before[:251]+bytes([fill])*(1920-251)
            for op,row,col in [(6,24,0),(6,0,80),(8,0,33),(9,0,0),(10,0,65),(13,0,65),(15,0,2),(16,0,0)]:
                before=cells(); wire=len(output)
                assert call(op,row,col)==255, (name,op)
                assert cells()==before and len(output)==wire, (name,op,'mutated')
            print(f'PASS {name} at {base:04X}: screen, reverse, scroll, lines, invalid arguments')


if __name__ == '__main__': main()
