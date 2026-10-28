#!/usr/bin/env python3
"""Assemble five review-only ZIPs from exact source and validated media receipts.

No emulator launches, baseline promotions, tags or uploads. Model 4 execution
and fresh-package installation remain explicit acceptance gates.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PENDING = ['Manual Model 4 runtime campaign', 'Fresh-package installation on both platforms',
           'Final conformance applicability/accounting', 'Manual/generated-edition reconciliation',
           'License/attribution/source-completeness audit', 'Maintainer release acceptance']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True)+'\n').encode()


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *map(str,args)])


def checked_name(name):
    p=PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or '\\' in name:
        raise ValueError('unsafe archive name: '+name)
    return name


def read_report(folder, commit):
    folder=Path(folder)
    report=json.loads((folder/'report.json').read_text())
    if report['source']['revision']!=commit:
        raise ValueError('System build source commit differs: '+str(folder))
    name=checked_name(report['image'])
    if PurePosixPath(name).name!=name:
        raise ValueError('System image must have a simple filename')
    data=(folder/name).read_bytes()
    if sha(data)!=report['sha256']:
        raise ValueError('System image differs from receipt')
    for gate in ('filesystem','file_integrity','config_fingerprint'):
        if report['validation'].get(gate)!='PASS':
            raise ValueError('System construction gate missing: '+gate)
    return report,data


def write_package(path, root_name, files, record):
    if path.exists():
        raise ValueError('candidate archive already exists: '+str(path))
    files=dict(files)
    files['RELEASE.json']=encoded(record)
    files['SHA256SUMS.txt']=''.join(f'{sha(data)}  {name}\n' for name,data in sorted(files.items())).encode()
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(files.items()):
            name=checked_name(name)
            info=zipfile.ZipInfo(root_name+'/'+name,(1980,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(0o100644<<16)
            z.writestr(info,data)
    # Check the actual delivered archive, including exact membership/checksums.
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None or set(z.namelist())!={root_name+'/'+n for n in files}:
            raise ValueError('candidate archive integrity/membership failure')
        for name,data in files.items():
            if z.read(root_name+'/'+name)!=data:
                raise ValueError('candidate archive readback differs: '+name)
    return {'filename':path.name,'sha256':sha(path.read_bytes()),'size_bytes':path.stat().st_size}


def source_files():
    names=[n.decode() for n in git('ls-files','-z').split(b'\0') if n]
    # Preserve symlinked source fragments as their resolved bytes, rejecting
    # references that escape the tracked source tree.
    result={}
    for name in names:
        p=ROOT/name
        p.resolve().relative_to(ROOT)
        result[name]=p.read_bytes()
    return result


def upstream_bundle(repository, commit, destination):
    """Bundle an exact commit without adding a ref to the caller's repository."""
    with tempfile.TemporaryDirectory(prefix='bcpm-bundle-source-') as tmp:
        private=Path(tmp)/'source.git'
        subprocess.run(['git','clone','--bare','--shared',str(repository),str(private)],
                       check=True,capture_output=True)
        subprocess.run(['git','-C',str(private),'update-ref','refs/heads/bettercpm-pinned',commit],check=True)
        subprocess.run(['git','-C',str(private),'bundle','create',str(destination),
                        'refs/heads/bettercpm-pinned'],check=True)
        subprocess.run(['git','-C',str(private),'bundle','verify',str(destination)],
                       check=True,capture_output=True)


def assemble(args):
    if git('status','--porcelain','--untracked-files=no').strip():
        raise ValueError('candidate assembly requires clean tracked source')
    commit=git('rev-parse','HEAD').decode().strip()
    layout=json.loads((ROOT/'metadata/release-assets.json').read_text())
    output=args.output.resolve()/'candidates'/commit
    output.mkdir(parents=True,exist_ok=False)
    # Failed candidates are preserved for inspection; never overwrite/reuse.
    tracked=source_files()
    identity=encoded({'source_commit':commit,'status':'CANDIDATE; NOT ACCEPTED'})
    source_manifest={n:sha(data) for n,data in sorted(tracked.items())}
    common={'SOURCE-IDENTITY.json':identity}
    pin=json.loads(tracked['third_party/z80pack/upstream.json'])
    runtime=json.loads(args.runtime_manifest.read_text())
    if (runtime.get('status')!='BUILT' or runtime.get('profile')!='runtime'
            or runtime.get('bettercpm_revision')!=commit
            or runtime.get('upstream')!=pin
            or runtime.get('builder_sha256')!=sha(tracked['tools/build_qualified_cpmsim.py'])):
        raise ValueError('runtime reconstruction receipt differs from candidate source')
    with tempfile.TemporaryDirectory(prefix='bcpm-upstream-bundle-') as tmp:
        bundle=Path(tmp)/'z80pack-pinned.bundle'
        upstream_bundle(args.upstream,pin['commit'],bundle)
        upstream=bundle.read_bytes()
    upstream_name='z80pack-'+pin['commit']+'.bundle'
    restore=('Pinned upstream source for offline emulator reconstruction\n\n'
             'From this directory run:\n  git init z80pack-upstream\n'
             f'  git -C z80pack-upstream fetch ../{upstream_name} refs/heads/bettercpm-pinned\n'
             f'  git -C z80pack-upstream checkout --detach {pin["commit"]}\n'
             'Then pass that repository to tools/build_qualified_cpmsim.py --source.\n'
             'Use --profile runtime for ordinary operation. Keep the build environment.json.\n').encode()
    host={n:tracked[n] for n in tracked if n.startswith('third_party/z80pack/')}
    host['tools/build_qualified_cpmsim.py']=tracked['tools/build_qualified_cpmsim.py']
    host['docs/platform/CPMSIM-INSTALLATION.md']=tracked['docs/platform/CPMSIM-INSTALLATION.md']
    host.update(common)
    host['dependencies/'+upstream_name]=upstream
    host['dependencies/README.txt']=restore
    util=args.utilities.resolve()
    sums={}
    for line in (util/'Utilities-SHA256SUMS.txt').read_text().splitlines():
        digest,name=line.split(None,1);name=checked_name(name.strip())
        if PurePosixPath(name).name!=name:
            raise ValueError('Utilities input must use simple filenames')
        data=(util/name).read_bytes()
        if sha(data)!=digest:
            raise ValueError('Utilities companion checksum differs: '+name)
        sums[name]=data
    inventory=json.loads(args.inventory.read_text())
    if inventory.get('status')!='PASS':
        raise ValueError('independent Utilities inventory has not passed')
    images={}
    util_reports={}
    for platform,target in [('cpmsim','z80pack'),('Model4','trs80gp')]:
        row=inventory['platforms'][target]
        for proof in (row,row['noah_companion']):
            name=proof['image'];data=sums[name]
            if sha(data)!=proof['image_sha256']:
                raise ValueError('inventory/image mismatch: '+name)
            report=json.loads(sums[name+'.json'])
            if report['source']['revision']!=commit or report['sha256']!=sha(data):
                raise ValueError('Utilities source/image receipt differs')
            images[name]=platform
            util_reports[name]=report
    reports={}
    packages=[]
    for asset in layout['assets']:
        id=asset['id'];files=dict(common);evidence={}
        template=tracked[asset['readme_template']].decode()
        template=template.replace('ASSEMBLY TEMPLATE — not a completed or accepted release package.\nRemove this notice only after the release acceptance checks pass.',
                                  'CANDIDATE — assembled for review; NOT ACCEPTED FOR RELEASE.')
        files['README.txt']=template.encode()
        if id in ('system-cpmsim','system-model4'):
            platform='cpmsim' if id=='system-cpmsim' else 'Model4'
            folder=args.cpmsim_system if platform=='cpmsim' else args.model4_system
            report,data=read_report(folder,commit)
            expected='z80pack' if platform=='cpmsim' else 'trs80gp'
            if report['target']!=expected:
                raise ValueError('wrong System platform receipt')
            if platform=='cpmsim' and report['validation'].get('boot')!='PASS':
                raise ValueError('cpmsim candidate requires its own boot evidence')
            files['images/'+report['image']]=data
            files['evidence/system-report.json']=(folder/'report.json').read_bytes()
            files['images/diskdefs']=(folder/'diskdefs').read_bytes()
            work=(folder/'work-image').read_bytes()
            if sha(work)!=report['work_image_sha256']:
                raise ValueError('work image differs from preparation receipt')
            files['images/'+('BetterCPM-Work-332K.dsk' if platform=='cpmsim' else 'BetterCPM-Work-800K.dmk')]=work
            guide='CPMSIM-INSTALLATION.md' if platform=='cpmsim' else 'MODEL4-INSTALLATION.md'
            files['docs/platform/'+guide]=tracked['docs/platform/'+guide]
            files['docs/user/users_guide.md']=tracked['docs/user/users_guide.md']
            files['docs/engineering/Model 4 Release Checklist.md']=tracked['docs/engineering/Model 4 Release Checklist.md']
            files['docs/releases/RELEASE-NOTES-1.0.md']=tracked['docs/releases/RELEASE-NOTES-1.0.md']
            evidence={'system':report}
            if platform=='cpmsim':
                files.update({'host/BetterCPM/'+n:d for n,d in host.items()})
                evidence['emulator']=runtime
        elif id=='utilities':
            for name,data in sums.items():
                dest='images/'+images[name]+'/'+name if name in images else 'source/'+name
                files[dest]=data
            files['evidence/independent-inventory.json']=args.inventory.read_bytes()
            files['docs/user/utilities_manual.md']=tracked['docs/user/utilities_manual.md']
            files['docs/engineering/Model 4 Release Checklist.md']=tracked['docs/engineering/Model 4 Release Checklist.md']
            evidence={'images':util_reports,'independent_inventory':inventory}
        elif id=='source':
            files.update({'source/BetterCPM/'+n:d for n,d in tracked.items()})
            files['source/BetterCPM/SOURCE-IDENTITY.json']=identity
            files['source/BetterCPM/SOURCE-FILES.json']=encoded(source_manifest)
            files['source/dependencies/'+upstream_name]=upstream
            files['source/dependencies/README.txt']=restore
            for name,data in sums.items():
                if name not in images and not name.endswith('.dmk.json') and not name.endswith('.dsk.json'):
                    files['source/native-companions/'+name]=data
        else:
            for name,data in tracked.items():
                if name.startswith('docs/') and Path(name).suffix.lower() in ('.md','.txt','.json','.tsv','.png','.svg'):
                    files[name]=data
            files['CONTENTS.md']=tracked['packaging/1.0/DOCUMENTATION-CONTENTS.md']
            evidence['generated_editions']='PDF/DOCX omitted pending source-to-edition reconciliation'
        # Retain tracked licensing/permission and provenance files in each ZIP.
        for name,data in tracked.items():
            if name.startswith('third_party/') and any(x in Path(name).name.lower() for x in ('license','permission','provenance','copying','notice')):
                files['licenses/'+name]=data
        record={'schema':1,'package':id,'version':'1.0','source_commit':commit,
                'status':'CANDIDATE; NOT ACCEPTED','accepted_commit':None,'tag':None,
                'platforms':asset['platforms'],'pending':PENDING,'evidence':evidence,
                'files':{n:sha(d) for n,d in sorted(files.items())}}
        filename=asset['filename'][:-4]+'-candidate.zip'
        packages.append(write_package(output/filename,asset['archive_root']+'-candidate',files,record))
    index={'schema':1,'status':'CANDIDATE; NOT ACCEPTED','source_commit':commit,
           'accepted_commit':None,'tag':None,'assets':packages,'pending':PENDING}
    (output/'BetterCPM-1.0-CANDIDATE.json').write_bytes(encoded(index))
    (output/'SHA256SUMS.txt').write_text(''.join(f'{p["sha256"]}  {p["filename"]}\n' for p in packages)+
         f'{sha(encoded(index))}  BetterCPM-1.0-CANDIDATE.json\n')
    print(output)
    return output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('cpmsim-system','model4-system','utilities','inventory','upstream','runtime-manifest','output'):
        p.add_argument('--'+name,type=Path,required=True)
    assemble(p.parse_args())


if __name__=='__main__':
    main()
