#!/usr/bin/env python3
"""Prepare and cross-build TED development sources, never a distribution TED.COM.

Flatten the upstream relocatable modules deterministically into one absolute
module. Both assemblers consume these instructions; no instruction-byte patching
or host-generated machine code is involved. Native preparation only materializes
reserved storage (the same convention as the DASM native build).
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
MODULES = ('termdef', 'main', 'fileio', 'scrn', 'cmds', 'cpmio')
TOKEN = re.compile(r"'(?:[^']|'')*'|;.*|[A-Za-z_$?][A-Za-z0-9_$?]*")


def verify_reference():
    base = ROOT / 'third_party/ted'
    manifest = json.loads((base/'provenance.json').read_text())
    archive = (base/manifest['archive']).read_bytes()
    assert hashlib.sha256(archive).hexdigest() == manifest['archive_sha256']
    archived = {}
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        for member in source:
            if member.isfile():
                archived[member.name] = source.extractfile(member).read()
    assert set(archived) == set(manifest['files'])
    for name, expected in manifest['files'].items():
        data = (base/name).read_bytes()
        assert archived[name] == data, name
        assert hashlib.sha256(data).hexdigest() == expected, name
    return manifest


def source(reference=False):
    """Retain each module's symbol scope, then lay out code followed by data."""
    verify_reference()
    base = ROOT / ('third_party/ted' if reference else 'src/utilities/ted')
    common = (base/'ted.inc').read_text(encoding='ascii')
    code, data = [], []
    symbol_map = {}
    for index, module in enumerate(MODULES):
        text = (base/(module+'.mac')).read_text(encoding='ascii')
        exported = {'START', '$MEMRY'}
        for match in re.finditer(r'^\s*public\s+([^;\n]+)', text, re.M|re.I):
            exported.update(x.strip().upper() for x in match[1].split(','))
        labels = re.findall(r'^([A-Za-z_$?][A-Za-z0-9_$?]*)(?::|\s+equ\b)', text, re.M|re.I)
        local = {name.upper(): f'T{index}L{serial}' for serial, name in enumerate(labels)
                 if name.upper() not in exported}
        symbol_map[module] = local
        def rename(match):
            value = match[0]
            return local.get(value.upper(), value) if value[0] not in "';" else value
        text = TOKEN.sub(rename, text)
        section = code
        for line in text.splitlines():
            bare = line.split(';', 1)[0].strip()
            directive = bare.split(None, 1)[0].upper() if bare else ''
            if directive in ('.Z80', 'TITLE', 'SUBTTL', 'INCLUDE', 'PUBLIC', 'EXTRN', 'END'):
                continue
            if directive in ('CSEG', 'DSEG'):
                section = code if directive == 'CSEG' else data
                continue
            if directive == 'ORG':
                assert module == 'termdef'
                line = ' REPT (103H+('+bare.split(None, 1)[1]+'))-$\n DB 0FFH\n ENDM'
            # LINK normally initializes this distinguished public word to the
            # first free address. Make the same dependency explicit for ASEG.
            if re.match(r'^\$MEMRY:', line):
                line = '$MEMRY: DW TED_END'
            section.append(line.replace('START::', 'START:'))
    prepared = ' ASEG\n ORG 100H\n JP START\n'+common+'\n'+'\n'.join(code+data)+'\nTED_END EQU $\n END\n'
    return native_source(prepared), symbol_map


def native_source(text):
    # ZSM4/LINK absolute sections must contain the same bytes for DS reserves.
    return re.sub(r'(?mi)^([^;\n]*?)(?:\bDS\b)\s+([^;\n]+)(?:;[^\n]*)?$',
                  r'\1\n REPT \2\n DB 0\n ENDM', text)


def build(assembler, output, reference=False):
    output.mkdir(parents=True, exist_ok=True)
    text, symbols = source(reference)
    prepared = output/'TEDDEV.MAC'
    prepared.write_text(text, encoding='ascii')
    (output/'TEDNAT.MAC').write_bytes(native_source(text).replace('\n', '\r\n').encode('ascii')+b'\x1a')
    subprocess.run([str(assembler), '-e32', '-fb', '-o'+str((output/'TEDDEV.BIN').resolve()),
                    '-l'+str((output/'TEDDEV.LST').resolve()), str(prepared.resolve())], check=True)
    image = (output/'TEDDEV.BIN').read_bytes()
    if image[:256] == bytes(256):
        image = image[256:]
    (output/'TEDDEV.COM').write_bytes(image)
    report = {'status': 'DEVELOPMENT_ONLY', 'release_qualified': False,
              'reference': reference, 'bytes': len(image), 'sha256': hashlib.sha256(image).hexdigest(),
              'prepared_source_sha256': hashlib.sha256(prepared.read_bytes()).hexdigest(),
              'local_symbols': symbols}
    (output/'ted-build.json').write_text(json.dumps(report, indent=2)+'\n')
    return image


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler', type=Path, default=Path.home()/'bin/z80asm')
    p.add_argument('--output', type=Path, default=ROOT/'build/ted-development')
    p.add_argument('--reference', action='store_true')
    a = p.parse_args()
    print(len(build(a.assembler, a.output, a.reference)), 'development bytes')
