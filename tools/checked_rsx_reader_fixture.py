#!/usr/bin/env python3
"""Execute the maintained copied reader against every checked reconstruction slot."""
from pathlib import Path
import tempfile, json, binascii, struct, hashlib
from build_ccp import assemble
from system_layout import LAYOUT
from test_bios import Z80
from build_z80pack_image import symbols
from rsx_container import NAMES
ROOT=Path(__file__).resolve().parents[1]
STREAM=0x1000
IO=0x6400
NAME=0x5F20
LIMIT=0x5FF0
FAILREC=0x5FF1

def run_reader_cases(foreign=None):
    images={n+'.RSX':(ROOT/'build/system'/ (n+'.RSX')).read_bytes() for n in NAMES}
    data=(ROOT/'build/system/R3PACK.RSX').read_bytes()
    assert len(data)==15872 and data[:4]==b"BCPH"
    results=[]
    cases=[]
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
        LD (0{LAYOUT['FILE']+124:04X}H),A
        XOR A
        RET
READ:   PUSH BC
        LD A,(0{LAYOUT['FILE']+141:04X}H)
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
        LD A,(0{LAYOUT['FILE']+141:04X}H)
        INC A
        LD (0{LAYOUT['FILE']+141:04X}H),A
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
        def run(slot,length=124,failure=255,record=None, damaged=None, mode=0, expected=None):
            c=Z80(b'');c.mem[STREAM:STREAM+len(data)]=data if damaged is None else damaged
            bios=(ROOT/"build/z80pack/bios.bin").read_bytes();c.mem[LAYOUT["BIOS"]:LAYOUT["BIOS"]+len(bios)]=bios
            loader=(ROOT/'build/system/fileloader.bin').read_bytes()
            c.mem[LAYOUT['FILE']:LAYOUT['FILE']+len(loader)]=loader
            c.mem[LAYOUT['EXTENSIONS']:LAYOUT['EXTENSIONS']+len(stub)]=stub
            io=bytearray((ROOT/'build/system/rsxio.bin').read_bytes());assert len(io)<=512
            if expected is not None:
                at=symbols(ROOT/'build/system/rsxio.lst')['RI_EXPECT']+1
                io[at:at+2]=expected.to_bytes(2,'little')
            c.mem[IO:IO+len(io)]=io;c.mem[NAME]=slot*8 if record is None else record
            c.mem[LIMIT]=length;c.mem[FAILREC]=failure
            c.mem[LAYOUT['CONFIG']:LAYOUT['CONFIG']+1024]=b'\xa5'*1024
            c.mem[LAYOUT['RSX']:LAYOUT['RSX']+1024]=b'\xa5'*1024
            c.a=mode;c.hl=IO;c.de=NAME;c.ix=0x1234;c.sp=0x5E00
            if mode:
                c.mem[NAME+8:NAME+14]=struct.pack('<HHH',NAME,IO-1024,0);c.de=NAME+8
            c.run(IO,limit=1000000)
            assert c.ix==0x1234 and c.sp==0x5E00
            cases.append({'slot':slot,'length_records':length,'failed_record':failure,'mode':mode,'accepted':c.a==0,'damaged_sha256':hashlib.sha256(damaged).hexdigest() if damaged is not None else None})
            return c
        for slot,name in enumerate(NAMES):
            c=run(slot);assert c.a==0,name
            assert bytes(c.mem[LAYOUT['CONFIG']:LAYOUT['CONFIG']+1024])==images[name+'.RSX'],name
        for slot,name in enumerate(NAMES):
            c=run(slot,mode=1);assert c.a==0,name
            assert bytes(c.mem[LAYOUT['RSX']:LAYOUT['RSX']+1012])==images[name+'.RSX'][:1012]
            assert bytes(c.mem[LAYOUT['RSX']+1012:LAYOUT['RSX']+1024])==b'\xa5'*12
            assert bytes(c.mem[LAYOUT['CONFIG']:LAYOUT['CONFIG']+1024])==b'\xa5'*1024
        for slot,length,failure in [(0,123,255),(14,123,255),(15,124,255),(0,124,0),(0,124,3),(14,124,122),(14,124,123)]:
            c=run(slot,length,failure);assert c.a!=0,(slot,length,failure)
            assert bytes(c.mem[LAYOUT['CONFIG']:LAYOUT['CONFIG']+1024])==b'\xa5'*1024
        c=run(0,record=1);assert c.a!=0
        for slot in range(15):
            # Every record in the header and the requested slot can fail.
            for rec in list(range(4))+list(range(4+slot*8,12+slot*8)):
                c=run(slot,failure=rec);assert c.a!=0,(slot,rec)
                assert bytes(c.mem[LAYOUT['CONFIG']:LAYOUT['CONFIG']+1024])==b'\xa5'*1024
                results.append(['read-failure',slot,rec])
            for off in (0,511,1023):
                bad=bytearray(data);bad[512+slot*1024+off]^=1
                c=run(slot,damaged=bad);assert c.a!=0,(slot,off)
                assert bytes(c.mem[LAYOUT['CONFIG']:LAYOUT['CONFIG']+1024])==b'\xa5'*1024
                results.append(['payload-corruption',slot,off])
        for off in list(range(34))+[40,153,511]:
            bad=bytearray(data);bad[off]^=1
            c=run(0,damaged=bad);assert c.a!=0,off
            assert bytes(c.mem[LAYOUT['CONFIG']:LAYOUT['CONFIG']+1024])==b'\xa5'*1024
            results.append(['header-corruption',off])
        if foreign is not None:
            foreign=Path(foreign).read_bytes()
            assert foreign[8:24]!=data[8:24]
            c=run(0,damaged=foreign);assert c.a!=0
            c=run(0,damaged=foreign,expected=binascii.crc_hqx(foreign[:512],0xffff));assert c.a!=0
            results.append(['foreign-pack-rejected'])
    return {'matched_slots':15,'cases':cases,'rejections':results,'status':'PASS'}
