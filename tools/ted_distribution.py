"""Deterministic corresponding source companion for the GPL TED adaptation."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


def companions(root):
    root=Path(root)
    names=subprocess.run(['git','-C',str(root),'ls-files','-z'],check=True,capture_output=True).stdout.split(b'\0')
    files={n.decode():(root/n.decode()).read_bytes() for n in names if n}
    plan=json.loads((root/'metadata/component-inputs.json').read_text())['components']['utility:TED']
    required=set(plan['files'])|{'tools/ted_distribution.py','src/distribution/TED.TXT','src/distribution/TEDCOPY.TXT'}
    if not required<=files.keys():raise ValueError('TED source companion requires tracked implementation files')
    record=json.loads((root/'build/utilities/TED-build-report.json').read_text())
    if record['artifact']['sha256']!=hashlib.sha256((root/'build/utilities/TED.COM').read_bytes()).hexdigest():
        raise ValueError('TED binary differs from build record')
    for name,wanted in record['input_record']['inputs']['files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=wanted:
            raise ValueError('TED corresponding source differs from build inputs: '+name)
    native=(root/'build/utilities/TEDNAT.MAC').read_bytes()
    normalized=native.rstrip(b'\x1a').replace(b'\r\n',b'\n')
    prepared=json.loads((root/'build/utilities/ted-build.json').read_text())
    if hashlib.sha256(normalized).hexdigest()!=prepared['prepared_source_sha256']:
        raise ValueError('TED native source differs from cross build')
    files['native/TEDNAT.MAC']=(root/'build/utilities/TEDNAT.MAC').read_bytes()
    files['native/TED-build-report.json']=(root/'build/utilities/TED-build-report.json').read_bytes()
    files['TED-SOURCE-MANIFEST.json']=(json.dumps({'schema':1,'files':{n:hashlib.sha256(d).hexdigest() for n,d in sorted(files.items())}},indent=2)+'\n').encode()
    content=io.BytesIO()
    with tarfile.open(fileobj=content,mode='w') as archive:
        for name,data in sorted(files.items()):
            info=tarfile.TarInfo('BetterCPM-source/'+name)
            info.size=len(data);info.mode=0o644;info.mtime=info.uid=info.gid=0
            archive.addfile(info,io.BytesIO(data))
    return {'BetterCPM-TED-SOURCE.tar.gz':gzip.compress(content.getvalue(),mtime=0),
            'TED-SOURCE-README.txt':b'''BetterCP/M TED corresponding source (GPL-2.0-or-later)
Extract BetterCPM-TED-SOURCE.tar.gz. Complete tracked repository sources,
immutable upstream TED, license, build tools, tests and documentation are
included, together with exact standalone native/TEDNAT.MAC and build record.
Each file is hashed in TED-SOURCE-MANIFEST.json.
Host build: python3 tools/build_ted.py --output build/utilities
Native: copy native/TEDNAT.MAC to a CP/M work disk, then run
  B:ZSM4 TED=TEDNAT
  B:LINK TED[A]
ZSM4/LINK retain their external versions. See TED Qualification.md for
actual execution evidence; a source companion is not qualification.
'''}
