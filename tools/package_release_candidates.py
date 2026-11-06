#!/usr/bin/env python3
"""Assemble six review-only ZIPs from exact source and validated media receipts.

No emulator launches, baseline promotions, tags or uploads. Model 4 execution
and fresh-package installation remain explicit acceptance gates.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import zipfile
from build_qualified_cpmsim import offline_inputs, source_archive, verified_sources
from release_source import source_files as selected_source_files, forbidden_digests, verify_members

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


def project_license_files(tracked):
    files={'licenses/BetterCPM/'+name:tracked[name]
           for name in ('LICENSE','COPYING','NOTICE')}
    files['licenses/BetterCPM/CC-BY-4.0.txt']=tracked['LICENSES/CC-BY-4.0.txt']
    files['docs/LICENSING.md']=tracked['docs/LICENSING.md']
    return files


def source_files():
    return selected_source_files(ROOT)


def utilities_members(platform, sums, images, reports, inventory):
    """Keep matching disk images/receipts and the complete shared source kit."""
    target={'cpmsim':'z80pack','Model4':'trs80gp'}[platform]
    selected={name for name,owner in images.items() if owner==platform}
    if len(selected)!=2:
        raise ValueError('Utilities package requires primary and companion images')
    files={}
    for name,data in sums.items():
        image=name[:-5] if name.endswith('.json') else name
        if image in images:
            if image not in selected:
                continue
            destination=('images/'+platform+'/'+name if name in images
                         else 'evidence/'+name)
        else:
            destination='source/'+name
        files[destination]=data
    proof={**inventory,'platforms':{target:inventory['platforms'][target]}}
    files['evidence/independent-inventory.json']=encoded(proof)
    return files,{'images':{name:reports[name] for name in sorted(selected)},
                  'independent_inventory':proof}


def package_license_files(tracked, package_id, version="1.0"):
    """Attach the first-party grants and notices for this independent download."""
    notices = json.loads(tracked['packaging/'+version+'/third-party-notices.json'])
    selected = [row for row in notices if package_id in row['packages']]
    if not selected:
        raise ValueError('missing package notice inventory: ' + package_id)
    sections = [
        'BetterCP/M '+version+' — ' + package_id,
        'Original BetterCP/M software and original code examples: GPL-2.0-or-later (licenses/BetterCPM/LICENSE and COPYING).',
        'Original BetterCP/M documentation prose and illustrations: '
        'CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). '
        'Retain named credits and indicate changes. See licenses/BetterCPM/CC-BY-4.0.txt.',
        'Third-party works retain their own terms. Keep the applicable license '
        'texts, provenance and corresponding-source companions with each download.',
    ]
    for row in selected:
        sections.append(row['work'] + '\n' + row['notice'])
    files = project_license_files(tracked)
    files['THIRD-PARTY-NOTICES.txt'] = ('\n\n'.join(sections) + '\n').encode('utf-8')
    return files


def documentation_members(tracked, commit, version):
    """Deliver the maintained four-manual edition with source-pinned links."""
    from release_documentation import selection_mapping, remap_links, check_links, excluded
    selected='packaging/'+version+'/documentation-selection.json'
    selection=json.loads(tracked[selected]);mapping=selection_mapping(selection)
    mapping['README.md']='packaging/'+version+'/README-Documentation.md'
    mapping['Provenance/selection.json']=selected
    mapping.pop('Provenance/SOFTWARE-PACKAGES.json')
    files={}
    for dest,source in mapping.items():
        if excluded(dest):raise ValueError('excluded documentation member: '+dest)
        files[dest]=remap_links(source,dest,tracked[source],mapping,commit,selection.get('external_references',{}))
    links=check_links(files)
    files['Provenance/SOURCE-IDENTITY.json']=encoded({'source_commit':commit,'release_version':version,'edition':'four maintained Markdown manuals'})
    return files,{'manuals':selection['manuals'],'local_links_checked':links,'source_commit':commit,'generated_editions':'PDF/DOCX not included'}


def assemble(args):
    version=getattr(args,'version','1.0')
    if version not in ('1.0','1.0.1'):
        raise ValueError('unsupported release version')
    if version=='1.0' and (ROOT / 'docs/releases/non-documentation-lock-1.0/LOCK.json').exists():
        raise ValueError('Five 1.0 packages are locked; use build_documentation.py. Do not rebuild the six-package set during documentation sync.')
    if git('status','--porcelain','--untracked-files=no').strip():
        raise ValueError('candidate assembly requires clean tracked source')
    commit=git('rev-parse','HEAD').decode().strip()
    layout=json.loads((ROOT/('metadata/release-assets.json' if version=='1.0' else 'metadata/release-assets-'+version+'.json')).read_text())
    if layout['version']!=version or json.loads((ROOT/'metadata/release-package.json').read_text())['version']!=version:
        raise ValueError('release version metadata mismatch')
    output=args.output.resolve()/'candidates'/commit
    output.mkdir(parents=True,exist_ok=False)
    # Failed candidates are preserved for inspection; never overwrite/reuse.
    from cpm_tools_source import verify as verify_cpm_tools_source
    cpm_source_paths=verify_cpm_tools_source(ROOT)
    tracked=source_files()
    forbidden=forbidden_digests(ROOT)
    inspected=set()
    if not cpm_source_paths <= tracked.keys():
        raise ValueError('CP/M Tools source companion is not completely tracked')
    identity=encoded({'source_commit':commit,'status':'CANDIDATE; NOT ACCEPTED'})
    source_manifest={n:sha(data) for n,data in sorted(tracked.items())}
    common={'SOURCE-IDENTITY.json':identity,
            'docs/platform/FORMAT-SUPPORT-1.0.md':tracked['docs/platform/FORMAT-SUPPORT-1.0.md']}
    pin=json.loads(tracked['third_party/z80pack/upstream.json'])
    runtime=json.loads(args.runtime_manifest.read_text())
    if (runtime.get('status')!='BUILT' or runtime.get('profile')!='runtime'
            or runtime.get('bettercpm_revision')!=commit
            or runtime.get('upstream')!=pin
            or runtime.get('builder_sha256')!=sha(tracked['tools/build_qualified_cpmsim.py'])):
        raise ValueError('runtime reconstruction receipt differs from candidate source')
    expected = offline_inputs(pin['commit'])
    upstream = source_archive(args.upstream, pin['commit'], expected)
    verified_sources(upstream, expected)
    if sha(upstream) != runtime['source_archive_sha256']:
        raise ValueError('offline sources differ from runtime build receipt')
    upstream_name = 'z80pack-cpmsim-' + pin['commit'] + '.tar'
    restore = ('Pinned cpmsim build sources for offline reconstruction\n\n'
               'Use a C compiler, make, Git (for applying patches), and Python 3. '
               'On macOS the build also needs codesign.\n'
               'From the directory containing tools/ run:\n'
               f'  python3 tools/build_qualified_cpmsim.py --source <path-to-dependencies>/{upstream_name} '
               '--output build/cpmsim-runtime --profile runtime\n'
               'Use dependencies/ in the System host kit or ../dependencies/ in the Source kit. '
               'The builder verifies every file against third_party/z80pack/offline-inputs.json.\n').encode()
    host={n:tracked[n] for n in tracked if n.startswith('third_party/z80pack/')}
    host['tools/build_qualified_cpmsim.py']=tracked['tools/build_qualified_cpmsim.py']
    host['tools/cpmsim_terminal.py']=tracked['tools/cpmsim_terminal.py']
    # The offline guest labels use registry/input guards too. Include their
    # complete selected-input closure, rather than a builder that imports
    # helpers absent from this independently downloadable System host kit.
    for name in ('component-registry.json','component-inputs.json','component-baselines.json'):
        host['metadata/'+name]=tracked['metadata/'+name]
    plans=json.loads(tracked['metadata/component-inputs.json'])['components']
    for owner in ('utility:R','utility:W','utility:MOUNT'):
        for name in plans[owner]['files']:
            host[name]=tracked[name]
    host['docs/platform/CPMSIM-INSTALLATION.md']=tracked['docs/platform/CPMSIM-INSTALLATION.md']
    host.update(common)
    for name in ('LICENSE','COPYING','NOTICE'):
        host[name]=tracked[name]
    host['LICENSES/CC-BY-4.0.txt']=tracked['LICENSES/CC-BY-4.0.txt']
    host['docs/LICENSING.md']=tracked['docs/LICENSING.md']
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
        files.update(package_license_files(tracked, id, version))
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
            if platform=='cpmsim':
                files['third_party/z80pack/README.md']=tracked['third_party/z80pack/README.md']
            files['docs/manuals/Users-Guide.md']=tracked['docs/manuals/Users-Guide.md']
            files['docs/user/FDB.md']=tracked['docs/user/FDB.md']
            files['docs/platform/MODEL4-SHIPPED-INSTALLATION.txt']=tracked['docs/platform/MODEL4-SHIPPED-INSTALLATION.txt']
            files['docs/engineering/BCPM780-Installation-Qualification.md']=tracked['docs/engineering/BCPM780-Installation-Qualification.md']
            files['docs/engineering/Model 4 Release Checklist.md']=tracked['docs/engineering/Model 4 Release Checklist.md']
            files['docs/releases/RELEASE-NOTES-'+version+'.md']=tracked['docs/releases/RELEASE-NOTES-'+version+'.md']
            evidence={'system':report}
            if platform=='cpmsim':
                files.update({'host/BetterCPM/'+n:d for n,d in host.items()})
                runtime_source=args.runtime_manifest.resolve().parent/'z80pack'
                for name in ('r','w','mount'):
                    relative='cpmtools/'+name+'.com'
                    payload=(runtime_source/relative).read_bytes()
                    if sha(payload)!=runtime['guest_utilities'][relative]:
                        raise ValueError('guest utility differs from runtime receipt: '+name)
                    files['host/guest-tools/'+name.upper()+'.COM']=payload

                evidence['emulator']=runtime
        elif id in ('utilities-cpmsim','utilities-model4'):
            selected,evidence=utilities_members(asset['platforms'][0],sums,images,
                                                util_reports,inventory)
            files.update(selected)
            files['docs/manuals/Command-and-Utilities-Reference.md']=tracked['docs/manuals/Command-and-Utilities-Reference.md']
            files['docs/platform/MODEL4-SHIPPED-INSTALLATION.txt']=tracked['docs/platform/MODEL4-SHIPPED-INSTALLATION.txt']
            files['docs/engineering/BCPM780-Installation-Qualification.md']=tracked['docs/engineering/BCPM780-Installation-Qualification.md']
            for guide in ('FDB.md','ZSM4.md','LINK.md','SQ.md','USQ.md','CR.md','UNCR.md','LZH.md','UNLZH.md'):
                files['docs/user/'+guide]=tracked['docs/user/'+guide]
            files['docs/engineering/Model 4 Release Checklist.md']=tracked['docs/engineering/Model 4 Release Checklist.md']
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
            if version=='1.0.1':
                selected,evidence=documentation_members(tracked,commit,version)
                files.update(selected)
            else:
                for name,data in tracked.items():
                    if name == 'docs/user/users_guide_backup.md':
                        continue
                    if name.startswith('docs/') and Path(name).suffix.lower() in ('.md','.txt','.json','.tsv','.png','.svg'):
                        files[name]=data
                files['CONTENTS.md']=tracked['packaging/'+version+'/DOCUMENTATION-CONTENTS.md']
                files['third_party/z80pack/README.md']=tracked['third_party/z80pack/README.md']
                evidence['generated_editions']='PDF/DOCX omitted pending source-to-edition reconciliation'
        # Retain tracked licensing/permission and provenance files in each ZIP.
        for name,data in tracked.items():
            if name.startswith('third_party/') and any(x in Path(name).name.lower() for x in ('license','permission','provenance','copying','notice')):
                files['licenses/'+name]=data
        verify_members(files, forbidden, inspected)
        record={'schema':1,'package':id,'version':version,'source_commit':commit,
                'status':'CANDIDATE; NOT ACCEPTED','accepted_commit':None,'tag':None,
                'platforms':asset['platforms'],'pending':PENDING,'evidence':evidence,
                'files':{n:sha(d) for n,d in sorted(files.items())}}
        filename=asset['filename'][:-4]+'-candidate.zip'
        packages.append(write_package(output/filename,asset['archive_root']+'-candidate',files,record))
    index={'schema':1,'status':'CANDIDATE; NOT ACCEPTED','source_commit':commit,
           'accepted_commit':None,'tag':None,'assets':packages,'pending':PENDING}
    (output/('BetterCPM-'+version+'-CANDIDATE.json')).write_bytes(encoded(index))
    (output/'SHA256SUMS.txt').write_text(''.join(f'{p["sha256"]}  {p["filename"]}\n' for p in packages)+
         f'{sha(encoded(index))}  BetterCPM-{version}-CANDIDATE.json\n')
    print(output)
    return output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--version',choices=('1.0','1.0.1'),default='1.0')
    for name in ('cpmsim-system','model4-system','utilities','inventory','upstream','runtime-manifest','output'):
        p.add_argument('--'+name,type=Path,required=True)
    assemble(p.parse_args())


if __name__=='__main__':
    main()
