"""Artifact-driven external release records; immutable, with no self-checksum."""
from pathlib import Path
import argparse
import json
import re
from component_registry import load, ROOT
from component_inputs import canonical, digest


def immutable_write(path, value):
    data = json.dumps(value, indent=2, sort_keys=True).encode()+b'\n'
    path = Path(path)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError('refusing to redefine existing release record: '+str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as output:
        output.write(data)


def disk_record(report, image, *, root=ROOT, require_commit=False):
    """Use actual included bytes/build records; never substitute a cached identity."""
    root = Path(root)
    if report.get('sha256') != digest(image):
        raise ValueError('disk report checksum differs from final image')
    registry = load(root/'metadata/component-registry.json')['components']
    source = report.get('source', {})
    commit = source.get('revision')
    if require_commit and (not isinstance(commit, str) or not re.fullmatch(r'[0-9a-f]{40}',commit)):
        raise ValueError('frozen disk record requires a full source commit')
    records = []
    inventory_path=root/'docs/engineering/BATCH-COMPONENT-INVENTORY.json'
    inventory=json.loads(inventory_path.read_text()) if inventory_path.is_file() else {'components':[]}
    for original in report['included']:
        row = dict(original)
        name = row['name']
        stem = name.split('.')[0]
        key = ('utility:'+stem if name.upper().endswith('.COM') or name=='RCP.CPX'
               else 'module:'+stem)
        component = registry.get(key)
        if component:
            relative = row.get('artifact') or ('build/cpx/'+name if name.endswith('.CPX') else
                       'build/rsx/'+name if name.endswith('.RSX') else
                       'build/z80pack-tools/'+name if name=='BYE.COM' else 'build/utilities/'+name)
            artifact = root/relative
            data = artifact.read_bytes()
            if digest(data) != row['sha256']:
                raise ValueError('included artifact changed: '+name)
            candidates = [artifact.parent/(stem+'-build-report.json'), artifact.parent/'build-report.json']
            if name=='DDT.COM': candidates.insert(0,root/'build/ddt-development/build-report.json')
            build = None
            for candidate in candidates:
                if candidate.is_file():
                    observed = json.loads(candidate.read_text())
                    if observed.get('component')==key and observed.get('artifact',{}).get('sha256')==row['sha256']:
                        build=observed;break
            if build:
                row['identity']=build['identity']
                row['build_provenance']=build.get('provenance')
                row['input_record']=build.get('input_record')
                if require_commit:
                    recorded_commit=(build.get('provenance') or {}).get('repository_commit')
                    if not isinstance(recorded_commit,str) or not re.fullmatch(r'[0-9a-f]{40}',recorded_commit):
                        raise ValueError('cached artifact lacks frozen-release source provenance: '+name)
            else:
                cached=next((item for item in inventory['components'] if item['component']==key
                             and any(a['sha256']==row['sha256'] for a in item['artifacts'])),None)
                if cached:
                    row['identity']={'version':cached['version'],'revision':cached['revision']}
                    row['component']=key
                    row['build_provenance']={'kind':'checksum-matched existing artifact inventory',
                                            'source_commit':inventory.get('source_commit'),
                                            'inventory_sha256':digest(inventory_path.read_bytes())}
                    if require_commit and not row['build_provenance']['source_commit']:
                        raise ValueError('cached artifact lacks frozen-release source provenance: '+name)
                    records.append(row)
                    continue
                if require_commit:
                    raise ValueError('frozen artifact requires its original build record: '+name)
                # Legacy builders may have no sidecar. Verify their included
                # identity bytes instead of silently trusting the latest row.
                if key.startswith('utility:') and name!='RCP.CPX':
                    expected=f"{stem} {component['version']} ({component['revision']:03d}"
                    if expected.encode() not in data:raise ValueError('unrecorded artifact identity differs: '+name)
                elif name=='RCP.CPX' or key.startswith('module:'):
                    if tuple(data[40:42])!=tuple(map(int,component['version'].split('.'))):
                        raise ValueError('unrecorded carrier identity differs: '+name)
                    # Module revision is not encoded in historical headers.
                    if not source.get('inputs'):
                        raise ValueError('unrecorded module requires exact build-source input provenance: '+name)
                row['identity']={'version':component['version'],'revision':component['revision']}
                row['build_provenance']={'source_commit':commit,'inputs':source.get('inputs'),
                                         'kind':'validated source generation; no original sidecar'}
            row['component']=key
        elif name in ('ZSM4.COM','LINK.COM'):
            row['upstream_version']=report.get('third_party_versions',{}).get(name)
            row['bettercpm_identity']=None
        elif name=='R3PACK.RSX':
            row['owner']='subsystem:RSX'
        records.append(row)
    core = {key.split(':')[1]:{'version':value['version'],'revision':value['revision'],
                             'api_version':value['api_version']}
            for key,value in registry.items() if key.startswith('subsystem:')}
    result={'schema':1,'kind':'disk','frozen':require_commit,'target':report['target'],
            'profile':source.get('profile',{'profile':'default'}),
            'image':{'name':report['image'],'sha256':digest(image),'bytes':len(image)},
            'core':{'state':'development','after_frozen_core':'1.0','components':core},
            'included':records,'source':source,'tools':report.get('tools',{}),
            'acceptance':report.get('validation',report.get('status','not asserted')),
            'redistribution_companions':report.get('toolchain_companions',{})}
    resident=next((path for path in (root/('build/'+report['target']+'/resident.bin'),root/'build/system/resident.bin') if path.is_file()),None)
    if resident:
        result['core']['resident_sha256']=digest(resident.read_bytes())
    # Revision is a content identity over the record before adding itself.
    result['revision']=digest(canonical(result))
    return result


def package_record(version, revision, manifests):
    disks=[]
    for path in manifests:
        data=Path(path).read_bytes();record=json.loads(data)
        if record.get('kind')!='disk' or not record.get('revision') or not record.get('frozen'):
            raise ValueError('package must reference disk release records')
        original=dict(record);identity=original.pop('revision')
        if digest(canonical(original))!=identity:raise ValueError('disk record content identity mismatch')
        disks.append({'manifest':Path(path).name,'sha256':digest(data),
                      'disk_revision':identity,'image':record['image'],'target':record['target']})
    return {'schema':1,'kind':'package','version':version,'revision':revision,'disks':disks}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='operation',required=True)
    disk=sub.add_parser('disk');disk.add_argument('--report',type=Path,required=True)
    disk.add_argument('--image',type=Path,required=True);disk.add_argument('--output',type=Path,required=True)
    disk.add_argument('--root',type=Path,default=ROOT);disk.add_argument('--freeze',action='store_true')
    package=sub.add_parser('package');package.add_argument('--version',required=True)
    package.add_argument('--revision',required=True);package.add_argument('--disk',type=Path,action='append',required=True)
    package.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.operation=='disk':
        result=disk_record(json.loads(args.report.read_text()),args.image.read_bytes(),root=args.root,require_commit=args.freeze)
    else:result=package_record(args.version,args.revision,args.disk)
    immutable_write(args.output,result)


if __name__=='__main__':main()
