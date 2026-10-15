#!/usr/bin/env python3
"""Build the unshipped ED invocation foundation; no PL/M build dependency."""
import argparse
from pathlib import Path
from build_ccp import assemble
from utility_versions import expand_versions
ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'build/ed-development'


def expanded_source():
    text=(ROOT/'src/utilities/ed.mac').read_text()
    text=text.replace('; @ed-invocation@',(ROOT/'src/utilities/common/ed-invocation.inc').read_text())
    for part in ('buffer','command','lines','type','input','console','source','append'):
        text=text.replace('; @ed-'+part+'@',(ROOT/'src/utilities/common'/('ed-'+part+'.inc')).read_text())
    return expand_versions(text)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    args=p.parse_args();BUILD.mkdir(parents=True,exist_ok=True)
    text=expanded_source().replace('        CSEG\n        .PHASE  ','        ASEG\n        ORG     ').replace('        .DEPHASE\n','')
    data=assemble(args.assembler,text,BUILD/'EDDEV.COM',BUILD/'ed.lst',0x100)
    print(f'ED development core: {len(data)} bytes; EDDEV.COM is not a usable editor or distribution artifact')


if __name__=='__main__':main()
