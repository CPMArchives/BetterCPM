#!/usr/bin/env python3
"""Inspect delivered 1.3 ZIPs, manifests, source offers and platform separation."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def audit(folder):
    index = json.loads((folder/'BetterCPM-1.3-CANDIDATE.json').read_bytes())
    assert index['status'] == 'CANDIDATE; NOT ACCEPTED' and index['accepted_commit'] is None
    assert len(index['assets']) == 8
    commit = index['source_commit']
    packages = {}
    for asset in index['assets']:
        raw = (folder/asset['filename']).read_bytes()
        assert digest(raw) == asset['sha256'], asset['filename']
        with zipfile.ZipFile(folder/asset['filename']) as archive:
            assert archive.testzip() is None
            roots = {name.split('/')[0] for name in archive.namelist()}
            assert len(roots) == 1
            prefix = roots.pop()+'/'
            files = {name[len(prefix):]:archive.read(name) for name in archive.namelist()}
        release_bytes = files.pop('RELEASE.json')
        record = json.loads(release_bytes)
        checksums = files.pop('SHA256SUMS.txt').decode().splitlines()
        assert record['source_commit'] == commit and record['accepted_commit'] is None
        assert record['status'] == 'CANDIDATE; NOT ACCEPTED' and record['pending']
        assert record['files'] == {name:digest(data) for name,data in files.items()}
        delivered_sums = dict(line.split(None,1)[::-1] for line in checksums)
        # SHA256SUMS includes RELEASE.json, whose exact bytes were read above.
        assert delivered_sums.pop('RELEASE.json') == digest(release_bytes)
        assert delivered_sums == record['files']
        package = record['package']
        assert package not in packages
        packages[package] = {'record':record,'files':files}
    expected = {'source','documentation'} | {kind+'-'+platform for kind in
               ('system','utilities') for platform in ('cpmsim','model4','model2')}
    assert set(packages) == expected
    for package, row in packages.items():
        files = row['files']
        if package.startswith(('system-','utilities-')):
            offer = json.loads(files['SOURCE-DOWNLOAD.json'])
            assert offer['filename'] == 'BetterCPM-1.3-Source.zip' and offer['source_commit'] == commit
            assert not any(name.startswith('source/') for name in files)
        if package.startswith('utilities-'):
            images = [name for name in files if name.startswith('images/')]
            assert len(images) == 2, (package,images)
            platform = row['record']['platforms'][0]
            assert all(name.startswith('images/'+platform+'/') for name in images)
            assert len(row['record']['evidence']['images']) == 2
    docs = packages['documentation']
    assert len(docs['record']['evidence']['manuals']) == 4
    assert not any(name.startswith('docs/engineering/') for name in docs['files'])
    assert not any(name.lower().endswith(('.pdf','.docx')) for name in docs['files'])
    source = packages['source']['files']
    assert 'source/BetterCPM/src/ccp/ccp.mac' in source
    assert 'source/BetterCPM/tools/pack_ccp.py' in source
    return {'status':'PASS_CANDIDATE_ARCHIVE_AUDIT','source_commit':commit,
            'packages':{name:{'files':len(row['files']),'platforms':row['record']['platforms']}
                        for name,row in packages.items()},
            'checks':['ZIP readback and file hashes','source offers and commit binding',
                      'all three Utilities primary/companion pairs','four-manual Documentation selection',
                      'retained editable inner CCP source'],
            'release_acceptance':'PENDING'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.folder),indent=2))
