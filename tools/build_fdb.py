#!/usr/bin/env python3
"""Build the native FDB catalogue workbench from specification 209."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile

from checked_carriers import selected_contract

ROOT = Path(__file__).resolve().parents[1]
UTILITIES = ROOT/'src/utilities'


def build(assembler=Path.home()/'bin/z80asm', destination=ROOT/'build/fdb'):
    selected_contract(assembler)
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    # CONFIG has a fixed reader workspace. FDB uses the same validator, with
    # a lower ceiling while its interactive editor is resident above the pool.
    validator = 'FDBVALID:' + (UTILITIES/'disk/fdbread.inc').read_text().split('FDBVALID:', 1)[1]
    fixed_limit = 'LD HL,FDFLIM\n'
    if validator.count(fixed_limit) != 1:
        raise ValueError('check the shared validator workspace limit')
    source = '\n'.join([
        (UTILITIES/'fdb.mac').read_text(),
        (UTILITIES/'disk/fdbsession.inc').read_text(),
        validator.replace(fixed_limit, 'LD HL,(ARENALIMIT)\n'),
        'STACK: DS 512\nSTACKTOP:\nIMAGEEND:',
        '        .PHASE 0BD00H\nEDITORBASE:',
        (UTILITIES/'disk/fdbdrive.inc').read_text(),
        (UTILITIES/'common/monitorconsole.inc').read_text(),
        'EDITOREND:\n        .DEPHASE\n        END\n',
    ])
    output = destination/'FDB.COM'
    listing = destination/'fdb.lst'
    with tempfile.TemporaryDirectory(prefix='fdb-build-') as temporary:
        staged = Path(temporary)/'fdb.mac'
        staged.write_text(source)
        subprocess.run([str(assembler), '-e32', '-fb', f'-o{output}', f'-l{listing}',
                        str(staged)], check=True)
    image = output.read_bytes()
    if image[:256] == bytes(256):
        image = image[256:]
        output.write_bytes(image)
    layout = listing.read_text()
    def address(label):
        return int(re.search(rf'^([0-9a-f]{{4}}).*?\b{label}:', layout, re.M | re.I)[1], 16)
    if address('IMAGEEND') > 0x3600 or address('EDITOREND') > 0xd400:
        raise ValueError('FDB editor exceeds the session memory layout')
    return image


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT/'build/fdb')
    print(f'{len(build(destination=parser.parse_args().output_dir))} bytes')
