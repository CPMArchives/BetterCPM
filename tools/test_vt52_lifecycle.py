#!/usr/bin/env python3
"""Exercise real VT52 installation, queued-state movement and lookup on cpmsim."""
import argparse
import tempfile
from pathlib import Path
from test_vt52_foundation import ROOT,OUT,symbols
from test_bios import Z80
from system_layout import LAYOUT
import test_rsx_stage3 as stage


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bios',type=Path,default=ROOT/'build/z80pack')
    args=parser.parse_args()
    bios=symbols(args.bios/'bios.lst')
    base=bios['MONRAW']-69
    cpu=Z80(b'')
    image=(args.bios/'bios.bin').read_bytes()
    cpu.mem[base:base+len(image)]=image
    cpu.setword(1,base+3)
    stage.FILES=(("R3PACK  ","build/system/R3PACK.RSX"),
                 ("HELLO   ","build/rsx/HELLO.RSX"),
                 ("VT52    ","build/vt52-development/VT52.RSX"))
    sources=(0x7800,0xB400,0xB800)
    for (_,path),address in zip(stage.FILES,sources):
        image=(ROOT/path).read_bytes();cpu.mem[address:address+len(image)]=image
    with tempfile.TemporaryDirectory() as temporary:stub=stage.file_stub(Path(temporary),sources)
    cpu.mem[LAYOUT['FILE']:LAYOUT['FILE']+len(stub)]=stub
    cpu.mem[base+60:base+63]=b'\xaf\xc9\0'
    cpu.port_read=lambda port:0
    emitted=[]
    cpu.port_write=lambda port,value:emitted.append(value)
    binding=bios['MP_MON']
    cpu.run(base+72);basic=cpu.word(binding)
    for address,value in [(stage.HEAD,0),(stage.LOW,LAYOUT['RSX']),
                          (stage.TPA,LAYOUT['TPA']),(6,LAYOUT['TPA']),(stage.GEN,1)]:cpu.setword(address,value)
    cpu.mem[stage.RSTCOUNT:stage.RSTCOUNT+41]=bytes(41)
    bootstrap=(ROOT/'build/system/r3entry.bin').read_bytes()
    syms=symbols(OUT/'vt52.lst')
    def change(op,name):
        stage.invoke(cpu,bootstrap,op,name)
        assert cpu.a==0,(op,name,cpu.a)
    def call(op,char=0):
        cpu.a,cpu.c=op,char
        cpu.run(base+66,limit=20000)
        return cpu.a
    change(1,b'HELLO   ');change(1,b'VT52    ')
    old=cpu.word(stage.LOW)
    assert cpu.word(binding)==old+syms['VT_ENTRY']-0x8000
    for char in b'\x1bZ':call(0,char)
    assert call(2)==27
    for char in b'\x1bY!':call(0,char)
    change(2,b'HELLO   ')
    new=cpu.word(stage.LOW)
    assert new>old and cpu.word(binding)==new+syms['VT_ENTRY']-0x8000
    for label,value in [('VT_STATE',3),('VT_ROW',0),('VT_PEND',1),('VQ_COUNT',2)]:
        assert cpu.mem[new+syms[label]-0x8000]==value,label
    emitted.clear();call(0,32+10)
    assert bytes(emitted)==b'\x1bY!*'
    call(5);assert call(1)==255
    assert call(2)==ord('/') and call(2)==ord('K') and call(1)==0
    extension=(ROOT/'build/system/extensions.bin').read_bytes()
    cpu.mem[LAYOUT['EXTENSIONS']:LAYOUT['EXTENSIONS']+len(extension)]=extension
    request=0x7000
    cpu.mem[request:request+20]=bytes([1,20,0,0])+b'MCON'+bytes([1,0])+bytes(10)
    cpu.de=request;cpu.c=182
    cpu.run(LAYOUT['EXTENSIONS'],limit=20000)
    assert cpu.a==0 and cpu.word(request+12)==cpu.word(binding)
    change(2,b'VT52    ')
    assert cpu.word(binding)==basic and cpu.word(6)==LAYOUT['TPA']
    assert cpu.mem[stage.RSTCOUNT]==0
    print('PASS: actual VT52 install, partial-parser/reply relocation, continuation, service lookup and 53K unload')


if __name__=='__main__':main()
