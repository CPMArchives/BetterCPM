#!/usr/bin/env python3
"""Production profile dependency/rebinding tests with synthetic screen callbacks."""
import argparse
import tempfile
from pathlib import Path
from build_rsx_module import make_module
from system_layout import LAYOUT
from test_bios import Z80
from test_vt52_foundation import symbols
from test_screen_backend_registry import backend
import test_rsx_stage3 as stage

ROOT=Path(__file__).resolve().parents[1]


def frontend(*,slot=12,repairs=(),runtime=(),dual=False,capabilities=4,minor=1,reconstruction='STATEFUL',dispatch=8,entry=15):
    code=bytearray(128)
    code[8:12]=bytes((0x2A,0,0x80,0xE9))
    code[15:19]=bytes((0x2A,12,0x80,0xE9))
    if slot!=12:code[12]=1  # malformed non-null binding declaration
    # MCON entry dispatches through its declared, loader-owned backend word.
    services=[(b'MCON',1,minor,entry,capabilities)]
    if dual:services.append((b'SCRN',1,0,13,1))
    return make_module(name='PORTMON',version=(0,1),services=[],linked_base=0x8000,
        code=bytes(code),entry_offset=dispatch,relocations=[9,16]+list(repairs),runtime_pointers=list(runtime),
        reconstruction_class=reconstruction,callable_services=services)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--full-scx',action='store_true',help='require MCON 1.2 / SCRN 1.1 admission')
    parser.add_argument('--bios',type=Path,default=ROOT/'build/bios')
    args=parser.parse_args();bios=args.bios
    syms=symbols(bios/'bios.lst');bits=1 if 'M4CURSOR' in syms else 2
    out=ROOT/'build/test-results/monitor-backend-binding';out.mkdir(parents=True,exist_ok=True)
    goodfront=frontend(minor=2 if args.full_scx else 1);goodback=backend(bits=bits,minor=1 if args.full_scx else 0)
    (out/'PORTMON.RSX').write_bytes(goodfront);(out/'SCRTEST.RSX').write_bytes(goodback)
    alternate=bytearray(goodback);alternate[32:40]=b'SCRALT  '
    (out/'SCRALT.RSX').write_bytes(alternate)
    stage.FILES=(("R3PACK  ","build/system/R3PACK.RSX"),
                 ("HELLO   ","build/rsx/HELLO.RSX"),
                 ("SCRTEST ",str((out/'SCRTEST.RSX').relative_to(ROOT))),
                 ("PORTMON ",str((out/'PORTMON.RSX').relative_to(ROOT))),
                 ("SCRALT  ",str((out/'SCRALT.RSX').relative_to(ROOT))))
    sources=(0x7800,0xB400,0xB800,0xBC00,0xC000)
    cpu=Z80((bios/'bios.bin').read_bytes())
    for (_,path),address in zip(stage.FILES,sources):
        image=(ROOT/path).read_bytes();cpu.mem[address:address+len(image)]=image
    with tempfile.TemporaryDirectory() as temporary:stub=stage.file_stub(Path(temporary),sources)
    cpu.mem[LAYOUT['FILE']:LAYOUT['FILE']+len(stub)]=stub
    cpu.mem[LAYOUT['BIOS']+60:LAYOUT['BIOS']+63]=b'\xaf\xc9\0'
    cpu.run(LAYOUT['BIOS']+72);binding=syms['MP_MON'];basic=cpu.word(binding)
    extension=(ROOT/'build/system/extensions.bin').read_bytes()
    cpu.mem[LAYOUT['EXTENSIONS']:LAYOUT['EXTENSIONS']+len(extension)]=extension
    for address,value in [(stage.HEAD,0),(stage.LOW,LAYOUT['RSX']),
                          (stage.TPA,LAYOUT['TPA']),(6,LAYOUT['TPA']),(stage.GEN,1)]:cpu.setword(address,value)
    cpu.mem[stage.RSTCOUNT:stage.RSTCOUNT+41]=bytes(41)
    bootstrap=(ROOT/'build/system/r3entry.bin').read_bytes()
    def change(op,name,ok=True):
        before=(cpu.word(binding),cpu.word(stage.GEN),cpu.word(6),
                bytes(cpu.mem[stage.RSTCOUNT:stage.RSTCOUNT+41]),
                bytes(cpu.mem[cpu.word(stage.LOW):LAYOUT['RSX']]))
        stage.invoke(cpu,bootstrap,op,name.ljust(8).encode())
        assert (cpu.a==0)==ok,(op,name,cpu.a)
        if not ok:
            after=(cpu.word(binding),cpu.word(stage.GEN),cpu.word(6),
                   bytes(cpu.mem[stage.RSTCOUNT:stage.RSTCOUNT+41]),
                   bytes(cpu.mem[cpu.word(stage.LOW):LAYOUT['RSX']]))
            assert after==before,('rejection mutated profile',name)
    def check():
        entry=cpu.word(binding);frontbase=entry-15
        # Backend entry returns 42. Its address in the frontend must match the
        # actual retained allocation above it after any reconstruction.
        assert cpu.word(frontbase+12)==frontbase+256+13
        request=0x7100
        cpu.mem[request:request+20]=bytes([1,20,0,0])+b'MCON'+bytes([1,0])+bytes(10)
        cpu.de=request;cpu.c=182;cpu.run(LAYOUT['EXTENSIONS'],limit=20000)
        assert cpu.a==0 and cpu.word(request+12)==entry,(cpu.a,hex(cpu.word(request+12)),hex(entry),bytes(cpu.mem[request:request+20]))
        cpu.a=0;cpu.c=ord('X');cpu.run(LAYOUT['BIOS']+66,limit=2000)
        assert cpu.a==42
        return frontbase
    change(1,'PORTMON',False)            # no backend: rollback before detach
    change(1,'HELLO')
    if args.full_scx:
        oldback=backend(bits=bits)
        cpu.mem[0xB800:0xB800+len(oldback)]=oldback
        change(1,'SCRTEST')
        change(1,'PORTMON',False)        # existing SCRN is insufficient, not missing
        change(2,'SCRTEST')
        cpu.mem[0xB800:0xB800+len(goodback)]=goodback
    change(1,'SCRTEST')
    for image in [frontend(repairs=(11,)),frontend(repairs=(12,)),frontend(repairs=(13,)),
                  frontend(runtime=(12,)),frontend(runtime=(13,)),
                  frontend(slot=127),frontend(dual=True),frontend(capabilities=0),
                  frontend(capabilities=0x104),frontend(minor=3),
                  frontend(reconstruction='STATELESS'),frontend(reconstruction='STATE_PRESERVING'),
                  frontend(reconstruction='COLD_ONLY'),frontend(dispatch=10),frontend(entry=13)]:
        cpu.mem[0xBC00:0xBC00+len(image)]=image
        change(1,'PORTMON',False)
    cpu.mem[0xBC00:0xBC00+len(goodfront)]=goodfront
    class ObservedMemory(bytearray):
        publications=0
        def __setitem__(self,key,value):
            if key==stage.GEN:
                names=bytes(self[stage.RSTCOUNT+1:stage.RSTCOUNT+1+self[stage.RSTCOUNT]*8])
                if b'PORTMON ' in names:
                    entry=cpu.word(binding)
                    assert entry!=basic
                    frontbase=entry-15
                    assert cpu.word(frontbase+12)==frontbase+256+13, 'generation preceded backend rebinding'
                self.publications+=1
            super().__setitem__(key,value)
    cpu.mem=ObservedMemory(cpu.mem)
    change(1,'PORTMON');old=check()
    change(1,'SCRALT',False)            # selected backend must be unambiguous
    container=cpu.mem.find(b'R3PACK  ',LAYOUT['FILE'],LAYOUT['FILE']+len(stub))
    assert container>=0
    cpu.mem[container]=ord('X')
    change(2,'HELLO',False)             # retained carrier read failure is reversible
    cpu.mem[container]=ord('R')
    cpu.mem[old+80]=0xA5
    change(2,'SCRTEST',False)           # live dependency cannot be removed
    change(2,'HELLO');new=check()
    assert new>old and cpu.mem[new+80]==0xA5
    change(1,'HELLO');check()           # unrelated append also rebinds
    change(2,'HELLO');check()
    change(2,'PORTMON');assert cpu.word(binding)==basic
    change(2,'SCRTEST')
    assert cpu.word(6)==LAYOUT['TPA'] and cpu.mem[stage.RSTCOUNT]==0
    assert cpu.mem.publications>=6
    print('PASS: production missing/removal dependency guards, repair-word overlaps, bounds/dual-role rejection, retained rebinding/state, callback and 53K unload')


if __name__=='__main__':main()
