#!/usr/bin/env python3
"""Build the DRI-compatible Z80 DUMP utility with its visual /VER identity."""
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
    return (ROOT/'src/utilities/dump.mac').read_text().replace('; @dump-version@', text)


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
