#!/usr/bin/env python3
"""Saved inspection uses checked carrier reads and cannot reach save/activation."""
import struct
from pathlib import Path
from test_bios import Z80
from test_utility_versions import address
from sysgen_image import sysgen_image
from system_layout import LAYOUT
ROOT=Path(__file__).resolve().parents[1]


def main():
    program=(ROOT/'build/utilities/CONFIG.COM').read_bytes()
    listing=(ROOT/'build/utilities/config.lst').read_text()
    resident=(ROOT/'build/system/resident.bin').read_bytes()
    reference=sysgen_image(resident,LAYOUT['SYSTEM'],52,8,36)
    signature=resident.index(b'BDCF'+bytes((5,4,4,64)))
    def addr(n):return address(listing,n)
    for failure in (None,0,1,27,52,'carrier','disk-read'):
        c=Z80(b'');c.mem[256:256+len(program)]=program;c.mem[:3]=bytes.fromhex('c3ffff')
        c.mem[5:8]=bytes((0xdb,254,0xc9));c.mem[addr('CF_MODE')]=1
        for label,port in [('SGREADF',230),('API',231),('SGBIOS',232),('SGIO',233)]:
            at=addr(label);c.mem[at:at+3]=bytes((0xdb,port,0xc9))
        # Successful inspection exits before current-state fetch or write paths.
        at=addr('CF_SDRIVES');c.mem[at:at+3]=bytes.fromhex('c3ffff')
        c.mem[0x9000:0x9010]=bytes(16);c.mem[0x900a:0x900c]=struct.pack('<H',0x9100)
        c.mem[0x9100:0x9110]=bytes(16);c.mem[0x9100:0x9102]=struct.pack('<H',36)
        c.mem[0x910d:0x910f]=struct.pack('<H',4)
        c.mem[0x9200:0x9210]=resident[signature:signature+16]
        reads=0;carrier_reads=0;out=[];seen=[]
        def io(port):
            nonlocal reads,carrier_reads
            port&=255
            if port==254:
                if c.c==2:out.append(c.e);return 0
                assert c.c in (15,16),('unexpected interaction/write',c.c)
                return 0
            if port==230:
                n=reads;reads+=1
                if failure==n:c.z=False;return 1
                if n==53:c.z=False;return 1  # exact file EOF
                c.mem[c.de:c.de+128]=reference[n*128:(n+1)*128];c.z=True;return 0
            if port==231:
                assert c.b==0,('inspection attempted activation/current fetch',c.b)
                c.hl=0x9200;c.z=True;return 0
            if port==232:
                assert c.a==27,('unexpected BIOS action',c.a)
                c.hl=0x9000;return 0
            assert port==233 and c.a==0,'inspection attempted write'
            n=c.mem[addr('SGINDEX')];at=c.word(addr('SGIOBUF'))
            if failure=='disk-read' and n==27:c.z=False;return 1
            data=bytearray(reference[128+n*128:256+n*128])
            if failure=='carrier' and n==0:data[0]^=1
            c.mem[at:at+128]=data;c.z=True;carrier_reads+=1;seen.append(n);return 0
        c.port_read=io;c.run(addr('SYSGEN'),limit=3000000)
        assert b'Push ENTER' not in bytes(out) and b'(Y/N)' not in bytes(out)
        if failure is None:assert seen==list(range(52)) and not out
        elif failure=='carrier':assert b'Boot disk does not match' in bytes(out)
        elif failure=='disk-read':assert b'Cannot read boot system records' in bytes(out)
        else:assert b'Missing or invalid' in bytes(out)
    print('PASS: inspection validation, early/middle/final reference read failures, carrier mismatch and no writes/activation/prompts')


if __name__=='__main__':main()
