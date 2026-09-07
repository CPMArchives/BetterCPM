#!/usr/bin/env python3
"""Execute relocated FDF machine code against independent surface/ID cases."""
import struct
from pathlib import Path
from test_bios import Z80
from test_disk_utilities import records
from system_layout import LAYOUT as L
ROOT=Path(__file__).resolve().parents[1]

def cpu_at(base):
    carrier=(ROOT/'build/rsx/FDF.RSX').read_bytes()
    size=struct.unpack_from('<H',carrier,12)[0]
    cpu=Z80(b'')
    cpu.mem[base:base+size]=carrier[512:512+size]
    count=struct.unpack_from('<H',carrier,22)[0]
    linked=struct.unpack_from('<H',carrier,10)[0]
    for i in range(count):
        off=struct.unpack_from('<H',carrier,48+2*i)[0]
        cpu.setword(base+off,(cpu.word(base+off)+base-linked)&65535)
    cpu.setword(base,0x7000)
    cpu.mem[0x7000:0x7004]=bytes([0x21,0x34,0x12,0xc9])
    cpu.mem[L['BDOS']:L['BDOS']+2]=bytes([0xaf,0xc9])
    cpu.sp=0x6000
    return cpu

def main():
    cases=0
    for base in (0x8000,0xB103):
        cpu=cpu_at(base)
        cpu.bc=208
        cpu.run(base+4)
        assert cpu.hl==0x4644
        for name,binding in records():
            cpu.ix=L['TABLES']+96
            cpu.mem[cpu.ix:cpu.ix+64]=binding
            cyls,secs,size,flags=binding[16:20]
            # Explicit expected surface sequence, independent of the assembly
            # track arithmetic. A sector's position in the skew list is its
            # logical number; the value stored there is its on-disk ID.
            if not flags&64:
                order=[(c,0) for c in range(cyls)]
            elif flags&2:
                second=list(range(cyls))
                if flags&1: second.reverse()
                order=[(c,0) for c in range(cyls)]+[(c,1) for c in second]
            else:
                order=[(c,s) for c in range(cyls) for s in (0,1)]
            for track in sorted(set([0,len(order)//2-1,len(order)//2,len(order)-1])):
                cyl,side=order[track]
                for record in (0, (secs<<size)-1):
                    cpu.bc=0x1D0;cpu.de=track;cpu.hl=record
                    cpu.run(base+4,limit=1000)
                    expected_id=binding[20+(record>>size)]+(secs if side and flags&8 else 0)
                    assert cpu.a==0 and cpu.b==(128|(size<<3)|(record&((1<<size)-1))), (name,track,record)
                    assert (cpu.c,cpu.d,cpu.e,cpu.h,cpu.l)==(cyl,side,expected_id,2*cyl+side if flags&4 else cyl,cyl),(name,track,record)
                    assert cpu.sp==0x6000
                    cases+=1
            cpu.bc=0x1D0;cpu.de=len(order);cpu.hl=0
            cpu.run(base+4)
            assert cpu.a==255 and not cpu.b&128, name
        # Mixed media: different lengths in the middle, not just a short tail.
        for sizes in ([0,3,1,2], [3,3,3,3,3,2], [2,0,2,1,3,0]):
            binding=bytearray(records()[0][1])
            binding[1:3]=sum(1<<n for n in sizes).to_bytes(2,'little')
            binding[17:20]=bytes([len(sizes),3,0x80])
            binding[20:52]=bytes(range(1,len(sizes)+1)).ljust(32,b'\0')
            binding[52]=1
            binding[53:61]=bytes(8)
            for i,n in enumerate(sizes): binding[53+i//4] |= n << (2*(i%4))
            cpu.ix=0x9000
            cpu.mem[0x9000:0x9050]=bytes([1])+binding+bytes(15)
            cpu.bc=0x2D0
            cpu.run(base+4)
            assert cpu.hl==0x4644, sizes
            cpu.ix=L['TABLES']+96
            cpu.mem[cpu.ix:cpu.ix+64]=binding
            record=0
            for index,size in enumerate(sizes):
                for quarter in range(1<<size):
                    cpu.bc=0x1D0;cpu.de=2;cpu.hl=record
                    cpu.run(base+4,limit=4000)
                    assert (cpu.a,cpu.b,cpu.c,cpu.d,cpu.e,cpu.h,cpu.l)==(0,128|(size<<3)|quarter,2,0,index+1,2,2),(sizes,record)
                    record+=1
        # Refuse a size-map sum which disagrees with the DPB.
        cpu.ix=0x9000;cpu.mem[0x9002]+=1;cpu.bc=0x2D0
        cpu.run(base+4)
        assert cpu.a==255
        # Unload detaches only dependent aliases, then tails into the manager.
        for i,f in enumerate((0xE0,0xC4,0x80,0xD2)):
            addr=L['TABLES']+80*i+16
            cpu.mem[addr]=i;cpu.mem[addr+19]=f
        cpu.mem[0x7100:0x710C]=bytes([1,2,0,0])+b'FDF     '
        cpu.bc=202;cpu.de=0x7100
        cpu.run(base+4)
        assert cpu.hl==0x1234
        assert [cpu.mem[L['TABLES']+80*i+16] for i in range(4)]==[0,255,2,255]
    print(f'PASS: {cases} catalogue boundary mappings at two relocations; rejection, stack and unload')
if __name__=='__main__':main()
