#!/usr/bin/env python3
"""Execute portable SGR state conversion at two relocated addresses."""
from pathlib import Path
from build_ccp import assemble
from build_cpx_module import relocation_offsets
from test_bios import Z80
ROOT=Path(__file__).resolve().parents[1]


def main():
    out=ROOT/'build/screen-rendition-prototype';out.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'src/rsx/screen/rendition-prototype.mac').read_text().replace('        INCLUDE rendition.inc',(ROOT/'src/rsx/screen/rendition.inc').read_text())
    code=assemble(Path.home()/'bin/z80asm',source,out/'rendition.bin',out/'rendition.lst',0x8000)
    alt=assemble(Path.home()/'bin/z80asm',source.replace('08000H','08101H'),out/'rendition-alt.bin',out/'rendition-alt.lst',0x8101)
    slots=relocation_offsets(code,alt,0x101)
    cases=0
    for base in (0x6000,0x8101):
        cpu=Z80(b'');relocated=bytearray(code)
        for slot in slots:
            relocated[slot:slot+2]=(int.from_bytes(code[slot:slot+2],'little')+base-0x8000).to_bytes(2,'little')
        cpu.mem[base:base+len(code)]=relocated
        def call(params,expected=None,error=False):
            nonlocal cases
            assert len(params)<=17
            encoded=b''.join(n.to_bytes(2,'little') for n in params)
            cpu.mem[0x4000:0x4000+len(encoded)]=encoded
            cpu.hl=0x4000;cpu.c=len(params);sp=cpu.sp
            cpu.run(base,limit=30000);assert cpu.sp==sp
            cases+=1
            if error:
                assert cpu.a==255,params
                return
            assert cpu.a==0,params
            value=bytes(cpu.mem[cpu.hl:cpu.hl+9])
            if expected is not None:assert value==bytes(expected),(params,value,expected)
            return value
        zero=bytes(9)
        call([],zero)
        for sgr,bit in [(1,1),(2,2),(3,4),(4,8),(5,16),(6,16),(7,32),(8,64),(9,128)]:
            call([0,sgr],[bit]+[0]*8)
        call([0,1,2,3,4,5,7,8,9],[255]+[0]*8)
        call([22,23,24,25,27,28,29],zero)
        for sgr,start,slot,bright in [(30,30,1,0),(40,40,5,0),(90,90,1,8),(100,100,5,8)]:
            for index in range(8):
                expected=bytearray(9);expected[slot]=1;expected[slot+1]=index+bright
                call([0,sgr+index],expected)
        call([39,49],zero)
        for selector,slot in [(38,1),(48,5)]:
            for index in range(256):
                expected=bytearray(9);expected[slot]=1;expected[slot+1]=index
                call([0,selector,5,index],expected)
            for rgb in [(0,0,0),(255,255,255),(1,128,254),(200,10,80)]:
                expected=bytearray(9);expected[slot]=2;expected[slot+1:slot+4]=bytes(rgb)
                call([0,selector,2,*rgb],expected)
        expected=bytes([32,2,1,2,3,1,200,0,0])
        call([0,7,38,2,1,2,3,48,5,200],expected)
        # Bad/incomplete groups and oversized lists cannot partially commit.
        for params in [[1,38],[1,38,5],[1,48,2,1,2],[1,38,3],[1,38,5,256],[1,48,2,0,256,0],[1]*17]:
            call(params,error=True)
            call([999],expected)
        call([0]*16,zero)
        call([65535,256,10,26],zero)  # unknown ordinary codes never wrap
    print(f'PASS {cases} rendition/list/relocation cases; {len(code)} prototype bytes, {len(slots)} relocations; no production integration')


if __name__=='__main__':main()
