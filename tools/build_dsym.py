#!/usr/bin/env python3
"""Cross-build native DSYM without changing the packaged assembler or linker."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import re
from build_dasm import validate_native_identifiers

ROOT=Path(__file__).resolve().parents[1]


def source():
    text=(ROOT/'src/utilities/dsym.mac').read_text()
    for name in ('codecfile.mac','dsymdu.inc','printnum.inc','duselect.inc','filespec.inc','zsm4words.inc'):
        text=text.replace('        INCLUDE '+name,
                          (ROOT/'src/utilities/common'/name).read_text())
    definitions=[]
    def move(match):
        definitions.append(match[0]);return ''
    text=re.sub(r'(?m)^DU_\w+\s+EQU[^\n]*\n',move,text)
    text=re.sub(r'(?m)^\s*END\s*$', '\n'+''.join(definitions)+'\n END\n',text)
    return text



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
    p.add_argument('--output',type=Path,default=ROOT/'build/dasm-development')
    a=p.parse_args();image=build(a.assembler,a.output)
    print(len(image),'bytes;',hashlib.sha256(image).hexdigest())
