#!/usr/bin/env python3
"""Read-only review of six BetterCP/M ZIPs. Writes an acceptance report separately."""
import argparse, hashlib, json, csv, subprocess, tempfile, sys, zipfile
from pathlib import Path, PurePosixPath
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('packages', type=Path)
p.add_argument('--repository', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
repo = a.repository.resolve()
sys.path.insert(0, str(repo / 'tools'))
from release_source import forbidden_digests, verify_members
from add_cpm_file_to_dmk import extract_raw
from convert_fdf_image import dmk_to_raw
from fdf_format import select_fdf
from build_z80pack_image import disk_definition
pins = json.loads((repo / 'docs/engineering/evidence/2026-11-04-qualification-35c56a03/identities.json').read_text())
locked = {}
reserved = {}
for row in csv.DictReader((repo / 'docs/engineering/evidence/2026-11-04-qualification-35c56a03/components.tsv').open(), delimiter='\t'):
    if row['class'] == 'RAM reserved system area':
        reserved[row['target']] = (int(row['component'].split()[0]), row['sha256'])
    if row['class'] in ('system file', 'utilities file', 'companion file') and row['status'] == 'locked':
        locked[row['target'], row['component']] = row['sha256']

def read_records(raw, fmt):
    mapping = fmt.raw_record_map()

    def record(n):
        (track, slot) = divmod(n, fmt.spt)
        at = (track * fmt.spt + mapping[slot]) * 128
        return raw[at:at + 128]

    def data(n):
        return record(fmt.reserved_records + n)
    directory = b''.join((data(n) for n in range((fmt.drm + 1) * 32 // 128)))
    parts = {}
    for at in range(0, len(directory), 32):
        e = directory[at:at + 32]
        if e[0] >= 32:
            continue
        name = e[1:9].decode().rstrip() + '.' + e[9:12].decode().rstrip()
        extent = (e[12] & 31) + (e[14] & 63) * 32
        count = (extent & fmt.exm) * 128 + e[15]
        blocks = [int.from_bytes(e[i:i + 2], 'little') for i in range(16, 32, 2)] if fmt.dsm > 255 else list(e[16:32])
        payload = b''.join((data(block * (1 << fmt.bsh) + n) for block in blocks if block for n in range(1 << fmt.bsh)))[:count * 128]
        parts.setdefault((e[0], name), {})[extent & ~fmt.exm] = payload
    return {key: b''.join((v[i] for i in sorted(v))) for (key, v) in parts.items()}
sha = lambda b: hashlib.sha256(b).hexdigest()
rows = []
seen = set()
commits = set()
ids = set()
failures = []
changes = []
open_items = []
found = set()
image_names = set()
for path in sorted(a.packages.glob('*.zip')):
    try:
        with zipfile.ZipFile(path) as z:
            assert len(set(z.namelist())) == len(z.namelist()), 'duplicate ZIP members'
            root = {n.split('/')[0] for n in z.namelist()}
            assert len(root) == 1
            root = root.pop() + '/'
            data = {n[len(root):]: z.read(n) for n in z.namelist() if not n.endswith('/')}
            assert all((not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts for n in data))
            sums = {n: v for (v, n) in (line.split(None, 1) for line in data['SHA256SUMS.txt'].decode().splitlines())}
            assert set(sums) == set(data) - {'SHA256SUMS.txt'}, 'checksum membership'
            assert all((sha(data[n]) == v for (n, v) in sums.items())), 'member checksum'
            rec = json.loads(data['RELEASE.json'])
            identity = json.loads(data['SOURCE-IDENTITY.json'])
            assert rec['source_commit'] == identity['source_commit']
            commits.add(rec['source_commit'])
            assert rec['package'] not in ids
            ids.add(rec['package'])
            for n in ['LICENSE', 'COPYING', 'NOTICE', 'CC-BY-4.0.txt']:
                assert 'licenses/BetterCPM/' + n in data
            assert 'docs/LICENSING.md' in data and 'THIRD-PARTY-NOTICES.txt' in data
            verify_members(data, forbidden_digests(repo), seen)
            report = {'package': rec['package'], 'zip': path.name, 'sha256': sha(path.read_bytes()), 'images': []}
            for (n, b) in data.items():
                if not n.startswith('images/') or not n.endswith(('.dmk', '.dsk')):
                    continue
                name = PurePosixPath(n).name
                image_names.add(name)
                if name in pins['reference_disk_images'] and sha(b) != pins['reference_disk_images'][name]:
                    changes.append(name)
                if 'Work-' in name:
                    continue
                target = 'trs80gp' if name.endswith('.dmk') else 'z80pack'
                receipt = json.loads(data['evidence/system-report.json'] if rec['package'].startswith('system-') else data['evidence/' + name + '.json'])
                assert receipt['sha256'] == sha(b) and receipt['source']['revision'] == rec['source_commit']
                with tempfile.TemporaryDirectory() as tmp:
                    work = Path(tmp)
                    raw = work / 'image.raw'
                    raw.write_bytes((extract_raw(b) if rec['package'].startswith('system-') else dmk_to_raw(b, select_fdf(repo / 'metadata/DISK.FDF', 'MMI008'))) if target == 'trs80gp' else b)
                    if rec['package'].startswith('system-'):
                        defs = data['images/diskdefs']
                    elif target == 'trs80gp':
                        defs = disk_definition(select_fdf(repo / 'metadata/DISK.FDF', 'MMI008')).encode()
                    else:
                        defs = b''
                    if target == 'z80pack' and (not rec['package'].startswith('system-')):
                        defs = b'diskdef bettercpm-default\n seclen 256\n tracks 80\n sectrk 18\n blocksize 2048\n maxdir 64\n skewtab 0,4,8,12,16,2,6,10,14,1,5,9,13,17,3,7,11,15\n boottrk 6\n os 2.2\nend\n'
                    (work / 'diskdefs').write_bytes(defs)
                    cmd = ['fsck.cpm', '-T', 'raw,pcw800' if target == 'trs80gp' and rec['package'].startswith('system-') else 'raw', '-f', 'bettercpm-default', '-n', str(raw)]
                    fs = subprocess.run(cmd, cwd=work, capture_output=True)
                    assert fs.returncode == 0, fs.stdout.decode(errors='replace')
                    if rec['package'].startswith('system-'):
                        length, expected_core = reserved[target]
                        if sha(raw.read_bytes()[:length]) != expected_core:
                            failures.append('Locked reserved system area changed: ' + target)
                    for f in receipt['included']:
                        dst = work / 'file'
                        subprocess.run(['cpmcp', '-T', 'raw,pcw800' if target == 'trs80gp' and rec['package'].startswith('system-') else 'raw', '-f', 'bettercpm-default', str(raw), f"{f.get('user', 0)}:{f['name']}", str(dst)], cwd=work, check=True, capture_output=True)
                        payload = dst.read_bytes()
                        if not rec['package'].startswith('system-'):
                            fmt = select_fdf(repo / 'metadata/DISK.FDF', 'MMI008' if target == 'trs80gp' else 'MMF017')
                            payload = read_records(raw.read_bytes(), fmt)[f.get('user', 0), f['name']]
                        assert len(payload) >= f['bytes'], f['name']
                        actual = sha(payload[:f['bytes']])
                        assert actual == f['sha256'], f['name']
                        found.add((target, f['name']))
                        expected = locked.get((target, f['name']))
                        if expected and expected != actual:
                            failures.append('Locked component changed: ' + target + '/' + f['name'])
                        if f['name'] in ('FDB.COM', 'CONFIG.COM', 'DISK.FDB'):
                            open_items.append([target, f['name'], actual])
                    report['images'].append({'name': name, 'sha256': sha(b), 'files_verified': len(receipt['included']), 'filesystem': 'PASS'})
            rows.append(report)
    except Exception as e:
        failures.append(path.name + ': ' + str(e))
expected = {'system-cpmsim', 'system-model4', 'utilities-cpmsim', 'utilities-model4', 'source', 'documentation'}
if ids != expected:
    failures.append('Expected all six package IDs')
if set(locked) - found:
    failures.append('Missing locked components: ' + str(sorted(set(locked) - found)))
if len(image_names) != 8:
    failures.append('Expected eight selected disk images')
if len(commits) != 1:
    failures.append('Mixed source commits')
result = {'status': 'FAIL' if failures else 'STATIC_CHECKS_PASS', 'freeze': 'HOLD', 'packages': rows, 'source_commits': sorted(commits), 'changed_images': changes, 'open_integration_components': open_items, 'failures': failures, 'remaining_gates': ['Final FDB/CONFIG/catalogue integration and placement', 'Catalogue binding/read and installation runtime acceptance', 'Source rebuild from the final exported ZIP', 'Final documentation sign-off', 'Affected regressions for changed media', 'Maintainer package freeze approval']}
a.output.write_text(json.dumps(result, indent=2) + '\n')
print(result['status'], len(rows), 'packages', len(changes), 'changed images')
print(*failures, sep='\n')
sys.exit(bool(failures))
