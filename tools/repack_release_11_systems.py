"""Slim System ZIP envelopes without changing any disk-image bytes."""
import argparse,json,subprocess
from pathlib import Path
from finalize_release_101 import candidate_files
from package_release_candidates import lean_system,encoded,sha,write_package,ROOT


def repack(original,index_path,output):
    original=Path(original);output=Path(output);output.mkdir(exist_ok=False)
    index=json.loads(Path(index_path).read_text())
    source=next(a for a in index['assets'] if a['package']=='source')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();results=[]
    for asset in index['assets']:
        if not asset['package'].startswith('system-'):continue
        path=original/asset['filename'];assert sha(path.read_bytes())==asset['sha256']
        files=candidate_files(path,asset['archive_root']);record=json.loads(files.pop('RELEASE.json'));files.pop('SHA256SUMS.txt')
        images={n:sha(b) for n,b in files.items() if n.startswith('images/')}
        host={n:sha(b) for n,b in files.items() if n.startswith('host/')}
        platform=asset['platforms'][0] if 'platforms' in asset else record['platforms'][0]
        guide='docs/platform/'+{'cpmsim':'CPMSIM-INSTALLATION.md','Model4':'MODEL4-INSTALLATION.md','Model2':'MODEL2-INSTALLATION.md'}[platform]
        files[guide]=(ROOT/guide).read_bytes()
        files,evidence=lean_system(files,record['evidence'],record['source_commit'],platform)
        offer=json.loads(files['SOURCE-DOWNLOAD.json']);offer['sha256']=source['sha256'];files['SOURCE-DOWNLOAD.json']=encoded(offer)
        # Preserve license texts; direct source access replaces duplicate source folders.
        files['THIRD-PARTY-NOTICES.txt']=files['THIRD-PARTY-NOTICES.txt'].replace(b'texts, provenance and corresponding-source companions with each download.',b'texts and provenance. Complete matching corresponding source is available in the separate Source download from the same release.')
        template=(ROOT/('packaging/1.1/README-System-'+platform+'.txt')).read_text()
        files['README.txt']=template.replace('ASSEMBLY TEMPLATE — not a completed or accepted release package.\nRemove this notice only after the release acceptance checks pass.','Qualified 1.1 release package.').replace('CANDIDATE — NOT ACCEPTED FOR RELEASE.','Qualified 1.1 release package.').encode()
        assert images=={n:sha(b) for n,b in files.items() if n.startswith('images/')}
        assert not any(n.startswith(('src/','third_party/','evidence/')) for n in files)
        assert host=={n:sha(b) for n,b in files.items() if n.startswith('host/')}
        proof={'status':'PASS_PACKAGING_ONLY','packaging_commit':revision,'previous_archive_sha256':asset['sha256'],'unchanged_images':images,'unchanged_cpmsim_host_kit':host,'corresponding_source':offer}
        files['Provenance/PACKAGING-CORRECTION.json']=encoded(proof)
        record.update(evidence=evidence,packaging_commit=revision,packaging_revision='system-layout-correction-2026-11-08',files={n:sha(b) for n,b in sorted(files.items())})
        asset.update(write_package(output/asset['filename'],asset['archive_root'],files,record));results.append(proof)
    index.update(packaging_revision='system-layout-correction-2026-11-08',packaging_commit=revision)
    (output/'BetterCPM-1.1-RELEASE.json').write_bytes(encoded(index))
    (output/'BetterCPM-1.1-SHA256SUMS.txt').write_text(''.join(a['sha256']+'  '+a['filename']+'\n' for a in index['assets'])+sha(encoded(index))+'  BetterCPM-1.1-RELEASE.json\n')
    (output/'packaging-verification.json').write_bytes(encoded({'status':'PASS','systems':results,'engineering_tests_run':False,'other_packages_unchanged':True}))
    for a in index['assets']:
        if a['package'].startswith('system-'):print(a['filename'],a['size_bytes'],'bytes')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('original','index','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();repack(a.original,a.index,a.output)
