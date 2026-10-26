"""Keep SEARCH's prepared native source, provenance and evidence with Utilities."""
import hashlib
import io
import json
from pathlib import Path
import tarfile
from component_inputs import source_path

sha=lambda data:hashlib.sha256(data).hexdigest()


def companions(root,source_companions,acceptance=None):
    binary=(root/'build/utilities/SEARCH.COM').read_bytes()
    native=(root/'build/utilities/SEARCH-NATIVE.MAC').read_bytes()
    prepared=json.loads((root/'build/utilities/SEARCH-native.json').read_text())
    report=(root/'build/utilities/SEARCH-build-report.json').read_bytes()
    record=json.loads(report)
    if prepared!={'binary_sha256':sha(binary),'native_source_sha256':sha(native)} or record['artifact']['sha256']!=sha(binary):
        raise ValueError('SEARCH prepared source or executable differs from build record')
    # The existing full-repository GPL companion already contains SEARCH. Check
    # every selected input there rather than adding a redundant third snapshot.
    with tarfile.open(fileobj=io.BytesIO(source_companions['BetterCPM-TED-SOURCE.tar.gz']),mode='r:gz') as archive:
        for name,wanted in record['input_record']['inputs']['files'].items():
            data=source_path(root,name).read_bytes()
            if sha(data)!=wanted or archive.extractfile('BetterCPM-source/'+name).read()!=data:
                raise ValueError('SEARCH corresponding source differs: '+name)
    files={'SEARCH-NATIVE.MAC':native,'SEARCH-Build-Provenance.json':report,
        'SEARCH-SOURCE-README.txt':b'''SEARCH 1.0 native build and corresponding source
SEARCH-NATIVE.MAC includes the exact prepared numeric identity and fixed storage.
Copy SEARCH-NATIVE.MAC to the native filesystem as SEARCH.MAC, then run:
  ZSM4 SEARCH=SEARCH
  LINK SEARCH[A]
The complete tracked repository, SEARCH sources, tests, documentation, input
baselines and licenses are in BetterCPM-TED-SOURCE.tar.gz under BetterCPM-source/.
That existing full-repository source companion is shared; retain it with these
images. SEARCH-Build-Provenance.json binds every selected source input and the
exact program checksum. SEARCH-Utilities-Acceptance.json, when supplied, binds
execution to the exact paired images; absent evidence is not a PASS.
'''}
    if acceptance:
        receipt=json.loads(acceptance.read_text())
        if receipt['binary']['sha256']!=sha(binary) or receipt['native_source_sha256']!=sha(native):
            raise ValueError('SEARCH acceptance differs from packaged native source')
        name=receipt['evidence']['name']
        if Path(name).name!=name:
            raise ValueError('SEARCH evidence requires a simple filename')
        evidence=acceptance.parent/name
        packed=evidence.read_bytes()
        if sha(packed)!=receipt['evidence']['sha256']:
            raise ValueError('SEARCH qualification evidence checksum differs')
        files['SEARCH-Utilities-Acceptance.json']=acceptance.read_bytes()
        files[evidence.name]=packed
    return files
