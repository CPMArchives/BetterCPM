#!/usr/bin/env python3
"""Refresh unchanged TED/DASM media placement using fresh native/workflow gates.

Historical compiled/full-component coverage is retained only for identical
programs and the identical System image. Fresh executions bind new Utilities
images explicitly; historical media hashes are never relabelled.
"""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile
from search_source import ROOT

sha=lambda data:hashlib.sha256(data).hexdigest()


def archive_evidence(destination,folders,records=None):
    files=dict(records or {})
    for label,folder in folders.items():
        for path in sorted(folder.rglob('*')):
            if path.is_file() and not path.is_symlink():
                files[label+'/'+str(path.relative_to(folder))]=path.read_bytes()
    files['EVIDENCE-MANIFEST.json']=json.dumps({name:sha(data) for name,data in sorted(files.items())},indent=2).encode()+b'\n'
    content=io.BytesIO()
    with tarfile.open(fileobj=content,mode='w') as archive:
        for name,data in sorted(files.items()):
            entry=tarfile.TarInfo(name);entry.size=len(data);entry.mode=0o644;entry.mtime=0
            archive.addfile(entry,io.BytesIO(data))
    packed=gzip.compress(content.getvalue(),mtime=0)
    destination.write_bytes(packed)
    return {'name':destination.name,'sha256':sha(packed),'bytes':len(packed)}


def refresh(kind,prior_path,inventory_path,folders,output,native_cpm=None):
    prior=json.loads(prior_path.read_text())
    inventory=json.loads(inventory_path.read_text())
    assert inventory['status']=='PASS' and prior[kind.lower()+'_acceptance']=='PASS'
    names=['TED.COM'] if kind=='TED' else ['DASM.COM','DSYM.COM','DLINK.COM']
    binaries={name:{'sha256':sha((ROOT/'build/utilities'/name).read_bytes()),
                    'bytes':(ROOT/'build/utilities'/name).stat().st_size} for name in names}
    for name,row in binaries.items():
        original=prior['binary'] if kind=='TED' else prior['binaries'][name]
        assert original['sha256']==row['sha256'],('retained binary changed',name)
    platforms={}
    for target,folder in folders.items():
        r=json.loads((folder/'report.json').read_text())
        e=json.loads((folder/target/'execution.json').read_text())
        assert r['status']=='PASS' and r['platforms'][target]['status']=='PASS'
        assert e['original_media_unchanged']
        assert e['system_sha256']==prior['platforms'][target]['system_sha256'], 'System changed; full retained coverage cannot transfer'
        assert e['utilities_sha256']==inventory['platforms'][target]['image_sha256']
        for name,row in binaries.items():
            assert inventory['platforms'][target]['files_sha256'][name]==row['sha256']
            assert name in e['utilities_members']
        if kind=='TED':
            assert r['installed'] and r['payload_sha256']==binaries['TED.COM']['sha256']
            assert set(r['platforms'][target]['scenarios'])=={'GROUPS','INTERACTION','LARGE'}
            assert r['platforms'][target]['api_stack_high_water']<=1536
            parity_folder=native_cpm if target=='z80pack' else folder
            native_report=json.loads((parity_folder/'report.json').read_text())
            ne=json.loads((parity_folder/target/'execution.json').read_text())
            assert native_report['status']=='PASS' and native_report['payload_sha256']==binaries['TED.COM']['sha256']
            assert native_report['platforms'][target]['native_cross_parity']
            assert ne['utilities_sha256']==e['utilities_sha256'] and ne['system_sha256']==e['system_sha256']
            native=(parity_folder/target/'after-TEDDEV.COM').read_bytes()
            program=(ROOT/'build/utilities/TED.COM').read_bytes()
            assert native[:len(program)]==program and set(native[len(program):])<={0,26}
        else:
            assert r['platforms'][target]['native_cross_parity'] and r['platforms'][target]['symbol_conversion']
        platforms[target]={'status':'PASS','system_sha256':e['system_sha256'],
            'utilities_sha256':e['utilities_sha256'],'fresh_report_sha256':sha((folder/'report.json').read_bytes()),
            'fresh_execution_sha256':sha((folder/target/'execution.json').read_bytes()),
            'fresh_scope':r['scope'],'prior_utilities_sha256':prior['platforms'][target]['utilities_sha256'],
            'unchanged_programs':binaries,'native_cross_parity':True}
    assert set(platforms)=={'z80pack','trs80gp'}
    result={'schema':1,kind.lower()+'_acceptance':'PASS',
        'scope':'Fresh paired-media native/workflow revalidation; unchanged full-component coverage retained from identified historical acceptance',
        'prior_full_acceptance':{'name':prior_path.name,'sha256':sha(prior_path.read_bytes())},
        'platforms':platforms,'limits':prior.get('limits',[])}
    result['binary' if kind=='TED' else 'binaries']=binaries['TED.COM'] if kind=='TED' else binaries
    roots=dict(folders)
    if native_cpm:roots['native-cpm']=native_cpm
    result['evidence_archive']=archive_evidence(output.parent/(kind+'-Utilities-Refresh-Evidence.tar.gz'),roots,
        {'prior-full-acceptance.json':prior_path.read_bytes(),'inventory.json':inventory_path.read_bytes()})
    output.write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind',choices=['TED','DASM'],required=True)
    for name in ['prior','inventory','z80pack','trs80gp','output']:
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--native-cpm',type=Path)
    args=parser.parse_args()
    refresh(args.kind,args.prior,args.inventory,{'z80pack':args.z80pack,'trs80gp':args.trs80gp},args.output,args.native_cpm)
    print('PASS',args.kind,'fresh paired-media acceptance; historical full coverage retained explicitly')
