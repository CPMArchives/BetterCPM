#!/usr/bin/env python3
"""CLI startup saves share verified writes and rollback without hidden pauses."""
from pathlib import Path
from test_bios import Z80
from test_utility_versions import address
from startup_record import build,parse
from system_layout import LAYOUT
ROOT=Path(__file__).resolve().parents[1]


def main():
    image=(ROOT/'build/utilities/CONFIG.COM').read_bytes()
    listing=(ROOT/'build/utilities/config.lst').read_text()
    def addr(name):return address(listing,name)
    old=build('OLD STARTUP',system_base=LAYOUT['SYSTEM'])
    for failed in ((),(1,),(2,),(1,2)):
        c=Z80(b'');c.mem[256:256+len(image)]=image;c.mem[:3]=bytes.fromhex('c3ffff')
        c.mem[5:8]=bytes((0xdb,254,0xc9));disk=bytearray(old);ops=[];out=[];writes=0
        for name,port in [('STLOAD',230),('SGIO',231),('SGVERIFY',232)]:
            at=addr(name);c.mem[at:at+3]=bytes((0xdb,port,0xc9))
        def io(port):
            nonlocal writes
            if port&255==254:
                if c.c==2:out.append(c.e);return 0
                assert c.c==6 and c.e==255,('unexpected input',c.c,c.e)
                return ord('Y')
            if port&255==230:
                c.mem[0x8000:0x8100]=old;c.z=True;c.carry=False;return 0
            index=c.mem[addr('SGINDEX')];pointer=c.word(addr('SGIOBUF'));start=(index-1)*128
            assert index in (1,2)
            if port&255==231:
                assert c.a==1
                writes+=1;ops.append(('write',index))
                if writes in failed:
                    disk[start:start+128]=b'!'*128;c.z=False;return 1
                disk[start:start+128]=c.mem[pointer:pointer+128];c.z=True;return 0
            assert port&255==232
            ops.append(('verify',index));assert disk[start:start+128]==c.mem[pointer:pointer+128]
            c.z=True;return 0
        c.port_read=io;c.mem[addr('CF_MODE')]=2
        command=b'NEW STARTUP';c.mem[addr('CF_LEN')]=len(command);at=addr('CF_TEXT');c.mem[at:at+len(command)]=command
        c.run(addr('CF_START'),limit=500000)
        text=bytes(out)
        assert b'Push ENTER' not in text
        if not failed:
            assert parse(bytes(disk),system_base=LAYOUT['SYSTEM'])=='NEW STARTUP'
            assert b'saved and verified' in text
            assert ops==[('write',1),('verify',1),('write',2),('verify',2)]
        elif failed==(1,2):
            assert b'Boot disk may be damaged' in text and bytes(disk)!=old
            assert b'Original startup defaults restored' not in text
        else:
            assert bytes(disk)==old and b'Original startup defaults restored' in text,(failed,text,ops)
            assert b'saved and verified' not in text
    print('PASS: CLI startup save, first/second-write rollback, failed rollback reporting and no completion pause')


if __name__=='__main__':main()
