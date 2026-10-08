#!/usr/bin/env python3
"""Qualify native CPX/transient wildcard COPY with multi-extent and attributes."""
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
    parser.add_argument('--format', choices=('default', '800k'), default='default')
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
            subprocess.run([tool, '-T', 'raw', '-f', ('bettercpm-mm-80t-ds-data' if args.format == '800k' and disk.name != 'drivea.dsk' else 'bettercpm-default'), str(disk), *map(str, arguments)], cwd=work, check=True)
        cpm('cpmrm', a, '0:copy.com', '0:move.com', '0:rcp.cpx')
        if profile == 'transient':
            cpm('cpmcp', a, ROOT / 'build/utilities/COPY.COM', '0:copy.com')
            cpm('cpmcp', a, ROOT / 'build/utilities/MOVE.COM', '0:move.com')
        cpm('cpmcp', a, ROOT / 'build/cpx/RCP.CPX', '0:rcp.cpx')
        fmt = None
        if args.format == '800k':
            from fdf_format import select_fdf
            from test_z80pack_native_build import build_binding_program
            fmt = select_fdf(ROOT / 'third_party/montezuma/DISK-INT.FDF',
                             'Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)')
            setup = build_binding_program(work)
            cpm('cpmcp', a, setup, '0:SETBUILD.COM')
            for letter in ('b', 'c'):
                (work / 'disks' / f'drive{letter}.dsk').write_bytes(bytes([0xe5]) * fmt.image_bytes)
        b.write_bytes(bytes([0xe5]) * len(b.read_bytes()))
        fixtures = {}
        for number in reversed(range(6)):
            name = f'F{number:03}.DAT'
            payload = bytes((index * 29 + index // 128 + index // 32768 + number) & 255 for index in range((513 if number == 3 else 3) * 128))
            source = work / name; source.write_bytes(payload)
            cpm('cpmcp', b, source, '1:' + name)
            attr = ('', 'r', 's', 'a', 'rsa', 'sa')[number]
            if attr:
                cpm('cpmchattr', b, attr, '1:' + name)
            fixtures[name] = payload
        sentinel = work / 'KEEP.TXT'; sentinel.write_bytes(bytes(128))
        cpm('cpmcp', b, sentinel, '1:KEEP.TXT')
        cpm('cpmcp', b, sentinel, '3:KEEP.TXT')
        def raw_entries(user, image=b):
            if fmt is None:
                raw = directory(image, work / 'diskdefs')
            else:
                data = image.read_bytes()
                mapping = fmt.raw_record_map()
                raw = b''.join(data[(logical // fmt.spt * fmt.spt + mapping[logical % fmt.spt]) * 128:
                                    (logical // fmt.spt * fmt.spt + mapping[logical % fmt.spt]) * 128 + 128]
                               for logical in range((fmt.drm + 1) * 32 // 128))
            return {bytes(value & 127 for value in raw[n + 1:n + 12]): [raw[m:m + 32] for m in range(0, len(raw), 32)
                    if raw[m] == user and bytes(value & 127 for value in raw[m + 1:m + 12]) == bytes(value & 127 for value in raw[n + 1:n + 12])]
                    for n in range(0, len(raw), 32) if raw[n] == user}
        source_before = raw_entries(1)
        sentinel_before = raw_entries(3)[b'KEEP    TXT']
        def invoke(command, label):
            if profile == 'transient' and command.startswith('COPY '):
                command += ' /B'
            commands = ([(b'SETBUILD\r', b'A0>_ ', 30)] if fmt is not None else [])
            commands.append((b'CPX UNLOAD RCP\r', b'A0>_ ', 30))
            if profile == 'cpx':
                commands.append((b'CPX LOAD RCP\r', b'A0>_ ', 30))
            commands.append((command.encode() + b'\r', b'A0>_ ', 60))
            return session(simulator, work / 'disks', commands, work / (label + '.txt'))
        for label, command, user, destination in [('copy', 'COPY B1:F***.DAT B3:', 3, b),
                                                  ('assign', 'COPY B4:=B1:F?*.DAT', 4, b),
                                                  ('cross-drive', 'COPY B1:F*.DAT C2:', 2, work / 'disks/drivec.dsk')]:
            text = invoke(command, label)
            for error in (b'NO FILE', b'FILE EXISTS', b'COPY source destination', b'READ ERROR', b'WRITE ERROR', b'NO SPACE'):
                assert error not in text, (command, text)
            target = raw_entries(user, destination)
            for name, payload in fixtures.items():
                key = name.split('.')[0].ljust(8).encode() + b'DAT'
                assert key in target and len(target[key]) == len(source_before[key]), (name, target)
                assert all(dest[9:12] == source[9:12] for dest, source in zip(target[key], source_before[key])), name
                extracted = work / f'{user}-{name}'
                cpm('cpmcp', destination, str(user) + ':' + name, extracted)
                assert extracted.read_bytes() == payload, name
            assert raw_entries(1) == source_before
            assert target.get(b'KEEP    TXT') == (sentinel_before if user == 3 else None)
            assert set(target) == set(source_before) - {b'KEEP    TXT'} | ({b'KEEP    TXT'} if user == 3 else set())
            observations.append({'profile': profile, 'format': args.format, 'command': command, 'files': 6, 'multi_extent_records': 513})
        for number, (command, expected) in enumerate([
                ('COPY B1:F*.DAT B1:', b'FILE EXISTS' if profile == 'cpx' else b'COPY DESTINATION CONFLICT'),
                ('COPY B1:F*.DAT B3:', b'FILE EXISTS'),
                ('COPY B1:Z*.DAT B5:', b'NO FILE'),
                ('COPY B1:F*.DAT B5:ONE.DAT', b'COPY source destination' if profile == 'cpx' else b'COPY DESTINATION CONFLICT'),
                ('COPY B1:F*X.DAT B5:', b'COPY source destination'),
                ('MOVE B1:F*.DAT B5:', b'COPY source destination')]):
            before = {p.name: p.read_bytes() for p in (work / 'disks').glob('*.dsk')}
            text = invoke(command, f'reject-{number}')
            assert expected in text, (command, text)
            assert all((work / 'disks' / name).read_bytes() == data for name, data in before.items()), command
        # A collision after three copies stops the batch without replacing it.
        collision = work / 'collision.dat'; collision.write_bytes(b'KEEP EXISTING'.ljust(128, b'!'))
        cpm('cpmcp', b, collision, '5:F003.DAT')
        prior = raw_entries(5)[b'F003    DAT']
        text = invoke('COPY B1:F*.DAT B5:', 'mid-batch-collision')
        assert b'FILE EXISTS' in text
        target = raw_entries(5)
        assert set(target) == {f'F{n:03}    DAT'.encode() for n in range(4 if profile == 'cpx' else 6)}
        assert target[b'F003    DAT'] == prior
        for name in ('F000.DAT', 'F001.DAT', 'F002.DAT', 'F003.DAT'):
            extracted = work / ('collision-' + name)
            cpm('cpmcp', b, '5:' + name, extracted)
            assert extracted.read_bytes() == (collision.read_bytes() if name == 'F003.DAT' else fixtures[name])
        assert raw_entries(1) == source_before
    (report / 'evidence.json').write_text(json.dumps({'result': 'PASS', 'observations': observations,
        'cpx_has_no_copy_com': True, 'rejections_preserve_media': True,
        'mid_batch_collision_preserves_existing_target': True,
        'bdos_sha256': hashlib.sha256((ROOT / 'build/bdos/bdos.bin').read_bytes()).hexdigest(),
        'simulator_sha256': hashlib.sha256(simulator.read_bytes()).hexdigest(),
        'copy_sha256': hashlib.sha256((ROOT / 'build/utilities/COPY.COM').read_bytes()).hexdigest(),
        'rcp_sha256': hashlib.sha256((ROOT / 'build/cpx/RCP.CPX').read_bytes()).hexdigest()}, indent=2) + '\n')
    print('Native wildcard COPY transfers each multi-extent file once, preserving data and attributes in both profiles')


if __name__ == '__main__':
    main()
