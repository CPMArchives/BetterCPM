"""Bind COMPARE's prepared native source and provenance to Utilities packages."""
import hashlib
import io
import json
from pathlib import Path
import tarfile
from component_inputs import source_path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def companions(root, source_companions, acceptance=None):
    root = Path(root)
    binary = (root/'build/utilities/COMPARE.COM').read_bytes()
    native = (root/'build/utilities/COMPARE-NATIVE.MAC').read_bytes()
    prepared = json.loads((root/'build/utilities/COMPARE-native.json').read_text())
    report = (root/'build/utilities/COMPARE-build-report.json').read_bytes()
    record = json.loads(report)
    if (prepared != {'binary_sha256':sha(binary), 'native_source_sha256':sha(native)}
            or record['artifact']['sha256'] != sha(binary)):
        raise ValueError('COMPARE prepared source or executable differs from build record')
    # The existing corresponding-source archive contains the full repository.
    # Check COMPARE's selected closure there; do not ship a redundant snapshot.
    with tarfile.open(fileobj=io.BytesIO(source_companions['BetterCPM-TED-SOURCE.tar.gz']), mode='r:gz') as archive:
        for name, wanted in record['input_record']['inputs']['files'].items():
            data = source_path(root, name).read_bytes()
            if sha(data) != wanted or archive.extractfile('BetterCPM-source/'+name).read() != data:
                raise ValueError('COMPARE corresponding source differs: '+name)
    files = {'COMPARE-NATIVE.MAC':native, 'COMPARE-Build-Provenance.json':report,
             'COMPARE-SOURCE-README.txt':b'''COMPARE 1.0 native build and corresponding source
Copy COMPARE-NATIVE.MAC to a native work disk as COMPARE.MAC, then run:
  ZSM4 COMPARE=COMPARE
  LINK COMPARE[A]
The prepared source includes the exact displayed identity and fixed storage.
The full repository, sources, tests and documentation travel in the shared
BetterCPM-TED-SOURCE.tar.gz archive under BetterCPM-source/. Retain it with
these images. COMPARE-Build-Provenance.json binds selected inputs and COM bytes.
COMPARE-Utilities-Acceptance.json, when supplied, binds runtime acceptance to
the exact paired images. Its absence is not a PASS.
'''}
    if acceptance:
        receipt = json.loads(acceptance.read_text())
        if receipt['binary']['sha256'] != sha(binary) or receipt['native_source_sha256'] != sha(native):
            raise ValueError('COMPARE acceptance differs from packaged native source')
        name = receipt['evidence']['name']
        if Path(name).name != name:
            raise ValueError('COMPARE evidence requires a simple filename')
        packed = (acceptance.parent/name).read_bytes()
        if sha(packed) != receipt['evidence']['sha256']:
            raise ValueError('COMPARE qualification evidence checksum differs')
        files['COMPARE-Utilities-Acceptance.json'] = acceptance.read_bytes()
        files[name] = packed
    return files


def validate_acceptance(receipt, files, target, image):
    proof = receipt['platforms'][target]
    if (receipt.get('compare_acceptance') != 'PASS' or proof.get('status') != 'PASS'
            or proof['utilities_sha256'] != sha(image)
            or receipt['binary']['sha256'] != sha(files['COMPARE.COM'])
            or not proof.get('system_sha256') or not proof.get('utilities_unchanged')
            or not proof.get('fixtures_unchanged') or not proof.get('native_cross_parity')):
        raise ValueError('COMPARE acceptance does not match packaged '+target)
    return proof
