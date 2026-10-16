#!/usr/bin/env python3
"""Exercise SCRN admission/rejection with the production manager and registry.

Synthetic callback tests identity/lifecycle plumbing, not screen semantics.
"""
import tempfile
from pathlib import Path
from build_rsx_module import make_module
from system_layout import LAYOUT
from test_bios import Z80
from test_monitor_selection import provider
from test_vt52_foundation import symbols
import test_rsx_stage3 as stage

ROOT=Path(__file__).resolve().parents[1]


def backend(*,bits=1,major=1,minor=0,reconstruction='STATEFUL'):
    code=b'\0'*8+bytes((0x2A,0,0x80,0xE9,0xC9,0x3E,42,0xC9))
    return make_module(name='SCRTEST',version=(0,1),services=[],linked_base=0x8000,
        code=code,relocations=[9],reconstruction_class=reconstruction,
        callable_services=[(b'SCRN',major,minor,13,bits)])


def main():
    out=ROOT/'build/test-results/screen-backend-registry';out.mkdir(parents=True,exist_ok=True)
    mon=provider('MONTEST')
    (out/'MONTEST.RSX').write_bytes(mon)
    (out/'SCRTEST.RSX').write_bytes(backend())
    stage.FILES=(("R3PACK  ","build/system/R3PACK.RSX"),
                 ("MONTEST ",str((out/'MONTEST.RSX').relative_to(ROOT))),
                 ("SCRTEST ",str((out/'SCRTEST.RSX').relative_to(ROOT))))
    cpu=Z80((ROOT/'build/bios/bios.bin').read_bytes())
    for (_,path),address in zip(stage.FILES,(0x7800,0xB400,0xB800)):
        image=(ROOT/path).read_bytes();cpu.mem[address:address+len(image)]=image
    with tempfile.TemporaryDirectory() as temporary:
        stub=stage.file_stub(Path(temporary),(0x7800,0xB400,0xB800))
    cpu.mem[LAYOUT['FILE']:LAYOUT['FILE']+len(stub)]=stub
    cpu.mem[LAYOUT['BIOS']+60:LAYOUT['BIOS']+63]=b'\xaf\xc9\0'
    cpu.run(LAYOUT['BIOS']+72)
    syms=symbols(ROOT/'build/bios/bios.lst');binding=syms['MP_MON']
    for address,value in [(stage.HEAD,0),(stage.LOW,LAYOUT['RSX']),
                          (stage.TPA,LAYOUT['TPA']),(6,LAYOUT['TPA']),(stage.GEN,1)]:cpu.setword(address,value)
    cpu.mem[stage.RSTCOUNT:stage.RSTCOUNT+41]=bytes(41)
    bootstrap=(ROOT/'build/system/r3entry.bin').read_bytes()
    stage.invoke(cpu,bootstrap,1,b'MONTEST ');assert cpu.a==0
    cases=[dict(bits=0),dict(bits=2),dict(bits=3),dict(bits=0x101),
           dict(major=0),dict(major=2),dict(minor=2),
           dict(reconstruction='STATELESS'),dict(reconstruction='STATE_PRESERVING'),
           dict(reconstruction='COLD_ONLY')]
    for args in cases:
        image=backend(**args);cpu.mem[0xB800:0xB800+len(image)]=image
        before=(cpu.word(binding),cpu.word(stage.GEN),cpu.word(6),cpu.mem[stage.RSTCOUNT],
                bytes(cpu.mem[cpu.word(stage.LOW):LAYOUT['RSX']]))
        stage.invoke(cpu,bootstrap,1,b'SCRTEST ')
        assert cpu.a!=0,args
        after=(cpu.word(binding),cpu.word(stage.GEN),cpu.word(6),cpu.mem[stage.RSTCOUNT],
               bytes(cpu.mem[cpu.word(stage.LOW):LAYOUT['RSX']]))
        assert after==before,('rejection changed live monitor/profile',args)
    image=backend();cpu.mem[0xB800:0xB800+len(image)]=image
    stage.invoke(cpu,bootstrap,1,b'SCRTEST ');assert cpu.a==0
    extension=(ROOT/'build/system/extensions.bin').read_bytes()
    cpu.mem[LAYOUT['EXTENSIONS']:LAYOUT['EXTENSIONS']+len(extension)]=extension
    request=0x7100
    cpu.mem[request:request+20]=bytes([1,20,0,0])+b'SCRN'+bytes([1,0])+bytes(10)
    cpu.de=request;cpu.c=182;cpu.run(LAYOUT['EXTENSIONS'],limit=20000)
    assert cpu.a==0
    cpu.run(cpu.word(request+12),limit=1000);assert cpu.a==42
    stage.invoke(cpu,bootstrap,2,b'SCRTEST ');assert cpu.a==0
    assert cpu.word(binding)!=syms['MC_RAW']
    stage.invoke(cpu,bootstrap,2,b'MONTEST ');assert cpu.a==0
    assert cpu.word(binding)==syms['MC_RAW'] and cpu.word(6)==LAYOUT['TPA']
    assert cpu.mem[stage.RSTCOUNT]==0
    print('PASS: 10 rejected SCRN loads preserve live monitor/profile; valid registry lookup/call; coexistence, removal and 53K recovery')


if __name__=='__main__':main()
