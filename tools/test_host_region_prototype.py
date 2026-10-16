#!/usr/bin/env python3
"""Exercise experimental host-region scrolling against independent pyte state."""
from pathlib import Path
import pyte
from build_ccp import assemble
from build_cpx_module import relocation_offsets
from test_bios import Z80
from test_vt52_foundation import symbols
ROOT=Path(__file__).resolve().parents[1]


def main():
    out=ROOT/'build/screen-region-prototype';out.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'src/rsx/screen/host-region-prototype.mac').read_text()
    code=assemble(Path.home()/'bin/z80asm',source,out/'host.bin',out/'host.lst',0x8000)
    alt=assemble(Path.home()/'bin/z80asm',source.replace('08000H','08101H'),out/'host-alt.bin',out/'host-alt.lst',0x8101)
    slots=relocation_offsets(code,alt,0x101)
    biosdir=ROOT/'build/audit/release-090-z80pack';bios=symbols(biosdir/'bios.lst');origin=bios['MONRAW']-69
    cases=0
    for base in (0x6000,0x8101):
        cpu=Z80(b'');image=(biosdir/'bios.bin').read_bytes();cpu.mem[origin:origin+len(image)]=image;cpu.setword(1,origin+3)
        relocated=bytearray(code)
        for slot in slots:
            relocated[slot:slot+2]=(int.from_bytes(code[slot:slot+2],'little')+base-0x8000).to_bytes(2,'little')
        cpu.mem[base:base+len(code)]=relocated
        for top,bottom in [(0,23),(3,20),(5,6),(0,0),(12,12),(23,23)]:
            for direction in (0,1):
                for fill in (32,160):
                    screen=pyte.Screen(80,24);stream=pyte.Stream(screen)
                    for row in range(24):stream.feed(f'\x1b[{row+1};1H'+chr(65+row)*80)
                    stream.feed('\x1b[8;14H\x1b[1;4;7m')
                    before=[''.join(screen.buffer[r][c].data for c in range(80)) for r in range(24)]
                    attrs=screen.cursor.attrs;position=(screen.cursor.x,screen.cursor.y)
                    output=[]
                    def emit(port,value):
                        assert port&255==1
                        output.append(value);stream.feed(chr(value))
                    cpu.port_write=emit;cpu.a,cpu.b,cpu.c,cpu.e=direction,top,bottom,fill
                    sp=cpu.sp;cpu.run(base,limit=100000)
                    expected=before[:]
                    expected[top:bottom+1]=(before[top+1:bottom+1]+[' '*80] if direction==0 else [' '*80]+before[top:bottom])
                    assert screen.display==expected,(base,top,bottom,direction,fill)
                    row=bottom if direction==0 else top
                    assert all(screen.buffer[row][col].reverse==(fill==160) for col in range(80))
                    assert (screen.cursor.x,screen.cursor.y)==position
                    assert screen.cursor.attrs==attrs
                    assert screen.margins is None
                    assert cpu.a==0 and cpu.sp==sp
                    cases+=1
        for op,top,bottom,fill in [(2,0,23,32),(0,0,24,32),(1,10,9,32),(0,255,23,32),(0,0,23,0)]:
            output.clear();cpu.a,cpu.b,cpu.c,cpu.e=op,top,bottom,fill;cpu.run(base,limit=10000)
            assert cpu.a==255 and not output
    print(f'PASS {cases} host region/direction/fill/relocation cases, cursor/rendition restoration and invalid arguments; {len(code)} prototype bytes, {len(slots)} relocations; no production integration')


if __name__=='__main__':main()
