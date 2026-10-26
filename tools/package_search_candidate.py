#!/usr/bin/env python3
"""Package a reviewable SEARCH candidate without changing frozen release media."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile
from search_source import ROOT

sha = lambda data: hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--qualification',type=Path,required=True)
    args = parser.parse_args()
    binary = (ROOT/'build/utilities/SEARCH.COM').read_bytes()
    build = (ROOT/'build/utilities/SEARCH-build-report.json').read_bytes()
    record = json.loads(build)
    proof = json.loads(args.qualification.read_text())
    if record['artifact']['sha256'] != sha(binary) or proof['binary_sha256'] != sha(binary):
        raise ValueError('candidate/build/qualification binary identities differ')
    for name,wanted in record['input_record']['inputs']['files'].items():
        if sha((ROOT/name).read_bytes()) != wanted:
            raise ValueError('candidate source differs from build: '+name)
    for target in ('cpmsim','model4'):
        if proof.get(target,{}).get('result') != 'PASS':
            raise ValueError('both platform qualification results are required')
    names = subprocess.run(['git','-C',str(ROOT),'ls-files','-z'],check=True,capture_output=True).stdout.split(b'\0')
    sources = {name.decode():(ROOT/name.decode()).read_bytes() for name in names if name}
    # Keep the complete tracked repository, including imported source licenses
    # and build helpers, rather than guessing a smaller transitive closure.
    for name in ('tools/qualify_search_native.py','tools/qualify_search_resources.py','tools/package_search_candidate.py'):
        sources[name] = (ROOT/name).read_bytes()
    source_manifest = {name:sha(data) for name,data in sorted(sources.items())}
    native = (ROOT/'build/utilities/SEARCH-NATIVE.MAC').read_bytes()
    label=f"SEARCH {record['identity']['version']} ({record['identity']['revision']:03d}"
    label+=('-dev)' if record['display_selection']['development'] else ')')
    files = {'SEARCH.COM':binary,'SEARCH-build-report.json':build,
             'SEARCH-Qualification.json':args.qualification.read_bytes(),
             'native/SEARCH.MAC':native,
             'SEARCH-SOURCE-MANIFEST.json':(json.dumps(source_manifest,indent=2)+'\n').encode(),
             'README.txt':(label+' review candidate\n').encode()+b'''
This review package is not a published Utilities Disk or an accepted baseline.
SEARCH.COM is the exact binary identified by the build/qualification records.
Complete tracked sources, documentation, tests and licenses are under source/.
Host rebuild: python3 tools/build_search.py
Native build: python3 tools/build_native_search.py --verify
The native/ source is for ZSM4 4.7 and LINK 1.3 (not supplied here).
Keep the source manifest and qualification limits with the candidate.
Final Utilities Disk integration requires new paired-image acceptance; existing
TED/DASM/toolchain receipts do not transfer to changed disk images.
'''}
    files.update({'source/'+name:data for name,data in sources.items()})
    files['SHA256SUMS.txt'] = ''.join(f'{sha(data)}  {name}\n' for name,data in sorted(files.items())).encode()
    destination = args.output.resolve()
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():
        raise ValueError('refusing to replace an existing candidate package')
    content = io.BytesIO()
    with zipfile.ZipFile(content,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(files.items()):
            info = zipfile.ZipInfo(name,(1980,1,1,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info,data)
    payload = content.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        assert archive.testzip() is None
        assert archive.read('SEARCH.COM') == binary
        for name,data in files.items():
            assert archive.read(name) == data
    destination.write_bytes(payload)
    print(f'{destination}: {len(payload)} bytes; SHA-256 {sha(payload)}')


if __name__ == '__main__':
    main()
