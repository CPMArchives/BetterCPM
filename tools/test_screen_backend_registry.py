#!/usr/bin/env python3
"""Exercise SCRN admission/rejection with the production manager and registry.

Synthetic callback tests identity/lifecycle plumbing, not screen semantics.
"""
from pathlib import Path
from build_rsx_module import make_module
from system_layout import LAYOUT
from test_rsx_disk_cache import DiskMachine
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
    # The current manager reads both its overlay pack and its disk cache.
    cpu=DiskMachine()
    bios=(ROOT/'build/bios/bios.bin').read_bytes()
    cpu.mem[LAYOUT['BIOS']:LAYOUT['BIOS']+len(bios)]=bios
    cpu.run(LAYOUT['BIOS']+72)
    syms=symbols(ROOT/'build/bios/bios.lst')
    binding=syms['MP_MON']
    cpu.files[0,0,'MONTEST.RSX']=provider('MONTEST')
    assert cpu.change(1,b'MONTEST',(0,0))==0
    cases=[dict(bits=0),dict(bits=2),dict(bits=3),dict(bits=4),dict(bits=0x101),
           dict(major=0),dict(major=2),dict(minor=2),
           dict(reconstruction='STATELESS'),dict(reconstruction='STATE_PRESERVING'),
           dict(reconstruction='COLD_ONLY')]
    for args in cases:
        cpu.files[0,0,'SCRTEST.RSX']=backend(**args)
        before=(cpu.word(binding),cpu.word(stage.GEN),cpu.word(6),cpu.mem[stage.RSTCOUNT],
                cpu.chain())
        assert cpu.change(1,b'SCRTEST',(0,0))!=0,args
        after=(cpu.word(binding),cpu.word(stage.GEN),cpu.word(6),cpu.mem[stage.RSTCOUNT],
               cpu.chain())
        assert after==before,('rejection changed live monitor/profile',args)
    cpu.files[0,0,'SCRTEST.RSX']=backend()
    assert cpu.change(1,b'SCRTEST',(0,0))==0
    extension=(ROOT/'build/system/extensions.bin').read_bytes()
    cpu.mem[LAYOUT['EXTENSIONS']:LAYOUT['EXTENSIONS']+len(extension)]=extension
    request=0x7100
    cpu.mem[request:request+20]=bytes([1,20,0,0])+b'SCRN'+bytes([1,0])+bytes(10)
    cpu.pair('DE',request);cpu.reg['C'].value=182
    assert cpu.run(LAYOUT['EXTENSIONS'])==0
    assert cpu.run(cpu.word(request+12))==42
    assert cpu.change(2,b'SCRTEST',(0,0))==0
    assert cpu.word(binding)!=syms['MC_RAW']
    assert cpu.change(2,b'MONTEST',(0,0))==0
    assert cpu.word(binding)==syms['MC_RAW'] and cpu.word(6)==LAYOUT['TPA']
    assert cpu.mem[stage.RSTCOUNT]==0
    print('PASS: 11 rejected SCRN loads preserve live monitor/profile; valid registry lookup/call; coexistence, removal and 53K recovery')


if __name__=='__main__':main()
