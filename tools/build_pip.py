#!/usr/bin/env python3
"""Build the development PIP foundation without publishing a distribution utility."""
import argparse,hashlib
from pathlib import Path
from build_ccp import assemble
from utility_versions import expand_versions
ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'build/pip-development'
def expanded_source():
 text=(ROOT/'src/utilities/pip.mac').read_text()
 text=text.replace('; @pip-parser@','\n'.join((ROOT/'src/utilities/common'/n).read_text() for n in ['pipparse.inc','pipoperand.inc','piptransfer.inc','pipconcat.inc','pipwild.inc']))
 return expand_versions(text)
def main():
 p=argparse.ArgumentParser();p.add_argument('--assembler',type=Path,default=Path('/Users/nathanael/bin/z80asm'));args=p.parse_args()
 BUILD.mkdir(parents=True,exist_ok=True)
 text=expanded_source().replace('        CSEG\n        .PHASE  ','        ASEG\n        ORG     ').replace('        .DEPHASE\n','')
 data=assemble(args.assembler,text,BUILD/'PIP.COM',BUILD/'pip.lst',0x100)
 assert data[3:10]==bytes((0xC9,0,0,0xC9,0,0,0x1A))
 print(f'{hashlib.sha256(data).hexdigest()}  development PIP: {len(data)} bytes; not for distribution')
if __name__=='__main__':main()
