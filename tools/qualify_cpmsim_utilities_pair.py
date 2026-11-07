#!/usr/bin/env python3
"""Run submitted Function 10 input using the shipped cpmsim System and Utilities pair."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from build_z80pack_image import DEFAULT_FORMAT, disk_definition
from fdf_format import select_fdf
from test_z80pack_submit_xsub import input_probe
from test_z80pack_sysgen_install import session


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True, help='z80pack System generation directory')
    parser.add_argument('--utilities', type=Path, required=True, help='cpmsim Utilities disk image')
    parser.add_argument('--simulator', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    system = json.loads((args.system/'report.json').read_text())
    utilities = json.loads(Path(str(args.utilities)+'.json').read_text())
    image = args.system/system['image']
    if (system['profile'] != 'cpmsim-fullram' or utilities['profile'] != system['profile'] or
            utilities['compatibility_id'] != system['compatibility_id']):
        raise ValueError('System and Utilities disks must have matching full-RAM identities')
    for path, report in ((image, system), (args.utilities, utilities)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != report['sha256']:
            raise ValueError(f'{path}: image differs from its build report')

    out = args.output.resolve()
    disks = out/'disks'
    disks.mkdir(parents=True)
    root = Path(__file__).resolve().parents[1]
    (out/'diskdefs').write_text(disk_definition(select_fdf(root/'metadata/DISK.FDF', DEFAULT_FORMAT)))
    for drive in 'abcd':
        shutil.copy2(args.utilities if drive == 'b' else image, disks/f'drive{drive}.dsk')
    batch = b'B0:XSUB B0:\r\nINPUT\r\nBATCHFULL\r\nRSX UNLOAD BATCHIO\r\nRSX LIST\r\n\x1a'
    for name, data in [('INPUT.COM', input_probe(out)), ('PAIR.SUB', batch)]:
        path = out/name
        path.write_bytes(data)
        subprocess.run(['cpmcp', '-f', 'bettercpm-default', disks/'drivea.dsk', path, '0:'+name],
                       cwd=out, check=True)
    expected = system['validation']['acceptance']['unloaded_tpa']
    commands = [(b'SUBMIT PAIR\r', b'No RSXs loaded', 45),
                (b'STAT MEM\r', f'Maximum loadable COM: {expected} bytes'.encode(), 35)]
    transcript = session(args.simulator.resolve(), disks, commands, out/'transcript.bin')
    if b'INPUT OK' not in transcript or b'INPUT FAILED' in transcript or b'Xsub Load Error' in transcript:
        raise ValueError('BATCHIO failed to supply the submitted input')
    result = {'system_sha256': system['sha256'], 'utilities_sha256': utilities['sha256'],
              'compatibility_id': system['compatibility_id'], 'submitted_input': 'PASS',
              'unload': 'PASS', 'recovered_tpa': expected}
    (out/'results.json').write_text(json.dumps(result, indent=2)+'\n')
    print('PASS checked System and Utilities pair')


if __name__ == '__main__':
    main()
