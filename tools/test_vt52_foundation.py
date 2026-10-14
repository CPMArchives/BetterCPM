#!/usr/bin/env python3
"""Execute VT52 screen foundation against the cpmsim BIOS at two load addresses."""
import argparse
import re
from pathlib import Path
from test_bios import Z80
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/vt52-development'


def symbols(path):
    return {name:int(address,16) for address,name in re.findall(r'^([0-9a-f]{4})\s+.*?\b([A-Z][A-Z0-9_]*):',path.read_text(),re.M)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bios',type=Path,default=ROOT/'build/z80pack')
    args=parser.parse_args()
    syms=symbols(OUT/'vt52.lst')
    bios=symbols(args.bios/'bios.lst')
    base_bios=bios['MONRAW']-69
    code=(OUT/'vt52.bin').read_bytes()
    carrier=(OUT/'VT52.RSX').read_bytes()
    count=int.from_bytes(carrier[22:24],'little')
    slots=[int.from_bytes(carrier[48+2*i:50+2*i],'little') for i in range(count)]
    cases=0
    for base in [0x6000,0x8101]:
        cpu=Z80(b'')
        data=(args.bios/'bios.bin').read_bytes()
        cpu.mem[base_bios:base_bios+len(data)]=data
        cpu.setword(1,base_bios+3)
        relocated=bytearray(code)
        for slot in slots:
            value=int.from_bytes(code[slot:slot+2],'little')+base-0x8000
            relocated[slot:slot+2]=value.to_bytes(2,'little')
        cpu.mem[base:base+len(code)]=relocated
        entry=syms['VT_ENTRY']+base-0x8000
        rowaddr=syms['VT_ROW']+base-0x8000
        coladdr=syms['VT_COL']+base-0x8000
        state=syms['VT_STATE']+base-0x8000
        output=[]
        def write(port,value):
            assert port&255==1
            output.append(value)
        cpu.port_write=write
        cpu.port_read=lambda port:3 if port&255==0 else ord('a')
        def call(op,char=0):
            sp=cpu.sp
            cpu.a,cpu.c=op,char
            cpu.run(entry,limit=10000)
            assert cpu.sp==sp
            return cpu.a
        def send(chars):
            output.clear()
            for char in chars:call(0,char)
            return bytes(output)
        def position(row,col):return f'\x1b[{row+1};{col+1}H'.encode()
        for row in range(24):
            for col in range(80):
                cpu.mem[rowaddr],cpu.mem[coladdr]=0,0
                actual=send(bytes([27,ord('Y'),32+row,32+col]))
                assert actual==position(row,col),(row,col,actual,position(row,col))
                assert (cpu.mem[rowaddr],cpu.mem[coladdr])==(row,col)
                for seq in [b'X',b'\x08',b'\x09',b'\x0a',b'\x0d',b'\x1bA',b'\x1bB',b'\x1bC',b'\x1bD',b'\x1bH',b'\x1bI',b'\x1bJ',b'\x1bK']:
                    cpu.mem[rowaddr],cpu.mem[coladdr]=row,col
                    r,c=row,col
                    expected=b''
                    if seq==b'X':
                        c=min(79,col+1)
                        expected=b'X'+(position(r,c) if col==79 else b'')
                    elif seq in [b'\x08',b'\x1bD']:
                        c=max(0,col-1)
                        expected=position(r,c) if col else b''
                    elif seq==b'\x09':
                        c=min(79,col+1) if col>=72 else (col//8+1)*8
                        expected=position(r,c) if col<79 else b''
                    elif seq==b'\x0a':r=min(23,row+1);expected=b'\n'
                    elif seq==b'\x0d':c=0;expected=position(r,c)
                    elif seq==b'\x1bA':r=max(0,row-1);expected=position(r,c) if row else b''
                    elif seq==b'\x1bB':r=min(23,row+1);expected=position(r,c) if row<23 else b''
                    elif seq==b'\x1bC':c=min(79,col+1);expected=position(r,c) if col<79 else b''
                    elif seq==b'\x1bH':r,c=0,0;expected=position(r,c)
                    elif seq==b'\x1bI':r=max(0,row-1);expected=position(r,c) if row else b'\x1bM'
                    elif seq==b'\x1bJ':expected=b'\x1b[0J'
                    elif seq==b'\x1bK':expected=b'\x1b[0K'
                    assert send(seq)==expected,(base,row,col,seq,output,expected)
                    assert (cpu.mem[rowaddr],cpu.mem[coladdr])==(r,c),(row,col,seq)
                    cases+=1
        # Invalid high row retains the previous row; high column clips.
        cpu.mem[rowaddr],cpu.mem[coladdr]=5,10
        assert send(b'\x1bY\x7f\x7f')==position(5,79)
        for prefix in [b'\x1b',b'\x1bY',b'\x1bY!']:
            send(prefix)
            old=(cpu.mem[rowaddr],cpu.mem[coladdr])
            output.clear();call(5)
            assert cpu.mem[state]==0 and not output
            assert (cpu.mem[rowaddr],cpu.mem[coladdr])==old
        output.clear();call(4)
        assert bytes(output)==b'\x1b[2J\x1b[H'
        assert cpu.mem[rowaddr]==cpu.mem[coladdr]==cpu.mem[state]==0
        assert send(b'\x00\x7f')==b''
        assert send(b'\x07')==b'\x07'
        assert call(1)==1  # raw transport; public BIOS normalizes the status
        assert call(2)==ord('a')
        assert call(6)==255
        # Execute the assembled utility with controlled service lookup/input.
        image=(OUT/'VT52TST.COM').read_bytes()
        cpu.mem[256:256+len(image)]=image
        cpu.mem[0:3]=bytes([0xC3,(base_bios+3)&255,(base_bios+3)>>8])
        cpu.mem[base_bios+3:base_bios+6]=bytes.fromhex('c3ffff')
        cpu.mem[5:8]=bytes.fromhex('d3fec9')
        for available in [False,True]:
            pauses=[]
            output.clear()
            messages=bytearray()
            def bdos(port,value):
                if port&255==1:
                    output.append(value)
                    return
                assert port&255==254
                if cpu.c==182:
                    assert bytes(cpu.mem[cpu.de+4:cpu.de+10])==b'MCON\x01\x00'
                    cpu.setword(cpu.de+12,entry)
                    cpu.a=0 if available else 255
                elif cpu.c==6:
                    messages.append(cpu.e)
                    if available:
                        saved={k:getattr(cpu,k) for k in ['a','b','c','d','e','h','l','pc','z','carry']}
                        call(0,cpu.e)
                        for k,v in saved.items():setattr(cpu,k,v)
                elif cpu.c==1:
                    pauses.append((cpu.mem[rowaddr],cpu.mem[coladdr]))
                    cpu.a=32
                else:raise AssertionError(('unexpected utility BDOS',cpu.c))
            cpu.port_write=bdos
            cpu.run(256,limit=100000)
            if available:
                assert len(pauses)==3
                assert b'VT52 foundation exercise complete.' in messages
                assert b'\x1b[6;11H' in bytes(output)
                assert b'\x1b[11;80H' in bytes(output)
                assert b'\x1b[0K' in bytes(output) and b'\x1b[0J' in bytes(output)
                assert cpu.mem[state]==0
            else:
                assert not pauses and messages.startswith(b'No MCON provider loaded.')
        cpu.port_write=write

    print(f'PASS: {cases} relocated VT52 cursor/control cases, ANSI translation, reset/clear and raw input bypass')


if __name__=='__main__':main()
