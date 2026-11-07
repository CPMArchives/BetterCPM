#!/usr/bin/env python3
"""Execute the actual checked raw reader with a deterministic sector-transfer fixture."""
import argparse
import json
import tempfile
from pathlib import Path

from build_ccp import assemble
from build_z80pack_image import symbols
from test_bios import Z80

# Each sector emits a 3-byte witness per 128-byte quarter. All Model II raw
# mapping, real copy/deblocking, cross-sector iteration and errors stay live.
STUB="""        ORG 8000H
        LD A,D
        OR A
        LD B,1
        JR Z,ONE
        LD B,4
ONE:    LD C,0
LOOP:   LD (HL),D
        INC HL
        LD (HL),E
        INC HL
        LD (HL),C
        PUSH DE
        LD DE,126
        ADD HL,DE
        POP DE
        INC C
        DJNZ LOOP
        XOR A
        RET
        END
"""


def check(out):
    names=symbols(out/'disk.lst')
    stub=0x8000
    base=names['DC_RAW'] # private vector itself jumps past the 6-entry table
    disk=(out/'disk.bin').read_bytes()
    origin=json.loads((out.parent/'profile/context.json').read_text())['symbols']['LY_DISK']
    assert int.from_bytes(disk[16:18],'little')==base
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp)
        code=assemble(Path.home()/'bin/z80asm',STUB,tmp/'fixture.bin',tmp/'fixture.lst',stub)
    def read(first,count,valid):
        m=Z80(b'')
        m.mem[origin:origin+len(disk)]=disk
        m.mem[names['M2_XFER']:names['M2_XFER']+3]=bytes((0xC3,0,0x80))
        m.mem[stub:stub+len(code)]=code
        m.de,m.b,m.hl=first,count,0x3000
        m.run(origin+15,limit=80000)
        if (m.a==0)!=valid:raise ValueError((first,count,m.a))
        if not valid:
            if any(m.mem[0x3000:0x3080]):raise ValueError('invalid read changed target')
            return
        for i in range(count):
            n=first+i
            if n<8: addr=(0,13 if n==3 else n+1,0)
            else: addr=(1+(n-8)//64,1+((n-8)//4)%16,(n-8)%4)
            got=tuple(m.mem[0x3000+128*i:0x3003+128*i])
            if got!=addr:raise ValueError((first,count,i,addr,got))
    for n in range(160):read(n,1,True)
    for n,k in [(0,8),(2,12),(6,16),(8,52),(60,8),(68,8),(76,8),(84,16),(100,8),(108,52),(139,21)]:
        read(n,k,True)
    for n,k in [(1,0),(160,1),(159,2),(256,1),(255,1)]:read(n,k,False)
    print('PASS: assembled raw reader, 160 single records, aligned and split carriers, invalid bounds (FDC/DMA stubbed)')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('artifacts',type=Path)
    check(p.parse_args().artifacts.resolve())
