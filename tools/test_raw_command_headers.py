#!/usr/bin/env python3
"""Execute raw reader admission for packed and legacy CCP headers and CPX class."""
import struct
from pathlib import Path
from test_bios import Z80
from build_z80pack_image import symbols
from system_layout import LAYOUT as L

ROOT=Path(__file__).resolve().parents[1]


def main():
    image=(ROOT/'build/trs80/ccpreload.bin').read_bytes()
    sy=symbols(ROOT/'build/trs80/ccpreload.lst')
    for cpx,kind,accepted in ((False,1,True),(False,2,True),(False,0,False),
                               (False,3,False),(True,1,True),(True,2,False)):
        c=Z80(b'');base=L['RELOADER'];c.mem[base:base+len(image)]=image;c.sp=0x1000
        payload=bytearray(32);payload[10:12]=(0x8010).to_bytes(2,'little')
        if cpx:
            header=bytearray(512)
            struct.pack_into('<4sBBBBHHHHHHHHHHHH8sBBBBH',header,0,
                b'BCPX',1,kind,1,0,0,0x8000,32,256,8,0xffff,0xffff,1,512,512,48,544,
                b'PROBE   ',1,0,1,0,sum(payload)&65535)
            header[48:50]=(10).to_bytes(2,'little')
        else:
            header=bytearray(max(1,kind)*512)
            struct.pack_into('<4sBBHHHHH',header,0,b'BCM1',1,kind,0x8000,32,256,0,1)
            header[16:18]=(10).to_bytes(2,'little')
        data=(bytes(header)+payload).ljust(len(header)+512,b'\0');cursor=0
        c.mem[sy['CRNEXT']:sy['CRNEXT']+4]=b'\xd3\x01\xb7\xc9'
        c.mem[sy['CRRESET']:sy['CRRESET']+4]=b'\xd3\x02\xaf\xc9'
        def transfer(port,value):
            nonlocal cursor
            if port&255==2:cursor=0;return
            assert port&255==1
            assert cursor+512<=len(data)
            c.mem[c.hl:c.hl+512]=data[cursor:cursor+512];c.hl+=512;cursor+=512;c.a=0
        c.port_write=transfer
        c.mem[sy['CRFILE']]=int(cpx)
        c.setword(sy['CRMAGPTR'],sy['CRCPXMAG' if cpx else 'CRCCPMAG'])
        c.setword(sy['CRBOUND'],0x9000)
        c.run(sy['CRLOAD'],limit=100000)
        assert (c.a==0)==accepted,(cpx,kind,c.a)
        if accepted:
            assert c.word(0x8f0a)==0x8f10
            assert c.word(sy['CRBASE'])==0x8f00
    print('PASS raw one/two-sector CCP, invalid CCP size and strict CPX class admission')


if __name__=='__main__':main()
