#!/usr/bin/env python3
"""Build SEARCH.COM and prepared native source without changing disk images."""
import argparse
from pathlib import Path
import hashlib
import json
import re
from build_ccp import assemble
from component_build import recorded_build
from component_identity import identification, title
from utility_versions import identities, display_development
from search_source import development_source, ROOT


def assembly_string(label, text):
    lines = [label+':']
    lines += [("        DB '"+line.replace("'", "''")+"',13,10")
              if line else "        DB 13,10" for line in text.splitlines()]
    return '\n'.join(lines)+ '\n        DB 0\n'


def expanded_source():
    version, revision = identities()['SEARCH']
    dev = display_development('utility:SEARCH')
    identity = identification('SEARCH', version, revision, 'File Content Search', development=dev)
    help_text = (title('SEARCH', version, revision, development=dev) +
                 '\n  - - -\n | File Content Search\n |\n'
                 ' |   Usage: SEARCH [options] "pattern" filespec [options]\n\n'
                 '   Options:\n'
                 '     /NOHEX     Disable HEX interpretation.\n'
                 '     /NOTEXT    Disable TEXT; require valid HEX.\n'
                 '     /NOCASE    Ignore ASCII letter case in TEXT.\n'
                 '     /P         Page results forward.\n\n'
                 '     /HELP      Display this help.\n'
                 '     /VER       Display utility identification.\n')
    text = (ROOT/'src/utilities/search.mac').read_text()
    text = text.replace('; @search-modules@', development_source())
    text = text.replace('; @search-display@', (ROOT/'src/utilities/search/display.inc').read_text())
    return text.replace('; @search-identity@', assembly_string('DVERSION', identity)+
                        assembly_string('DHELPTXT', help_text))


def native_source():
    text=re.sub(r'(?m)^(?:(\w+:)\s*)? +DS +([0-9]+) *$',
                r'\1\n        REPT \2\n        DB 0FFH\n        ENDM',expanded_source())
    return text.replace('\n','\r\n').encode('ascii')+b'\x1a'


@recorded_build('utility:SEARCH')
def build(assembler, destination):
    source = expanded_source().replace('        CSEG\n', '        ASEG\n').replace(
        '        .PHASE 0103H\n', '        ORG 0103H\n').replace('        .DEPHASE\n', '')
    raw = assemble(assembler, source, destination/'search.bin', destination/'search.lst', 0x103)
    data = b'\xc3\x03\x01'+raw
    (destination/'SEARCH.COM').write_bytes(data)
    native=native_source()
    (destination/'SEARCH-NATIVE.MAC').write_bytes(native)
    (destination/'SEARCH-native.json').write_text(json.dumps({
        'binary_sha256':hashlib.sha256(data).hexdigest(),
        'native_source_sha256':hashlib.sha256(native).hexdigest()},indent=2)+'\n')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler', type=Path, default=Path.home()/'bin/z80asm')
    args = parser.parse_args()
    data = build(args.assembler, ROOT/'build/utilities')
    print(f'SEARCH.COM: {len(data)} bytes; SHA-256 {hashlib.sha256(data).hexdigest()}')


if __name__ == '__main__':
    main()
