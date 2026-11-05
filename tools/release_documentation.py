"""GPL-2.0-or-later. Documentation-only assembly and split-identity checks."""
import hashlib
import json
import posixpath
import re
import subprocess
import urllib.parse
import zipfile
from pathlib import Path, PurePosixPath

LOCK_PATH = 'docs/releases/non-documentation-lock-1.0/LOCK.json'
SELECTION_PATH = 'packaging/1.0/documentation-selection.json'
FINAL_NAME = 'BetterCPM-1.0-Documentation.zip'
ROOT_NAME = 'BetterCPM-1.0-Documentation'
LIMIT = 100 * 1024 * 1024


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def safe_name(name):
    if (not name or PurePosixPath(name).is_absolute() or '\\' in name or
            any(p in ('', '.', '..') for p in name.split('/'))):
        raise ValueError('Unsafe archive/input name: ' + name)
    return name


def read_source(repo, name, revision=None):
    safe_name(name)
    if revision:
        return subprocess.check_output(['git', '-C', str(repo), 'show', revision + ':' + name])
    path = repo / name
    path.resolve().relative_to(repo.resolve())
    if path.is_symlink() or not path.is_file():
        raise ValueError('Missing regular input: ' + name)
    return path.read_bytes()


def load_lock(repo, revision=None):
    raw = read_source(repo, LOCK_PATH, revision)
    lock = json.loads(raw)
    expected = {'source', 'system-model4', 'system-cpmsim', 'utilities-model4', 'utilities-cpmsim'}
    if len(lock['packages']) != 5 or {p['package'] for p in lock['packages']} != expected:
        raise ValueError('Expected five locked identities')
    if len({p['filename'] for p in lock['packages']}) != 5:
        raise ValueError('Duplicate locked filename')
    for p in lock['packages']:
        safe_name(p['filename'])
        if not re.fullmatch('[0-9a-f]{64}', p['sha256']) or p['size_bytes'] <= 0:
            raise ValueError('Invalid locked identity')
    return lock, raw


def lock_rows(lock):
    return [{k: p[k] for k in ('package', 'filename', 'sha256', 'size_bytes')} for p in lock['packages']]


def locked_files(folder, lock):
    rows = []
    for row in lock['packages']:
        p = folder / row['filename']
        if not p.is_file() or p.is_symlink():
            raise ValueError('Missing regular locked package: ' + str(p))
        if p.stat().st_size != row['size_bytes'] or file_sha(p) != row['sha256']:
            raise ValueError('Locked package identity changed: ' + p.name)
        rows.append({**{k: row[k] for k in ('package', 'filename', 'sha256', 'size_bytes')}, 'verification': 'EXACT_LOCK_MATCH'})
    return rows


def heading_ids(text):
    result = set(re.findall(r'<a id="([^"]+)"', text))
    seen = {}
    for line in re.sub(r'```.*?```', '', text, flags=re.S).splitlines():
        m = re.match(r'^#{1,6} (.+)', line)
        if m:
            title = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', m[1])
            key = re.sub(r'[^\w\- ]', '', title.lower()).replace(' ', '-')
            n = seen.get(key, 0)
            seen[key] = n + 1
            result.add(key + ('-' + str(n) if n else ''))
    return result


def resolve_link(name, target):
    path, _, fragment = urllib.parse.unquote(target).partition('#')
    return (posixpath.normpath(posixpath.join(posixpath.dirname(name), path)) if path else name), fragment


def rewrite_links(name, data, members, software, overrides):
    if not name.endswith('.md') or name.startswith('licenses/'):
        return data
    def replace(m):
        if re.match(r'\w+://|mailto:', m[2]):
            return m[0]
        target, fragment = resolve_link(name, m[2])
        if target in members or any(n.startswith(target.rstrip('/') + '/') for n in members):
            return m[0]
        if target.startswith(('../', '/')):
            raise ValueError('Link escapes collection: ' + name + ' -> ' + m[2])
        override = overrides.get(target, {})
        url = ('https://github.com/CPMArchives/BetterCPM/blob/' + override.get('revision', software) + '/' +
               urllib.parse.quote(override.get('path', target), safe='/'))
        return '[' + m[1] + '](' + url + ('#' + fragment if fragment else '') + ')'
    chunks = re.split(r'(```.*?```)', data.decode(), flags=re.S)
    for i in range(0, len(chunks), 2):
        chunks[i] = re.sub(r'\[([^\n]*?)\]\(([^\n]*?)\)', replace, chunks[i])
    return ''.join(chunks).encode()


def check_links(files):
    count = 0
    for name, data in files.items():
        if not name.endswith('.md') or name.startswith('licenses/'):
            continue
        text = re.sub(r'```.*?```', '', data.decode(), flags=re.S)
        for link in re.findall(r'\[[^\n]*?\]\(([^\n]*?)\)', text):
            if re.match(r'\w+://|mailto:', link):
                continue
            target, fragment = resolve_link(name, link)
            if target not in files:
                if not any(n.startswith(target.rstrip('/') + '/') for n in files):
                    raise ValueError('Broken package link: ' + name + ' -> ' + link)
            elif fragment and target.endswith('.md') and fragment not in heading_ids(files[target].decode()):
                raise ValueError('Broken package anchor: ' + name + ' -> ' + link)
            count += 1
    return count


def excluded(name):
    return (PurePosixPath(name).suffix.lower() in ('.pdf', '.docx', '.zip', '.gz', '.tar', '.com', '.bin', '.dsk', '.dmk') or
            '/development/' in name or 'users_guide_backup' in name or '/montezuma/' in name)


def selection_mapping(selection):
    mapping = {n: n for n in selection['files'] + selection['publication_tools']}
    mapping.update({'licenses/' + n: n for n in selection['license_records']})
    mapping.update({'licenses/BetterCPM/' + n: n for n in ('LICENSE', 'COPYING', 'NOTICE')})
    mapping['licenses/BetterCPM/CC-BY-4.0.txt'] = 'LICENSES/CC-BY-4.0.txt'
    mapping.update({'CONTENTS.md': 'packaging/1.0/DOCUMENTATION-CONTENTS.md', 'README.txt': 'packaging/1.0/README-Documentation.txt', SELECTION_PATH: SELECTION_PATH})
    return mapping


def assemble(repo, output, *, revision=None, preview=False):
    repo, output = Path(repo).resolve(), Path(output).resolve()
    if bool(revision) == bool(preview):
        raise ValueError('Choose an actual commit OR an explicit preview')
    if revision:
        if not re.fullmatch('[0-9a-f]{40}', revision):
            raise ValueError('Documentation revision must be a full actual commit')
        actual = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', revision + '^{commit}']).decode().strip()
        if actual != revision:
            raise ValueError('Not the exact documentation commit')
    lock, raw = load_lock(repo, revision)
    if revision == lock['software_source_revision']:
        raise ValueError('Old software revision is not the new documentation revision')
    if output.exists():
        raise ValueError('Output already exists; no overwrite')
    if preview and ('review' not in output.name.lower() or output.name == FINAL_NAME):
        raise ValueError('Preview requires a distinct review ZIP filename')
    if not preview and output.name != FINAL_NAME:
        raise ValueError('Committed candidate requires Documentation filename')
    if output.suffix.lower() != '.zip':
        raise ValueError('Expected ZIP output')
    selection_raw = read_source(repo, SELECTION_PATH, revision)
    selection = json.loads(selection_raw)
    mapping = selection_mapping(selection)
    files, inputs = {}, {}
    for dest, source in mapping.items():
        safe_name(dest)
        if excluded(dest):
            raise ValueError('Excluded publication input: ' + dest)
        files[dest] = read_source(repo, source, revision)
        inputs[source] = sha(files[dest])
    if not set(selection['manuals']) <= files.keys():
        raise ValueError('Missing principal manual')
    files['THIRD-PARTY-NOTICES.txt'] = (
        'BetterCP/M documentation collection\n\n'
        'Original prose/illustrations: CC BY 4.0. Original software/tools/reusable examples: GPL-2.0-or-later.\n'
        'Keep licenses/BetterCPM and licenses/third_party. No new rightsholder grant is asserted.\n'
        'This selection contains manuals, examples and legal/provenance text, not historical scans/software/source archives.\n'
        'The five locked downloads retain their independent source/notice obligations.\n'
        'Historical format data retain their provenance and distribution rights undetermined notice. Original Montezuma DISK.FDF, utilities and disassemblies are excluded.\n'
        'See docs/LICENSING.md and docs/LICENSING-INVENTORY.md for attribution, sources and exclusions.\n').encode()
    origin = {'kind': 'commit' if revision else 'working-tree-review-snapshot', 'revision': revision,
              'base_commit': revision or subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD']).decode().strip(),
              'manifest_sha256': sha(encoded(inputs))}
    identity = {'schema': 2, 'software_source_revision': lock['software_source_revision'],
                'documentation_revision': revision, 'documentation_source': origin}
    files['SOURCE-IDENTITY.json'] = encoded(identity)
    known = set(files) | {'RELEASE.json', 'SHA256SUMS.txt'}
    files = {n: rewrite_links(n, d, known, lock['software_source_revision'], selection.get('external_references', {})) for n, d in files.items()}
    links = check_links(files)
    record = {**identity, 'package': 'documentation', 'version': '1.0',
              'status': 'AUTHORING_PREVIEW_NOT_ACCEPTED' if preview else 'DOCUMENTATION_CANDIDATE_NOT_ACCEPTED',
              'qualification_merge_revision': lock['qualification_merge_revision'], 'locked_packages': lock_rows(lock),
              'lock_sha256': sha(raw), 'selection_sha256': sha(selection_raw), 'source_files': inputs,
              'files': {n: sha(d) for n, d in files.items()},
              'checks': {'local_links': links, 'runtime_qualification': 'NOT_CLAIMED', 'publication': 'HOLD'}}
    files['RELEASE.json'] = encoded(record)
    files['SHA256SUMS.txt'] = ''.join(sha(d) + '  ' + n + '\n' for n, d in sorted(files.items())).encode()
    if sum(map(len, files.values())) > LIMIT:
        raise ValueError('Documentation exceeds bounded size')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(ROOT_NAME + '/' + name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return {'filename': output.name, 'sha256': file_sha(output), 'size_bytes': output.stat().st_size,
            **verify_documentation(output, lock, raw, allow_preview=preview, repo=repo)}


def verify_documentation(path, lock, raw, *, allow_preview=False, repo=None):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if not names or len(names) != len(set(names)):
            raise ValueError('Duplicate/empty documentation ZIP')
        if sum(i.file_size for i in archive.infolist()) > LIMIT:
            raise ValueError('Documentation exceeds bounded size')
        files = {}
        for name in names:
            safe_name(name)
            prefix, slash, relative = name.partition('/')
            if prefix != ROOT_NAME or not slash or name.endswith('/'):
                raise ValueError('Unexpected documentation root/member')
            if ((archive.getinfo(name).external_attr >> 16) & 0o170000) not in (0, 0o100000):
                raise ValueError('Non-regular documentation member')
            files[relative] = archive.read(name)
    required = {'RELEASE.json', 'SOURCE-IDENTITY.json', 'SHA256SUMS.txt', 'README.txt', 'CONTENTS.md',
                'THIRD-PARTY-NOTICES.txt', 'docs/LICENSING.md', 'docs/LICENSING-INVENTORY.md', SELECTION_PATH, LOCK_PATH}
    required |= {'licenses/BetterCPM/' + n for n in ('LICENSE', 'COPYING', 'NOTICE', 'CC-BY-4.0.txt')}
    if not required <= files.keys():
        raise ValueError('Missing required documentation records/notices')
    sums = {}
    for line in files['SHA256SUMS.txt'].decode().splitlines():
        h, n = line.split('  ', 1)
        safe_name(n)
        if n in sums or not re.fullmatch('[0-9a-f]{64}', h):
            raise ValueError('Invalid/duplicate checksum')
        sums[n] = h
    if set(sums) != files.keys() - {'SHA256SUMS.txt'} or any(sha(files[n]) != h for n, h in sums.items()):
        raise ValueError('Documentation member checksum/membership mismatch')
    rec, identity = json.loads(files['RELEASE.json']), json.loads(files['SOURCE-IDENTITY.json'])
    if rec['schema'] != 2 or rec['package'] != 'documentation':
        raise ValueError('Not split-provenance documentation')
    for k in ('software_source_revision', 'documentation_revision', 'documentation_source'):
        if rec[k] != identity[k]:
            raise ValueError('Source identities disagree')
    if rec['software_source_revision'] != lock['software_source_revision'] or rec['qualification_merge_revision'] != lock['qualification_merge_revision']:
        raise ValueError('Wrong software/qualification source')
    if rec['lock_sha256'] != sha(raw) or files[LOCK_PATH] != raw or rec['locked_packages'] != lock_rows(lock):
        raise ValueError('Five-package lock reference changed')
    origin = rec['documentation_source']
    if origin['manifest_sha256'] != sha(encoded(rec['source_files'])):
        raise ValueError('Input manifest mismatch')
    rev = rec['documentation_revision']
    if origin['kind'] == 'working-tree-review-snapshot':
        if not allow_preview or rev is not None or rec['status'] != 'AUTHORING_PREVIEW_NOT_ACCEPTED':
            raise ValueError('Preview is not a committed documentation candidate')
    elif (origin['kind'] != 'commit' or not isinstance(rev, str) or not re.fullmatch('[0-9a-f]{40}', rev) or
          origin['revision'] != rev or rev == lock['software_source_revision'] or rec['status'] != 'DOCUMENTATION_CANDIDATE_NOT_ACCEPTED'):
        raise ValueError('Invalid separate documentation revision')
    if set(rec['files']) != files.keys() - {'RELEASE.json', 'SHA256SUMS.txt'} or any(sha(files[n]) != h for n, h in rec['files'].items()):
        raise ValueError('Release member manifest mismatch')
    selection = json.loads(files[SELECTION_PATH])
    if rec['selection_sha256'] != sha(files[SELECTION_PATH]):
        raise ValueError('Selection identity mismatch')
    mapping = selection_mapping(selection)
    if set(rec['source_files']) != set(mapping.values()):
        raise ValueError('Selected input membership mismatch')
    for dest, source in mapping.items():
        if dest.startswith('licenses/') and sha(files[dest]) != rec['source_files'][source]:
            raise ValueError('Legal record was not copied verbatim')
    if rev is not None:
        if repo is None:
            raise ValueError('Committed documentation needs source revision verification')
        actual = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', rev + '^{commit}']).decode().strip()
        source_bytes = {n: read_source(Path(repo), n, rev) for n in rec['source_files']}
        if actual != rev or any(sha(source_bytes[n]) != h for n, h in rec['source_files'].items()):
            raise ValueError('Actual documentation commit/input bytes disagree')
        for dest, source in mapping.items():
            expected_bytes = rewrite_links(dest, source_bytes[source], set(files),
                                           lock['software_source_revision'], selection.get('external_references', {}))
            if files[dest] != expected_bytes:
                raise ValueError('Packaged document differs from actual commit: ' + dest)
    expected = set(mapping) | {'THIRD-PARTY-NOTICES.txt', 'SOURCE-IDENTITY.json', 'RELEASE.json', 'SHA256SUMS.txt'}
    if set(files) != expected or not set(selection['manuals']) <= files.keys() or any(excluded(n) for n in files):
        raise ValueError('Invalid selection/edition membership')
    return {'package': 'documentation', 'filename': Path(path).name, 'sha256': file_sha(path), 'size_bytes': Path(path).stat().st_size, 'documentation_revision': rev, 'documentation_source': origin,
            'files_verified': len(files), 'local_links_verified': check_links(files),
            'status': 'REVIEW_STATIC_CHECKS_PASS' if rev is None else 'DOCUMENTATION_STATIC_CHECKS_PASS', 'publication': 'HOLD'}
