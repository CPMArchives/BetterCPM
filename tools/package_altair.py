#!/usr/bin/env python3
"""Package qualified Altair media and its exact corresponding-source offer."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile
from altair_media import image
from release_source import source_files,forbidden_digests,verify_members
from toolchain_distribution import companions

ROOT=Path(__file__).resolve().parents[1]
sha=lambda data:hashlib.sha256(data).hexdigest()
encoded=lambda data:(json.dumps(data,indent=2,sort_keys=True)+'\n').encode()


def archive(path,files):
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as bundle:
        for name,data in sorted(files.items()):
            entry=zipfile.ZipInfo(name,(1980,1,1,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED
            entry.external_attr=0o100644<<16;bundle.writestr(entry,data)
    with zipfile.ZipFile(path) as bundle:
        assert bundle.testzip() is None
        assert set(bundle.namelist())==set(files)
        for name,data in files.items():assert bundle.read(name)==data
    return {'name':path.name,'bytes':path.stat().st_size,'sha256':sha(path.read_bytes()),
            'members':{name:{'bytes':len(data),'sha256':sha(data)} for name,data in sorted(files.items())}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build-root',type=Path,required=True)
    p.add_argument('--acceptance',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.build_root.resolve();out=a.output.resolve();accept=a.acceptance.resolve()
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT):
        p.error('commit tracked source changes before packaging')
    state=json.loads((root/'profile-state.json').read_text())['source']
    if state['revision']!=commit:p.error('build source commit differs from HEAD')
    for name,wanted in state['inputs'].items():
        if sha((ROOT/name).read_bytes())!=wanted:p.error('build input differs: '+name)
    release=root/'build/altair/release';collection=json.loads((release/'collection.json').read_text())
    proof=json.loads((accept/'result.json').read_text())
    system=collection['volumes'][0]['sha256']
    if proof['status']!='PASS' or proof['system_sha256']!=system:p.error('acceptance differs from collection')
    for name in ('loader','install','media','utilities','compatibility','shared-core','hardware'):
        row=json.loads((accept/name/'result.json').read_text())
        if row['status']!='PASS':p.error('failed acceptance gate: '+name)
        if name in ('loader','install','media','utilities','compatibility') and row['system_sha256']!=system:
            p.error('different accepted media: '+name)
    out.mkdir(parents=True,exist_ok=False)
    files=source_files(ROOT)
    # Verify selected corresponding source and all nested redistribution inputs.
    verify_members(files,forbidden_digests(ROOT))
    source_manifest={n:sha(d) for n,d in sorted(files.items())}
    source_identity={'source_commit':commit,'target':'altair','version':'1.3',
                     'status':'qualified emulator candidate; publication separate',
                     'selected_sources_sha256':sha(encoded(source_manifest))}
    files['SOURCE-FILES.json']=encoded(source_manifest)
    files['SOURCE-IDENTITY.json']=encoded(source_identity)
    # Preserve exact native prepared source and build reports next to the full
    # maintained implementation and its original third-party sources/licenses.
    for path in (root/'build/utilities').iterdir():
        if path.suffix in ('.json','.MAC'):
            files['native/'+path.name]=path.read_bytes()
    files['ALTAIR-INSTALLATION.md']=(ROOT/'docs/platform/ALTAIR-INSTALLATION.md').read_bytes()
    source_record=archive(out/'BetterCPM-1.3-Altair-Source.zip',{'BetterCPM-source/'+n:d for n,d in files.items()})
    media={}
    for row in collection['volumes']:
        data=(release/row['image']).read_bytes()
        assert sha(data)==row['sha256']
        media['Media/'+row['image']]=data
    media['Media/BetterCPM-1.3-Altair-Work.dsk']=image(bytes(20480),[])
    for name in ('diskdefs','system.conf','collection.json'):media['Media/'+name]=(release/name).read_bytes()
    media['Run-Altair.py']=(ROOT/'tools/altair/run.py').read_bytes()
    for name in ('tools/prepare_altair_emulator.py','tools/altair/no-video.c',
                 'third_party/z80pack/altair-offline.tar.gz','third_party/z80pack/altair-offline.json'):
        media['Host/'+name]=(ROOT/name).read_bytes()
    media['ALTAIR-INSTALLATION.md']=files['ALTAIR-INSTALLATION.md']
    media['SOURCE-IDENTITY.json']=encoded(source_identity)
    for name,data in companions(ROOT).items():media['Source-Notices/'+name]=data
    for path in ROOT.glob('LICENSE*'):
        if path.is_file():media['Source-Notices/'+path.name]=path.read_bytes()
    media['SOURCE-OFFER.txt']=b'''Complete matching source is provided as BetterCPM-1.3-Altair-Source.zip
at the same release location as this media archive. Download both archives.
It includes the maintained OS/utilities, original imported sources, build
scripts, exact native prepared sources, license texts and provenance.
ZSM4 corresponding source and LINK permission accompany this media archive.
The pinned Altair emulator/assembler source and its upstream license are also
included in Host/third_party/z80pack/altair-offline.tar.gz.
See SOURCE-IDENTITY.json for the exact source commit and selected manifest.
'''
    evidence={}
    for path in sorted(accept.rglob('*')):
        if path.is_file() and (path.name in ('result.json','transcript.txt') or path.parent==accept and path.suffix=='.log') and not {'mounts','comparison'} & set(path.relative_to(accept).parts):
            evidence[str(path.relative_to(accept))]=path.read_bytes()
    for name,data in evidence.items():media['Evidence/'+name]=data
    media_record=archive(out/'BetterCPM-1.3-Altair.zip',{'BetterCPM-1.3-Altair/'+n:d for n,d in media.items()})
    ledger={'status':'PASS; ready for maintainer review/publication','source':source_identity,
            'collection':collection,'acceptance':proof,'assets':[media_record,source_record],
            'existing_1_3_assets':'unchanged; additive platform assets only'}
    (out/'ALTAIR-RELEASE.json').write_bytes(encoded(ledger))
    (out/'SHA256SUMS-Altair-1.3.txt').write_text(''.join(row['sha256']+'  '+row['name']+'\n' for row in [media_record,source_record])+
                                    sha((out/'ALTAIR-RELEASE.json').read_bytes())+'  ALTAIR-RELEASE.json\n')
    print(out,flush=True)


if __name__=='__main__':main()
