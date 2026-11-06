#!/usr/bin/env python3
"""Qualify expanded PIP selectors against real CP/M BDOS directory services."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile
from test_z80pack_sysgen_install import session

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image-dir', type=Path, default=ROOT / 'build/z80pack')
    parser.add_argument('--simulator', type=Path, default=Path.home() / 'projects/git/z80pack/cpmsim/cpmsim')
    args = parser.parse_args()
    report = ROOT / 'build/test-results/pip-selectors'
    report.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='pip-selectors-') as tmp:
        work = Path(tmp)
        shutil.copytree(args.image_dir / 'disks', work / 'disks')
        shutil.copy2(args.image_dir / 'diskdefs', work / 'diskdefs')
        def disk(drive):
            return work / f'disks/drive{drive.lower()}.dsk'
        def put(drive, user, name, payload):
            source = work / name
            source.write_bytes(payload)
            subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default', str(disk(drive)), str(source), f'{user}:{name}'], cwd=work, check=True)
        def get(drive, user, name):
            out = work / f'out-{drive}{user}-{name}'
            result = subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default', str(disk(drive)), f'{user}:{name}', str(out)], cwd=work, capture_output=True)
            return out.read_bytes() if result.returncode == 0 and out.exists() else None
        put('A', 0, 'PIPSEL.COM', (ROOT / 'build/pip-development/PIP.COM').read_bytes())
        expected = {'PSZERO.COM': b'0' * 128, 'PSLAST.COM': b'Z' * 33024, 'PSSYS.COM': b'S' * 128}
        put('B', 0, 'PSZERO.COM', expected['PSZERO.COM'])
        put('B', 31, 'PSLAST.COM', expected['PSLAST.COM'])
        put('C', 7, 'PSSYS.COM', expected['PSSYS.COM'])
        subprocess.run(['cpmchattr', '-T', 'raw', '-f', 'bettercpm-default', str(disk('C')), 's', '7:PSSYS.COM'], cwd=work, check=True)
        put('B', 7, 'PDNAME.COM', b'first'.ljust(128, b'1'))
        put('B', 9, 'PDNAME.COM', b'second'.ljust(128, b'2'))
        put('B', 0, 'PDUNIQ.COM', b'unique'.ljust(128, b'3'))
        old = b'old destination'.ljust(128, b'D')
        staging = b'old staging'.ljust(128, b'T')
        put('D', 5, 'PDNAME.COM', old)
        put('D', 5, 'PDNAME.$$$', staging)
        before = {d: disk(d).read_bytes() for d in 'BC'}
        transcript = session(args.simulator, work / 'disks', [
            (b':PIPSEL D4:=[B[0,31],C7]:PS*.COM[RV]\r', b'A0>_ ', 120),
            (b':PIPSEL D5:=B[-]:PD*.COM[VW]\r', b'A0>_ ', 120),
        ], report / 'transcript.txt')
        assert b'DUPLICATE DESTINATION NAME' in transcript and b'No files copied.' in transcript
        assert b'B7:PDNAME.COM' in transcript and b'B9:PDNAME.COM' in transcript
        assert b'INVALID FORMAT' not in transcript and b'VERIFY ERROR' not in transcript
        for name, data in expected.items():
            assert get('D', 4, name) == data, name
        assert get('D', 5, 'PDNAME.COM') == old
        assert get('D', 5, 'PDNAME.$$$') == staging
        assert get('D', 5, 'PDUNIQ.COM') is None
        assert all(disk(d).read_bytes() == data for d, data in before.items()), 'source disk changed'
    print('PASS: real cpmsim BDOS compound/all-user selectors, user 31, SYS/V, multi-extents and duplicate-name rejection without destination/staging/source changes')

if __name__ == '__main__':
    main()
