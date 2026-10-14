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
        test_queue(cpu,entry,base,syms,output)
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
                    elif seq==b'\x0a':
                        r=min(23,row+1)
                        expected=b'\n' if row<23 else b'\x1b[1;24r'+position(row,col)+b'\n\x1b[r'+position(row,col)
                    elif seq==b'\x0d':c=0;expected=position(r,c)
                    elif seq==b'\x1bA':r=max(0,row-1);expected=position(r,c) if row else b''
                    elif seq==b'\x1bB':r=min(23,row+1);expected=position(r,c) if row<23 else b''
                    elif seq==b'\x1bC':c=min(79,col+1);expected=position(r,c) if col<79 else b''
                    elif seq==b'\x1bH':r,c=0,0;expected=position(r,c)
                    elif seq==b'\x1bI':r=max(0,row-1);expected=position(r,c) if row else b'\x1b[1;24r'+position(row,col)+b'\x1bM\x1b[r'+position(row,col)
                    elif seq==b'\x1bJ':expected=b'\x1b[0J'
                    elif seq==b'\x1bK':expected=b'\x1b[0K'
                    assert send(seq)==expected,(base,row,col,seq,output,expected)
                    assert (cpu.mem[rowaddr],cpu.mem[coladdr])==(r,c),(row,col,seq)
                    cases+=1
        # Invalid high row retains the previous row; high column clips.
        cpu.mem[rowaddr],cpu.mem[coladdr]=5,10
        assert send(b'\x1bY\x7f\x7f')==position(5,79)
        for prefix in [b'\x1b',b'\x1bY',b'\x1bY!']:
            old=(cpu.mem[rowaddr],cpu.mem[coladdr])
            send(prefix)
            assert (cpu.mem[rowaddr],cpu.mem[coladdr])==old
            output.clear();call(5)
            assert cpu.mem[state]==0 and not output
            assert (cpu.mem[rowaddr],cpu.mem[coladdr])==old
        output.clear();call(4)
        assert bytes(output)==b'\x1b[2J\x1b[H'
        assert cpu.mem[rowaddr]==cpu.mem[coladdr]==cpu.mem[state]==0
        assert send(b'\x00\x7f')==b''
        assert send(b'\x07')==b'\x07'
        assert call(1)==255
        assert call(2)==ord('a')
        assert call(6)==255
        # Research finals remain non-contractual, but must recover safely.
        for final in set(range(256))-set(b'YHABCDIJKZ'):
            old=(cpu.mem[rowaddr],cpu.mem[coladdr])
            count=cpu.mem[syms['VQ_COUNT']+base-0x8000]
            assert send(bytes([27,final]))==b''
            assert cpu.mem[state]==0
            assert (cpu.mem[rowaddr],cpu.mem[coladdr])==old
            assert cpu.mem[syms['VQ_COUNT']+base-0x8000]==count

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
                elif cpu.c==6 and cpu.e==255:
                    saved={k:getattr(cpu,k) for k in ['b','c','d','e','h','l','pc','z','carry']}
                    value=call(2)
                    for k,v in saved.items():setattr(cpu,k,v)
                    cpu.a=value
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
                assert len(pauses)==3,(base,pauses,bytes(messages),cpu.mem[syms['VQ_COUNT']+base-0x8000])
                assert b'VT52 monitor exercise complete.' in messages
                assert b'\x1b[6;11H' in bytes(output)
                assert b'\x1b[11;80H' in bytes(output)
                assert b'\x1b[0K' in bytes(output) and b'\x1b[0J' in bytes(output)
                assert cpu.mem[state]==0
            else:
                assert not pauses and messages.startswith(b'No MCON provider loaded.')
        cpu.port_write=write

    print(f'PASS: {cases} relocated VT52 cursor/control cases, ANSI translation, reset/clear and raw input bypass')


def test_queue(cpu,entry,base,syms,output):
    from collections import deque
    addresses={name:syms[name]+base-0x8000 for name in ['VQ_HEAD','VQ_TAIL','VQ_COUNT','VQ_DATA']}
    reads=[]
    hardware=deque()
    def read(port):
        if port&255==0:return int(bool(hardware))
        assert port&255==1 and hardware
        value=hardware.popleft()
        reads.append(value)
        return value
    cpu.port_read=read
    def call(op,char=0):
        sp=cpu.sp
        cpu.a,cpu.c=op,char
        cpu.run(entry,limit=10000)
        assert cpu.sp==sp
        return cpu.a
    def identify():
        before=len(output)
        call(0,27);call(0,ord('Z'))
        assert len(output)==before
    for phase in range(16):
        cpu.mem[addresses['VQ_HEAD']]=cpu.mem[addresses['VQ_TAIL']]=phase
        cpu.mem[addresses['VQ_COUNT']]=0
        hardware.clear();hardware.extend(b'AB')
        reads.clear()
        assert call(1)==255 and reads==[ord('A')]
        for _ in range(5):
            identify()
        # A + five whole replies fills all 16 slots; another reply is dropped.
        assert cpu.mem[addresses['VQ_COUNT']]==16
        identify()
        assert cpu.mem[addresses['VQ_COUNT']]==16
        expected=deque(b'A'+b'\x1b/K'*5)
        for prefix in [b'\x1b',b'\x1bY',b'\x1bY!']:
            for byte in prefix:call(0,byte)
            call(5)
            assert cpu.mem[addresses['VQ_COUNT']]==16
        call(4)
        assert cpu.mem[addresses['VQ_COUNT']]==16
        while expected:
            head=cpu.mem[addresses['VQ_HEAD']]
            count=cpu.mem[addresses['VQ_COUNT']]
            for _ in range(3):assert call(1)==255
            assert cpu.mem[addresses['VQ_HEAD']]==head
            assert cpu.mem[addresses['VQ_COUNT']]==count
            assert reads==[ord('A')]
            assert call(2)==expected.popleft()
        assert call(2)==ord('B') and reads==[ord('A'),ord('B')]
        assert call(1)==0
    # Exercise capacity 0..16 without relying on a particular ring start.
    for capacity_used in range(17):
        cpu.mem[addresses['VQ_HEAD']]=cpu.mem[addresses['VQ_TAIL']]=0
        cpu.mem[addresses['VQ_COUNT']]=0
        hardware.clear()
        for _ in range(6):identify()
        assert cpu.mem[addresses['VQ_COUNT']]==15
        # Queue a key once empty; then rebuild occupancy by complete replies
        # and partial consumption to cover every remaining-free-space boundary.
        while cpu.mem[addresses['VQ_COUNT']]:call(2)
        hardware.append(ord('Q'));call(1)
        for _ in range(5):identify()
        for _ in range(16-capacity_used):call(2)
        before=cpu.mem[addresses['VQ_COUNT']]
        snapshot=bytes(cpu.mem[addresses['VQ_DATA']:addresses['VQ_DATA']+16])
        identify()
        assert cpu.mem[addresses['VQ_COUNT']]==before+(3 if before<=13 else 0)
        if before>13:
            assert bytes(cpu.mem[addresses['VQ_DATA']:addresses['VQ_DATA']+16])==snapshot
    while cpu.mem[addresses['VQ_COUNT']]:call(2)
    print('PASS: queue ordering, all 16 ring phases/17 capacity boundaries, atomic overflow and reset/clear preservation')


if __name__=='__main__':main()
