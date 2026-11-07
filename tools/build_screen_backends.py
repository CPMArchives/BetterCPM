#!/usr/bin/env python3
"""Build the selected platform's unloadable screen backends."""
import argparse
from pathlib import Path

from build_ccp import assemble
from build_cpx_module import relocation_offsets
from build_rsx_module import make_module
from build_z80pack_image import symbols
from component_registry import module_version
from system_layout import CONTEXT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'build/screen-backends'


def crt_bindings(listing, model2=False):
    table = symbols(listing)
    position, column = (('M2_POS', 'M2_COL') if model2 else ('M4CURSOR', 'M4COLUMN'))
    if model2 and max(table[position]+1, table[column]) >= 0xF800:
        raise ValueError('Model II cursor state overlaps the video overlay')
    return (f'CRT_POS EQU 0{table[position]:04X}H\nCRT_COL EQU 0{table[column]:04X}H\n'
            f'M2BANK EQU {int(model2)}')


def build(assembler, name, source, bindings, capability, entry):
    text = (ROOT/'src/rsx/screen'/source).read_text(encoding='ascii').replace(
        '        INCLUDE backend.inc', bindings)
    listing = OUT/(name+'.lst')
    code = assemble(assembler,text,OUT/(name+'.bin'),listing,0x8000)
    alt = assemble(assembler,text.replace('08000H','08101H'),OUT/(name+'-alt.bin'),
                   OUT/(name+'-alt.lst'),0x8101)
    relocs = relocation_offsets(code,alt,0x101)
    callback = symbols(listing)[entry]-0x8000
    carrier = make_module(name=name,version=module_version(name),services=[],linked_base=0x8000,
        code=code,relocations=relocs,reconstruction_class='STATEFUL',
        callable_services=[(b'SCRN',1,1,callback,capability)])
    for folder in (OUT, ROOT/'build/rsx'):
        (folder/(name+'.RSX')).write_bytes(carrier)
    print(f'{name}: {len(code)} payload bytes, {int.from_bytes(carrier[14:16],"little")} allocated; {len(relocs)} relocations')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    args = p.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    (ROOT/'build/rsx').mkdir(parents=True,exist_ok=True)
    if CONTEXT and CONTEXT[0]['target']=='trs80m2':
        bindings=crt_bindings(ROOT/'build/trs80m2/bios.lst',model2=True)
        build(args.assembler,'M2SCRN','crt80x24.mac',bindings,4,'S_ENTRY')
        return
    if not CONTEXT:
        bindings=crt_bindings(ROOT/'build/bios/bios.lst')
        build(args.assembler,'M4SCRN','crt80x24.mac',bindings,1,'S_ENTRY')
    build(args.assembler,'ANSISCRN','ansi-host.mac','',2,'SB_ENTRY')


if __name__=='__main__':
    main()
