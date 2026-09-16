#!/usr/bin/env python3
"""Build CONFIG, DUP and SYSGEN as ordinary transient programs."""
from pathlib import Path
import argparse
import json
import math
from build_ccp import assemble
from system_layout import expand_layout
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
    ccp = (ROOT/'build/ccp/ccp.bin').read_bytes()
    rlm = (ROOT/'build/ccp/ccp.rlm').read_bytes()
    relocations = int.from_bytes(rlm[14:16], 'little')
    ccpmeta = (f"CCP_SIZE EQU {len(ccp)}\n"
               f"CCP_ALLOC EQU {(len(ccp)+255)&~255}\n"
               f"CCP_RECORDS EQU {math.ceil(len(ccp)/128)}\n"
               f"CCP_RELOCS EQU {relocations}\n")
    partmeta = "".join(
        f"{symbol}_SIZE EQU {(ROOT/path).stat().st_size}\n"
        for symbol, path in (
            ('GATEWAY', 'build/system/gateway.bin'),
            ('BDOS', 'build/bdos/bdos.bin'),
            ('EXTENS', 'build/system/extensions.bin'),
            ('DISK', 'build/system/disk.bin'),
            ('BIOS', 'build/bios/bios.bin'),
            ('FILELOAD', 'build/system/fileloader.bin'),
            ('TABLES', 'build/system/tables.bin'),
        ))
    for stem in ('config','dup','sysgen','sysbuild','respack','rlmbuild'):
        source=ROOT/f'src/utilities/{stem}.mac'
        text=expand_layout(source.read_text()).replace('        INCLUDE ccpmeta.inc', ccpmeta).replace('        INCLUDE partmeta.inc', partmeta).replace('        INCLUDE disk/sysgen.inc',
            (ROOT/'src/utilities/disk/sysgen.inc').read_text()).replace('        INCLUDE disk/common.inc',
            (ROOT/'src/utilities/disk/common.inc').read_text()).replace('        INCLUDE disk/builtins.inc', builtin)
        data=assemble(args.assembler,text,out/(stem.upper()+'.COM'),out/(stem+'.lst'),0x100)
        if len(data)>0x3D00:
            raise SystemExit(f'{stem}: program overlaps private stack')
        print(f'{stem.upper()}.COM: {len(data)} bytes')
if __name__=='__main__': main()
