#!/usr/bin/env python3
"""Build unloadable screen backends; no resident image is changed."""
import argparse
import re
from pathlib import Path
from build_ccp import assemble
from build_cpx_module import relocation_offsets
from build_rsx_module import make_module
from component_registry import module_version

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/screen-backends'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    args=p.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    (ROOT/'build/rsx').mkdir(parents=True,exist_ok=True)
    from checked_carriers import selected_contract
    checked = selected_contract(args.assembler)
    listing = '' if checked else (ROOT/'build/bios/bios.lst').read_text(errors='replace')
    bindings=''
    for name in ([] if checked else ['M4CURSOR','M4COLUMN']):
        value=int(re.search(r'^([0-9a-f]{4})\s+.*\b'+name+':',listing,re.M)[1],16)
        bindings+=f'{name} EQU 0{value:04X}H\n'
    for name,source,bits,entry in [('M4SCRN','model4.mac',1,'S_ENTRY'),('ANSISCRN','ansi-host.mac',2,'SB_ENTRY')]:
        if checked and name == 'M4SCRN':
            continue
        text=(ROOT/'src/rsx/screen'/source).read_text(errors='replace').replace('        INCLUDE backend.inc',bindings)
        code=assemble(args.assembler,text,OUT/(name+'.bin'),OUT/(name+'.lst'),0x8000)
        alt=assemble(args.assembler,text.replace('08000H','08101H'),OUT/(name+'-alt.bin'),OUT/(name+'-alt.lst'),0x8101)
        relocs=relocation_offsets(code,alt,0x101)
        listing=(OUT/(name+'.lst')).read_text(errors='replace')
        callback=int(re.search(r'^([0-9a-f]{4})\s+.*\b'+entry+':',listing,re.M)[1],16)-0x8000
        carrier=make_module(name=name,version=module_version(name),services=[],linked_base=0x8000,
            code=code,relocations=relocs,reconstruction_class='STATEFUL',
            callable_services=[(b'SCRN',1,1,callback,bits)])
        (OUT/(name+'.RSX')).write_bytes(carrier)
        (ROOT/'build/rsx'/(name+'.RSX')).write_bytes(carrier)
        print(f'{name}: {len(code)} payload bytes, {int.from_bytes(carrier[14:16],"little")} allocated; {len(relocs)} relocations')


if __name__=='__main__':main()
