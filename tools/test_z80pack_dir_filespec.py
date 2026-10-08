#!/usr/bin/env python3
"""Qualify bounded DIR wildcard grammar in CPX-only and transient profiles."""
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
    parser.add_argument('--image-dir', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    observations = []
    for profile in ('cpx', 'transient'):
        work = report / profile
        work.mkdir()
        shutil.copytree(args.image_dir / 'disks', work / 'disks')
        shutil.copy2(args.image_dir / 'diskdefs', work / 'diskdefs')
        a, b = [work / 'disks' / f'drive{x}.dsk' for x in 'ab']
        def cpm(tool, disk, *values):
            subprocess.run([tool, '-T', 'raw', '-f', 'bettercpm-default', str(disk), *map(str, values)], cwd=work, check=True)
        cpm('cpmrm', a, '0:DIR.COM', '0:RCP.CPX')
        cpm('cpmcp', a, ROOT / 'build/cpx/RCP.CPX', '0:RCP.CPX')
        if profile == 'transient':
            cpm('cpmcp', a, ROOT / 'build/utilities/DIR.COM', '0:DIR.COM')
        b.write_bytes(bytes([229]) * len(b.read_bytes()))
        names = ['FOO.DAT', 'FOO.COM', 'FOO', 'F01.DAT', 'FOOBIG.DAT', 'ZOO.DAT', 'FSYS.DAT']
        for name in names:
            f = work / name
            f.write_bytes(bytes(20000 if name == 'FOOBIG.DAT' else 128))
            cpm('cpmcp', b, f, '1:' + name)
        cpm('cpmchattr', b, 's', '1:FSYS.DAT')
        simulator = Path.home() / 'projects/git/z80pack/cpmsim/cpmsim'
        def invoke(pattern, label):
            steps = [(b'CPX UNLOAD RCP\r', b'A0>_ ', 30)]
            if profile == 'cpx':
                steps.append((b'CPX LOAD RCP\r', b'A0>_ ', 30))
            steps.append((('DIR B1:' + pattern).encode() + b'\r', b'A0>_ ', 30))
            before = {p.name: p.read_bytes() for p in (work / 'disks').glob('*.dsk')}
            text = session(simulator, work / 'disks', steps, work / (label + '.txt'))
            assert all((work / 'disks' / name).read_bytes() == data for name, data in before.items())
            assert b'CPX module or profile error' not in text
            return text
        for i, (pattern, expected) in enumerate([
                ('F?*.DAT', ['FOO.DAT', 'F01.DAT', 'FOOBIG.DAT']),
                ('F***.D**', ['FOO.DAT', 'F01.DAT', 'FOOBIG.DAT']),
                ('*.COM', ['FOO.COM']), ('FOO.*', ['FOO.DAT', 'FOO.COM', 'FOO']),
                ('FOO', ['FOO']), ('', names[:-1])]):
            text = invoke(pattern, f'valid-{i}')
            assert b'Invalid filespec.' not in text
            for name in names:
                stem, _, ext = name.partition('.')
                rendered = (stem.ljust(8) + ' ' + ext.ljust(3)).encode()
                assert (rendered in text) == (name in expected), (profile, pattern, name, text)
                if name in expected:
                    assert text.count(rendered) == 1, (pattern, name)
            observations.append({'profile': profile, 'pattern': pattern, 'accepted': True})
        for i, pattern in enumerate(['F*A.DAT', 'F**?.DAT', 'FOO.*X', 'F?**?.DAT',
                                     'FOO..DAT', 'ABCDEFGHI.DAT', 'FOO.ABCD', 'F?.DAT*']):
            text = invoke(pattern, f'invalid-{i}')
            assert b'Invalid filespec.' in text, (profile, pattern, text)
            assert b'NO FILE' not in text
            observations.append({'profile': profile, 'pattern': pattern, 'accepted': False})
    (report / 'evidence.json').write_text(json.dumps({'result': 'PASS', 'cases': observations,
        'media_unchanged': True, 'caller_restored': 'A0', '20k_file_listed_once': True,
        'dir_sha256': hashlib.sha256((ROOT / 'build/utilities/DIR.COM').read_bytes()).hexdigest(),
        'rcp_sha256': hashlib.sha256((ROOT / 'build/cpx/RCP.CPX').read_bytes()).hexdigest()}, indent=2) + '\n')
    print('CPX/transient DIR bounded wildcards, rejection, DU restoration and EXM listing pass')


if __name__ == '__main__':
    main()
