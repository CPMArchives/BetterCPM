#!/usr/bin/env python3
"""Build CONFIG and DUP as ordinary transient programs; no resident slots."""
from pathlib import Path
import argparse
import json
from build_ccp import assemble
ROOT = Path(__file__).resolve().parents[1]

def builtin_source():
    rows=json.loads((ROOT/'metadata/mm-builtin-formats.json').read_text())['formats']
    catalogue=''.join('*'+v['name']+'\r\n'+','.join(map(str,v['parameters']))+'\r\n'+','.join(map(str,v['sector_ids']))+'\r\n' for v in rows).encode('ascii')
    builtin='BUILTINS:\n'+'\n'.join('        DB '+','.join(map(str,catalogue[i:i+16])) for i in range(0,len(catalogue),16))+'\nBUILTINEND:\n'
    return builtin

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    args=p.parse_args()
    out=ROOT/'build/utilities'
    out.mkdir(parents=True,exist_ok=True)
    builtin=builtin_source()
    for stem in ('config','dup'):
        source=ROOT/f'src/utilities/{stem}.mac'
        text=source.read_text().replace('        INCLUDE disk/sysgen.inc',
            (ROOT/'src/utilities/disk/sysgen.inc').read_text()).replace('        INCLUDE disk/common.inc',
            (ROOT/'src/utilities/disk/common.inc').read_text()).replace('        INCLUDE disk/builtins.inc', builtin)
        data=assemble(args.assembler,text,out/(stem.upper()+'.COM'),out/(stem+'.lst'),0x100)
        if len(data)>0x3D00:
            raise SystemExit(f'{stem}: program overlaps private stack')
        print(f'{stem.upper()}.COM: {len(data)} bytes')
if __name__=='__main__': main()
