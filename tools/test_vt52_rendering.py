#!/usr/bin/env python3
"""Render actual provider output with an independent native VT52 wire model.

This model deliberately has no ANSI parser. It is automated protocol evidence,
not a substitute for qualification against a real VT52-capable terminal.
"""
import argparse
from test_vt52_foundation import ROOT,OUT,symbols
from test_bios import Z80


class NativeVT52:
    """Fixed 80x24 screen, native addressing and scroll semantics."""
    def __init__(self):
        self.cells = [[' ']*80 for _ in range(24)]
        self.row = self.col = 0
        self.pending = ''
        self.address_row = 0

    @property
    def display(self):
        return [''.join(line) for line in self.cells]

    def feed(self, char):
        value = ord(char)
        if self.pending == 'row':
            assert 32 <= value < 56
            self.address_row = value-32
            self.pending = 'col'
        elif self.pending == 'col':
            assert 32 <= value < 112
            self.row, self.col = self.address_row, value-32
            self.pending = ''
        elif self.pending == 'esc':
            self.pending = ''
            if char == 'Y':
                self.pending = 'row'
            elif char == 'H':
                self.row = self.col = 0
            elif char in 'JK':
                self.cells[self.row][self.col:] = [' ']*(80-self.col)
                if char == 'J':
                    for row in range(self.row+1,24):
                        self.cells[row] = [' ']*80
            elif char == 'I':
                if self.row:
                    self.row -= 1
                else:
                    self.cells.insert(0,[' ']*80)
                    self.cells.pop()
            else:
                raise AssertionError(('unexpected native VT52 final', char))
        elif value == 27:
            self.pending = 'esc'
        elif value == 10:
            if self.row == 23:
                self.cells.pop(0)
                self.cells.append([' ']*80)
            else:
                self.row += 1
        elif value == 7:
            pass
        elif 32 <= value < 127:
            self.cells[self.row][self.col] = char
            self.col = min(self.col+1,79)
        else:
            raise AssertionError(('unexpected native VT52 byte', value))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bios',type=type(ROOT),default=ROOT/'build/z80pack')
    args=parser.parse_args()
    syms=symbols(OUT/'vt52.lst');bios=symbols(args.bios/'bios.lst')
    base_bios=bios['MONRAW']-69
    code=(OUT/'vt52.bin').read_bytes();carrier=(OUT/'VT52.RSX').read_bytes()
    slots=[int.from_bytes(carrier[48+2*i:50+2*i],'little') for i in range(int.from_bytes(carrier[22:24],'little'))]
    for base in (0x6000, 0x8101):
        cpu=Z80(b'');data=(args.bios/'bios.bin').read_bytes()
        cpu.mem[base_bios:base_bios+len(data)]=data;cpu.setword(1,base_bios+3)
        relocated=bytearray(code)
        for slot in slots:
            value=int.from_bytes(code[slot:slot+2],'little')+base-0x8000
            relocated[slot:slot+2]=value.to_bytes(2,'little')
        cpu.mem[base:base+len(code)]=relocated
        screen=NativeVT52()
        cpu.port_write=lambda port,value:screen.feed(chr(value))
        entry=syms['VT_ENTRY']+base-0x8000
        def call(op,char=0):cpu.a,cpu.c=op,char;cpu.run(entry,limit=20000)
        def send(data):
            for char in data:call(0,char)
        def address(row,col):send(bytes([27,ord('Y'),row+32,col+32]))
        call(4)
        address(5,78);send(b'ABC')
        assert screen.display[5][78:80]=='AC' and screen.col==79
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
        assert (screen.row,screen.col)==(23,17)
        address(0,19);send(b'\x1bI')
        assert screen.display[0][:80]==' '*80
        assert screen.display[1][:80]=='B'*80
        assert (screen.row,screen.col)==(0,19)
        address(4,0);send(b'KEEP remove');address(4,4);send(b'\x1bK')
        assert screen.display[4][:80]=='KEEP'+' '*76
        address(6,10);send(b'\x1bJ')
        assert all(line[:80]==' '*80 for line in screen.display[7:24])
        assert (screen.row,screen.col)==(6,10)
    print('PASS: native VT52-only screen model at two relocation bases; margins, scrolling, erase and partial reset; no ANSI parser')


if __name__=='__main__':main()
