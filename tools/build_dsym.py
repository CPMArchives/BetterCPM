#!/usr/bin/env python3
"""Cross-build native DSYM without changing the packaged assembler or linker."""
import argparse
import hashlib
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def source():
    text=(ROOT/'src/utilities/dsym.mac').read_text()
    return text.replace('        INCLUDE codecfile.mac',
                        (ROOT/'src/utilities/common/codecfile.mac').read_text())


def build(assembler, output):
    output.mkdir(parents=True,exist_ok=True)
    path=output/'dsym.mac';path.write_text(source())
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
