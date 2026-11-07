#!/usr/bin/env python3
"""Execute SYSGEN's destination patch on a real checked Model II package."""
import argparse
from pathlib import Path
from build_z80pack_image import symbols
from test_bios import Z80
from model2_media import geometry


def check(staged):
    out=staged/'build'
    utility=(out/'utilities/SYSGEN.COM').read_bytes()
    names=symbols(out/'utilities/sysgen.lst')
    payload=(out/'trs80m2/SYSTEM.SYS').read_bytes()[128:]
    disk=symbols(out/'trs80m2/disk.lst')
    import json
    layout=json.loads((out/'profile/context.json').read_text())['symbols']
    physical=1024+disk['DC_PHYS']-layout['LY_SYS']
    for size in (8,5):
        cpu=Z80(b'')
        cpu.mem[0x100:0x100+len(utility)]=utility
        cpu.mem[0x4000:0x4000+len(payload)]=payload
        # The caller's GET PHYSICAL returns this six-byte descriptor in REQ.
        cpu.mem[names['API']:names['API']+2]=bytes((0xaf,0xc9))
        descriptor=bytes((size,77,1,0,0,17))
        cpu.mem[names['REQ']+1:names['REQ']+7]=descriptor
        cpu.mem[names['TARGET']:names['TARGET']+64]=geometry().binding(1)
        cpu.run(names['PATCHTARGET'],limit=200000)
        expected=bytearray(payload)
        if size==8:expected[physical:physical+6]=descriptor
        if (cpu.a==0)!=(size==8) or cpu.mem[0x4000:0x4000+len(payload)]!=expected:
            raise ValueError(f'SYSGEN target type {size}: status {cpu.a}, package mismatch or incorrect admission')
    print('PASS: assembled SYSGEN accepts an 8-inch target, copies its physical descriptor, and rejects a 5-inch target before changing the package')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('staged',type=Path)
    check(p.parse_args().staged)
