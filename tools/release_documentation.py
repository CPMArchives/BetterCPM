"""GPL-2.0-or-later. Reader-oriented documentation build; software is read-only."""
import hashlib
import json
import posixpath
import re
import subprocess
import urllib.parse
import zipfile
from pathlib import Path, PurePosixPath

SELECTION_PATH = 'packaging/1.0/documentation-selection.json'
SOFTWARE_PATH = 'packaging/1.0/software-packages-1.0.json'
FINAL_NAME = 'BetterCPM-1.0-Documentation.zip'
ROOT_NAME = 'BetterCPM-1.0-Documentation'
LIMIT = 100 * 1024 * 1024
MANIFEST = 'Provenance/MANIFEST.json'
IDENTITY = 'Provenance/SOURCE-IDENTITY.json'
SUMS = 'Provenance/SHA256SUMS.txt'
MANUALS = ('Users-Guide.md', 'Command-and-Utilities-Reference.md',
           'Programmers-Guide.md', 'Practical-Porting-Guide.md')


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
    if not name or '\\' in name or PurePosixPath(name).is_absolute() or any(p in ('', '.', '..') for p in name.split('/')):
        raise ValueError('Unsafe archive/input path: ' + name)
    return name


def read_source(repo, name, revision=None):
    safe_name(name)
    if revision:
        return subprocess.check_output(['git', '-C', str(repo), 'show', revision + ':' + name])
    path = Path(repo) / name
    path.resolve().relative_to(Path(repo).resolve())
    if not path.is_file() or path.is_symlink():
        raise ValueError('Missing regular input: ' + name)
    return path.read_bytes()


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
    target = target[1:-1] if target.startswith('<') and target.endswith('>') else target
    path, _, fragment = urllib.parse.unquote(target).partition('#')
    return (posixpath.normpath(posixpath.join(posixpath.dirname(name), path)) if path else name), fragment


def links(text):
    text = re.sub(r'```.*?```', '', text, flags=re.S)
    return re.findall(r'\[[^\n]*?\]\(([^\n]*?)\)', text) + re.findall(r'(?m)^\s*\[[^\]]+\]:\s*(\S+)', text) + re.findall(r'href=["\']([^"\']+)["\']', text)


def excluded(name):
    return (PurePosixPath(name).suffix.lower() in ('.pdf', '.docx', '.zip', '.gz', '.tar', '.com', '.bin', '.dsk', '.dmk') or
            any(x in name.lower() for x in ('utilities_manual', 'users_guide_backup', '/development/', 'manual_entry', 'packaging-history')))


def selection_mapping(selection):
    mapping = {}
    for source in selection['manuals']:
        mapping[PurePosixPath(source).name] = source
    for source in selection['references']:
        mapping['Supporting-Reference/' + source.removeprefix('docs/')] = source
    for source in selection['license_records']:
        mapping['Licenses/' + source] = source
    for source in ('LICENSE', 'COPYING', 'NOTICE'):
        mapping['Licenses/BetterCPM/' + source] = source
    mapping['Licenses/BetterCPM/CC-BY-4.0.txt'] = 'LICENSES/CC-BY-4.0.txt'
    mapping['README.md'] = 'packaging/1.0/README-Documentation.md'
    mapping['Provenance/selection.json'] = SELECTION_PATH
    mapping['Provenance/SOFTWARE-PACKAGES.json'] = SOFTWARE_PATH
    if len(selection['manuals']) != 4 or set(PurePosixPath(x).name for x in selection['manuals']) != set(MANUALS):
        raise ValueError('Expected four clearly named manuals')
    if len(mapping) != len(set(mapping.values())):
        raise ValueError('Duplicate selected source')
    return mapping


def remap_links(source, dest, data, mapping, software, overrides):
    if not source.endswith(('.md', '.txt')) or dest.startswith('Licenses/'):
        return data
    reverse = {s: d for d, s in mapping.items()}
    reverse['docs/README.md'] = 'README.md'
    def target(link):
        if re.match(r'\w+://|mailto:', link):
            return link
        old, fragment = resolve_link(source, link)
        if old in reverse:
            path = posixpath.relpath(reverse[old], posixpath.dirname(dest) or '.')
            if reverse[old] == dest and fragment:
                path = ''
            result = urllib.parse.quote(path, safe='/._-')
        elif any(s.startswith(old.rstrip('/') + '/') for s in reverse):
            targets = [reverse[s] for s in reverse if s.startswith(old.rstrip('/') + '/')]
            directory = posixpath.commonpath(targets)
            result = urllib.parse.quote(posixpath.relpath(directory, posixpath.dirname(dest) or '.'), safe='/._-')
        else:
            if old.startswith(('../', '/')):
                raise ValueError('Link escapes repository: ' + source + ' -> ' + link)
            override = overrides.get(old, {})
            result = 'https://github.com/CPMArchives/BetterCPM/blob/' + override.get('revision', software) + '/' + urllib.parse.quote(override.get('path', old), safe='/')
        return result + ('#' + fragment if fragment else '')
    parts = re.split(r'(```.*?```)', data.decode(), flags=re.S)
    for i in range(0, len(parts), 2):
        text = re.sub(r'\[([^\n]*?)\]\(([^\n]*?)\)', lambda m: '[' + m[1] + '](' + target(m[2]) + ')', parts[i])
        text = re.sub(r'(?m)^(\s*\[[^\]]+\]:\s*)(\S+)', lambda m: m[1] + target(m[2]), text)
        parts[i] = re.sub(r'(href=["\'])([^"\']+)(["\'])', lambda m: m[1] + target(m[2]) + m[3], text)
    return ''.join(parts).encode()


def check_links(files):
    count = 0
    for name, data in files.items():
        if not name.endswith(('.md', '.txt')) or name.startswith(('Licenses/', 'Provenance/')):
            continue
        for link in links(data.decode()):
            if re.match(r'\w+://|mailto:', link):
                continue
            target, fragment = resolve_link(name, link)
            if target not in files:
                if any(n.startswith(target.rstrip('/') + '/') for n in files):
                    count += 1
                    continue
                raise ValueError('Broken package link: ' + name + ' -> ' + link)
            if fragment and target.endswith(('.md', '.txt')) and fragment not in heading_ids(files[target].decode()):
                raise ValueError('Broken package anchor: ' + name + ' -> ' + link)
            count += 1
    return count


def build_files(repo, revision=None):
    selection_raw = read_source(repo, SELECTION_PATH, revision)
    selection = json.loads(selection_raw)
    baseline_raw = read_source(repo, SOFTWARE_PATH, revision)
    baseline = json.loads(baseline_raw)
    if revision == baseline['software_source_revision']:
        raise ValueError('Documentation revision must be separate from locked software')
    mapping = selection_mapping(selection)
    files, inputs = {}, {}
    for dest, source in mapping.items():
        safe_name(dest)
        if excluded(dest):
            raise ValueError('Excluded documentation member: ' + dest)
        raw = read_source(repo, source, revision)
        inputs[source] = sha(raw)
        files[dest] = remap_links(source, dest, raw, mapping, baseline['software_source_revision'], selection.get('external_references', {}))
    identity = {'schema': 3, 'documentation_revision': revision,
                'documentation_source': {'kind': 'commit' if revision else 'authoring-preview', 'revision': revision, 'input_manifest_sha256': sha(encoded(inputs))},
                'software_source_revision': baseline['software_source_revision'],
                'qualification_merge_revision': baseline['qualification_merge_revision'],
                'software_packages': baseline['packages'],
                'software_scope': 'No software/source/media changes; documentation independently rebuilt.'}
    files[IDENTITY] = encoded(identity)
    files[MANIFEST] = encoded({**identity, 'package': 'documentation', 'format': 'Markdown/text',
                               'manuals': list(MANUALS), 'source_files': inputs,
                               'files': {n: sha(d) for n, d in files.items()},
                               'local_links_verified': check_links(files),
                               'evidence_limits': 'New example native/runtime trials and further programmer/porting expansion remain separate from locked 1.0 software scope.'})
    files[SUMS] = ''.join(sha(d) + '  ' + n + '\n' for n, d in sorted(files.items())).encode()
    return files


def assemble(repo, output, *, revision=None, preview=False):
    repo, output = Path(repo).resolve(), Path(output).resolve()
    if bool(revision) == bool(preview):
        raise ValueError('Choose actual revision OR preview')
    if revision:
        if not re.fullmatch('[0-9a-f]{40}', revision):
            raise ValueError('Expected full actual documentation commit')
        subprocess.run(['git', '-C', str(repo), 'rev-parse', '--verify', revision + '^{commit}'], check=True, capture_output=True)
    if output.exists():
        raise ValueError('Output already exists; no overwrite')
    if preview and ('review' not in output.name.lower() or output.name == FINAL_NAME):
        raise ValueError('Preview needs distinct review filename')
    if not preview and output.name != FINAL_NAME:
        raise ValueError('Expected final Documentation filename')
    files = build_files(repo, revision)
    if sum(map(len, files.values())) > LIMIT:
        raise ValueError('Documentation exceeds size bound')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(files.items()):
            item = zipfile.ZipInfo(ROOT_NAME + '/' + name, (1980, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            z.writestr(item, data)
    return verify_documentation(output, repo=repo, allow_preview=preview)


def verify_documentation(path, *, repo, allow_preview=False):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if not names or len(names) != len(set(names)) or sum(i.file_size for i in z.infolist()) > LIMIT:
            raise ValueError('Duplicate/empty/oversized archive')
        files = {}
        for n in names:
            safe_name(n)
            prefix, _, name = n.partition('/')
            if prefix != ROOT_NAME or not name or n.endswith('/') or ((z.getinfo(n).external_attr >> 16) & 0o170000) not in (0, 0o100000):
                raise ValueError('Unexpected root or non-regular member')
            files[name] = z.read(n)
    if not {IDENTITY, MANIFEST, SUMS, 'README.md', *MANUALS} <= files.keys():
        raise ValueError('Missing manual/provenance record')
    sums = {}
    for line in files[SUMS].decode().splitlines():
        h, n = line.split('  ', 1)
        safe_name(n)
        if n in sums:
            raise ValueError('Duplicate checksum')
        sums[n] = h
    if set(sums) != files.keys() - {SUMS} or any(sha(files[n]) != h for n, h in sums.items()):
        raise ValueError('Member checksum mismatch')
    identity = json.loads(files[IDENTITY])
    revision = identity['documentation_revision']
    if revision is None and not allow_preview:
        raise ValueError('Preview cannot satisfy final acceptance')
    if revision is not None and not re.fullmatch('[0-9a-f]{40}', revision):
        raise ValueError('Invalid revision')
    expected = build_files(Path(repo), revision)
    if files != expected:
        raise ValueError('Package bytes/membership differ from actual documentation source')
    return {'package': 'documentation', 'filename': Path(path).name, 'sha256': file_sha(path), 'size_bytes': Path(path).stat().st_size,
            'documentation_revision': revision, 'software_source_revision': identity['software_source_revision'],
            'files_verified': len(files), 'local_links_verified': check_links(files),
            'status': 'REVIEW_PASS' if revision is None else 'DOCUMENTATION_VERIFIED'}


def verify_software(folder, baseline):
    rows = []
    for row in baseline['packages']:
        p = Path(folder) / safe_name(row['filename'])
        if not p.is_file() or p.is_symlink() or p.stat().st_size != row['size_bytes'] or file_sha(p) != row['sha256']:
            raise ValueError('Software/evidence package identity mismatch: ' + row['filename'])
        rows.append(row)
    return rows
