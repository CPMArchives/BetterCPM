#!/usr/bin/env python3
"""Exercise real ANSI installation, buffered-state movement and lookup on cpmsim."""
import argparse
import tempfile
from pathlib import Path
from test_ansi_foundation import ROOT,OUT
from test_vt52_foundation import symbols
from test_bios import Z80
from system_layout import LAYOUT
import test_rsx_stage3 as stage


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reject-portable-candidate',action='store_true',help='prove unadmitted MCON 1.2 cannot replace the live monitor')
    parser.add_argument('--bios',type=Path,default=ROOT/'build/z80pack')
    args=parser.parse_args()
    bios=symbols(args.bios/'bios.lst')
    base=bios['MONRAW']-69
    cpu=Z80(b'')
    image=(args.bios/'bios.bin').read_bytes()
    cpu.mem[base:base+len(image)]=image
    cpu.setword(1,base+3)
    backend='M4SCRN' if 'M4CURSOR' in bios else 'ANSISCRN'
    stage.FILES=(("R3PACK  ","build/system/R3PACK.RSX"),
                 ("HELLO   ","build/rsx/HELLO.RSX"),
                 ("ANSI    ","build/ansi-development/ANSI.RSX"))
    if args.reject_portable_candidate:
        stage.FILES=(("R3PACK  ","build/system/R3PACK.RSX"),(backend.ljust(8),f'build/screen-backends/{backend}.RSX'),("ANSI    ","build/ansi-portable-candidate/ANSI.RSX"))
    sources=(0x7800,0xB400,0xC000 if args.reject_portable_candidate else 0xB800)
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
    syms=symbols(OUT/'ansi.lst')
    def change(op,name):
        stage.invoke(cpu,bootstrap,op,name)
        assert cpu.a==0,(op,name,cpu.a)
    def call(op,char=0):
        cpu.a,cpu.c=op,char
        cpu.run(base+66,limit=20000)
        return cpu.a
    if args.reject_portable_candidate:
        change(1,backend.ljust(8).encode())
        addresses=[binding,stage.HEAD,stage.LOW,stage.TPA,6,stage.GEN]
        before=[cpu.word(address) for address in addresses]
        count=cpu.mem[stage.RSTCOUNT]
        stage.invoke(cpu,bootstrap,1,b'ANSI    ')
        assert cpu.a!=0 and before==[cpu.word(address) for address in addresses]
        assert cpu.mem[stage.RSTCOUNT]==count
        change(2,backend.ljust(8).encode())
        assert cpu.word(binding)==basic and cpu.word(6)==LAYOUT['TPA']
        print('PASS: unadmitted portable ANSI candidate rejected atomically with backend present; unload/53K')
        return
    change(1,b'HELLO   ');change(1,b'ANSI    ')
    old=cpu.word(stage.LOW)
    assert cpu.word(binding)==old+syms['AN_ENTRY']-0x8000
    emitted.clear()
    for char in b'\x1b[12;':call(0,char)
    assert emitted==[]
    change(2,b'HELLO   ')
    new=cpu.word(stage.LOW)
    assert new>old and cpu.word(binding)==new+syms['AN_ENTRY']-0x8000
    assert cpu.mem[new+syms['AN_STATE']-0x8000]==2
    assert cpu.mem[new+syms['AN_COUNT']-0x8000]==5
    start=new+syms['AN_BUFFER']-0x8000
    assert bytes(cpu.mem[start:start+5])==b'\x1b[12;'
    emitted.clear()
    for char in b'15H':call(0,char)
    assert bytes(emitted)==b'\x1b[12;15H'
    for char in b'\x1b[7;':call(0,char)
    call(5);emitted.clear();call(0,ord('X'))
    assert bytes(emitted)==b'X'
    extension=(ROOT/'build/system/extensions.bin').read_bytes()
    cpu.mem[LAYOUT['EXTENSIONS']:LAYOUT['EXTENSIONS']+len(extension)]=extension
    request=0x7000
    cpu.mem[request:request+20]=bytes([1,20,0,0])+b'MCON'+bytes([1,0])+bytes(10)
    cpu.de=request;cpu.c=182
    cpu.run(LAYOUT['EXTENSIONS'],limit=20000)
    assert cpu.a==0 and cpu.word(request+12)==cpu.word(binding)
    change(2,b'ANSI    ')
    assert cpu.word(binding)==basic and cpu.word(6)==LAYOUT['TPA']
    assert cpu.mem[stage.RSTCOUNT]==0
    print('PASS: actual ANSI install, partial-sequence relocation, continuation, service lookup and 53K unload')


if __name__=='__main__':main()
