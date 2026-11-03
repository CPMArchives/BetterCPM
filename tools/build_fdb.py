#!/usr/bin/env python3
"""Build the native FDB catalogue workbench from specification 209."""
import argparse
import binascii
import zlib
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
    validator, runtime = validator.split('; Convert a catalogue/bootstrap', 1)
    runtime = '; Convert a catalogue/bootstrap' + runtime
    fixed_limit = 'LD HL,FDFLIM\n'
    if validator.count(fixed_limit) != 1:
        raise ValueError('check the shared validator workspace limit')
    source = '\n'.join([
        (UTILITIES/'fdb.mac').read_text(),
        (UTILITIES/'disk/fdbsession.inc').read_text(),
        validator.replace(fixed_limit, 'LD HL,(ARENALIMIT)\n').replace(
            '        LD (FDBOWNBASE),HL', '        LD A,(VIEWACTIVE)\n        OR A\n        JR Z,VIEWOWNNORMAL\n        LD HL,IMPORTBUF\n        LD (FDBOWNBASE),HL\n        JR FDBOWNFIT\nVIEWOWNNORMAL:LD (FDBOWNBASE),HL'),
        'STACK: DS 512\nSTACKTOP:\nIMAGEEND:',
        '        .PHASE 0B900H\nEDITORBASE:',
        (UTILITIES/'disk/fdbdrive.inc').read_text(),
        runtime,
        (UTILITIES/'disk/fdbexchange.inc').read_text(),
        (UTILITIES/'disk/fdbviewload.inc').read_text(),
        (UTILITIES/'common/monitorconsole.inc').read_text(),
        'EDITOREND:\n        .DEPHASE\n        END\n',
    ])
    token = zlib.crc32(source.encode()).to_bytes(4,'little')
    source = source.replace('VIEWTOKEN:DB 0,0,0,0', 'VIEWTOKEN:DB '+','.join(map(str,token)))
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
    # Compile the read-only viewer against this exact resident symbol table.
    symbols = {}
    for value, label in re.findall(r'^([0-9a-f]{4}).*?\b([A-Z][A-Z0-9_]*):', layout, re.M|re.I):
        symbols[label.upper()] = int(value,16)
    view = (UTILITIES/'disk/fdbview.inc').read_text()
    labels = set(re.findall(r'^([A-Z][A-Z0-9_]*):', view, re.M))
    links = 'WORKBUF EQU 05B00H\nBDOS EQU 5\nIMPORTBUF EQU 03600H\nFDFRAM EQU 08000H\n' + ''.join(f'{label} EQU 0{value:04X}H\n' for label,value in symbols.items() if label not in labels)
    with tempfile.TemporaryDirectory(prefix='fdb-view-') as temp:
        source = Path(temp)/'view.mac'
        source.write_text('        ASEG\n        ORG 0A500H\n'+links+'EDITBIND EQU CURB\n'+'        JP VIEWENTRY\n        DB '+','.join(map(str,token))+'\n        DW 0\n'+view+'\n        END\n')
        subprocess.run([str(assembler),'-e32','-fb',f'-o{destination / "FDBVIEW.OVL"}',f'-l{destination / "view.lst"}',str(source)],check=True)
    overlay = (destination/'FDBVIEW.OVL').read_bytes()
    if overlay[:0xa500] == bytes(0xa500):
        overlay=overlay[0xa500:]
    if len(overlay)>0x1400:
        raise ValueError('FDB viewer exceeds its overlay arena')
    overlay = bytearray(overlay)
    overlay.extend(bytes((-len(overlay)) % 128))
    overlay[7:9] = binascii.crc_hqx(overlay[9:], 0xffff).to_bytes(2,'little')
    (destination/'FDBVIEW.OVL').write_bytes(overlay)
    return image


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT/'build/fdb')
    print(f'{len(build(destination=parser.parse_args().output_dir))} bytes')
