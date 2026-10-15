#!/usr/bin/env python3
"""Build a private host monitor from the editable starter and translation profile."""
import argparse
import re
from pathlib import Path
from build_ccp import assemble
from build_cpx_module import relocation_offsets
from build_rsx_module import make_module
ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=ROOT/'src/rsx/monitor-template'


def build(assembler,engine,profile,name,out):
    if not re.fullmatch(r'[A-Z][A-Z0-9]{0,7}',name):
        raise ValueError('module name must be 1..8 uppercase letters/digits, starting with a letter')
    out.mkdir(parents=True,exist_ok=True)
    source=engine.read_text().replace('        INCLUDE profile.inc',profile.read_text())
    source=source.replace('        CSEG\n        .PHASE BASE','        ASEG\n        ORG BASE').replace('        .DEPHASE\n','')
    code=assemble(assembler,source,out/'monitor.bin',out/'monitor.lst',0x8000)
    alt=assemble(assembler,source.replace('BASE EQU 08000H','BASE EQU 08101H'),out/'monitor-alt.bin',out/'monitor-alt.lst',0x8101)
    relocations=relocation_offsets(code,alt,0x101)
    labels={label:int(address,16)-0x8000 for address,label in re.findall(r'^([0-9a-f]{4})\s+.*?\b(TP_[A-Z]+):',(out/'monitor.lst').read_text(),re.M)}
    # Reject count mistakes before emitting a loadable carrier.
    start,end=labels['TP_CLS'],labels['TP_BYTES']
    if start+1+code[start]!=end:
        raise ValueError('clear sequence byte count does not match its data')
    for first,last in [('TP_BYTES','TP_CODES'),('TP_CODES','TP_END')]:
        offset,end=labels[first],labels[last];seen=set()
        while offset<end and code[offset]:
            key=code[offset]
            if key in seen or offset+1>=end:
                raise ValueError('duplicate or incomplete translation entry')
            seen.add(key);offset+=2+code[offset+1]
        if offset!=end-1 or code[offset]!=0:
            raise ValueError('translation byte count or terminating zero is invalid')
    entry=int(re.search(r'^([0-9a-f]{4})\s+.*\bTP_ENTRY:',(out/'monitor.lst').read_text(),re.M)[1],16)-0x8000
    carrier=make_module(name=name,version=(0,1),services=[],linked_base=0x8000,code=code,relocations=relocations,reconstruction_class='STATEFUL',callable_services=[(b'MCON',1,0,entry,2)])
    (out/(name+'.RSX')).write_bytes(carrier)
    print(f'{name}: {len(code)} payload bytes, {len(relocations)} relocations; host-only development module')
    return carrier


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    p.add_argument('--engine',type=Path,default=TEMPLATE/'host.mac')
    p.add_argument('--profile',type=Path,default=TEMPLATE/'ansi-demo.inc')
    p.add_argument('--name',default='MONDEMO')
    p.add_argument('--output',type=Path,default=ROOT/'build/monitor-template')
    a=p.parse_args();build(a.assembler,a.engine,a.profile,a.name,a.output)


if __name__=='__main__':main()
