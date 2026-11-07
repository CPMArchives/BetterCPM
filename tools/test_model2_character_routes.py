#!/usr/bin/env python3
"""Exercise assembled Model II BIOS IOBYTE routing and the keyboard handshake."""
import argparse
import hashlib
import json
from pathlib import Path

from build_z80pack_image import symbols
from test_bios import Z80


def check(out):
    bios = (out/'bios.bin').read_bytes()
    names = symbols(out/'bios.lst')
    base = names['BIOS']
    cpu = Z80(b'')
    cpu.mem[base:base+len(bios)] = bios
    cpu.sp = 0xb000
    wire = []
    keys = []
    def read(port):
        if port & 255 == 0xff:
            return 0x80 if keys else 0
        assert port & 255 == 0xfc and keys
        return keys.pop(0)
    def write(port, value):
        assert port & 255 == 0x30
        wire.append(value)
    cpu.port_read = read
    cpu.port_write = write
    # Observe the output value after the real monitor and IOBYTE dispatch.
    # Direct VRAM rendering has a separate emulator check.
    at = names['PL_CONOT']
    cpu.mem[at:at+4] = bytes((0x79,0xd3,0x30,0xc9))
    cpu.run(base+72)
    for byte in range(256):
        cpu.mem[3] = byte
        console, listing = byte & 3, byte >> 6
        for offset, emits in ((12,console==1 or (console==2 and listing==1)),(15,listing==1),(18,False)):
            for value in (65,9,16):
                wire.clear()
                cpu.c = value
                cpu.run(base+offset)
                assert wire == ([value] if emits else []), (byte,offset,value,wire)
        keys[:] = [0xe1]
        for offset, expected in ((6,255 if console==1 else 0),(6,255 if console==1 else 0),
                                 (21,0x1a),(45,255 if listing==1 else 0)):
            cpu.run(base+offset)
            assert cpu.a==expected and keys==[0xe1], (byte,offset,cpu.a,keys)
        cpu.run(base+9)
        assert cpu.a==(0x61 if console==1 else 0x1a) and keys==([] if console==1 else [0xe1])
        keys.clear()
        cpu.run(base+6)
        assert cpu.a==0 and cpu.mem[3]==byte
    return {'status':'PASS','iobyte_values':256,'bios_sha256':hashlib.sha256(bios).hexdigest(),
            'facilities':['CONST','CONIN','CONOUT','LIST','PUNCH','READER','LISTST'],
            'scope':'Model II production BIOS with synthetic keyboard ports and intercepted CRT output; two status polls preserve the queued key, input masks bit 7 and empty status is zero.'}


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build',type=Path)
    print(json.dumps(check(parser.parse_args().build), indent=2))
