#!/usr/bin/env python3
"""CRC-32 oracle vectors, masked fields, read failures and pre-write rejection."""
import struct
import zlib
from pathlib import Path
from test_bios import Z80
from test_utility_versions import address
from config_validation import validation_record,normalized
from system_layout import LAYOUT
ROOT=Path(__file__).resolve().parents[1]


def main():
    program=(ROOT/'build/utilities/CONFIG.COM').read_bytes()
    listing=(ROOT/'build/utilities/config.lst').read_text()
    resident=(ROOT/'build/system/resident.bin').read_bytes().ljust(52*128,b'\0')
    signature=resident.index(b'BDCF'+bytes((5,4,4,64)))
    physical,logical=struct.unpack_from('<HH',resident,signature+8)
    def addr(n):return address(listing,n)
    def cpu():
        c=Z80(b'');c.mem[256:256+len(program)]=program;c.mem[:3]=bytes.fromhex('c3ffff')
        return c
    vectors=[b'',b'123456789',bytes(range(256)),b'\0'*127,b'\xff'*129,
             normalized(resident,LAYOUT['SYSTEM'],physical,logical)]
    assert zlib.crc32(b'123456789')==0xcbf43926
    for data in vectors:
        c=cpu();c.mem[0x6000:0x6000+len(data)]=data;c.hl=0x6000;c.bc=len(data)
        c.run(addr('SGCRC32'),limit=15000000)
        got=struct.unpack_from('<I',c.mem,addr('SGCRC'))[0]
        assert got==zlib.crc32(data),(len(data),hex(got),hex(zlib.crc32(data)))
    failures=(None,'editable','first','middle','last','disk-read','layout','geometry')
    cases=[(f,1) for f in failures]+[(f,0) for f in failures if f not in (None,'editable')]
    for failure,mode in cases:
        c=cpu();c.mem[5:8]=bytes((0xdb,254,0xc9));c.mem[addr('CF_MODE')]=mode
        if mode==0:
            # Skip presentation and final menu cleanup, retaining the complete
            # validation/save entry. Any confirmation or write still fails.
            for label in ('HEADER','PAUSE'):c.mem[addr(label)]=0xc9
            c.mem[addr('SGEXIT'):addr('SGEXIT')+3]=bytes.fromhex('c3ffff')
        for label,port in [('API',231),('SGBIOS',232),('SGIO',233)]:
            at=addr(label);c.mem[at:at+3]=bytes((0xdb,port,0xc9))
        at=addr('CF_SDRIVES');c.mem[at:at+3]=bytes.fromhex('c3ffff')
        c.mem[0x900a:0x900c]=struct.pack('<H',0x9100)
        c.mem[0x9100:0x9102]=struct.pack('<H',36 if failure=='geometry' else 80)
        c.mem[0x910d:0x910f]=struct.pack('<H',4)
        c.mem[0x9200:0x9210]=resident[signature:signature+16]
        if failure=='layout':c.mem[0x9208]^=1
        source=bytearray(resident)
        if failure=='editable':
            for start,size in [(physical-LAYOUT['SYSTEM'],24)]+[(logical-LAYOUT['SYSTEM']+i*80+16,64) for i in range(4)]:
                for n in range(start,start+size):source[n]^=0xa5
        for label,n in [('first',0),('middle',len(source)//2),('last',len(source)-1)]:
            if failure==label:source[n]^=1
        out=[];seen=[]
        def io(port):
            port&=255
            if port==254:
                assert c.c==2,('unexpected interaction/file access/write',c.c)
                out.append(c.e);return 0
            if port==231:
                assert c.b==0,('inspection attempted activation/current fetch',c.b)
                c.hl=0x9200;c.z=True;return 0
            if port==232:
                assert c.a==27,('unexpected BIOS action',c.a)
                c.hl=0x9000;return 0
            assert port==233 and c.a==0,'inspection attempted write'
            n=c.mem[addr('SGINDEX')];at=c.word(addr('SGIOBUF'));seen.append(n)
            if failure=='disk-read' and n==27:c.z=False;return 1
            c.mem[at:at+128]=source[n*128:n*128+128];c.z=True;return 0
        c.port_read=io;c.run(addr('SYSGEN'),limit=18000000)
        text=bytes(out)
        assert b'Push ENTER' not in text and b'(Y/N)' not in text
        if failure in (None,'editable'):
            assert seen==list(range(52)) and not out,(failure,text)
            assert bytes(c.mem[0x4080:0x5a80])==bytes(source),'rollback original changed'
            assert bytes(c.mem[0x6000:0x7a00])==bytes(source),'masked defaults not restored'
        elif failure=='disk-read':assert b'Cannot read boot system records' in text
        else:assert b'Boot disk does not match' in text,(failure,text)
    print('PASS: Z80 CRC-32 oracle vectors, editable masking, fixed-byte corruption, layout/geometry/read failures and exact originals retained; no file access/writes/prompts')


if __name__=='__main__':main()
