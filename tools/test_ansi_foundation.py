#!/usr/bin/env python3
"""Execute bounded ANSI parsing at two relocated addresses against actual host BIOS."""
import argparse
from pathlib import Path
from test_bios import Z80
from test_vt52_foundation import symbols
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/ansi-development'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bios',type=Path,default=ROOT/'build/z80pack')
    args=p.parse_args()
    sym=symbols(OUT/'ansi.lst');bios=symbols(args.bios/'bios.lst')
    origin=bios['MONRAW']-69
    image=(OUT/'ansi.bin').read_bytes();carrier=(OUT/'ANSI.RSX').read_bytes()
    count=int.from_bytes(carrier[22:24],'little')
    slots=[int.from_bytes(carrier[48+i*2:50+i*2],'little') for i in range(count)]
    for base in (0x6000,0x8101):
        cpu=Z80(b'');data=(args.bios/'bios.bin').read_bytes()
        cpu.mem[origin:origin+len(data)]=data;cpu.setword(1,origin+3)
        code=bytearray(image)
        for slot in slots:
            code[slot:slot+2]=(int.from_bytes(code[slot:slot+2],'little')+base-0x8000).to_bytes(2,'little')
        cpu.mem[base:base+len(code)]=code
        entry=sym['AN_ENTRY']+base-0x8000
        state=sym['AN_STATE']+base-0x8000
        used=sym['AN_COUNT']+base-0x8000
        guard=base+len(code);cpu.mem[guard:guard+16]=b'G'*16
        output=[]
        cpu.port_write=lambda port,value:output.append(value)
        cpu.port_read=lambda port:1 if port&255==0 else ord('a')
        def call(op,char=0):
            stack=cpu.sp;cpu.a,cpu.c=op,char;cpu.run(entry,limit=10000)
            assert cpu.sp==stack
            assert cpu.mem[used]<=31
            assert bytes(cpu.mem[guard:guard+16])==b'G'*16
            return cpu.a
        def send(data):
            output.clear()
            for char in data:call(0,char)
            return bytes(output)
        for sequence in (b'hello\r\n',b'\x1b[5;10H',b'\x1b[2J',b'\x1b[K',b'\x1b[1;7m',b'\x1b[0m',b'\x1b[3A',b'\x1b[4B',b'\x1b[2C',b'\x1b[2D',b'\x1b[1;24r',b'\x1b[s',b'\x1b[u',b'\x1b7',b'\x1b8',b'\x1bD',b'\x1bE',b'\x1bM',b'\x1b[?25l',b'\x1b[?25h'):
            assert send(sequence)==sequence,sequence
        for prefix in (b'\x1b',b'\x1b[',b'\x1b[12;',b'\x1b[?25',b'\x1b]title',b'\x1bPdata'):
            assert send(prefix)==b'';call(5)
            assert send(b'X')==b'X'
        for sequence in (b'\x1b[6n',b'\x1b[c',b'\x1b[?7h',b'\x1b[?1049h',b'\x1b]title\x07',b'\x1bPdata\x1b\\',b'\x1bc'):
            assert send(sequence+b'X')==b'X',sequence
        for length in list(range(41))+[64,255,1000]:
            call(5)
            sequence=b'\x1b['+b'1'*length+b'm'
            assert send(sequence+b'X')==(sequence+b'X' if length<=28 else b'X'),length
            assert cpu.mem[state]==0
        assert send(b'\x1b[12\x1b[H')==b'\x1b[H'
        assert send(b'\x1b[12\x18X')==b'X'
        assert send(b'\x1b[12\x1aX')==b'X'
        send(b'\x1b[12');output.clear();call(4)
        assert bytes(output)==b'\x1b[2J\x1b[H'
        assert call(1)!=0 and call(2)==ord('a')
        import pyte
        screen=pyte.Screen(80,24);stream=pyte.Stream(screen)
        call(4);stream.feed(bytes(output).decode('ascii'))
        stream.feed(send(b'\x1b[6;11HMARK\x1b[7mREV\x1b[0m').decode('ascii'))
        assert screen.display[5][10:17]=='MARKREV'
        assert screen.buffer[5][14].reverse and not screen.buffer[5][10].reverse
        stream.feed(send(b'\x1b[6;15H\x1b[K').decode('ascii'))
        assert screen.display[5][10:17]=='MARK   '
        assert (screen.cursor.x,screen.cursor.y)==(14,5)
        print(f'PASS ANSI relocated {base:04X}: supported sequences, reset/cancel, bounded overflow, suppressed queries/strings and raw input')


if __name__=='__main__':main()
