#!/usr/bin/env python3
"""Build the portable MM-style ADM-3A personality and its standalone test utility."""
import argparse
import re
from pathlib import Path
from build_ccp import assemble
from build_cpx_module import relocation_offsets
from build_rsx_module import make_module
from utility_versions import expand_versions

from component_registry import module_version

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'build/monitor-development'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler',type=Path,default=Path('/Users/nathanael/bin/z80asm'))
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'src/rsx/adm3a.mac').read_text()
    text=source.replace('        CSEG\n        .PHASE ', '        ASEG\n        ORG ').replace('        .DEPHASE\n','')
    code=assemble(args.assembler,text,OUT/'adm3a.bin',OUT/'adm3a.lst',0x8000)
    alternate=assemble(args.assembler,text.replace('08000H','08101H'),OUT/'adm3a-alt.bin',OUT/'adm3a-alt.lst',0x8101)
    relocs=relocation_offsets(code,alternate,0x101)
    table=(OUT/'adm3a.lst').read_text(errors='replace')
    entry=int(re.search(r'^([0-9a-f]{4})\s+.*\bAM_ENTRY:',table,re.M)[1],16)-0x8000
    carrier=make_module(name='ADM3A',version=module_version('ADM3A'),services=[],linked_base=0x8000,
                        code=code,relocations=relocs,reconstruction_class='STATEFUL',
                        callable_services=[(b'MCON',1,1,entry,4)])
    (OUT/'ADM3A.RSX').write_bytes(carrier)
    test=expand_versions((ROOT/'src/utilities/admtst.mac').read_text()).replace('        CSEG\n        .PHASE ', '        ASEG\n        ORG ').replace('        .DEPHASE\n','')
    assemble(args.assembler,test,OUT/'ADMTST.COM',OUT/'admtst.lst',0x100)
    for folder,name,data in [('rsx','ADM3A.RSX',carrier),('utilities','ADMTST.COM',(OUT/'ADMTST.COM').read_bytes())]:
        destination=ROOT/'build'/folder
        destination.mkdir(parents=True,exist_ok=True)
        (destination/name).write_bytes(data)
    print(f'ADM3A provider: {len(code)} payload bytes; {len(relocs)} relocations; portable SCRN backend required')


if __name__=='__main__':main()
