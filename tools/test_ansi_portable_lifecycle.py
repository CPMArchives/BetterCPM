#!/usr/bin/env python3
"""Qualify admitted portable ANSI through the actual manager on either platform."""
import argparse
import tempfile
from pathlib import Path
from test_ansi_foundation import ROOT,OUT
from test_vt52_foundation import symbols
from test_bios import Z80
from system_layout import LAYOUT
import test_rsx_stage3 as stage


def main(production=False):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bios',type=Path,default=ROOT/'build/bios')
    args=parser.parse_args()
    provider='build/ansi-development' if production else 'build/ansi-portable-candidate'
    bios=symbols(args.bios/'bios.lst');origin=bios['MONRAW']-69
    model4='M4CURSOR' in bios;backend='M4SCRN' if model4 else 'ANSISCRN'
    cpu=Z80(b'');image=(args.bios/'bios.bin').read_bytes()
    cpu.mem[origin:origin+len(image)]=image;cpu.setword(1,origin+3)
    stage.FILES=(("R3PACK  ","build/system/R3PACK.RSX"),("HELLO   ","build/rsx/HELLO.RSX"),
        (backend.ljust(8),f"build/screen-backends/{backend}.RSX"),("ANSI    ",provider+"/ANSI.RSX"))
    sources=(0x7100,0xAD00,0xB000,0xB800)
    # Keep synthetic disk bytes above transaction RAM/stack and below the
    # lowest prospective live allocation; larger ANSI otherwise overwrites them.
    low=LAYOUT['RSX']-sum(int.from_bytes((ROOT/path).read_bytes()[14:16],'little') for _,path in stage.FILES[1:])
    assert all(address+len((ROOT/path).read_bytes())<=low for (_,path),address in zip(stage.FILES,sources))
    for (_,path),address in zip(stage.FILES,sources):
        image=(ROOT/path).read_bytes();cpu.mem[address:address+len(image)]=image
    with tempfile.TemporaryDirectory() as temporary:stub=stage.file_stub(Path(temporary),sources)
    cpu.mem[LAYOUT['FILE']:LAYOUT['FILE']+len(stub)]=stub
    cpu.mem[origin+60:origin+63]=b'\xaf\xc9\0';cpu.port_read=lambda port:0
    import pyte
    screen=pyte.Screen(80,24);stream=pyte.Stream(screen)
    def emit(port,value):
        if not model4:
            assert port&255==1;stream.feed(chr(value))
    cpu.port_write=emit
    binding=bios['MP_MON'];cpu.run(origin+72);basic=cpu.word(binding)
    for address,value in [(stage.HEAD,0),(stage.LOW,LAYOUT['RSX']),(stage.TPA,LAYOUT['TPA']),(6,LAYOUT['TPA']),(stage.GEN,1)]:cpu.setword(address,value)
    cpu.mem[stage.RSTCOUNT:stage.RSTCOUNT+41]=bytes(41)
    bootstrap=(ROOT/'build/system/r3entry.bin').read_bytes()
    syms=symbols(ROOT/provider/'ansi.lst')
    def change(op,name,ok=True):
        before=(cpu.word(binding),cpu.word(stage.GEN),cpu.word(6),bytes(cpu.mem[stage.RSTCOUNT:stage.RSTCOUNT+41]))
        stage.invoke(cpu,bootstrap,op,name.ljust(8).encode())
        assert (cpu.a==0)==ok,(op,name,cpu.a)
        if not ok:assert before==(cpu.word(binding),cpu.word(stage.GEN),cpu.word(6),bytes(cpu.mem[stage.RSTCOUNT:stage.RSTCOUNT+41]))
    def send(data):
        for char in data:
            cpu.a,cpu.c=0,char;cpu.run(origin+66,limit=300000)
    def cell(row,col):return cpu.mem[0xF800+80*row+col]&127 if model4 else ord(screen.buffer[row][col].data)
    change(1,'ANSI',False)
    change(1,'HELLO');change(1,backend);change(1,'ANSI')
    old=cpu.word(stage.LOW)
    assert cpu.word(binding)==old+syms['AN_ENTRY']-0x8000
    send(b'\x1b[1;7;38;2;10;128;250m\x1b[6;11H\x1b7\x1b[12;')
    change(2,backend,False)
    change(2,'HELLO');new=cpu.word(stage.LOW)
    assert new>old and cpu.word(binding)==new+syms['AN_ENTRY']-0x8000
    assert cpu.mem[new+syms['AN_STATE']-0x8000]==2 and cpu.mem[new+syms['AN_COUNT']-0x8000]==5
    send(b'15HR\x1b8S\x1b8T\x1b[22mU')
    assert cell(11,14)==ord('R') and cell(5,10)==ord('T') and cell(5,11)==ord('U')
    value=new+syms['AP_VALUE']-0x8000
    assert bytes(cpu.mem[value:value+9])==bytes([32,2,10,128,250,0,0,0,0])
    for label in ['AC_PTR','AP_PTR']:assert cpu.word(new+syms[label]-0x8000)==0
    if not model4:
        assert screen.buffer[5][10].bold and screen.buffer[5][10].reverse
        assert not screen.buffer[5][11].bold and screen.buffer[5][11].fg=='0a80fa'
    change(1,'HELLO');change(2,'HELLO')
    extension=(ROOT/'build/system/extensions.bin').read_bytes()
    cpu.mem[LAYOUT['EXTENSIONS']:LAYOUT['EXTENSIONS']+len(extension)]=extension
    request=0x7000;cpu.mem[request:request+20]=bytes([1,20,0,0])+b'MCON'+bytes([1,2])+bytes(10)
    cpu.de=request;cpu.c=182;cpu.run(LAYOUT['EXTENSIONS'],limit=20000)
    assert cpu.a==0 and cpu.word(request+12)==cpu.word(binding)
    change(2,'ANSI');change(2,backend)
    assert cpu.word(binding)==basic and cpu.word(6)==LAYOUT['TPA'] and cpu.mem[stage.RSTCOUNT]==0
    print(f'PASS {backend}: admitted portable ANSI, partial parser/saved rendition relocation, repeated restore, backend guard, public lookup and 53K unload')


if __name__=='__main__':main()
