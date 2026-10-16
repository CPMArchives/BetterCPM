#!/usr/bin/env python3
"""Pending-only startup default, with no drive activation or implicit save."""
import json
from pathlib import Path
from test_bios import Z80
from test_utility_versions import address
from startup_record import build
from system_layout import LAYOUT
ROOT=Path(__file__).resolve().parents[1]

def main():
    image=(ROOT/'build/utilities/CONFIG.COM').read_bytes()
    listing=(ROOT/'build/utilities/config.lst').read_text();a=lambda n:address(listing,n)
    def cpu(tail):
        c=Z80(b'');c.mem[256:256+len(image)]=image;c.mem[:3]=bytes.fromhex('c3ffff')
        c.mem[5:8]=bytes((0xdb,254,0xc9));data=tail.encode()
        c.mem[128]=len(data);c.mem[129:129+len(data)]=data;return c
    for tail in ['/DEFAULT',' /default\t']:
        c=cpu(tail);c.run(a('CF_PARSE'),limit=200000)
        assert not c.carry and c.mem[a('CF_MODE')]==7
    for tail in ['/DEFAULT X','/DEFAULT /SHOW','/DEFAULT /STARTUP="X"','/DEFAULT=1']:
        c=cpu(tail);out=[]
        def invalid_io(port):
            assert c.c==2,('invalid default performed I/O',c.c)
            out.append(c.e);return 0
        c.port_read=invalid_io;c.run(256,limit=200000)
        assert bytes(out)==b'Invalid CONFIG usage.\r\n',tail
    c=cpu('/DEFAULT');c.run(a('CF_PARSE'),limit=200000);out=[];entered=[]
    c.mem[a('PAUSE')]=0xc9
    c.mem[a('STARTMENU'):a('STARTMENU')+3]=bytes((0xdb,233,0xc9))
    def io(port):
        if port&255==233:entered.append(True);return 0
        assert c.c==2,('default activated/saved/read settings',c.c)
        out.append(c.e);return 0
    c.port_read=io;c.run(a('CF_DEFAULT'),limit=200000)
    default=json.loads((ROOT/'metadata/distribution.json').read_text())['cold_start_command']
    assert default=='SUBMIT STARTUP','update CONFIG and its default contract with the distribution'
    assert bytes(c.mem[a('STPEND'):a('STPEND')+256])==build(default,system_base=LAYOUT['SYSTEM'])
    assert c.mem[a('STDIRTY')]==1 and c.mem[a('STSTATE')]==1
    assert c.mem[a('CF_MODE')]==0 and entered==[True]
    assert b'pending' in bytes(out) and b'drives unchanged' in bytes(out)
    print('PASS CONFIG /DEFAULT: full-tail rejection, canonical private startup record, no activation/save, interactive continuation')
if __name__=='__main__':main()
