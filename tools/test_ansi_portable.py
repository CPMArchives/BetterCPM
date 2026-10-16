#!/usr/bin/env python3
"""Exercise private typed ANSI candidate on actual relocated screen backends."""
import pyte
from test_screen_backends import fixture,load,ROOT
from test_vt52_foundation import symbols


def main():
    out=ROOT/'build/ansi-portable-candidate';cases=0
    for name in ('M4SCRN','ANSISCRN'):
        for front,back in [(0x9000,0x6000),(0x4001,0x8101)]:
            cpu,old,cells,wire=fixture(name,back,cpmsim_bios=ROOT/'build/audit/release-090-z80pack')
            syms=load(cpu,out,'ansi',front)
            cpu.setword(front+12,cpu.backend_entry)
            entry=front+syms['AN_ENTRY']-0x8000
            screen=pyte.Screen(80,24);stream=pyte.Stream(screen)
            if name=='ANSISCRN':
                def emit(port,value):
                    assert port&255==1
                    wire.append(value);stream.feed(chr(value))
                cpu.port_write=emit
            def field(label):return front+syms[label]-0x8000
            guard=front+len((out/'ansi.bin').read_bytes());cpu.mem[guard:guard+16]=b'G'*16
            def call(op,char=0):
                cpu.a,cpu.c=op,char;sp=cpu.sp
                cpu.run(entry,limit=300000)
                assert cpu.sp==sp and cpu.mem[field('AN_COUNT')]<=31
                assert bytes(cpu.mem[guard:guard+16])==b'G'*16
                assert cpu.word(field('AC_PTR'))==cpu.word(field('AP_PTR'))==0
                return cpu.a
            def send(data):
                nonlocal cases
                for char in data:call(0,char)
                cases+=1
            def text(row,start,end):
                if name=='M4SCRN':return bytes(x&127 for x in cpu.mem[0xF800+80*row+start:0xF800+80*row+end]).decode()
                return screen.display[row][start:end]
            call(4);send(b'\x1b[6;11HMARK\x1b[7mREV\x1b[0m')
            assert text(5,10,17)=='MARKREV',(name,text(5,0,30),text(0,0,30),bytes(wire))
            if name=='M4SCRN':assert cpu.mem[0xF800+5*80+14]&128
            else:assert screen.buffer[5][14].reverse
            send(b'\x1b[6;15H\x1b[K');assert text(5,10,17)=='MARK   '
            # Relative motion, omitted/zero defaults, CR/LF and backspace.
            send(b'\x1b[1;1H\x1b[2B\x1b[3CX\rY\nZ\bQ')
            assert text(2,0,1)=='Y' and text(2,3,4)=='X' and text(3,1,2)=='Q'
            send(b'\x1b[;H!');assert text(0,0,1)=='!'
            send(b'\x1b[0;0f?');assert text(0,0,1)=='?'
            # Shared SGR interpreter, atomic malformed extended groups, reusable saves.
            send(b'\x1b[1;7;38;2;10;128;250m')
            record=bytes([33,2,10,128,250,0,0,0,0])
            assert bytes(cpu.mem[field('AP_VALUE'):field('AP_VALUE')+9])==record
            send(b'\x1b[1;38;5m')
            assert bytes(cpu.mem[field('AP_VALUE'):field('AP_VALUE')+9])==record
            send(b'\x1b[10;20H\x1b7\x1b[0m\x1b[2;2H\x1b8R\x1b8S')
            assert text(9,19,20)=='S'
            assert bytes(cpu.mem[field('AP_VALUE'):field('AP_VALUE')+9])==record
            send(b'\x1b[s\x1b[0m\x1b[2;2H\x1b[uT')
            assert text(9,20,21)=='T'
            # Visibility is parsed, not a host private sequence passthrough.
            send(b'\x1b[?25l');assert cpu.mem[field('AN_VISIBLE')]==0
            send(b'\x1b[?25h');assert cpu.mem[field('AN_VISIBLE')]==1
            send(b'\x1b[0m\x1b[1;24r')
            for prefix in (b'\x1b',b'\x1b[',b'\x1b[12;',b'\x1b[?25',b'\x1b]title',b'\x1bPdata'):
                call(5);before=len(wire);video=bytes(cpu.mem[0xF800:0xFF80]);send(prefix)
                assert len(wire)==before and bytes(cpu.mem[0xF800:0xFF80])==video
                call(5);send(b'\x1b[1;1HX');assert text(0,0,1)=='X'
            for sequence in (b'\x1b[6n',b'\x1b[c',b'\x1b[?7h',b'\x1b[?1049h',b'\x1b]title\x07',b'\x1bPdata\x1b\\',b'\x1bc',b'\x1b[3J',b'\x1b[1;2;3H'):
                before=len(wire);video=bytes(cpu.mem[0xF800:0xFF80]);send(sequence)
                assert len(wire)==before and bytes(cpu.mem[0xF800:0xFF80])==video,sequence
            for length in list(range(41))+[64,255,1000]:
                call(5);send(b'\x1b['+b'1'*length+b'm')
                assert cpu.mem[field('AN_STATE')]==0
            record=bytes(cpu.mem[field('AP_VALUE'):field('AP_VALUE')+9])
            send(b'\x1b['+b';'*16+b'm')
            assert bytes(cpu.mem[field('AP_VALUE'):field('AP_VALUE')+9])==record
            send(b'\x1b[12\x18');send(b'\x1b[12\x1a');send(b'\x1b[12\x1b[H')
            assert cpu.mem[field('AN_STATE')]==0
            # Numeric overflow saturates rather than wrapping into an active SGR.
            send(b'\x1b[0m\x1b[65536m')
            assert bytes(cpu.mem[field('AP_VALUE'):field('AP_VALUE')+9])==bytes(9)
            send(b'\x1b[0m\x1b[1;24r\x1b[3;1HAAA\x1b[4;1HBBB\x1b[5;1HCCC\x1b[3;5r\x1b[5;1H\x1bD')
            assert text(2,0,3)=='BBB' and text(3,0,3)=='CCC' and text(4,0,3)=='   '
            if name=='ANSISCRN':
                for width,height in [(80,25),(100,40)]:
                    screen=pyte.Screen(width,height);stream=pyte.Stream(screen)
                    send(b'\x1b[0m\x1b[r'+f'\x1b[{height};{width}H'.encode()+b'XY')
                    assert screen.buffer[height-2][width-1].data=='X'
                    assert screen.buffer[height-1][0].data=='Y'
                    send(f'\x1b[{height};{width}H\x1b7\x1b[1;1H\x1b8Z'.encode())
                    assert screen.buffer[height-1][width-1].data=='Z'
            print(f'PASS {name} frontend {front:04X}/backend {back:04X}: typed ANSI dispatch, SGR/save, bounded parser and cancellation')
    print(f'PASS {cases} portable ANSI streams; private candidate only')


if __name__=='__main__':main()
