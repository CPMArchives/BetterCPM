#!/usr/bin/env python3
"""Render one portable VT52 binary through both actual screen backends.

NativeVT52 remains an independent historical wire model for reference users.
The production checks execute the Model 4 renderer and ANSI-host backend.
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
    from test_screen_backends import fixture, load
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bios',type=type(ROOT),default=ROOT/'build/z80pack')
    args=parser.parse_args()
    for name in ('M4SCRN','ANSISCRN'):
        for base in (0x6000,0x8101):
            cpu, backend_call, cells, output = fixture(name,base,cpmsim_bios=args.bios)
            frontend=0x7000
            syms=load(cpu,OUT,'vt52',frontend)
            cpu.setword(frontend+12,cpu.backend_entry)
            entry=syms['VT_ENTRY']+frontend-0x8000
            def call(op,char=0):
                sp=cpu.sp
                cpu.a,cpu.c=op,char
                cpu.run(entry,limit=200000)
                assert cpu.sp==sp
            def send(data):
                for char in data:call(0,char)
            def address(row,col):send(bytes([27,ord('Y'),row+32,col+32]))
            call(4)
            address(5,78);send(b'ABC')
            assert cells()[478:480]==b'AC'
            address(8,20);send(b'\x1bY!');call(5);send(b'X')
            assert cells()[660]==ord('X')
            for row in range(24):address(row,0);send(bytes([65+row])*80)
            address(23,17);send(b'\x1bB')
            assert cells()[:80]==b'A'*80
            send(b'\n')
            assert cells()[:80]==b'B'*80 and cells()[-80:]==b' '*80
            address(0,19);send(b'\x1bI')
            assert cells()[:80]==b' '*80 and cells()[80:160]==b'B'*80
            address(4,0);send(b'KEEP remove');address(4,4);send(b'\x1bK')
            assert cells()[320:400]==b'KEEP'+b' '*76
            address(6,10);send(b'\x1bJ')
            assert cells()[490:]==b' '*(1920-490)
            # Private cursor presentation advances exactly like ordinary output.
            before=(cpu.mem[syms['VT_ROW']+frontend-0x8000],cpu.mem[syms['VT_COL']+frontend-0x8000])
            cpu.de=ord('_')
            call(3,ord('_'))
            assert cpu.de==ord('_')
            assert cells()[before[0]*80+before[1]]==ord('_')|128
            assert (before[0],min(79,before[1]+1))==(cpu.mem[syms['VT_ROW']+frontend-0x8000],cpu.mem[syms['VT_COL']+frontend-0x8000])
            address(23,79);call(3,ord('X'))
            assert cpu.mem[syms['VT_COL']+frontend-0x8000]==79 and cells()[-1]==ord('X')|128
            print(f'PASS: identical portable VT52 through {name} at {base:04X}; screen, margins, scroll, erase and reset')


if __name__=='__main__':main()
