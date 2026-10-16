#!/usr/bin/env python3
"""Saved IOBYTE: strict parser, build-owned record, capability gate and rollback."""
from pathlib import Path
from test_bios import Z80
from test_utility_versions import address
ROOT=Path(__file__).resolve().parents[1]

def main():
    image=(ROOT/'build/utilities/CONFIG.COM').read_bytes()
    listing=(ROOT/'build/utilities/config.lst').read_text();a=lambda n:address(listing,n)
    def cpu(tail):
        c=Z80(b'');c.mem[256:256+len(image)]=image;c.mem[:3]=bytes.fromhex('c3ffff')
        c.mem[5:8]=bytes((0xdb,254,0xc9));d=tail.encode();c.mem[128]=len(d);c.mem[129:129+len(d)]=d
        return c
    for tail in ['/IOBYTE=85',' /iobyte=149 ']:
        c=cpu(tail);c.run(a('CF_PARSE'),limit=200000)
        assert not c.carry and c.mem[a('CF_MODE')]==8
    for tail in ['/IOBYTE=256','/IOBYTE=-1','/IOBYTE=0','/IOBYTE=87','/IOBYTE=',
                 '/IOBYTE=85 /SHOW','/IOBYTE=85X','/IOBYTE=85 /VER']:
        c=cpu(tail);out=[]
        def invalid_io(port):
            if c.c==9:
                out.extend(c.mem[c.de:c.mem.index(36,c.de)]);return 0
            assert c.c==2,('invalid IOBYTE did I/O',c.c)
            out.append(c.e);return 0
        c.port_read=invalid_io;c.run(256,limit=200000)
        assert bytes(out) in [b'Invalid CONFIG usage.\r\n',b'Invalid /VER usage.\r\n'],(tail,bytes(out))
    for boundary,allowed in [(0xabff,False),(0xac00,True)]:
        c=cpu('/IOBYTE=85');c.mem[5:8]=bytes((0xc3,boundary&255,boundary>>8))
        c.mem[boundary:boundary+3]=bytes((0xdb,254,0xc9))
        c.mem[a('INIT')]=0xc9;c.mem[a('IO_APPLY'):a('IO_APPLY')+3]=bytes((0xdb,244,0xc9))
        entered=[];out=[]
        def guarded_io(port):
            if port&255==244:entered.append(True);return 0
            if c.c==6:return 13
            assert c.c==2,c.c;out.append(c.e);return 0
        c.port_read=guarded_io;c.run(256,limit=200000)
        assert bool(entered)==allowed
        if not allowed:assert b'Not enough transient memory (43K required).'  in bytes(out)
    template=(ROOT/'build/trs80/stage1.bin').read_bytes()[:128].ljust(128,b'\0')
    for fault in [None,'decline','crc','read','write','verify','rollback','unsupported','factory','bad-console']:
        value=197 if fault=='unsupported' else (149 if fault=='factory' else 85)
        c=cpu('/IOBYTE='+str(value));c.run(a('CF_PARSE'),limit=200000);assert not c.carry
        disk=bytearray(template)
        if fault=='factory':disk[1]=85
        if fault=='crc':disk[20]^=1
        if fault=='bad-console':disk[1]=255
        original=bytes(disk);out=[];reads=[];writes=[];input_calls=[]
        c.mem[3]=0x55
        for label,port in [('SGDISKSET',230),('SGIO',231),('SGBIOS',232)]:
            c.mem[a(label):a(label)+3]=bytes((0xdb,port,0xc9))
        def io(port):
            port&=255
            if port==254:
                if c.c==2:out.append(c.e);return 0
                assert c.c==6,c.c;input_calls.append(True);return ord('N' if fault=='decline' else 'Y')
            if port==230:
                c.mem[a('SGSPT'):a('SGSPT')+2]=(80).to_bytes(2,'little');c.z=True;return 0
            if port==232:
                assert c.a==63;c.hl=0x2002;c.z=False;return 0
            assert port==231
            assert c.mem[a('SGINDEX')]==4 and c.mem[a('SGHEAD')+7]==0
            ptr=c.word(a('SGIOBUF'));op=c.a
            if op:
                writes.append(bytes(c.mem[ptr:ptr+128]))
                if fault=='write' and len(writes)==1:c.z=False;return 1
                disk[:]=c.mem[ptr:ptr+128]
            else:
                reads.append(True)
                if fault=='read':c.z=False;return 1
                data=bytearray(disk)
                if (fault in ('verify','rollback') and len(reads)==2) or (fault=='rollback' and len(reads)==3):data[40]^=1
                c.mem[ptr:ptr+128]=data
            c.z=True;return 0
        c.port_read=io;c.run(a('IO_APPLY'),limit=2000000)
        assert c.mem[3]==0x55,'saved change modified live IOBYTE'
        if fault in (None,'factory'):
            expected=bytearray(original);expected[1]=value
            assert disk==expected and len(writes)==1 and b'live unchanged' in bytes(out),(fault,bytes(out))
        else:
            assert bytes(disk)==original,(fault,bytes(out))
            if fault in ('crc','read','unsupported','bad-console'):assert not writes and not input_calls
            if fault in ('write','verify','rollback'):assert len(writes)==2
            if fault=='rollback':assert b'damaged' in bytes(out).lower(),bytes(out)
    print('PASS CONFIG saved IOBYTE: parser, capability/CRC gates, exact-byte save, live preservation, verification and rollback')
if __name__=='__main__':main()
