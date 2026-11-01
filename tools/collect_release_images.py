#!/usr/bin/env python3
"""Refresh stable platform image paths from a candidate and a supplied Model II image."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import zipfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def collect(candidate, model2, output):
    candidate = candidate.resolve()
    model2 = model2.resolve()
    output = output.resolve()
    checksums = {}
    for line in (candidate / 'SHA256SUMS.txt').read_text().splitlines():
        value, name = line.split(None, 1)
        checksums[name.strip().lstrip('*')] = value
    records = {'cpmsim': [], 'model4': [], 'model2': []}
    pending = []
    for platform, label in [('cpmsim', 'cpmsim'), ('model4', 'Model4')]:
        for kind in ('System', 'Utilities'):
            archive = ('BetterCPM-1.0-System-' + label + '-candidate.zip' if kind == 'System'
                       else 'BetterCPM-Utilities-1.0-' + label + '-candidate.zip')
            package = candidate / archive
            assert digest(package.read_bytes()) == checksums[archive], archive
            with zipfile.ZipFile(package) as z:
                identity_name = next(n for n in z.namelist() if n.endswith('/SOURCE-IDENTITY.json'))
                identity = json.loads(z.read(identity_name))
                for member in z.namelist():
                    if '/images/' not in member or not member.endswith(('.dsk', '.dmk')):
                        continue
                    name = Path(member).name
                    drive = ('D' if 'Work-' in name else 'C' if 'NOAH-' in name
                             else 'B' if 'Utilities-' in name else 'A')
                    data = z.read(member)
                    pending.append((platform, name, data))
                    records[platform].append(dict(filename=name, drive=drive, sha256=digest(data),
                        archive=str(package), member=member, source_identity=identity,
                        status='Release candidate; acceptance remains pending'))
        assert len(records[platform]) == 4, records[platform]
    data = model2.read_bytes()
    assert data.startswith(b'IMD'), 'Model II image is not ImageDisk format'
    pending.append(('model2', model2.name, data))
    records['model2'].append(dict(filename=model2.name, drive='A', sha256=digest(data),
        supplied_image=str(model2), status='Supplied a-griff development port; not upstream-qualified',
        note='Copied as supplied, including any existing guest writes; no matching-build claim.'))
    # Validate every input before replacing files. Each individual replacement is atomic.
    for platform, name, data in pending:
        folder = output / platform
        folder.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=folder, prefix='.refresh-')
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(data)
            os.chmod(temporary, 0o644)
            os.replace(temporary, folder / name)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        assert digest((folder / name).read_bytes()) == digest(data)
    for platform, images in records.items():
        folder = output / platform
        (folder / 'IMAGE-IDENTITY.json').write_text(json.dumps(images, indent=2) + '\n')
        (folder / 'SHA256SUMS.txt').write_text(''.join(
            r['sha256'] + '  ' + r['filename'] + '\n' for r in sorted(images, key=lambda r: r['filename'])))
    (output / 'README.txt').write_text(
        'Stable BetterCP/M emulator images\n\n'
        'cpmsim/ and model4/: A System, B Utilities, C NOAH companion, D Work.\n'
        'model2/: supplied Model II system image in A; other media not supplied.\n'
        'Files are writable copies. Emulator writes may change their checksums.\n'
        'SHA256SUMS.txt records the state at the last collection refresh.\n'
        'Re-run collect_release_images.py with the new candidate after rebuilds.\n'
        'Refresh overwrites the named images, including the work disks.\n'
        'Quit emulators before refresh; relaunch them after replacing images.\n')
    print(output)
    print('Verified and collected', len(pending), 'images.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--model2-image', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    collect(args.candidate, args.model2_image, args.output)
