#!/usr/bin/env python3
"""Exercise the private random-I/O decoder against an independent position oracle."""
import argparse,re
from pathlib import Path
from test_bios import Z80
from system_layout import LAYOUT


class GuardedCode(bytearray):
    def __setitem__(self,key,value):
        positions=range(*key.indices(len(self))) if isinstance(key,slice) else (key,)
        if getattr(self,'executing',False):
            assert not any(LAYOUT['BDOS']<=pos<self.code_end for pos in positions), 'write to BDOS code'
        super().__setitem__(key,value)


class GuardedCPU(Z80):
    code_end=0
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.sp=0xA000  # helper fixtures need a caller stack outside resident code
    def run(self,*args,**kwargs):
        if not isinstance(self.mem,GuardedCode):
            self.mem=GuardedCode(self.mem);self.mem.code_end=self.code_end
        self.mem.executing=True
        try:return super().run(*args,**kwargs)
        finally:self.mem.executing=False


def main():
    p=argparse.ArgumentParser();p.add_argument('--audit',type=Path,default=Path(__file__).resolve().parents[1]/'build/audit/random-same-extent');p.add_argument('--production',action='store_true',help='test the freshly built production BDOS instead of the private prototype');a=p.parse_args()
    image_path=(Path(__file__).resolve().parents[1]/'build/bdos/bdos.bin') if a.production else a.audit/'candidate.bin'
    listing_path=image_path.with_suffix('.lst')
    syms={}
    for line in (listing_path).read_text().splitlines():
        m=re.match(r'^([0-9a-f]{4})\s+.*\b([A-Z][A-Z0-9_]*):',line,re.I)
        if m:syms[m[2].upper()]=int(m[1],16)
    GuardedCPU.code_end=syms['UB_OLDSP']
    # Run existing public-call/mapping and grouped-extent checks on the exact
    # candidate too. Guarding starts after fixture providers are installed.
    import test_unified_bdos as foundation
    foundation.IMAGE=image_path;foundation.LISTING=listing_path;foundation.Z80=GuardedCPU
    foundation.main()
    import test_bdos_grouped_extents as grouped
    grouped.IMAGE=foundation.IMAGE;grouped.symbols=foundation.symbols;grouped.Z80=GuardedCPU;grouped.main()
    import test_bdos_extent_groups as compare
    compare.Z80=GuardedCPU;compare.symbols=foundation.symbols
    # This test reads the production path directly; redirect its private ROOT
    # through an isolated fixture tree instead of replacing production output.
    import tempfile
    with tempfile.TemporaryDirectory() as temporary:
        tree=Path(temporary);(tree/'build/bdos').mkdir(parents=True)
        (tree/'build/bdos/bdos.bin').write_bytes(foundation.IMAGE.read_bytes())
        compare.ROOT=tree;compare.main()
    c=GuardedCPU(b'');image=image_path.read_bytes();base=LAYOUT['BDOS'];c.mem[base:base+len(image)]=image
    # The decoder's slow-path Close must preserve its computed target even
    # when the real helper clobbers ordinary registers. Count calls explicitly.
    at=syms['UB_CCORE'];stub=bytes.fromhex('D3 FD 21 34 12 01 78 56 11 BC 9A AF C9');c.mem[at:at+len(stub)]=stub
    calls=[];c.port_write=lambda port,value:calls.append(value)
    fcb=0x7000;c.ix=fcb;c.sp=0xA000;cases=0
    for r1 in range(256):
        for r0 in (0,1,127,128,129,255):
            record=r1*256+r0;target=record//128
            for current in {target,(target+1)%512,(target+32)%512}:
                for rc in (0,1,128):
                    for clean in (0,0x80):
                        original=bytearray(36);original[1:12]=b'ACTIVE  DAT'
                        original[12]=current%32;original[14]=current//32|clean;original[15]=rc
                        original[16:18]=bytes((0x8F,1));original[32]=77;original[33:36]=bytes((r0,r1,0))
                        c.mem[fcb:fcb+36]=original;calls.clear();sp=c.sp
                        c.run(syms['UB_RDECODE'],limit=1000)
                        fast=rc>0 and current==target
                        expected=bytearray(original);expected[32]=record%128
                        if not fast:expected[12]=target%32;expected[14]=target//32
                        assert c.mem[fcb:fcb+36]==expected,(record,current,rc,clean)
                        assert c.carry is (not fast),(record,current,rc,clean,'carry')
                        assert len(calls)==(0 if fast or rc==0 else 1)
                        assert c.sp==sp
                        cases+=1
    for record in (0,127,128,65535):
        target=record//128
        for flags in (0x20,0x80,0xE0):
            for clean in (0,0x80):
                original=bytearray(36);original[12]=target%32|flags
                original[14]=target//32|clean;original[15]=1
                original[33:36]=record.to_bytes(3,'little')
                c.mem[fcb:fcb+36]=original;calls.clear()
                c.run(syms['UB_RDECODE'],limit=1000)
                assert c.carry and len(calls)==1
                assert c.mem[fcb+12]==target%32 and c.mem[fcb+14]==target//32
    # Test the newly needed instruction's actual flags contract, independently.
    for flags in range(256):
        for value in (0,127,128,255):
            c.mem[0x7200:0x7203]=bytes((0xCB,0xBF,0xC9));c.a=value;c.f=flags
            c.run(0x7200);assert c.a==value&127 and c.f==flags
    print(f'PASS: {cases} decoder cases across all R1 values; exact position, live FCB preservation, slow Close, carry result, stack and RES flags; BDOS code write-protected')


if __name__=='__main__':main()
