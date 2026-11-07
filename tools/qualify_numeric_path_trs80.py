#!/usr/bin/env python3
"""Prepare disposable PATH startup media and verify the submitted run in trs80gp."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

def marker(text):
    return bytes.fromhex('110901 0e09 cd0500 c9') + text.encode() + b'\r\n$'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', choices=('2', '4'), required=True)
    parser.add_argument('--build', type=Path, required=True, help='prepared target build/')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--emulator', type=Path)
    args = parser.parse_args()
    build = args.build.resolve()
    work = args.output.resolve()
    work.mkdir(parents=True, exist_ok=False)
    m2 = args.model == '2'
    if m2:
        # Use the port snapshot responsible for these build products.
        sys.path.insert(0, str(build.parent / 'tools'))
    from run_trs80_command import DEFAULT_EMULATOR
    from startup_record import build as startup
    from test_z80pack_submit_xsub import input_probe
    from trs80gp_launch import run
    maximum = 57344 if m2 else 54272
    drive = 'B' if m2 else 'A'
    search = f'{drive}3: . {drive}0:'
    xsub = 'B0:XSUB B0:' if m2 else 'A0:XSUB'
    sequence = [f'A0:PATH {search}', '5:', 'WHICH', 'FIT', 'BIG', 'WHICH',
                xsub, 'INPUT', 'BATCHFULL', f'{drive}0:WHICH', 'A0:PATH']
    if m2:
        sequence.insert(0, 'PATH')
        sequence.extend(['A0:PATH A9:', 'A0:PATH /DEFAULT', 'PATH', 'B0:PTDONE'])
    fixtures = [
        ('PTEST.SUB', ('\r\n'.join(sequence)+'\r\n\x1a').encode(), 0),
        ('WHICH.COM', marker(f'FIRST IMAGE {drive}3'), 3),
        ('WHICH.COM', marker(f'SECOND IMAGE {drive}0'), 0),
        ('FIT.COM', marker(f'FIT {maximum} OK').ljust(maximum, b'X'), 3),
        ('BIG.COM', marker('WRONG OVERSIZE EXECUTION').ljust(maximum+128, b'X'), 3),
        ('BIG.COM', marker('WRONG FALLBACK EXECUTION'), 0),
        ('INPUT.COM', input_probe(work), 3),
    ]
    def built(folder, name):
        return (name, (build/folder/name).read_bytes(), 0)

    if m2:
        from model2_media import image
        # Keep the assembled System disk intact. SUBMIT writes its queue on a
        # disposable copy. All test programs and the script come from drive B.
        disk = work/'Model-II-PATH.imd'
        shutil.copyfile(build/'trs80m2/Model-II-System-candidate.imd', disk)
        subprocess.run([sys.executable, '-B', build.parent/'tools/build_batch.py'],
                       env=dict(os.environ, BETTERCPM_BUILD_CONTEXT=str(build/'profile/context.json')),
                       check=True)
        batch = [built('utilities', 'SUBMIT.COM'), built('utilities', 'XSUB.COM'),
                 built('rsx', 'BATCHIO.RSX'), ('PTDONE.COM', marker('PACKAGED PATH DONE'), 0)]
        companion = work/'Model-II-PATH-Fixtures.imd'
        companion.write_bytes(image(bytes(160*128), batch + fixtures, bootable=False))
    else:
        from add_cpm_file_to_dmk import extract_raw
        from build_montezuma_extended_790k import build as dmk
        from system_layout import LAYOUT
        raw = extract_raw((build/'trs80/BetterCPM-Extended-80T-DS-System-790K.dmk').read_bytes())
        raw[128:384] = startup('SUBMIT PTEST', system_base=LAYOUT['SYSTEM'])
        from build_trs80_boot import FILESYSTEM_FIRST_SECTOR, SECTOR_SIZE, install_files
        directory = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE
        raw[directory:] = bytes([0xe5]) * (len(raw)-directory)
        common = [built('utilities', 'PATH.COM'), built('utilities', 'SUBMIT.COM'),
                  built('utilities', 'XSUB.COM'), built('cpx', 'RCP.CPX'),
                  built('rsx', 'BATCHIO.RSX'), built('system', 'R3PACK.RSX'),
                  built('system', 'R3CACHE.RSX')]
        install_files(raw, common + fixtures)
        disk = work/'Model4-PATH.dmk'
        disk.write_bytes(dmk(raw))

    expected = [f'FIRST IMAGE {drive}3', f'FIT {maximum} OK', 'FILE WILL NOT FIT',
                'INPUT OK', f'SECOND IMAGE {drive}0', f'PATH: {search}']
    command = [str(args.emulator or DEFAULT_EMULATOR), '-m'+args.model, '-batch', '-turbo', '-d0', str(disk),
               '-itime', '120000']
    if m2:
        command.extend(['-d1', str(companion), '-iw', 'A0>', '-i', 'B0:SUBMIT B:PTEST\r'])
        expected.insert(0, 'PATH: . A0:')
        expected.extend(['PATH: A9:', 'PATH: . A0:', 'PACKAGED PATH DONE'])
    for message in expected:
        command.extend(['-iw', message, '-id', '120', '-it'])
    command.append('-ix')
    report = {'model': args.model, 'disk_sha256': hashlib.sha256(disk.read_bytes()).hexdigest(),
              'expected': expected, 'command': command, 'result': 'prepared'}
    receipt = work/'path-run.json'
    receipt.write_text(json.dumps(report, indent=2)+'\n')
    if args.prepare_only:
        print(disk)
        return
    run(command, cwd=work, timeout=600)
    for n, message in enumerate(expected):
        screen = bytes(c & 127 for c in (work/f'trs80-text-{n}.bin').read_bytes()[:1920])
        if message.encode() not in screen or b'WRONG ' in screen or b'INPUT FAILED' in screen:
            raise RuntimeError(f'capture {n} failed for {message!r}')
    report['result'] = 'PASS'
    receipt.write_text(json.dumps(report, indent=2)+'\n')
    print(f'PASS Model {args.model} PATH and batch input')


if __name__ == '__main__':
    main()
