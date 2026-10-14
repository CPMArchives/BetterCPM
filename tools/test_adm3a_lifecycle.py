#!/usr/bin/env python3
"""Load the real ADM3A carrier through production RSX transactions and move it."""
import tempfile
from pathlib import Path
from test_adm3a_foundation import ROOT, OUT, symbols
from system_layout import LAYOUT
from test_bios import Z80
import test_rsx_stage3 as stage


def main():
    stage.FILES=(("R3PACK  ","build/system/R3PACK.RSX"),
                 ("HELLO   ","build/rsx/HELLO.RSX"),
                 ("ADM3A   ","build/monitor-development/ADM3A.RSX"))
    sources=(0x7800,0xB400,0xB800)
    cpu=Z80((ROOT/'build/bios/bios.bin').read_bytes())
    for (_,path),address in zip(stage.FILES,sources):
        image=(ROOT/path).read_bytes()
        cpu.mem[address:address+len(image)]=image
    with tempfile.TemporaryDirectory() as temp:
        stub=stage.file_stub(Path(temp),sources)
    cpu.mem[LAYOUT['FILE']:LAYOUT['FILE']+len(stub)]=stub
    cpu.mem[LAYOUT['BIOS']+60:LAYOUT['BIOS']+63]=b'\xaf\xc9\0'
    cpu.setword(1,LAYOUT['BIOS']+3)
    syms=symbols(OUT/'adm3a.lst')
    bios=symbols(ROOT/'build/bios/bios.lst')
    binding=bios['MP_MON']
    cpu.run(LAYOUT['BIOS']+72)
    basic=cpu.word(binding)
    cpu.setword(stage.HEAD,0)
    cpu.setword(stage.LOW,LAYOUT['RSX'])
    cpu.setword(stage.TPA,LAYOUT['TPA'])
    cpu.setword(6,LAYOUT['TPA'])
    cpu.setword(stage.GEN,1)
    cpu.mem[stage.RSTCOUNT:stage.RSTCOUNT+41]=bytes(41)
    bootstrap=(ROOT/'build/system/r3entry.bin').read_bytes()
    def change(mode,name):
        stage.invoke(cpu,bootstrap,mode,name)
        assert cpu.a==0,(mode,name,cpu.a)
    def output(char):
        cpu.a,cpu.c=0,char
        cpu.run(LAYOUT['BIOS']+66,limit=20000)
    change(1,b'HELLO   ')
    change(1,b'ADM3A   ')
    old=cpu.word(stage.LOW)
    assert cpu.word(binding)==old+syms['AM_ENTRY']-0x8000
    output(22)  # persistent reverse mode
    for char in b'\x1b0\x1b=!':output(char)  # hidden cursor and partial row address
    change(2,b'HELLO   ')
    new=cpu.word(stage.LOW)
    assert new>old and cpu.word(binding)==new+syms['AM_ENTRY']-0x8000
    for name,value in [('AM_STATE',3),('AM_PENDING_ROW',1),('AM_REVERSE',128),('AM_VISIBLE',0)]:
        assert cpu.mem[new+syms[name]-0x8000]==value,name
    output(32+10)
    assert cpu.word(bios['M4CURSOR'])==0xF800+90
    output(ord('A'))
    assert cpu.mem[0xF800+90]==193
    change(1,b'HELLO   ')
    assert cpu.word(binding)==new+syms['AM_ENTRY']-0x8000
    change(2,b'HELLO   ')
    assert cpu.word(binding)==new+syms['AM_ENTRY']-0x8000
    change(2,b'ADM3A   ')
    assert cpu.word(binding)==basic
    assert cpu.word(6)==LAYOUT['TPA'] and cpu.mem[stage.RSTCOUNT]==0
    assert cpu.word(bios['M4CURSOR'])==0xF800+91
    print('PASS: actual ADM3A install, upward movement with partial parser/modes, subsequent output, unload and 53K TPA restoration')


if __name__=='__main__':main()
