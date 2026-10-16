#!/usr/bin/env python3
"""Check typed host motion without fixing the host's terminal geometry."""
from pathlib import Path
import pyte
from build_ccp import assemble
from build_cpx_module import relocation_offsets
from test_bios import Z80
from test_vt52_foundation import symbols
ROOT=Path(__file__).resolve().parents[1]


def main():
    out=ROOT/'build/screen-motion-prototype';out.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'src/rsx/screen/host-motion-prototype.mac').read_text()
    code=assemble(Path.home()/'bin/z80asm',source,out/'motion.bin',out/'motion.lst',0x8000)
    alt=assemble(Path.home()/'bin/z80asm',source.replace('08000H','08101H'),out/'motion-alt.bin',out/'motion-alt.lst',0x8101)
    slots=relocation_offsets(code,alt,0x101)
    biosdir=ROOT/'build/audit/release-090-z80pack';bios=symbols(biosdir/'bios.lst');origin=bios['MONRAW']-69
    cases=0
    for base in (0x6000,0x8101):
        cpu=Z80(b'');image=(biosdir/'bios.bin').read_bytes();cpu.mem[origin:origin+len(image)]=image;cpu.setword(1,origin+3)
        relocated=bytearray(code)
        for slot in slots:
            relocated[slot:slot+2]=(int.from_bytes(code[slot:slot+2],'little')+base-0x8000).to_bytes(2,'little')
        cpu.mem[base:base+len(code)]=relocated
        for width,height in [(80,24),(80,25),(100,40)]:
            for op in range(5):
                for count in [0,1,9,10,24,25,40,80,100,255,256,9999,10000,65535]:
                    screen=pyte.Screen(width,height);stream=pyte.Stream(screen)
                    stream.feed('\x1b[12;15H')
                    output=[]
                    def emit(port,value):
                        assert port&255==1
                        output.append(value);stream.feed(chr(value))
                    cpu.port_write=emit;cpu.a=op;cpu.hl=count;cpu.de=100
                    sp=cpu.sp;cpu.run(base,limit=30000)
                    assert cpu.sp==sp and cpu.a==0
                    sequence=f'\x1b[{count}'+(';100H' if op==4 else 'ABCD'[op])
                    assert bytes(output)==sequence.encode('ascii'),(op,count,bytes(output))
                    n=max(1,count)
                    expected=[(14,max(0,11-n)),(14,min(height-1,11+n)),(min(width-1,14+n),11),(max(0,14-n),11),(min(width-1,99),min(height-1,n-1))][op]
                    assert (screen.cursor.x,screen.cursor.y)==expected,(width,height,op,count)
                    cases+=1
        output.clear();cpu.a=5;cpu.run(base,limit=10000)
        assert cpu.a==255 and not output
    print(f'PASS {cases} host motion/geometry/relocation cases and invalid operation; {len(code)} prototype bytes, {len(slots)} relocations; no production integration')


if __name__=='__main__':main()
