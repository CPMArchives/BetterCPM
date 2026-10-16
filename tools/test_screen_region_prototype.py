#!/usr/bin/env python3
"""Measure and execute the experimental Model 4 region-scrolling primitive.

No production carrier or published SCRN operation is changed by this probe.
"""
from pathlib import Path
from build_ccp import assemble
from build_cpx_module import relocation_offsets
from test_bios import Z80

ROOT=Path(__file__).resolve().parents[1]


def main():
    out=ROOT/'build/screen-region-prototype';out.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'src/rsx/screen/region-prototype.mac').read_text()
    code=assemble(Path.home()/'bin/z80asm',source,out/'region.bin',out/'region.lst',0x8000)
    alt=assemble(Path.home()/'bin/z80asm',source.replace('08000H','08101H'),out/'region-alt.bin',out/'region-alt.lst',0x8101)
    slots=relocation_offsets(code,alt,0x101)
    cases=0
    for base in (0x6000,0x8101):
        cpu=Z80(b'');relocated=bytearray(code)
        for slot in slots:
            relocated[slot:slot+2]=(int.from_bytes(code[slot:slot+2],'little')+base-0x8000).to_bytes(2,'little')
        cpu.mem[base:base+len(code)]=relocated
        before=b''.join(bytes([65+r])*80 for r in range(24))
        # Every legal pair, including single-row regions and full screen.
        for top in range(24):
            for bottom in range(top,24):
                for direction in (0,1):
                    for fill in (32,160):
                        cpu.mem[0xF800:0xFF80]=before
                        cpu.mem[0xF7F0:0xF800]=b'L'*16;cpu.mem[0xFF80:0xFF90]=b'R'*16
                        cpu.a,cpu.b,cpu.c,cpu.e=direction,top,bottom,fill
                        sp=cpu.sp;cpu.run(base,limit=30000)
                        expected=bytearray(before);start=top*80;end=(bottom+1)*80
                        expected[start:end]=(before[start+80:end]+bytes([fill])*80 if direction==0 else bytes([fill])*80+before[start:end-80])
                        assert bytes(cpu.mem[0xF800:0xFF80])==expected,(base,top,bottom,direction,fill)
                        assert cpu.a==0 and cpu.sp==sp
                        assert bytes(cpu.mem[0xF7F0:0xF800])==b'L'*16
                        assert bytes(cpu.mem[0xFF80:0xFF90])==b'R'*16
                        cases+=1
        for op,top,bottom,fill in [(2,0,23,32),(0,0,24,32),(1,10,9,32),(0,255,23,32),(0,0,23,0),(0,0,23,255)]:
            cpu.mem[0xF800:0xFF80]=before
            cpu.a,cpu.b,cpu.c,cpu.e=op,top,bottom,fill
            cpu.run(base,limit=30000)
            assert cpu.a==255 and bytes(cpu.mem[0xF800:0xFF80])==before
    print(f'PASS {cases} region/direction/fill/relocation cases and invalid arguments; {len(code)} prototype bytes, {len(slots)} relocations; no production integration')


if __name__=='__main__':main()
