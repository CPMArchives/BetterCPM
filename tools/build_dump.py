#!/usr/bin/env python3
"""Build the enhanced read-only DUMP utility and sealed DRI compatibility path."""
import argparse
import hashlib
from pathlib import Path
from build_ccp import assemble
from utility_versions import identities
ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build/utilities'


def version_text():
    version, build = identities()['DUMP']
    return (f'DUMP {version} (Build {build:03d})\r\n  - - -\r\n'
            ' | BetterCP/M Utilities\r\n | Hexadecimal File Display\r\n')


def expanded_source():
    title = version_text().split('\r\n')[0]
    text = f"UV_TEXT: DB '{title}',13,10\n"
    text += "        DB '  - - -',13,10,' | BetterCP/M Utilities',13,10\n"
    text += "        DB ' | Hexadecimal File Display',13,10,'$'\n"
    query = (ROOT/'src/utilities/common/version.inc').read_text()
    text += query[query.index('\nUV_QUERY:') + 1:]
    source = (ROOT/'src/utilities/dump.mac').read_text().replace('; @dump-version@', text)
    common = ROOT/'src/utilities/common'
    for part in ('parser', 'io', 'view', 'search', 'bare'):
        name = 'dumpparse.inc' if part == 'parser' else 'dump'+part+'.inc'
        source = source.replace('; @dump-'+part+'@', (common/name).read_text())
    from shared_ui import input_source
    source = source.replace('; @ui-input@', input_source())
    source = source.replace('; @ui-screen@', (common/'ui/screen.inc').read_text())
    selector = (common/'duselect.inc').read_text() + '\n' + (common/'filespec.inc').read_text()
    return source.replace('; @dump-selector@', selector)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler', type=Path, default=Path.home()/'bin/z80asm')
    a = p.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    source = expanded_source().replace('        CSEG\n', '        ASEG\n').replace('        .PHASE  0103H\n', '        ORG     0103H\n').replace('        .DEPHASE\n', '')
    raw = assemble(a.assembler, source, BUILD/'dump.bin', BUILD/'dump.lst', 0x103)
    data = b'\xc3\x03\x01' + raw
    (BUILD/'DUMP.COM').write_bytes(data)
    print(f'DUMP.COM: {len(data)} bytes; SHA-256 {hashlib.sha256(data).hexdigest()}')


if __name__ == '__main__':
    main()
