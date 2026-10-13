#!/usr/bin/env python3
"""Execute the copied reader against every packed slot and reject partial input."""
from pathlib import Path
import tempfile
from build_ccp import assemble
from system_layout import LAYOUT
from test_bios import Z80
from rsx_container import NAMES, PACK_BYTES, pack
ROOT=Path(__file__).resolve().parents[1]
STREAM=0x1000
IO=0x6C00
NAME=0x6620
LIMIT=0x5FF0
FAILREC=0x5FF1

def main():
    images={n+'.RSX':(ROOT/'build/system'/ (n+'.RSX')).read_bytes() for n in NAMES}
    data=(ROOT/'build/system/R3PACK.RSX').read_bytes()
    assert data==pack(images) and len(data)==PACK_BYTES
    # Fake disk adapter behind the real protected file loader. This retains
    # real OPEN/FCB/NEXT behavior while injecting deterministic disk failures.
    source=f'''        ASEG
        ORG 0{LAYOUT['EXTENSIONS']:04X}H
        JP NOOP
        JP NOOP
        JP OPEN
        JP READ
NOOP:   XOR A
        RET
OPEN:   LD A,({LIMIT:04X}H)
        LD (0ED02H),A
        XOR A
        RET
READ:   PUSH BC
        LD A,(0ED13H)
        LD HL,{FAILREC:04X}H
        CP (HL)
        JR Z,BAD
        LD L,A
        LD H,0
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        LD BC,{STREAM:04X}H
        ADD HL,BC
        POP DE
        LD BC,128
        LDIR
        LD A,(0ED13H)
        INC A
        LD (0ED13H),A
        XOR A
        RET
BAD:    POP BC
        LD A,1
        OR A
        RET
        END
'''
    with tempfile.TemporaryDirectory() as td:
        work=Path(td);stub=assemble(Path.home()/'bin/z80asm',source,work/'stub.bin',work/'stub.lst',LAYOUT['EXTENSIONS'])
        def run(slot,length=120,failure=255,record=None):
            c=Z80(b'');c.mem[STREAM:STREAM+len(data)]=data
            loader=(ROOT/'build/system/fileloader.bin').read_bytes()
            c.mem[LAYOUT['FILE']:LAYOUT['FILE']+len(loader)]=loader
            c.mem[LAYOUT['EXTENSIONS']:LAYOUT['EXTENSIONS']+len(stub)]=stub
            io=(ROOT/'build/system/rsxio.bin').read_bytes();assert len(io)<=256
            c.mem[IO:IO+len(io)]=io;c.mem[NAME]=slot*8 if record is None else record
            c.mem[LIMIT]=length;c.mem[FAILREC]=failure
            c.mem[LAYOUT['CONFIG']:LAYOUT['CONFIG']+1024]=b'\xa5'*1024
            c.a=0;c.hl=IO;c.de=NAME;c.ix=0x1234;c.sp=0x5E00
            c.run(IO,limit=100000)
            assert c.ix==0x1234 and c.sp==0x5E00
            return c
        for slot,name in enumerate(NAMES):
            c=run(slot);assert c.a==0,name
            assert bytes(c.mem[LAYOUT['CONFIG']:LAYOUT['CONFIG']+1024])==images[name+'.RSX'],name
        for slot,length,failure in [(0,119,255),(14,119,255),(15,120,255),(0,120,0),(0,120,3),(14,120,118),(14,120,119)]:
            c=run(slot,length,failure);assert c.a!=0,(slot,length,failure)
            assert bytes(c.mem[LAYOUT['CONFIG']:LAYOUT['CONFIG']+1024])==b'\xa5'*1024
        c=run(0,record=1);assert c.a!=0
    print('PASS: all 15 container slots, scratch frame, bounds, truncation and partial-read rejection')

if __name__=='__main__':main()
