#!/usr/bin/env python3
"""Build the CRC development candidate and prepared native Z80 source."""
from pathlib import Path
import argparse
import hashlib
import json
import re
from build_ccp import assemble
from component_build import recorded_build
from component_identity import identification, title
from utility_versions import identities, display_development
from search_source import selector_source

ROOT = Path(__file__).resolve().parents[1]


def expanded_source():
    source = (ROOT/'src/utilities/crc.mac').read_text()
    for name in ('command', 'traverse', 'render', 'lists', 'output', 'algorithms', 'support'):
        source = source.replace('; @'+name+'@', (ROOT/f'src/utilities/crc/{name}.inc').read_text())
    source = source.replace('; @list-parser@', (ROOT/'src/utilities/crc/list-parser.inc').read_text())
    version, revision = identities()['CRCKSUM']
    development = display_development('utility:CRCKSUM')
    identity = identification('CRCKSUM', version, revision, 'File Integrity Checking', development=development)
    help_text = (title('CRCKSUM', version, revision, development=development)+
                 '\n  - - -\n | File Integrity Checking\n |\n'
                 ' |   Usage: CRCKSUM [options] [filespec ...] [options]\n\n'
                 '   Options:\n'
                 '     /CRCK       Historical CRCK.\n'
                 '     /CRCK5      Corrected CRCK.\n'
                 '     /CHEK       CHEK (CRC-16/XMODEM).\n'
                 '     /CRC32      CRC-32/ISO-HDLC.\n'
                 '     /SUM8       Sum bytes modulo 256.\n'
                 '     /SUM16      Sum bytes modulo 65536.\n'
                 '     /KERM6      Kermit 6-bit checksum.\n'
                 '     /KERM12     Kermit 12-bit checksum.\n'
                 '     /FILE=name  Write a master list.\n'
                 '     /LOCAL=name Write a list in each target DU.\n'
                 '     /LEGACY     Use historical CRCKLIST format; force CRCK.\n'
                 '     /CHECK[=name] Verify against a list in each target DU.\n'
                 '     /40         Stacked screen display.\n\n'
                 '     /HELP       Display this help.\n'
                 '     /VER        Display utility identification.\n')
    def assembly_string(label, value):
        return label+':\n'+''.join(("        DB '"+line.replace("'", "''")+"',13,10\n")
                                    if line else '        DB 13,10\n'
                                    for line in value.replace('\r\n', '\n').splitlines())+'        DB 0\n'
    source = source.replace('; @identity@', assembly_string('VERSIONT', identity)+
                            assembly_string('HELPTEXT', help_text))
    return source.replace('; @selectors@', selector_source())


@recorded_build('utility:CRCKSUM')
def build(assembler, destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    text = expanded_source()
    cross = text.replace('        CSEG\n', '        ASEG\n').replace(
        '        .PHASE 0103H\n', '        ORG 0103H\n').replace('        .DEPHASE\n', '')
    data = b'\xc3\x03\x01'+assemble(assembler, cross, destination/'crc.bin', destination/'crc.lst', 0x103)
    (destination/'CRCKSUM.COM').write_bytes(data)
    native = re.sub(r'(?m)^(?:(\w+:)\s*)? +DS +([0-9]+) *$',
                    r'\1\n        REPT \2\n        DB 0FFH\n        ENDM', text)
    prepared = native.replace('\n', '\r\n').encode('ascii')+b'\x1a'
    (destination/'CRCKSUM-NATIVE.MAC').write_bytes(prepared)
    (destination/'CRCKSUM-native.json').write_text(json.dumps({
        'binary_sha256': hashlib.sha256(data).hexdigest(),
        'native_source_sha256': hashlib.sha256(prepared).hexdigest()}, indent=2)+'\n')
    return data


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler', type=Path, default=Path.home()/'bin/z80asm')
    a = p.parse_args()
    image = build(a.assembler, ROOT/'build/utilities')
    print(f'CRCKSUM.COM: {len(image)} bytes; SHA-256 {hashlib.sha256(image).hexdigest()}')
