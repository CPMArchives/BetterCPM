#!/usr/bin/env python3
"""Qualify transient COPY skip, conflicting options and read-only continuation."""
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
    sources = {}
    for name in ('A.DAT', 'B.DAT', 'C.DAT', 'D.DAT'):
        payload = name.encode().ljust(256, b'S')
        sources[name] = payload
        f = report / name
        f.write_bytes(payload)
        cpm('cpmcp', b, f, '1:' + name)
    old = {}
    for name in ('A.DAT', 'C.DAT'):
        f = report / ('old-' + name)
        old[name] = b'KEEP '.ljust(128, name[0].encode())
        f.write_bytes(old[name])
        cpm('cpmcp', b, f, '3:' + name)
    cpm('cpmchattr', b, 'rsa', '3:C.DAT')
    def entries(user):
        raw = directory(b, report / 'diskdefs')
        return [raw[i:i+32] for i in range(0, len(raw), 32) if raw[i] == user]
    source_entries = entries(1)
    protected_entry = next(e for e in entries(3) if e[1] == ord('C'))
    simulator = Path.home() / 'projects/git/z80pack/cpmsim/cpmsim'
    def invoke(command, label):
        return session(simulator, report / 'disks', [
            (b'CPX UNLOAD RCP\r', b'A0>_ ', 30),
            (command.encode() + b'\r', b'A0>_ ', 60)], report / (label + '.txt'))
    def data(user, name, label):
        output = report / (label + '-' + name)
        cpm('cpmcp', b, str(user) + ':' + name, output)
        return output.read_bytes()
    text = invoke('COPY B1:*.DAT B3: /S', 'mixed-skip')
    assert b'SKIPPED' in text and b'READ ONLY' in text, text
    for name in sources:
        assert data(3, name, 'skip') == old.get(name, sources[name])
    before = b.read_bytes()
    text = invoke('COPY B1:*.DAT B3: /S /S', 'all-exist')
    assert text.count(b'\r\nSKIPPED\r\n') == 3 and b'READ ONLY' in text, text
    assert b.read_bytes() == before
    for label, command, error in [
            ('conflict-os', 'COPY B1:*.DAT B3: /O /S', b'COPY source destination'),
            ('conflict-so', 'COPY B1:*.DAT B3: /S /O', b'COPY source destination'),
            ('unknown', 'COPY B1:*.DAT B3: /X', b'COPY source destination'),
            ('mapping', 'COPY B3:ONE.DAT=B1:*.DAT /S', b'COPY DESTINATION CONFLICT')]:
        before = b.read_bytes()
        text = invoke(command, label)
        assert error in text and b.read_bytes() == before, (command, text)
    text = invoke('COPY B1:*.DAT B3: /O /O', 'readonly-continue')
    assert b'READ ONLY' in text, text
    for name in sources:
        assert data(3, name, 'overwrite') == (old[name] if name == 'C.DAT' else sources[name])
        assert data(1, name, 'source') == sources[name]
    assert entries(1) == source_entries
    assert next(e for e in entries(3) if e[1] == ord('C')) == protected_entry
    (report / 'evidence.json').write_text(json.dumps({'result': 'PASS',
        'mixed_skip': True, 'all_existing_media_unchanged': True,
        'read_only_preserved_and_batch_continues': True, 'conflicting_options_no_writes': True,
        'copy_sha256': hashlib.sha256((ROOT / 'build/utilities/COPY.COM').read_bytes()).hexdigest()}, indent=2) + '\n')
    print('Transient COPY /S, option rejection and read-only continuation pass')


if __name__ == '__main__':
    main()
