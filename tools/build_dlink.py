#!/usr/bin/env python3
"""Build the checked transient LINK launcher without modifying external LINK."""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
from build_dasm import validate_native_identifiers
from component_build import recorded_build
from utility_versions import strings
ROOT=Path(__file__).resolve().parents[1]
def source():
    text=(ROOT/'src/utilities/dlink.mac').read_text()
    for name in ('duselect.inc','filespec.inc','dasmcrc.inc','printnum.inc','version.inc'):
        text=text.replace('INCLUDE '+name,(ROOT/'src/utilities/common'/name).read_text())
    text=text.replace('; @dlink-version@',strings('DLINK',label='DL_VERSION_TEXT'))
    definitions=[]
    def move(match):definitions.append(match[0]);return ''
    text=re.sub(r'(?m)^DU_\w+\s+EQU[^\n]*\n',move,text)
    # EQU evaluation must occur inside the phase, after DU_WORK exists.
    return text.replace(' .DEPHASE', ''.join(definitions)+' .DEPHASE')
@recorded_build('utility:DLINK')
def build(assembler,output):
    output.mkdir(parents=True,exist_ok=True)
    text=source();validate_native_identifiers(text)
    p=output/'dlink.mac';p.write_text(text)
    subprocess.run([str(assembler),'-e32','-fb','-o'+str((output/'dlink.bin').resolve()),
                    '-l'+str((output/'dlink.lst').resolve()),str(p.resolve())],check=True)
    image=(output/'dlink.bin').read_bytes()
    if image[:256]==bytes(256):image=image[256:]
    (output/'DLINK.COM').write_bytes(image)
    return image
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    p.add_argument('--output',type=Path,default=ROOT/'build/utilities')
    p.add_argument('--identity-state',choices=('auto','assigned','development'),default='auto')
    p.add_argument('--target',choices=('z80pack','trs80gp'),default='z80pack')
    a=p.parse_args();v=build(a.assembler,a.output,target=a.target,identity_state=a.identity_state)
    print(len(v),'bytes;',hashlib.sha256(v).hexdigest())
