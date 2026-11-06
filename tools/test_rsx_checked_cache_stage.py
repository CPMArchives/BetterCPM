#!/usr/bin/env python3
"""Execute checked scratch staging while reads destroy its original CFG code.

Authentication helpers are controlled stubs: this tests staging/restore and
failure control flow, not the separately tested CRC/identity algorithms.
"""
from pathlib import Path
import re
from build_ccp import assemble
from build_rsx_runtime_overlays import source
from test_rsx_disk_cache import setup, L, ROOT


def main():
    out=(ROOT/'build/rsx-checked-cache-stage');out.mkdir(exist_ok=True)
    links='LY_CCRC EQU 0EC66H\nLY_CBACK EQU 0EC84H\nLY_CCMP EQU 0E977H\nLY_CID EQU 0E981H\nBP_CACHE_CRC EQU 0\n'
    text=links+source('r3entry.mac','RVBASE',L['CONFIG']).replace('BP_CHECKED EQU 0','BP_CHECKED EQU 1')
    image=assemble(Path.home()/'bin/z80asm',text,out/'entry.bin',out/'entry.lst',L['CONFIG'])
    listing=(out/'entry.lst').read_text()
    sym=lambda n:int(re.search(r'^([0-9a-f]{4}).*\b'+n+':',listing,re.M|re.I)[1],16)
    assert len(image)<1000 and sym('PX_END')-sym('PX_CODE')<=512
    cases=[(None,0,0)]+[(n,0,255) for n in range(5)]+[(None,1,255)]
    for fault,crc,expected in cases:
        m=setup();m.stage_fault=fault
        m.mem[L['CONFIG']:L['CONFIG']+1024]=image.ljust(1024,b'\0')
        m.mem[0xEC66:0xEC6B]=bytes((0x21,crc,0,0xAF,0xC9))
        m.mem[0xE977:0xE979]=b'\xAF\xC9'
        m.mem[0x300:0x312]=bytes((2,1,0,0))+b'HELLO   '+bytes(2)+(0x405).to_bytes(2,'little')+(0x7000).to_bytes(2,'little')
        m.word(sym('RV_REQ'),0x300);m.word(sym('RV_HREQ')+2,0x6000)
        before=bytearray(m.mem[L['CONFIG']:L['CONFIG']+1024]);chain=m.chain()
        assert m.run(sym('PX_STAGE'))==expected,(fault,crc)
        at=sym('PX_HEADER')-L['CONFIG'];before[at:at+2]=(0x500).to_bytes(2,'little')
        assert bytes(m.mem[L['CONFIG']:L['CONFIG']+1024])==before,(fault,crc,'CFG not restored')
        assert m.chain()==chain
        assert m.context()==(2,17,0x1600)
    print('PASS checked staging: destructive CFG reads, five read failures, CRC rejection, frame/context preservation;',len(image),'entry bytes')


if __name__=='__main__':main()
