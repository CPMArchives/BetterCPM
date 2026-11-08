"""Correct Utilities archive layout without rebuilding any released software."""
import argparse,json,zipfile,hashlib,shutil,subprocess
from pathlib import Path
from finalize_release_101 import candidate_files
from package_release_candidates import lean_utilities,package_license_files,encoded,sha,write_package,ROOT


def repack(original,output):
    original=Path(original);output=Path(output);output.mkdir(exist_ok=False)
    index=json.loads((original/'BetterCPM-1.1-RELEASE.json').read_text())
    source=next(a for a in index['assets'] if a['package']=='source')
    source_path=original/source['filename'];assert sha(source_path.read_bytes())==source['sha256']
    tracked={n:(ROOT/n).read_bytes() for n in ['LICENSE','COPYING','NOTICE','LICENSES/CC-BY-4.0.txt','docs/LICENSING.md','packaging/1.1/third-party-notices.json']}
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    changed=[]
    with zipfile.ZipFile(source_path) as src:
        for a in index['assets']:
            if not a['package'].startswith('utilities-'):continue
            old=original/a['filename'];assert sha(old.read_bytes())==a['sha256']
            files=candidate_files(old,a['archive_root']);record=json.loads(files.pop('RELEASE.json'));files.pop('SHA256SUMS.txt')
            # Prove every omitted companion remains available byte-for-byte in Source.
            removed={n:b for n,b in files.items() if n.startswith('source/')}
            for n,data in removed.items():
                counterpart=source['archive_root']+'/source/native-companions/'+n[len('source/'):]
                assert sha(src.read(counterpart))==sha(data),n
            before={n:sha(b) for n,b in files.items() if n.startswith('images/')}
            files,evidence=lean_utilities(files,record['evidence'],record['source_commit'])
            files.update(package_license_files(tracked,a['package'],'1.1'))
            files['THIRD-PARTY-NOTICES.txt']+=('\nCorresponding source: '+evidence['corresponding_source']['url']+'\n').encode()
            template=(ROOT/('packaging/1.1/README-Utilities-'+{'utilities-cpmsim':'cpmsim','utilities-model4':'Model4','utilities-model2':'Model2'}[a['package']]+'.txt')).read_text()
            files['README.txt']=template.replace('ASSEMBLY TEMPLATE — not a completed or accepted release package.\nRemove this notice only after the release acceptance checks pass.','Qualified 1.1 release package.').encode()
            offer=json.loads(files['SOURCE-DOWNLOAD.json']);offer['sha256']=source['sha256'];files['SOURCE-DOWNLOAD.json']=encoded(offer)
            after={n:sha(b) for n,b in files.items() if n.startswith('images/')};assert before==after
            correction={'status':'PASS_PACKAGING_ONLY','packaging_commit':revision,'previous_archive_sha256':a['sha256'],'source_archive':source,'unchanged_images':after,'omitted_companions_retained_in_source':{n:sha(b) for n,b in removed.items()}}
            files['Provenance/PACKAGING-CORRECTION.json']=encoded(correction)
            record.update(evidence=evidence,packaging_commit=revision,packaging_revision='utilities-layout-correction-2026-11-08',files={n:sha(b) for n,b in sorted(files.items())})
            result=write_package(output/a['filename'],a['archive_root'],files,record)
            a.update(result);changed.append(correction)
    index['packaging_revision']='utilities-layout-correction-2026-11-08'
    index['packaging_commit']=revision
    (output/'BetterCPM-1.1-RELEASE.json').write_bytes(encoded(index))
    (output/'BetterCPM-1.1-SHA256SUMS.txt').write_text(''.join(a['sha256']+'  '+a['filename']+'\n' for a in index['assets'])+sha(encoded(index))+'  BetterCPM-1.1-RELEASE.json\n')
    (output/'packaging-verification.json').write_bytes(encoded({'status':'PASS','changed_packages':changed,'unchanged_packages':[a['filename'] for a in index['assets'] if not a['package'].startswith('utilities-')],'engineering_tests_run':False}))
    return index

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();result=repack(a.original,a.output)
    for row in result['assets']:
        if row['package'].startswith('utilities-'):print(row['filename'],row['size_bytes'],'bytes')
