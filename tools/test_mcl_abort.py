#!/usr/bin/env python3
"""Execute production resident abort sites and distinguish normal Function 0."""
from pathlib import Path
from build_z80pack_image import symbols
from system_layout import LAYOUT as L
from test_bios import Z80,SENTINEL

ROOT=Path(__file__).resolve().parents[1]
S=symbols(ROOT/'build/bdos/bdos.lst')


def machine():
    c=Z80(b'');data=(ROOT/'build/bdos/bdos.bin').read_bytes()
    c.mem[L['BDOS']:L['BDOS']+len(data)]=data
    c.mem[L['BIOS']+3:L['BIOS']+6]=bytes((0xc3,SENTINEL&255,SENTINEL>>8))
    c.mem[L['BIOS']+6:L['BIOS']+9]=b'\x3e\xff\xc9'
    c.mem[L['BIOS']+9:L['BIOS']+12]=b'\x3e\x03\xc9'
    c.mem[L['SYSTEM']+0x95]=3
    c.sp=0x7000
    return c


def main():
    for site in ('UB_CONIN','UB_PAUSE','UB_PUT','UB_PUTPAUSE','UB_RLCTRL','UB_SECKEY','UB_FROLOOP'):
        c=machine();c.ix=0x9000;c.hl=0x9000
        c.mem[S['UB_DIRTY']]=1
        c.run(S[site],limit=10000)
        assert c.mem[L['SYSTEM']+0x95]==7,site
        if site=='UB_SECKEY':assert c.mem[S['UB_DIRTY']]==0
    c=machine();c.c=0;c.run(S['UB_ENTRY'],limit=10000)
    assert c.mem[L['SYSTEM']+0x95]==3,'ordinary Function 0 latched cancellation'
    print('PASS seven production known-abort sites, failed-directory dirty reset and ordinary Function-0 continuation')


if __name__=='__main__':main()
