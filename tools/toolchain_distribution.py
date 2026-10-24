"""Verify selected native tools and supply their redistribution companions."""
import hashlib
import io
import json
import tarfile


def validate_acceptance(receipt, files, platform, image, accompanying):
    """Bind qualification to both tools, all cases, media and source companions."""
    sha = lambda data: hashlib.sha256(data).hexdigest()
    proof = receipt['platforms'][platform]
    required = {'PROBE', 'SQ', 'USQ', 'CR', 'UNCR', 'LZH', 'UNLZH'}
    if (receipt.get('status') != 'PASS' or proof.get('status') != 'PASS'
            or proof.get('system_audit_status') != 'PASS'
            or set(proof['cases']) != required
            or any(row.get('status') != 'PASS' for row in proof['cases'].values())
            or proof['utilities_sha256'] != sha(image)
            or receipt['tools_sha256'] != {n:sha(files[n]) for n in ('ZSM4.COM', 'LINK.COM')}
            or receipt['companions_sha256'] != {n:sha(d) for n,d in accompanying.items()}):
        raise ValueError('toolchain acceptance does not match packaged ' + platform)


def companions(root):
    z = root / 'third_party/zsm4'
    link = root / 'third_party/dri-link'
    zm = json.loads((z / 'provenance.json').read_text())
    lm = json.loads((link / 'provenance.json').read_text())
    sha = lambda data: hashlib.sha256(data).hexdigest()
    for name, expected in zm['files_sha256'].items():
        if sha((z / name).read_bytes()) != expected:
            raise ValueError('ZSM4 provenance mismatch: ' + name)
    if sha((link / 'LINK.COM').read_bytes()) != lm['binary_sha256']:
        raise ValueError('LINK provenance mismatch')
    if sha((link / 'permission.html').read_bytes()) != lm['redistribution']['permission_sha256']:
        raise ValueError('LINK permission record mismatch')
    archive = (z / 'source.tar.gz').read_bytes()
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as source:
        for name, expected in [('bin/zsm4.com', (z / 'ZSM4.COM').read_bytes()),
                               ('LICENSE', (z / 'LICENSE').read_bytes())]:
            if source.extractfile('zsm4-source/' + name).read() != expected:
                raise ValueError('ZSM4 source companion mismatch: ' + name)
        required = {'Makefile', 'zsm.mac', 'zsm.inc', 'cpmio.mac', 'alloc.mac',
                    'symbols.mac', 'listing.mac', 'eval.mac', 'macros.mac', 'genrel.mac'}
        if not {'zsm4-source/' + n for n in required} <= set(source.getnames()):
            raise ValueError('incomplete ZSM4 corresponding source')
    # Ensure readable on-disk notices contain the exact retained license text.
    for name, license_path in [('ZSM4COPY.TXT', z / 'LICENSE'),
                               ('LINKCOPY.TXT', link / 'LICENSE')]:
        notice = (root / 'src/distribution' / name).read_bytes()
        if notice != license_path.read_text().replace('\n', '\r\n').encode() + b'\x1a':
            raise ValueError('on-disk license mismatch: ' + name)
    return {
        'ZSM4-SOURCE.tar.gz': archive,
        'Toolchain-Provenance.json': (json.dumps({'ZSM4': zm, 'LINK': lm}, indent=2) + '\n').encode(),
        'LINK-Permission.html': (link / 'permission.html').read_bytes(),
        'TOOLCHAIN-README.txt': (
            'ZSM4 4.7 and Digital Research LINK 1.3\n\n'
            'Distribute this complete package, including ZSM4-SOURCE.tar.gz,\n'
            'with the Utilities images. It contains the complete corresponding\n'
            'source, original build scripts, manuals, notices and GPL terms.\n'
            'The disk images contain TOOLINFO.TXT, ZSM4COPY.TXT and LINKCOPY.TXT.\n'
            'Toolchain-Provenance.json records exact versions, hashes and origins.\n'
            'LINK-Permission.html retains the published CP/M permission.\n'
        ).encode(),
    }
