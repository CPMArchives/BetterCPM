#!/usr/bin/env python3
"""Qualify explicit COPY replacement using disposable native media."""
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
    parser.add_argument('--image-dir', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve(); report.mkdir(parents=True, exist_ok=False)
    simulator = Path.home() / 'projects/git/z80pack/cpmsim/cpmsim'
    observations = []
    for profile in ('cpx', 'transient'):
        work = report / profile; work.mkdir()
        shutil.copytree(args.image_dir / 'disks', work / 'disks')
        shutil.copy2(args.image_dir / 'diskdefs', work / 'diskdefs')
        a, b = (work / 'disks' / f'drive{letter}.dsk' for letter in 'ab')
        def cpm(tool, disk, *arguments):
            subprocess.run([tool, '-T', 'raw', '-f', 'bettercpm-default', str(disk), *map(str, arguments)], cwd=work, check=True)
        cpm('cpmrm', a, '0:COPY.COM', '0:MOVE.COM', '0:RCP.CPX')
        cpm('cpmcp', a, ROOT / 'build/cpx/RCP.CPX', '0:RCP.CPX')
        if profile == 'transient':
            for command in ('COPY', 'MOVE'):
                cpm('cpmcp', a, ROOT / 'build/utilities' / (command + '.COM'), '0:' + command + '.COM')
        b.write_bytes(bytes([0xe5]) * len(b.read_bytes()))
        source = work / 'source.dat'
        source.write_bytes(bytes((i * 29 + i // 128 + i // 32768) & 255 for i in range(513 * 128)))
        old = work / 'old.dat'; old.write_bytes(bytes([0x77]) * (769 * 128))
        tiny = work / 'tiny.dat'; tiny.write_bytes(b'UNCHANGED TARGET'.ljust(128, b'!'))
        cpm('cpmcp', b, source, '1:F003.DAT')
        cpm('cpmchattr', b, 'rsa', '1:F003.DAT')
        empty = work / 'empty.dat'; empty.write_bytes(b'')
        small = work / 'small.dat'; small.write_bytes(bytes(range(128)))
        cpm('cpmcp', b, empty, '1:F001.DAT')
        cpm('cpmcp', b, small, '1:F002.DAT')
        for user, payload in ((3, old), (4, tiny), (5, tiny)):
            cpm('cpmcp', b, payload, f'{user}:F003.DAT')
        cpm('cpmchattr', b, 'r', '4:F003.DAT')
        def entries(user):
            raw = directory(b, work / 'diskdefs')
            return [raw[n:n + 32] for n in range(0, len(raw), 32) if raw[n] == user]
        source_entries = [entry for entry in entries(1) if bytes(value & 127 for value in entry[1:12]) == b'F003    DAT']
        all_sources = entries(1)
        def invoke(command, label):
            if profile == 'transient' and command.startswith('COPY '):
                command += ' /B'
            commands = [(b'CPX UNLOAD RCP\r', b'A0>_ ', 30)]
            if profile == 'cpx':
                commands.append((b'CPX LOAD RCP\r', b'A0>_ ', 30))
            commands.append((command.encode() + b'\r', b'A0>_ ', 60))
            return session(simulator, work / 'disks', commands, work / (label + '.txt'))
        for number, (command, expected) in enumerate([
                ('COPY B1:F003.DAT B3:', b'FILE EXISTS'),
                ('COPY B1:F003.DAT B4: /O', b'READ ONLY'),
                ('COPY B1:F003.DAT B1: /O', b'FILE EXISTS' if profile == 'cpx' else b'COPY DESTINATION CONFLICT'),
                ('COPY B1:MISSING.DAT B5:F003.DAT /O', b'NO FILE'),
                ('COPY B1:F003.DAT B5: /X', b'COPY source destination'),
                ('COPY B1:F003.DAT B5: /O /O', b'COPY source destination'),
                ('COPY B1:F003.DAT B5: /O EXTRA', b'COPY source destination'),
                ('MOVE B1:F003.DAT B5: /O', b'COPY source destination')]):
            if profile == 'transient' and command.endswith(' /O /O'):
                continue  # Idempotent transient options are tested by test_z80pack_copy_skip.
            before = {p.name: p.read_bytes() for p in (work / 'disks').glob('*.dsk')}
            text = invoke(command, f'reject-{number}')
            assert expected in text, (command, text)
            assert all((work / 'disks' / name).read_bytes() == data for name, data in before.items()), command
        for label, command, user in [('replace-longer', 'COPY B1:F003.DAT B3: /O', 3),
                                     ('assignment', 'COPY B5:=B1:F003.DAT   /O  ', 5),
                                     ('wildcard', 'COPY B1:F***.DAT B7: /O', 7)]:
            if user == 7:
                for name in ('F001.DAT', 'F002.DAT', 'F003.DAT'):
                    cpm('cpmcp', b, tiny, '7:' + name)
                    cpm('cpmchattr', b, 'sa', '7:' + name)
            text = invoke(command, label)
            for error in (b'NO FILE', b'FILE EXISTS', b'READ ONLY', b'COPY source destination', b'WRITE ERROR', b'READ ERROR', b'NO SPACE'):
                assert error not in text, (command, text)
            result = work / (label + '.dat')
            cpm('cpmcp', b, f'{user}:F003.DAT', result)
            assert result.read_bytes() == source.read_bytes()
            target = [entry for entry in entries(user) if bytes(value & 127 for value in entry[1:12]) == b'F003    DAT']
            assert len(target) == len(source_entries)
            assert all(target[n][9:12] == source_entries[n][9:12] for n in range(len(target)))
            assert entries(1) == all_sources
            if user == 7:
                assert len(entries(7)) == len(source_entries) + 2
                for name, payload in (('F001.DAT', b''), ('F002.DAT', small.read_bytes())):
                    path = work / name
                    cpm('cpmcp', b, '7:' + name, path)
                    assert path.read_bytes() == payload
                    matching = [entry for entry in entries(7) if entry[1:9].decode().rstrip() == name.split('.')[0]]
                    assert len(matching) == 1 and not any(value & 128 for value in matching[0][9:12])
            observations.append({'profile': profile, 'command': command, 'records': 513})
    (report / 'evidence.json').write_text(json.dumps({'result': 'PASS', 'observations': observations,
        'rejections_preserve_media': True, 'longer_destination_tail_removed': True,
        'cpx_has_no_copy_com': True,
        'copy_sha256': hashlib.sha256((ROOT / 'build/utilities/COPY.COM').read_bytes()).hexdigest(),
        'rcp_sha256': hashlib.sha256((ROOT / 'build/cpx/RCP.CPX').read_bytes()).hexdigest(),
        'bdos_sha256': hashlib.sha256((ROOT / 'build/bdos/bdos.bin').read_bytes()).hexdigest()}, indent=2) + '\n')
    print('Explicit COPY overwrite, long-file replacement, attributes and rejection preservation pass in both profiles')


if __name__ == '__main__':
    main()
