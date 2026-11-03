#!/usr/bin/env python3
"""Verify the pinned CP/M Tools source companion and unchanged binary mapping."""
import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify(root=ROOT):
    root = Path(root)
    base = root/'third_party/cpm-tools'
    manifest = json.loads((base/'manifest.json').read_text())
    source = json.loads((base/'source-manifest.json').read_text())
    if (source['repository'] != manifest['repository'] or
            source['commit'] != manifest['commit']):
        raise ValueError('CP/M Tools source pin differs from binary snapshot')
    paths = {'third_party/cpm-tools/source-manifest.json',
             'third_party/cpm-tools/README.md'}
    for name, row in source['files'].items():
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name:
            raise ValueError('unsafe CP/M Tools source path')
        data = (base/'source'/name).read_bytes()
        blob = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if digest(data) != row['sha256'] or blob != row['git_blob']:
            raise ValueError('CP/M Tools source differs: '+name)
        paths.add('third_party/cpm-tools/source/'+name)
    binaries = {row['name']:row for row in manifest['files']
                if row['name'].endswith('.COM')}
    if set(binaries) != set(source['binaries']):
        raise ValueError('CP/M Tools source mapping incomplete')
    for name, row in source['binaries'].items():
        data = (base/name).read_bytes()
        blob = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if (digest(data) != binaries[name]['sha256'] or
                digest(data) != row['binary_sha256'] or
                blob != row['upstream_binary_git_blob']):
            raise ValueError('CP/M Tools binary differs: '+name)
        for key in ('source', 'build', 'host_builder'):
            if row[key] is not None and row[key] not in source['files']:
                raise ValueError('CP/M Tools build source absent: '+name)
    if (base/'LICENSE').read_bytes() != (base/'source/LICENSE').read_bytes():
        raise ValueError('CP/M Tools license differs')
    return paths


if __name__ == '__main__':
    paths = verify()
    print(f'PASS: seven pinned binaries and {len(paths)-2} source files verified')
