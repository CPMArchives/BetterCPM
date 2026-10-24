#!/usr/bin/env python3
"""Cross-build native DSYM without changing the packaged assembler or linker."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import re
from build_dasm import validate_native_identifiers
from component_build import recorded_build
from utility_versions import strings

ROOT=Path(__file__).resolve().parents[1]


def source():
    text=(ROOT/'src/utilities/dsym.mac').read_text()
    for name in ('codecfile.mac','dsymdu.inc','dsymlog.inc','printnum.inc','duselect.inc','filespec.inc','zsm4words.inc','version.inc'):
        text=text.replace('        INCLUDE '+name,
                          (ROOT/'src/utilities/common'/name).read_text())
    text=text.replace('; @dsym-version@',strings('DSYM',label='SY_VERSION'))
    definitions=[]
    def move(match):
        definitions.append(match[0]);return ''
    text=re.sub(r'(?m)^DU_\w+\s+EQU[^\n]*\n',move,text)
    text=re.sub(r'(?m)^\s*END\s*$', '\n'+''.join(definitions)+'\n END\n',text)
    return text



@recorded_build('utility:DSYM')
def build(assembler, output):
    output.mkdir(parents=True,exist_ok=True)
    text=source();validate_native_identifiers(text)
    path=output/'dsym.mac';path.write_text(text)
    subprocess.run([str(assembler),'-e32','-fb','-o'+str((output/'dsym.bin').resolve()),
                    '-l'+str((output/'dsym.lst').resolve()),str(path.resolve())],check=True)
    image=(output/'dsym.bin').read_bytes()
    if image[:256]==bytes(256):image=image[256:]
    (output/'DSYM.COM').write_bytes(image)
    return image


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    p.add_argument('--output',type=Path,default=ROOT/'build/utilities')
    p.add_argument('--identity-state',choices=('auto','assigned','development'),default='auto')
    p.add_argument('--target',choices=('z80pack','trs80gp'),default='z80pack')
    a=p.parse_args();image=build(a.assembler,a.output,target=a.target,identity_state=a.identity_state)
    print(len(image),'bytes;',hashlib.sha256(image).hexdigest())
