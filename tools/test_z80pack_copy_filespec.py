#!/usr/bin/env python3
"""Prove COPY rejects truncated-name aliases before native file operations."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from test_disk_utilities import ROOT
from test_z80pack_sysgen_install import session


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--image-dir', type=Path, default=ROOT / 'build/z80pack-iobyte-qualified')
    args = parser.parse_args()
    report = args.report.resolve(); report.mkdir(parents=True, exist_ok=False)
    work = report / 'runtime'; work.mkdir()
    shutil.copytree(args.image_dir / 'disks', work / 'disks')
    shutil.copy2(args.image_dir / 'diskdefs', work / 'diskdefs')
    a, b = (work / 'disks' / ('drive' + letter + '.dsk') for letter in 'ab')
    def cpm(tool, disk, *arguments):
        subprocess.run([tool, '-T', 'raw', '-f', 'bettercpm-default', str(disk), *map(str, arguments)], cwd=work, check=True)
    cpm('cpmrm', a, '0:copy.com', '0:rcp.cpx', '0:bdosprb.com', '0:rsx2tst.com')
    for name, path in [('COPY.COM', ROOT / 'build/utilities/COPY.COM'),
                       ('RCP.CPX', ROOT / 'build/cpx/RCP.CPX')]:
        shutil.copy2(path, report / name)
        cpm('cpmcp', a, path, '0:' + name)
    b.write_bytes(bytes([0xe5]) * len(b.read_bytes()))
    fixture = report / 'payload.dat'; fixture.write_bytes(bytes(range(128)))
    for name in ('ABCDEFGH.COM', 'SHORT.DAT'):
        cpm('cpmcp', b, fixture, '0:' + name)
    simulator = Path.home() / 'projects/git/z80pack/cpmsim/cpmsim'
    cases = ['COPY B:ABCDEFGHI.COM B:WRONG.DAT', 'COPY B:SHORT.DAT B:LONGNAME9.DAT',
             'COPY B:SHORT.DAT B:NEW.ABCD', 'COPY B:.DAT B:WRONG.DAT',
             'COPY B:F*X.DAT B:WRONG.DAT',
             'COPY B:WRONG.DAT:=B:SHORT.DAT', 'COPY =B:SHORT.DAT',
             'COPY B:WRONG.DAT=', 'COPY B:WRONG.DAT==B:SHORT.DAT']
    observations = []
    for profile in ('cpx', 'transient'):
        if profile == 'cpx':
            cpm('cpmrm', a, '0:copy.com')
        else:
            cpm('cpmcp', a, report / 'COPY.COM', '0:copy.com')
        for number, command in enumerate(cases):
            before = {p.name: p.read_bytes() for p in (work / 'disks').glob('*.dsk')}
            commands = [(b'CPX UNLOAD RCP\r', b'A0>_ ', 30)]
            if profile == 'cpx':
                commands.append((b'CPX LOAD RCP\r', b'A0>_ ', 30))
            commands.append((command.encode() + b'\r', b'A0>_ ', 30))
            text = session(simulator, work / 'disks', commands, report / f'{profile}-{number}.txt')
            assert b'CPX module or profile error' not in text, text
            assert b'COPY source destination OR destination=source' in text, text
            assert all((work / 'disks' / name).read_bytes() == data for name, data in before.items()), command
            observations.append({'profile': profile, 'command': command, 'media_unchanged': True})
    # Valid maximum-width names still copy identically through both profiles.
    for profile in ('cpx', 'transient'):
        if profile == 'cpx':
            cpm('cpmrm', a, '0:copy.com')
        else:
            cpm('cpmcp', a, report / 'COPY.COM', '0:copy.com')
        name = 'CPX.COM' if profile == 'cpx' else 'COM.COM'
        commands = [(b'CPX UNLOAD RCP\r', b'A0>_ ', 30)]
        if profile == 'cpx':
            commands.append((b'CPX LOAD RCP\r', b'A0>_ ', 30))
        commands.append((f'COPY B:ABCDEFGH.COM B:{name}\r'.encode(), b'A0>_ ', 30))
        text = session(simulator, work / 'disks', commands, report / f'{profile}-valid.txt')
        assert b'CPX module or profile error' not in text, text
        extracted = report / (profile + '-copied.dat')
        cpm('cpmcp', b, '0:' + name, extracted)
        assert extracted.read_bytes() == fixture.read_bytes()
    (report / 'evidence.json').write_text(json.dumps({'result': 'PASS', 'cases': observations,
        'valid_8_character_name_copies': True, 'cpx_tests_have_no_transient_fallback': True, 'copy_sha256': hashlib.sha256((report / 'COPY.COM').read_bytes()).hexdigest(),
        'rcp_sha256': hashlib.sha256((report / 'RCP.CPX').read_bytes()).hexdigest()}, indent=2) + '\n')
    print('Native CPX/transient COPY malformed-name rejection preserves disks; valid 8.3 copies pass')


if __name__ == '__main__':
    main()
