#!/usr/bin/env python3
"""Build the unshipped bounded ANSI/VT100 provider."""
import argparse
import re
from pathlib import Path
from build_ccp import assemble
from build_cpx_module import relocation_offsets
from build_rsx_module import make_module
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/ansi-development'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    text=(ROOT/'src/rsx/ansi.mac').read_text().replace('        CSEG\n        .PHASE BASE','        ASEG\n        ORG BASE').replace('        .DEPHASE\n','')
    code=assemble(args.assembler,text,OUT/'ansi.bin',OUT/'ansi.lst',0x8000)
    alt=assemble(args.assembler,text.replace('08000H','08101H'),OUT/'ansi-alt.bin',OUT/'ansi-alt.lst',0x8101)
    relocations=relocation_offsets(code,alt,0x101)
    entry=int(re.search(r'^([0-9a-f]{4})\s+.*\bAN_ENTRY:',(OUT/'ansi.lst').read_text(),re.M)[1],16)-0x8000
    carrier=make_module(name='ANSI',version=(0,1),services=[],linked_base=0x8000,code=code,relocations=relocations,reconstruction_class='STATEFUL',callable_services=[(b'MCON',1,0,entry,2)])
    (OUT/'ANSI.RSX').write_bytes(carrier)
    test=(ROOT/'src/utilities/ansitst.mac').read_text().replace('        CSEG\n        .PHASE 0100H','        ASEG\n        ORG 0100H').replace('        .DEPHASE\n','')
    assemble(args.assembler,test,OUT/'ANSITST.COM',OUT/'ansitst.lst',0x100)
    print(f'ANSI foundation: {len(code)} payload bytes, {len(relocations)} relocations; not distributed')


if __name__=='__main__':main()
