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
    parser.add_argument('--reject-portable-candidate',action='store_true',help='prove portable ANSI cannot replace the monitor with an insufficient backend')
    parser.add_argument('--bios',type=Path,default=ROOT/'build/z80pack')
    args=parser.parse_args()
    if not args.reject_portable_candidate:
        from test_ansi_portable_lifecycle import main as portable_main
        portable_main(production=True)
        return
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
        image=bytearray((ROOT/path).read_bytes())
        if args.reject_portable_candidate and path.endswith(backend+'.RSX'):
            metadata=int.from_bytes(image[30:32],'little')
            ident=image.index(b'SCRN',metadata);image[ident+5]=0
        cpu.mem[address:address+len(image)]=image
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
        print('PASS: portable ANSI rejected atomically with an insufficient SCRN 1.0 backend; unload/53K')
        return


if __name__=='__main__':main()
