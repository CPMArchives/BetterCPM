#!/usr/bin/env python3
"""Qualify COPY destination-DU shorthand through CPX and transient paths."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from test_disk_utilities import ROOT
from test_z80pack_attributes import directory
from test_z80pack_sysgen_install import session


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--image-dir', type=Path, default=ROOT / 'build/z80pack-iobyte-qualified')
    args = parser.parse_args()
    report = args.report.resolve(); report.mkdir(parents=True, exist_ok=False)
    simulator = Path.home() / 'projects/git/z80pack/cpmsim/cpmsim'
    observations = []
    for profile in ('cpx', 'transient'):
        work = report / profile; work.mkdir()
        shutil.copytree(args.image_dir / 'disks', work / 'disks')
        shutil.copy2(args.image_dir / 'diskdefs', work / 'diskdefs')
        a, b = (work / 'disks' / ('drive' + letter + '.dsk') for letter in 'ab')
        def cpm(tool, disk, *arguments):
            subprocess.run([tool, '-T', 'raw', '-f', 'bettercpm-default', str(disk), *map(str, arguments)], cwd=work, check=True)
        cpm('cpmrm', a, '0:copy.com', '0:rcp.cpx')
        if profile == 'transient':
            cpm('cpmcp', a, ROOT / 'build/utilities/COPY.COM', '0:copy.com')
        cpm('cpmcp', a, ROOT / 'build/cpx/RCP.CPX', '0:rcp.cpx')
        b.write_bytes(bytes([0xe5]) * len(b.read_bytes()))
        payload = bytes((index * 29 + 7) & 255 for index in range(777)) + bytes(119)
        source = work / 'source.dat'; source.write_bytes(payload)
        cpm('cpmcp', b, source, '1:SOURCE.DAT')
        cpm('cpmchattr', b, 'rsa', '1:SOURCE.DAT')
        def entry(user):
            raw = directory(b, work / 'diskdefs')
            matches = [raw[n:n + 32] for n in range(0, len(raw), 32)
                       if raw[n] == user and bytes(value & 127 for value in raw[n + 1:n + 12]) == b'SOURCE  DAT']
            assert len(matches) == 1, (user, matches)
            return matches[0]
        original = entry(1)
        assert all(value & 128 for value in original[9:12]), original
        def invoke(command, label):
            if profile == 'transient' and command.startswith('COPY '):
                command += ' /B'
            commands = [(b'CPX UNLOAD RCP\r', b'A0>_ ', 30)]
            if profile == 'cpx':
                commands.append((b'CPX LOAD RCP\r', b'A0>_ ', 30))
            commands.append((command.encode() + b'\r', b'A0>_ ', 30))
            return session(simulator, work / 'disks', commands, work / (label + '.txt'))
        for number, (command, user) in enumerate([
                ('COPY B1:SOURCE.DAT B3:', 3), ('COPY B1:SOURCE.DAT B31:', 31),
                ('COPY B1:SOURCE.DAT B:', 0), ('COPY B4:=B1:SOURCE.DAT', 4)]):
            text = invoke(command, f'copy-{number}')
            assert b'FILE EXISTS' not in text and b'COPY source destination' not in text, text
            destination = entry(user)
            assert destination[9:12] == original[9:12], (destination, original)
            extracted = work / f'copied-{user}.dat'
            cpm('cpmcp', b, f'{user}:SOURCE.DAT', extracted)
            assert extracted.read_bytes() == payload
            assert entry(1) == original
            observations.append({'profile': profile, 'command': command, 'destination_user': user,
                                 'attributes': destination[9:12].hex()})
        for number, (command, expected) in enumerate([
                ('COPY B1:SOURCE.DAT B1:', b'FILE EXISTS' if profile == 'cpx' else b'COPY DESTINATION CONFLICT'),
                ('COPY B1:SOURCE.DAT B3:', b'FILE EXISTS' if profile == 'cpx' else b'READ ONLY'),
                ('COPY B1: B5:', b'COPY source destination'),
                ('COPY B1:SOURCE.DAT B32:', b'COPY source destination')]):
            before = {p.name: p.read_bytes() for p in (work / 'disks').glob('*.dsk')}
            text = invoke(command, f'reject-{number}')
            assert expected in text, (command, text)
            assert all((work / 'disks' / name).read_bytes() == data for name, data in before.items()), command
    (report / 'evidence.json').write_text(json.dumps({'result': 'PASS', 'observations': observations,
        'copy_sha256': hashlib.sha256((ROOT / 'build/utilities/COPY.COM').read_bytes()).hexdigest(),
        'rcp_sha256': hashlib.sha256((ROOT / 'build/cpx/RCP.CPX').read_bytes()).hexdigest(),
        'cpx_has_no_copy_com': True, 'caller_context': 'A0',
        'rejected_operations_preserve_media': True}, indent=2) + '\n')
    print('COPY destination drive/user shorthand, attributes, self-copy and rejection passed in both profiles')


if __name__ == '__main__':
    main()
