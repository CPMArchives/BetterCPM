#!/usr/bin/env python3
"""Reject malformed transient DIR operands in the current pure selector parser.

Resident selector coverage is in test_rcp_shared_selector.py. DIR has its own
listing; the other non-COPY wrappers use the common transient listing.
"""
from pathlib import Path
from build_rcp_transients import COMMANDS, symbol
from test_bios import Z80
ROOT=Path(__file__).resolve().parents[1]


def main():
    for command,entry in COMMANDS.items():
        if command=='COPY':continue
        listing=ROOT/'build/utilities'/('dir-transient.lst' if command=='DIR' else 'rcp-transient.lst')
        image=(ROOT/'build/utilities'/(command+'.COM')).read_bytes()
        assert image[26]==0xcd
        assert int.from_bytes(image[27:29],'little')==symbol(listing,entry),command
    image=(ROOT/'build/utilities/DIR.COM').read_bytes()
    listing=ROOT/'build/utilities/dir-transient.lst'
    at=lambda name:symbol(listing,name)
    for pattern in ('F*A.DAT','F**?.DAT','F?**?.DAT','F.**A',
                    'ABCDEFGHI.COM','FOO.ABCD','FOO..DAT'):
        cpu=Z80(b'');cpu.mem[256:256+len(image)]=image
        cpu.mem[5]=0x76  # Any BDOS call fails this pure-parser check.
        fcb=at('BC_FCB');cpu.mem[fcb:fcb+36]=bytes([0xa5])*36
        cpu.mem[0x7000:0x7000+len(pattern)]=pattern.encode()
        cpu.hl,cpu.b,cpu.d,cpu.e=0x7000,len(pattern),0,0
        cpu.run(at('DP_PARSE'),limit=100000)
        assert cpu.carry,pattern
        assert bytes(cpu.mem[fcb:fcb+36])==bytes([0xa5])*36,pattern
    print('PASS current DIR wrapper targets and seven malformed operands: no BDOS I/O or command FCB expansion')


if __name__=='__main__':main()
