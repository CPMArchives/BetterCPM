"""Prepare final-named 1.1 archives from verified candidates and acceptance.

Never tags, uploads, publishes, overwrites a package, or alters the 1.0 lock.
"""
import argparse
import json
import re
from pathlib import Path
import tarfile
from package_release_candidates import checked_name,encoded,sha,write_package
from finalize_release_101 import candidate_files

ROOT=Path(__file__).resolve().parents[1]
ASSET_IDS={kind+'-'+platform for kind in ('system','utilities')
           for platform in ('cpmsim','model4','model2')}|{'source','documentation'}
REQUIRED={gate+'-'+platform for platform in ('cpmsim','model4','model2')
          for gate in ('system','utilities','path','memory','tcap','compatibility',
                       'install','reconstruction','recovery','ted','ver')}
REQUIRED|={'offline-runtime','source-reconstruction','documentation','licenses',
           'archive-readback','historical-package-locks'}

def prepare(candidates,acceptance,evidence,output,layout=None):
    layout=json.loads((ROOT/'metadata/release-assets-1.1.json').read_text()) if layout is None else layout
    acceptance=json.loads(Path(acceptance).read_text());evidence=Path(evidence);output=Path(output)
    if layout['version']!='1.1' or acceptance.get('version')!='1.1' or acceptance.get('status')!='PASS':raise ValueError('1.1 acceptance required')
    if not re.fullmatch(r'[0-9a-f]{40}',acceptance.get('source_commit','')):raise ValueError('full source commit required')
    checks={row['name']:row for row in acceptance['checks']}
    if len(checks)!=len(acceptance['checks']):raise ValueError('duplicate acceptance check')
    if not REQUIRED<=set(checks) or any(row['status']!='PASS' for row in checks.values()):raise ValueError('incomplete release acceptance')
    if any(not row.get('evidence') for row in checks.values()):raise ValueError('each acceptance check requires evidence references')
    if sha(evidence.read_bytes())!=acceptance['evidence_sha256']:raise ValueError('acceptance evidence differs')
    with tarfile.open(evidence,'r:gz') as archive:
        members=archive.getmembers()
        names=[checked_name(m.name) for m in members if m.isfile()]
        if len(names)!=len(set(names)) or any(not (m.isfile() or m.isdir()) for m in members):
            raise ValueError('unsafe or duplicate evidence member')
        for row in checks.values():
            refs=row['evidence']
            if not isinstance(refs,list) or any(not isinstance(n,str) or n not in names for n in refs):
                raise ValueError('acceptance references missing evidence')
    assets=layout['assets']
    if len(assets)!=8 or {a['id'] for a in assets}!=ASSET_IDS:raise ValueError('eight independent assets required')
    if any(len({a[k] for a in assets})!=8 for k in ('filename','archive_root')):
        raise ValueError('duplicate asset identity')
    # Validate all inputs before producing any final package.
    prepared=[];found_images={}
    for asset in assets:
        filename=checked_name(asset['filename']);root=checked_name(asset['archive_root'])
        if Path(filename).name!=filename or Path(root).name!=root or '1.1' not in filename or '1.1' not in root:raise ValueError('unsafe or non-1.1 asset identity')
        files=candidate_files(Path(candidates)/(filename[:-4]+'-candidate.zip'),root+'-candidate')
        record=json.loads(files.pop('RELEASE.json'));files.pop('SHA256SUMS.txt')
        if record['version']!='1.1' or record['source_commit']!=acceptance['source_commit'] or record['package']!=asset['id']:raise ValueError('candidate source/package mismatch')
        if record.get('files')!={n:sha(data) for n,data in files.items()}:raise ValueError('candidate file ledger mismatch')
        image_count=0
        for name,data in files.items():
            if name.startswith('images/') and name.endswith(('.dsk','.dmk','.imd')):
                key=asset['id']+'/'+name
                found_images[key]=sha(data)
                image_count+=1
        required_count=0 if asset['id'] in ('source','documentation') else 1 if asset['id']=='system-model2' else 2
        if image_count!=required_count:raise ValueError('incomplete package image set: '+asset['id'])
        prepared.append((asset,files,record))
    if found_images!=acceptance['images']:raise ValueError('accepted image identities do not match the delivered set')
    output.mkdir(parents=True,exist_ok=False);results=[]
    for asset,files,record in prepared:
        for name in list(files):
            if name in ('SOURCE-IDENTITY.json','host/BetterCPM/SOURCE-IDENTITY.json','source/BetterCPM/SOURCE-IDENTITY.json','Provenance/SOURCE-IDENTITY.json'):
                identity=json.loads(files[name]);identity.update(status='QUALIFIED RELEASE SOURCE',release_version='1.1');files[name]=encoded(identity)
        if 'README.txt' in files:
            files['README.txt']=files['README.txt'].replace(b'CANDIDATE \xe2\x80\x94 assembled for review; NOT ACCEPTED FOR RELEASE.',b'Qualified 1.1 release package; see RELEASE.json and acceptance evidence.')
            files['README.txt']=files['README.txt'].replace(b'CANDIDATE \xe2\x80\x94 NOT ACCEPTED FOR RELEASE.',b'Qualified 1.1 release package.')
        files['Provenance/RELEASE-ACCEPTANCE.json']=encoded(acceptance)
        if asset['id']=='source':files['source/release-evidence-1.1.tar.gz']=evidence.read_bytes()
        record.update(status='QUALIFIED RELEASE ARTIFACT',accepted_commit=acceptance['source_commit'],tag='v1.1',pending=[],
                      acceptance_sha256=sha(encoded(acceptance)),publication='Tagging/upload/publication are separate operations',
                      files={n:sha(b) for n,b in sorted(files.items())})
        result=write_package(output/asset['filename'],asset['archive_root'],files,record)
        results.append(dict(result,package=asset['id'],archive_root=asset['archive_root']))
    index={'schema':1,'version':'1.1','status':'READY FOR PUBLICATION','source_commit':acceptance['source_commit'],
           'tag':'v1.1','assets':results,'acceptance_sha256':sha(encoded(acceptance)),
           'publication_performed':False}
    (output/'BetterCPM-1.1-RELEASE.json').write_bytes(encoded(index))
    (output/'BetterCPM-1.1-SHA256SUMS.txt').write_text(''.join(f'{row["sha256"]}  {row["filename"]}\n' for row in results)+f'{sha(encoded(index))}  BetterCPM-1.1-RELEASE.json\n')
    return index


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('candidates','acceptance','evidence','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(prepare(a.candidates,a.acceptance,a.evidence,a.output),indent=2))
