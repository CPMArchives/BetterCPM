"""Select distributable package sources and reject stale Montezuma payloads."""
import gzip
import hashlib
import io
from pathlib import Path, PurePosixPath
import subprocess
import tarfile
import zipfile


# Keep the accepted format data and their provenance in release source kits.
MM_REFERENCE_DATA = {'readme.md', 'config-extraction-manifest.json', 'disk.fdf', 'disk-int.fdf'}
MM_ANALYSIS = {'disk-format-mm-config-analysis.md', 'mm-config-reverse-engineering.md'}
MM_REFERENCE = 'third_party/montezuma/'


def excluded_path(name):
    path = PurePosixPath(name.lower())
    if path.name in MM_ANALYSIS or 'mmcpm232' in path.parts or path.name == 'mmcpm232.zip':
        return True
    return ('/' + MM_REFERENCE in '/' + str(path) and path.name not in MM_REFERENCE_DATA)


def source_files(root):
    root = Path(root).resolve()
    names = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z'])
    result = {}
    for raw in names.split(b'\0'):
        if not raw:
            continue
        name = raw.decode()
        path = (root / name).resolve()
        target = path.relative_to(root).as_posix()
        if not (excluded_path(name) or excluded_path(target)):
            result[name] = path.read_bytes()
    return result


def forbidden_digests(root):
    refs = Path(root) / MM_REFERENCE
    digests = {hashlib.sha256(path.read_bytes()).digest() for path in refs.iterdir()
               if path.is_file() and excluded_path(MM_REFERENCE + path.name)}
    excerpt = Path(root) / 'docs/engineering/DISK-FORMAT-MM-CONFIG-ANALYSIS.md'
    if excerpt.exists():
        digests.add(hashlib.sha256(excerpt.read_bytes()).digest())
    # Original DUP 2.01 and the complete historical disassembly archive.
    digests.update(bytes.fromhex(value) for value in (
        '71df2862c4a5f645353f9d07d8b97fc230737e712df5bd99609035e98d0aac31',
        'e6a76f496240c22b92090ec1721b28a345ac815f54eecdfd36a88579177f50db'))
    return digests


def verify_members(files, forbidden, inspected=None):
    """Check each member name even when two archive entries share bytes."""
    seen = set() if inspected is None else inspected

    def inspect(name, data, location):
        digest = hashlib.sha256(data).digest()
        if excluded_path(name) or digest in forbidden:
            raise ValueError('excluded Montezuma material: ' + location)
        if digest in seen:
            return
        stream = io.BytesIO(data)
        if data.startswith(b'PK') and zipfile.is_zipfile(stream):
            with zipfile.ZipFile(stream) as archive:
                for member in archive.infolist():
                    if not member.is_dir():
                        inspect(member.filename, archive.read(member), location + '!' + member.filename)
        elif data[:2] == b'\x1f\x8b':
            inspect(name.removesuffix('.gz'), gzip.decompress(data), location + '!gzip')
        elif name.lower().endswith('.tar') or data[257:262] == b'ustar':
            with tarfile.open(fileobj=stream, mode='r:') as archive:
                for member in archive:
                    if member.isfile():
                        inspect(member.name, archive.extractfile(member).read(), location + '!' + member.name)
                    elif not member.isdir():
                        raise ValueError('unsupported nested archive member: ' + location + '!' + member.name)
        seen.add(digest)

    for name, data in files.items():
        inspect(name, data, name)
