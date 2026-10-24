#!/usr/bin/env python3
"""Compare the shallow host-output leaf with its retained MONRAW fallback.

Execute the assembled renderer at two relocation addresses, covering every
output byte and preserved register. The fallback retains the former B_EMIT
implementation, including the special 1Ch clear sequence.
"""
from pathlib import Path
import argparse,json,sys

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('root',type=Path)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();root=a.root.resolve()
sys.path.insert(0,str(root/'tools'))
from test_screen_backends import fixture
from build_z80pack_image import symbols
syms=symbols(root/'build/screen-backends/ANSISCRN.lst')
count=0
for base in (0x6000,0x8101):
    cpu,_,_,_=fixture('ANSISCRN',base,cpmsim_bios=root/'build/z80pack')
    wire=[]
    def write(port,value):
        assert port&255==1
        wire.append(value)
    cpu.port_write=write
    for value in range(256):
        outcomes=[]
        for entry in ('B_EMIT','B_EMIT_CLEAR'):
            wire.clear()
            cpu.bc=0x1200+value;cpu.de=0x3456;cpu.hl=0x789a;cpu.ix=0x2468
            sp=cpu.sp
            cpu.run(syms[entry]+base-0x8000)
            assert (cpu.bc,cpu.de,cpu.hl,cpu.ix,cpu.sp)==(0x1200+value,0x3456,0x789a,0x2468,sp)
            outcomes.append((bytes(wire),cpu.a,cpu.z,cpu.carry))
        assert outcomes[0]==outcomes[1],(base,value,outcomes)
        expected=b'\x1b[2J\x1b[H' if value==28 else bytes([value])
        assert outcomes[0][0]==expected,(base,value,outcomes)
        count+=1
a.output.write_text(json.dumps({'passed':True,'byte_and_relocation_cases':count,
    'scope':'Assembled leaf/fallback equivalence: wire bytes, A/Z/C and BC/DE/HL/IX/SP; all 256 bytes at two relocation bases.'},indent=2)+'\n')
print(f'PASS {count} assembled output equivalence cases')
