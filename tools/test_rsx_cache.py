#!/usr/bin/env python3
"""Check the transient cache worker's complete relocation closure."""
from pathlib import Path
import sys
from build_cpx_module import relocation_offsets
from build_rsx_runtime_overlays import source
from build_ccp import assemble
ROOT=Path(__file__).resolve().parents[1]

def main():
    out=(ROOT/'build/cache-relocation-test');out.mkdir(exist_ok=True)
    images=[]
    for base in (0x1000,0x1234,0x7141):
        images.append(assemble(Path.home()/'bin/z80asm',source('r3cache.mac','CBBASE',base),out/f'{base:x}.bin',out/f'{base:x}.lst',base))
    table=relocation_offsets(images[0],images[1],0x234)
    relocated=bytearray(images[0])
    for offset in table:
        value=int.from_bytes(relocated[offset:offset+2],'little')
        relocated[offset:offset+2]=((value+0x6141)&65535).to_bytes(2,'little')
    assert relocated==images[2]
    print('PASS cache relocation closure across page carries:',len(images[0]),'bytes,',len(table),'words')

if __name__=='__main__':main()
