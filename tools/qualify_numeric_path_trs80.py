#!/usr/bin/env python3
"""Prepare disposable PATH startup media and verify the submitted run in trs80gp."""
import argparse
import hashlib
import json
from pathlib import Path
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
    sequence = ('A0:PATH A3: . A0:', '5:', 'WHICH', 'FIT', 'BIG', 'WHICH',
                'A0:XSUB', 'INPUT', 'BATCHFULL', 'A0:WHICH', 'A0:PATH')
    fixtures = [
        ('PTEST.SUB', ('\r\n'.join(sequence)+'\r\n\x1a').encode(), 0),
        ('WHICH.COM', marker('FIRST IMAGE A3'), 3),
        ('WHICH.COM', marker('SECOND IMAGE A0'), 0),
        ('FIT.COM', marker(f'FIT {maximum} OK').ljust(maximum, b'X'), 3),
        ('BIG.COM', marker('WRONG OVERSIZE EXECUTION').ljust(maximum+128, b'X'), 3),
        ('BIG.COM', marker('WRONG FALLBACK EXECUTION'), 0),
        ('INPUT.COM', input_probe(work), 3),
    ]
    common = [(name, (build/folder/name).read_bytes(), 0) for folder, name in
              [('utilities','PATH.COM'), ('utilities','SUBMIT.COM'), ('utilities','XSUB.COM'),
               ('cpx','RCP.CPX'), ('rsx','BATCHIO.RSX'), ('system','R3PACK.RSX'),
               ('system','R3CACHE.RSX')]]
    if m2:
        # The port owns physical IMD layout and bootstrap placement.
        from model2_media import image
        package = build/'trs80m2/checked-package.json'
        base = json.loads(package.read_text())['system_base']
        tracks = bytearray((build/'trs80m2/system-tracks.bin').read_bytes())
        tracks[128:384] = startup('SUBMIT PTEST', system_base=base)
        disk = work/'Model-II-PATH.imd'
        disk.write_bytes(image(tracks, common + fixtures))
    else:
        from add_cpm_file_to_dmk import extract_raw
        from build_montezuma_extended_790k import build as dmk
        from system_layout import LAYOUT
        raw = extract_raw((build/'trs80/BetterCPM-Extended-80T-DS-System-790K.dmk').read_bytes())
        raw[128:384] = startup('SUBMIT PTEST', system_base=LAYOUT['SYSTEM'])
        from build_trs80_boot import FILESYSTEM_FIRST_SECTOR, SECTOR_SIZE, install_files
        directory = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE
        raw[directory:] = bytes([0xe5]) * (len(raw)-directory)
        install_files(raw, common + fixtures)
        disk = work/'Model4-PATH.dmk'
        disk.write_bytes(dmk(raw))

    expected = ['FIRST IMAGE A3', f'FIT {maximum} OK', 'FILE WILL NOT FIT',
                'INPUT OK', 'SECOND IMAGE A0', 'PATH: A3: . A0:']
    command = [str(args.emulator or DEFAULT_EMULATOR), '-m'+args.model, '-batch', '-turbo', '-d0', str(disk),
               '-itime', '120000']
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
