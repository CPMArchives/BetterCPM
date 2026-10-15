#!/usr/bin/env python3
"""Build the ED editor; no PL/M build dependency."""
import argparse
from pathlib import Path
from build_ccp import assemble
from utility_versions import expand_versions
ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'build/ed-development'


def expanded_source():
    text=(ROOT/'src/utilities/ed.mac').read_text()
    text=text.replace('; @ed-invocation@',(ROOT/'src/utilities/common/ed-invocation.inc').read_text())
    for part in ('buffer','command','lines','type','input','console','source','append','output','write','finish','files','publish','lifecycle','recovery','find','substitute','juxtapose','autoscan','macro','library','transfer','delay','page'):
        text=text.replace('; @ed-'+part+'@',(ROOT/'src/utilities/common'/('ed-'+part+'.inc')).read_text())
    return expand_versions(text)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    args=p.parse_args();BUILD.mkdir(parents=True,exist_ok=True)
    text=expanded_source().replace('        CSEG\n        .PHASE  ','        ASEG\n        ORG     ').replace('        .DEPHASE\n','')
    data=assemble(args.assembler,text,BUILD/'EDDEV.COM',BUILD/'ed.lst',0x100)
    release=ROOT/'build/utilities/ED.COM'
    release.parent.mkdir(parents=True,exist_ok=True)
    release.write_bytes(data)
    print(f'ED.COM: {len(data)} bytes; EDDEV.COM is the identical qualification copy')


if __name__=='__main__':main()
