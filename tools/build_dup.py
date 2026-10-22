#!/usr/bin/env python3
"""Build DUP alone using the same expanded source as native qualification."""
import argparse,hashlib
from pathlib import Path
from build_ccp import assemble
from build_disk_utilities import builtin_source
from system_layout import expand_layout
ROOT=Path(__file__).resolve().parents[1]

def expanded_source():
 text=expand_layout((ROOT/'src/utilities/dup.mac').read_text())
 text=text.replace('        INCLUDE dup-cli.inc',(ROOT/'src/utilities/dup-cli.inc').read_text())
 for name in ('common','fdbread'):
  text=text.replace('        INCLUDE disk/'+name+'.inc',(ROOT/'src/utilities/disk'/(name+'.inc')).read_text())
 text=text.replace('        INCLUDE disk/builtins.inc',builtin_source())
 text=text.replace('; @monitor-console@',(ROOT/'src/utilities/common/monitorconsole.inc').read_text())
 from shared_ui import expand_dup_ui
 return expand_dup_ui(text)

def main():
 p=argparse.ArgumentParser();p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm');a=p.parse_args()
 out=ROOT/'build/utilities';out.mkdir(parents=True,exist_ok=True)
 data=assemble(a.assembler,expanded_source(),out/'DUP.COM',out/'dup.lst',256)
 assert len(data)<=0x3d00,'DUP overlaps private stack'
 print(hashlib.sha256(data).hexdigest(),f'DUP: {len(data)} bytes')
if __name__=='__main__':main()
