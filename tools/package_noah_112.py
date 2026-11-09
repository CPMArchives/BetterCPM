#!/usr/bin/env python3
"""Package the approved NOAH-only 1.1.2 update from published 1.1.1 media.

No kernel build or guest campaign. Verify matching binaries, independent disk
readback, preservation of unrelated files, source identity and ZIP checksums.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from package_release_candidates import ROOT, encoded, sha, write_package
from finalize_release_101 import candidate_files
from release_source import source_files
from fdf_format import select_fdf
from convert_fdf_image import dmk_to_raw, raw_to_dmk


def package(base, output, binary):
    base, output, binary = map(lambda p: Path(p).resolve(), (base, output, binary))
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT):
        raise ValueError('commit publication source before packaging')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    output.mkdir(parents=True, exist_ok=False)
    published = output/'published'; published.mkdir()
    notes = (ROOT/'docs/releases/RELEASE-NOTES-1.1.2.md').read_bytes()
    replacements = {name: (binary/name).read_bytes() for name in ('NOAH.COM', 'NOAH.OVL')}
    replacements['NOAH.TXT'] = (ROOT/'src/distribution/NOAH.TXT').read_bytes()
    if b'NOAH 1.0 (021)' not in replacements['NOAH.COM']:
        raise ValueError('wrong NOAH revision')
    manifest = json.loads((base/'published/BetterCPM-1.1.1-RELEASE.json').read_text())
    assets = {a['package']: a for a in manifest['assets']}
    record = dict(schema=1, version='1.1.2', release_version='1.1.2', tag='v1.1.2',
                  source_commit=commit, source_revision=commit,
                  core_os_version='1.1.1', base_tag='v1.1.1',
                  status='MAINTAINER-APPROVED NOAH MAINTENANCE RELEASE',
                  validation='Existing focused checks; exact binary and package readback',
                  binary_sha256={n: sha(b) for n, b in replacements.items()},
                  experimental_1_2_features=False)

    def load(kind):
        asset = assets[kind]; path = base/'published'/asset['filename']
        if sha(path.read_bytes()) != asset['sha256']:
            raise ValueError('published baseline archive mismatch: '+kind)
        files = candidate_files(path, asset['archive_root'])
        files.pop('RELEASE.json'); files.pop('SHA256SUMS.txt')
        return files

    def write(kind, filename, files):
        r = dict(record, package=kind, files={n: sha(b) for n, b in sorted(files.items())})
        return dict(write_package(published/filename, filename[:-4], files, r), package=kind)

    # Preserve the existing corresponding-source companions and offline inputs.
    files = load('source')
    tracked = source_files(ROOT)
    for name, data in tracked.items():
        files['source/BetterCPM/'+name] = data
    files['source/BetterCPM/SOURCE-FILES.json'] = encoded({n: sha(b) for n,b in sorted(tracked.items())})
    for name in ('SOURCE-IDENTITY.json', 'source/BetterCPM/SOURCE-IDENTITY.json'):
        files[name] = encoded(record)
    for path in binary.glob('*.mac'):
        if path.name.lower() != 'resident-sizing.mac':
            files['source/noah-native/'+path.name.upper()] = path.read_bytes()
    files['source/noah-native/layout.json'] = (binary/'layout.json').read_bytes()
    files['RELEASE-NOTES-1.1.2.md'] = notes
    files['README.txt'] = b'BetterCP/M v1.1.2 corresponding source. Core OS remains 1.1.1.\nSee RELEASE-NOTES-1.1.2.md.\n'
    # Refresh old release links in the source-kit envelope, not historical source.
    for name in list(files):
        if name.endswith('SOURCE-DOWNLOAD.json'):
            files.pop(name)
    source = write('source', 'BetterCPM-1.1.2-Source.zip', files)
    del files
    results = [source]

    update = dict(replacements)
    update['README.txt'] = (ROOT/'packaging/1.1.2/README-NOAH-Update.txt').read_bytes()
    update['RELEASE-NOTES-1.1.2.md'] = notes
    for name in ('LICENSE', 'COPYING', 'NOTICE'):
        update[name] = (ROOT/name).read_bytes()
    update['SOURCE-IDENTITY.json'] = encoded(record)
    results.append(write('noah-update', 'BetterCPM-1.1.2-NOAH-Update.zip', update))
    evidence = []
    sys.path.insert(0, str(ROOT/'docs/engineering/evidence/2026-11-06-model2'))
    from adapt import to_raw, to_imd
    for platform, kind, folder, definition in (
        ('cpmsim', 'utilities-cpmsim', 'cpmsim-noah', 'bettercpm-default'),
        ('Model4', 'utilities-model4', 'model4-noah', 'bettercpm-mm-80t-ds-data'),
        ('Model2', 'utilities-model2', 'model2-noah', 'bcm2ss'),
    ):
        files = load(kind)
        image_name = next(n for n in files if '/BetterCPM-NOAH-' in n)
        before = files[image_name]
        if platform == 'Model4':
            fmt = select_fdf(ROOT/'metadata/DISK.FDF', 'Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)')
            raw = dmk_to_raw(before, fmt)
        elif platform == 'Model2':
            raw = to_raw(before)
        else:
            raw = before
        work = output/platform; work.mkdir()
        (work/'diskdefs').write_bytes((base/'media'/folder/'diskdefs').read_bytes())
        disk = work/'disk.raw'; disk.write_bytes(raw)

        def run(*args):
            return subprocess.run(list(map(str,args)), cwd=work, capture_output=True, check=True)

        def extract(destination):
            destination.mkdir()
            run('cpmcp', '-T', 'raw', '-f', definition, disk, '0:*', destination)
            return {p.name.upper():p.read_bytes() for p in destination.iterdir()}

        original = extract(work/'before')
        for name, data in replacements.items():
            path = work/name; path.write_bytes(data)
            run('cpmrm', '-T', 'raw', '-f', definition, disk, '0:'+name)
            run('cpmcp', '-T', 'raw', '-f', definition, disk, path, '0:'+name)
        after = extract(work/'after')
        if set(original) != set(after):
            raise ValueError('disk membership changed: '+platform)
        for name, data in after.items():
            if name in replacements:
                expected = replacements[name]
                assert data[:len(expected)] == expected and set(data[len(expected):]) <= {0,26}, name
            else:
                assert data == original[name], name
        run('fsck.cpm', '-T', 'raw', '-f', definition, '-n', disk)
        raw = disk.read_bytes()
        if platform == 'Model4':
            image = raw_to_dmk(raw, fmt)
            assert dmk_to_raw(image, fmt) == raw
        elif platform == 'Model2':
            image = to_imd(before, raw)
            assert to_raw(image) == raw
        else:
            image = raw
        files[image_name] = image
        unrelated = {n:sha(b) for n,b in original.items() if n not in replacements}
        proof = dict(platform=platform, base_image_sha256=sha(before), image_sha256=sha(image),
                     updated_files={n:sha(b) for n,b in replacements.items()},
                     unrelated_files_preserved=unrelated, independent_record_readback='PASS',
                     filesystem='PASS', container_roundtrip='PASS')
        evidence.append(proof)
        files['Provenance/NOAH-1.1.2-PATCH.json'] = encoded(proof)
        files['SOURCE-IDENTITY.json'] = encoded(record)
        files['SOURCE-DOWNLOAD.json'] = encoded(dict(version='1.1.2', filename=source['filename'],
            sha256=source['sha256'], url='https://github.com/CPMArchives/BetterCPM/releases/download/v1.1.2/'+source['filename']))
        files['RELEASE-NOTES-1.1.2.md'] = notes
        files['README.txt'] = (f'BetterCP/M v1.1.2 Utilities - {platform}\n\n'
            'The NOAH companion disk now contains matched NOAH 1.0 (021) files.\n'
            'The other Utilities disk and unrelated files are unchanged from 1.1.1.\n'
            'Use the v1.1.1 System disk. See RELEASE-NOTES-1.1.2.md.\n'
            'Source: https://github.com/CPMArchives/BetterCPM/releases/tag/v1.1.2\n').encode()
        results.append(write(kind, f'BetterCPM-Utilities-1.1.2-{platform}.zip', files))
        print('PASS:', platform, 'filesystem, matching NOAH pair, unrelated files and container readback', flush=True)
    (published/'RELEASE-NOTES-1.1.2.md').write_bytes(notes)
    (published/'PACKAGING-VERIFICATION-1.1.2.json').write_bytes(encoded(dict(status='PASS',source_commit=commit,platforms=evidence)))
    index = dict(record, assets=results)
    (published/'BetterCPM-1.1.2-RELEASE.json').write_bytes(encoded(index))
    sums = {p.name:sha(p.read_bytes()) for p in published.iterdir() if p.is_file()}
    (published/'BetterCPM-1.1.2-SHA256SUMS.txt').write_text(''.join(f'{h}  {n}\n' for n,h in sorted(sums.items())))
    print('PASS: source and five release archives verified; output:',published)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base','output','binary'):
        parser.add_argument('--'+name,type=Path,required=True)
    args = parser.parse_args()
    package(args.base,args.output,args.binary)
