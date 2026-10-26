#!/usr/bin/env python3
"""Build the streaming COMPARE utility; does not promote it to release media."""
import argparse
import hashlib
from pathlib import Path
from build_ccp import assemble
from component_identity import identification
from component_build import recorded_build
from utility_versions import identities, display_development
ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build/utilities'


def version_text():
    version, revision = identities()['COMPARE']
    return identification('COMPARE', version, revision, 'Binary File Comparison', development=display_development('utility:COMPARE'))


def expanded_source():
    text = (ROOT / 'src/utilities/compare.mac').read_text()
    common = ROOT / 'src/utilities/common'
    for part in ('parser', 'io', 'display'):
        filename = 'compareparse.inc' if part == 'parser' else 'compare'+part+'.inc'
        text = text.replace('; @compare-'+part+'@', (common / filename).read_text())
    selector = (common / 'duselect.inc').read_text() + '\n' + (common / 'filespec.inc').read_text()
    text = text.replace('; @compare-selector@', selector)
    version = 'VERSIONTEXT:\n' + ''.join("        DB '"+line+"',13,10\n" for line in version_text().splitlines()) + '        DB 0\n'
    return text.replace('; @compare-version@', version)


@recorded_build('utility:COMPARE')
def build(assembler, destination):
    source = expanded_source().replace('        CSEG\n', '        ASEG\n').replace('        .PHASE 0103H\n', '        ORG 0103H\n').replace('        .DEPHASE\n', '')
    raw = assemble(assembler, source, destination/'compare.bin', destination/'compare.lst', 0x103)
    data = b'\xc3\x03\x01' + raw
    (destination/'COMPARE.COM').write_bytes(data)
    return data


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler', type=Path, default=Path.home()/'bin/z80asm')
    a = p.parse_args()
    data = build(a.assembler, BUILD)
    print(f'COMPARE.COM: {len(data)} bytes; SHA-256 {hashlib.sha256(data).hexdigest()}')


if __name__ == '__main__':
    main()
