#!/usr/bin/env python3
"""Build the maintained DASM adaptation; keep upstream reference bytes separate."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import re

ROOT = Path(__file__).resolve().parents[1]


def source(reference=False):
    folder = ROOT / ('third_party/dasm' if reference else 'src/utilities')
    text = (folder / 'dasm.mac').read_text(encoding='ascii')
    for name in ('dasmzlg.mac', 'dasmtdl.mac'):
        text = text.replace('INCLUDE\t'+name.upper(), (folder / name).read_text(encoding='ascii'))
    if not reference:
        text = text.replace('INCLUDE dasmsafe.inc',
                            (ROOT/'src/utilities/common/dasmsafe.inc').read_text())
        for include in ('dasmrebase.inc','printnum.inc','dasmsymbol.inc','dasmfile.inc','dasmprolog.inc','zsm4words.inc','duselect.inc','filespec.inc'):
            text=text.replace('INCLUDE '+include,(ROOT/'src/utilities/common'/include).read_text())
        text=text.replace('\tORG\t$/100H*100H+100H',
                          ' REPT 100H-($ MOD 100H)\n DB 0FFH\n ENDM')
    # Both assemblers need the workspace EQU dependency chain after ENDALL.
    definitions=[]
    def move(match):
        definitions.append(match[0])
        return ''
    text=re.sub(r'(?m)^(?:CTLTBL|SYMTAB|INITOFF|COMTBL|D_BIN|D_BIN_LIMIT|D_CMT_LIMIT|D_STAGE|D_MEM_END)\s+EQU[^\n]*\n',move,text)
    text=re.sub(r'(?m)^\s*END\s*$', '\n'+''.join(definitions)+'\n END\n',text)
    return text


def validate_native_identifiers(text):
    """Pinned ZSM4 IDMAX is 15; reject ambiguous internal spellings."""
    names=re.findall(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?::|\s+EQU\b|\s+MACRO\b)',text,re.M|re.I)
    groups={}
    for name in names:groups.setdefault(name.upper()[:15],set()).add(name.upper())
    collisions=[sorted(names) for names in groups.values() if len(names)>1]
    if collisions:raise ValueError('ZSM4 significant-name collisions: '+repr(collisions))


def build(assembler, output, reference=False):
    output.mkdir(parents=True, exist_ok=True)
    name = 'dasm-reference' if reference else 'dasm'
    text = source(reference)
    validate_native_identifiers(text)
    prepared = output / (name+'.mac')
    prepared.write_text(text, encoding='ascii')
    binary = output / (name+'.bin')
    subprocess.run([str(assembler), '-e32', '-fb', '-o'+str(binary.resolve()),
                    '-l'+str((output/(name+'.lst')).resolve()), str(prepared.resolve())], check=True)
    image = binary.read_bytes()
    if image[:256] == bytes(256):
        image = image[256:]
    assert image and len(image) <= 0xD400
    (output / ('DASMREF.COM' if reference else 'DASM.COM')).write_bytes(image)
    report = {'kind': 'reference' if reference else 'adaptation', 'bytes': len(image),
              'sha256': hashlib.sha256(image).hexdigest(),
              'prepared_source_sha256': hashlib.sha256(prepared.read_bytes()).hexdigest()}
    (output/(name+'-build.json')).write_text(json.dumps(report, indent=2)+'\n')
    return image


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler', type=Path, default=Path.home()/'bin/z80asm')
    p.add_argument('--output', type=Path, default=ROOT/'build/dasm-development')
    p.add_argument('--reference', action='store_true')
    a = p.parse_args()
    print(len(build(a.assembler, a.output, a.reference)), 'bytes')
