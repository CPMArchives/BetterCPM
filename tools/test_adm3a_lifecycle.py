#!/usr/bin/env python3
"""Exercise real ADM3A installation, parser/mode state movement and lookup through the actual screen backend."""
import argparse
import tempfile
from pathlib import Path
from test_adm3a_foundation import ROOT,symbols
OUT=ROOT/'build/monitor-development'
from test_bios import Z80
from system_layout import LAYOUT
import test_rsx_stage3 as stage


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bios',type=Path,default=ROOT/'build/z80pack')
    args=parser.parse_args()
    bios=symbols(args.bios/'bios.lst')
    base=bios['MONRAW']-69
    model4='M4CURSOR' in bios
    backend='M4SCRN' if model4 else 'ANSISCRN'
    backsyms=symbols(ROOT/'build/screen-backends'/(backend+'.lst'))
    backentry=backsyms['S_ENTRY' if model4 else 'SB_ENTRY']-0x8000
    cpu=Z80(b'')
    image=(args.bios/'bios.bin').read_bytes()
    cpu.mem[base:base+len(image)]=image
    cpu.setword(1,base+3)
    stage.FILES=(("R3PACK  ","build/system/R3PACK.RSX"),
                 ("HELLO   ","build/rsx/HELLO.RSX"),
                 (backend.ljust(8),"build/screen-backends/"+backend+".RSX"),
                 ("ADM3A   ","build/monitor-development/ADM3A.RSX"))
    sources=(0x7800,0xB400,0xB800,0xC000)
    for (_,path),address in zip(stage.FILES,sources):
        image=(ROOT/path).read_bytes();cpu.mem[address:address+len(image)]=image
    with tempfile.TemporaryDirectory() as temporary:stub=stage.file_stub(Path(temporary),sources)
    cpu.mem[LAYOUT['FILE']:LAYOUT['FILE']+len(stub)]=stub
    cpu.mem[base+60:base+63]=b'\xaf\xc9\0'
    cpu.port_read=lambda port:0
    emitted=[]
    import pyte
    screen=pyte.Screen(80,24);stream=pyte.Stream(screen)
    def output(port,value):
        emitted.append(value)
        if not model4:
            assert port&255==1
            stream.feed(chr(value))
    cpu.port_write=output
    binding=bios['MP_MON']
    cpu.run(base+72);basic=cpu.word(binding)
    for address,value in [(stage.HEAD,0),(stage.LOW,LAYOUT['RSX']),
                          (stage.TPA,LAYOUT['TPA']),(6,LAYOUT['TPA']),(stage.GEN,1)]:cpu.setword(address,value)
    cpu.mem[stage.RSTCOUNT:stage.RSTCOUNT+41]=bytes(41)
    bootstrap=(ROOT/'build/system/r3entry.bin').read_bytes()
    syms=symbols(OUT/'adm3a.lst')
    def change(op,name):
        stage.invoke(cpu,bootstrap,op,name)
        assert cpu.a==0,(op,name,cpu.a)
    def call(op,char=0):
        cpu.a,cpu.c=op,char
        cpu.run(base+66,limit=200000)
        return cpu.a
    stage.invoke(cpu,bootstrap,1,b'ADM3A   ')
    assert cpu.a!=0 and cpu.word(binding)==basic
    change(1,b'HELLO   ');change(1,backend.ljust(8).encode());change(1,b'ADM3A   ')
    front_size=int.from_bytes((OUT/'ADM3A.RSX').read_bytes()[14:16],'little')
    def check_link(frontbase):
        assert cpu.word(frontbase+12)==frontbase+front_size+backentry
    def cells():
        return bytes(cpu.mem[0xF800:0xFF80]) if model4 else ''.join(screen.display).encode()
    call(4)
    for char in b'HELLO':call(0,char)
    assert cells()[:5]==b'HELLO'
    before=(cpu.word(binding),cpu.word(stage.GEN),cpu.word(6))
    stage.invoke(cpu,bootstrap,2,backend.ljust(8).encode())
    assert cpu.a!=0 and before==(cpu.word(binding),cpu.word(stage.GEN),cpu.word(6))
    old=cpu.word(stage.LOW)
    assert cpu.word(binding)==old+syms['AM_ENTRY']-0x8000
    check_link(old)
    for char in b'\x0f\x1b0\x1b=!':call(0,char)
    rendition=bytes([33,2,10,128,250,1,200,0,0])
    cpu.mem[0x7000:0x7009]=rendition
    backend_entry=cpu.word(old+12)
    cpu.a,cpu.hl=20,0x7000;cpu.run(backend_entry,limit=200000);assert cpu.a==0
    cpu.a,cpu.hl,cpu.de=22,4,20;cpu.run(backend_entry,limit=200000);assert cpu.a==0
    cpu.a,cpu.hl,cpu.de=18,12,80;cpu.run(backend_entry,limit=200000);assert cpu.a==0
    cpu.a,cpu.c=21,ord('R');cpu.run(backend_entry,limit=200000);assert cpu.a==0
    change(2,b'HELLO   ')
    new=cpu.word(stage.LOW)
    assert new>old and cpu.word(binding)==new+syms['AM_ENTRY']-0x8000
    check_link(new)
    backend_base=new+front_size
    attr_offset=backsyms['SX_ATTR' if model4 else 'BH_ATTR']-0x8000
    assert bytes(cpu.mem[backend_base+attr_offset:backend_base+attr_offset+9])==rendition
    if model4:
        assert cpu.mem[backend_base+backsyms['SX_PEND']-0x8000]==1
        assert cpu.mem[backend_base+backsyms['SM_TOPROW']-0x8000]==3
        assert cpu.mem[backend_base+backsyms['SM_BOTTOM']-0x8000]==19
    else:
        assert cpu.word(backend_base+backsyms['BH_PTR']-0x8000)==0
        assert screen.margins==(3,19)
    # Erase through the rebound callback without consuming deferred wrapping.
    cpu.a,cpu.b,cpu.c=19,0,0
    cpu.run(cpu.word(new+12),limit=200000);assert cpu.a==0
    assert cells()[11*80+79]&127==ord('R')
    cpu.a,cpu.c=21,ord('S');cpu.run(cpu.word(new+12),limit=200000);assert cpu.a==0
    assert cells()[12*80]&127==ord('S')
    for label,value in [('AM_STATE',3),('AM_ROWPOS',0),('AM_PENDING_ROW',1),('AM_REVERSE',128),('AM_VISIBLE',0)]:
        assert cpu.mem[new+syms[label]-0x8000]==value,label
    emitted.clear();call(0,32+10)
    assert cpu.mem[new+syms['AM_ROWPOS']-0x8000]==1
    assert cpu.mem[new+syms['AM_COLPOS']-0x8000]==10
    call(0,ord('X'));assert cells()[90]&127==ord('X')
    call(5);assert call(3)==0
    for char in b'\x0e\x1b1':call(0,char)
    assert call(3)==1
    extension=(ROOT/'build/system/extensions.bin').read_bytes()
    cpu.mem[LAYOUT['EXTENSIONS']:LAYOUT['EXTENSIONS']+len(extension)]=extension
    request=0x7000
    cpu.mem[request:request+20]=bytes([1,20,0,0])+b'MCON'+bytes([1,0])+bytes(10)
    cpu.de=request;cpu.c=182
    cpu.run(LAYOUT['EXTENSIONS'],limit=20000)
    assert cpu.a==0 and cpu.word(request+12)==cpu.word(binding)
    change(2,b'ADM3A   ')
    assert cpu.word(binding)==basic
    change(2,backend.ljust(8).encode())
    assert cpu.word(6)==LAYOUT['TPA']
    assert cpu.mem[stage.RSTCOUNT]==0
    print('PASS '+backend+': actual ADM3A install, partial-parser/mode relocation, continuation, service lookup and 53K unload')


if __name__=='__main__':main()
