#!/usr/bin/env python3
"""Qualify transient destination substitution and preflight on disposable disks."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from test_disk_utilities import ROOT
from test_z80pack_sysgen_install import session
from test_z80pack_attributes import directory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image-dir', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    shutil.copytree(args.image_dir / 'disks', report / 'disks')
    shutil.copy2(args.image_dir / 'diskdefs', report / 'diskdefs')
    a, b = [report / 'disks' / f'drive{x}.dsk' for x in 'ab']
    def cpm(tool, disk, *values):
        subprocess.run([tool, '-T', 'raw', '-f', 'bettercpm-default', str(disk), *map(str, values)], cwd=report, check=True)
    cpm('cpmrm', a, '0:COPY.COM')
    cpm('cpmcp', a, ROOT / 'build/utilities/COPY.COM', '0:COPY.COM')
    b.write_bytes(bytes([229]) * len(b.read_bytes()))
    fixtures = {'FOO.COM': b'F'*128, 'BAR.COM': b'B'*256, 'FOOBAR.COM': bytes(range(128))}
    for name, payload in fixtures.items():
        f = report / name
        f.write_bytes(payload)
        cpm('cpmcp', b, f, '1:' + name)
    cpm('cpmchattr', b, 'rsa', '1:FOO.COM')
    for name in ('FOO.COM', 'BAR.COM'):
        cpm('cpmcp', b, report / name, '2:' + name)
    simulator = Path.home() / 'projects/git/z80pack/cpmsim/cpmsim'
    observations = []
    def invoke(command, label):
        return session(simulator, report / 'disks', [
            (b'CPX UNLOAD RCP\r', b'A0>_ ', 30),
            (command.encode() + b'\r', b'A0>_ ', 60)], report / (label + '.txt'))
    for label, command, destination in [
            ('extension', 'COPY B3:*.DOC=B1:*.COM', '3'),
            ('positional', 'COPY B4:X?***.BAK=B1:FOOBAR.COM', '4'),
            ('same-du', 'COPY B2:*.DOC=B2:*.*', '2')]:
        text = invoke(command, label)
        for error in (b'COPY DESTINATION CONFLICT', b'INVALID DESTINATION NAME', b'COPY source destination', b'READ ERROR', b'WRITE ERROR'):
            assert error not in text, (command, text)
        if label == 'positional':
            expected = {'XOOBAR.BAK': fixtures['FOOBAR.COM']}
        else:
            expected = {name.replace('.COM', '.DOC'): payload for name, payload in fixtures.items()
                        if label != 'same-du' or name in ('FOO.COM', 'BAR.COM')}
        for name, payload in expected.items():
            output = report / (label + '-' + name)
            cpm('cpmcp', b, destination + ':' + name, output)
            assert output.read_bytes() == payload, name
        observations.append({'command': command, 'result': 'PASS'})
    for label, command, error in [
            ('duplicate', 'COPY B5:ONE.DOC=B1:*.COM /O', b'COPY DESTINATION CONFLICT'),
            ('source-overlap', 'COPY B1:BAR.COM=B1:*.COM /O', b'COPY DESTINATION CONFLICT'),
            ('self-copy', 'COPY B1:FOO.COM=B1:FOO.COM /O', b'COPY DESTINATION CONFLICT'),
            ('padded-hole', 'COPY B5:????X.BAK=B1:FOO.COM', b'INVALID DESTINATION NAME'),
            ('invalid-star', 'COPY B5:F*A.DAT=B1:FOO.COM', b'COPY source destination')]:
        before = b.read_bytes()
        text = invoke(command, label)
        assert error in text, (command, text)
        assert b.read_bytes() == before, command
        observations.append({'command': command, 'result': 'REJECTED_WITHOUT_MUTATION'})
    raw = directory(b, report / 'diskdefs')
    entries = [raw[i:i+32] for i in range(0, len(raw), 32)]
    def attributes(user, name):
        stem, ext = name.split('.')
        key = (stem.ljust(8) + ext.ljust(3)).encode()
        matches = [e for e in entries if e[0] == user and bytes(x & 127 for x in e[1:12]) == key]
        assert matches, (user, name)
        return bytes(x & 128 for x in matches[0][9:12])
    assert attributes(3, 'FOO.DOC') == attributes(1, 'FOO.COM')
    assert all(x & 128 for x in attributes(3, 'FOO.DOC'))
    for name, payload in fixtures.items():
        output = report / ('source-' + name)
        cpm('cpmcp', b, '1:' + name, output)
        assert output.read_bytes() == payload
    (report / 'evidence.json').write_text(json.dumps({'result': 'PASS', 'cases': observations,
        'copy_sha256': hashlib.sha256((ROOT / 'build/utilities/COPY.COM').read_bytes()).hexdigest()}, indent=2) + '\n')
    print('Transient COPY substitution, frozen same-DU batch and no-write conflict rejection pass')


if __name__ == '__main__':
    main()
