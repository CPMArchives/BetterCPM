#!/usr/bin/env python3
"""Collect passing TED tests and paired-emulator receipts without broadening scope."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()


def collect(output,engine,native_cpm,native_m4,installed,interaction_m4=None,sessions=None):
    output.mkdir(parents=True,exist_ok=True)
    binary=(ROOT/'build/utilities/TED.COM').read_bytes()
    payload=sha(binary)
    files={}
    tests={}
    for name in ('text','publisher','workspace','commands','frontend'):
        p=ROOT/('build/ted-'+name+'.json');r=json.loads(p.read_text())
        assert r['status']=='PASS',name
        files['compiled/'+p.name]=p.read_bytes();tests[name]=r['cases']
    test_inputs={}
    for p in sorted((ROOT/'tools').glob('test_ted_*.py')):
        files['test-tools/'+p.name]=p.read_bytes()
        test_inputs[str(p.relative_to(ROOT))]=sha(p.read_bytes())
    core=Path.home()/'projects/git/z80pack/z80core'
    for p in sorted(core.glob('*')):
        if p.is_file() and (p.name.startswith('simz80') or p.name in ('simglb.c','simdefs.h','simglb.h')):
            test_inputs['external/z80pack/z80core/'+p.name]=sha(p.read_bytes())
    files['TEST-INPUTS.json']=(json.dumps(test_inputs,indent=2)+'\n').encode()
    files['build/TED.COM']=binary
    for name in ('TEDNAT.MAC','TED-build-report.json','ted-build.json'):
        files['build/'+name]=(ROOT/'build/utilities'/name).read_bytes()
    # Archive complete disposable campaign evidence, including before/after
    # media and physical key invocations. Proprietary research is excluded.
    campaigns={'engine':engine,'native-z80pack':native_cpm,'native-trs80gp':native_m4,
               **{'installed-'+s:d for s,d in installed.items()}}
    if sessions:
        campaigns={'native-z80pack':native_cpm,**{'session-'+t:d for t,d in sessions.items()}}
    if sessions and native_m4:campaigns['native-trs80gp']=native_m4
    if interaction_m4:campaigns['installed-interaction-trs80gp']=interaction_m4
    for label,folder in campaigns.items():
        for p in sorted(folder.rglob('*')):
            if p.is_file():files['campaigns/'+label+'/'+str(p.relative_to(folder))]=p.read_bytes()
    eng=json.loads((engine/'report.json').read_text()) if not sessions else None
    if eng:assert eng['status']=='PASS'
    platforms={}
    for target,native in [('z80pack',native_cpm),('trs80gp',(native_m4 or sessions['trs80gp']) if sessions else native_m4)]:
        n=json.loads((native/'report.json').read_text())
        assert n['status']=='PASS'
        assert n['payload_sha256']==payload and n['platforms'][target]['status']=='PASS'
        assert n['platforms'][target]['native_cross_parity']
        native_image=(native/target/'after-TEDDEV.COM').read_bytes()
        assert native_image[:len(binary)]==binary, 'native payload mismatch'
        assert len(native_image) in (len(binary),(len(binary)+127)//128*128), 'unexpected native length'
        assert set(native_image[len(binary):])<={0,26}, 'unexpected native record padding'
        if eng:assert eng['platforms'][target]['status']=='PASS'
        proofs={}
        scenarios={s:sessions[target] for s in ('groups','interaction','large')} if sessions else installed
        for scenario,folder in scenarios.items():
            if target=='trs80gp' and scenario=='interaction' and interaction_m4:folder=interaction_m4
            r=json.loads((folder/'report.json').read_text())
            e=json.loads((folder/target/'execution.json').read_text())
            assert r['installed'] and r['payload_sha256']==payload
            assert r['status']=='PASS' and r['platforms'][target]['status']=='PASS'
            if sessions:
                reused=r['platforms'][target].get('reused_groups_receipt_sha256')
                if reused:
                    assert reused==sha((native/'report.json').read_bytes())
                    assert r['platforms'][target]['scenarios']['GROUPS']==n['platforms'][target]['scenarios']['GROUPS']
                assert set(r['platforms'][target]['scenarios'])=={'GROUPS','INTERACTION','LARGE'}
                assert r['platforms'][target]['api_stack_high_water']<=1536
                assert r['platforms'][target]['scenarios'][scenario.upper()]['stack_high_water']<=1536
            assert e['original_media_unchanged'] and 'TED.COM' in e['utilities_members']
            if target=='trs80gp':
                screens=sorted((folder/target).glob('trs80-text-*'))
                raw=[p.read_bytes() for p in screens]
                assert raw and all(len(b)==2048 for b in raw)
                assert all(b[1920:]==raw[0][1920:] for b in raw), 'video tail changed'
                assert any(bytes(c&127 for c in b[:80]).startswith(b'TED  ') for b in raw), 'no editor viewport capture'
            proofs[scenario]={'system_sha256':e['system_sha256'],'utilities_sha256':e['utilities_sha256'],
                             **r['platforms'][target]}
        pairs={(p['system_sha256'],p['utilities_sha256']) for p in proofs.values()}
        assert len(pairs)==1,'installed scenarios used different media'
        system,utilities=pairs.pop()
        if sessions:
            retained={sha(p.read_bytes()) for p in (sessions[target]/'paired-media').iterdir() if p.is_file()}
            assert {system,utilities}<=retained, 'original paired media not retained'
        native_execution=json.loads((native/target/'execution.json').read_text())
        assert (native_execution['system_sha256'],native_execution['utilities_sha256'])==(system,utilities), 'native parity used different media'
        platforms[target]={'status':'PASS','system_sha256':system,'utilities_sha256':utilities,
                           'native_cross_parity':True,'native_padding_bytes':len(native_image)-len(binary),
                           'native_file_sha256':sha(native_image),'scenarios':proofs}
    for name in ('collect_ted_qualification.py','qualify_ted_session.py','dasm_native.py'):
        files['test-tools/'+name]=(ROOT/'tools'/name).read_bytes()
    files['source-inputs.json']=(ROOT/'build/utilities/TED-build-report.json').read_bytes()
    files['EVIDENCE-MANIFEST.json']=(json.dumps({'schema':1,'files':{n:sha(d) for n,d in sorted(files.items())}},indent=2)+'\n').encode()
    out=io.BytesIO()
    with tarfile.open(fileobj=out,mode='w') as t:
        for n,d in sorted(files.items()):
            info=tarfile.TarInfo(n);info.size=len(d);info.mode=0o644;info.mtime=info.uid=info.gid=0
            t.addfile(info,io.BytesIO(d))
    data=gzip.compress(out.getvalue(),mtime=0)
    (output/'TED-Qualification-Evidence.tar.gz').write_bytes(data)
    receipt={'schema':1,'ted_acceptance':'PASS','scope':'TED 1.0 revision 001 on the exact legacy RAM emulator pairs; whole Utilities release acceptance separate',
             'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
             'binary':{'name':'TED.COM','bytes':len(binary),'sha256':payload},
             'compiled_cases':tests,'platforms':platforms,
             'evidence':{'name':'TED-Qualification-Evidence.tar.gz','sha256':sha(data)},
             'limits':['Physical hardware NOT RUN','ROM/XIP and checked-profile application acceptance NOT RUN',
                       'Physical arrow/control collisions use primary agreed control navigation',
                       'Model 4 physical Ctrl-underscore chord unavailable; ASCII US binding tested separately',
                       'Recovery restores committed checkpoint, not the latest unflushed RAM line']}
    (output/'TED-Qualification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('engine','native-cpm','native-m4','groups','large','interaction'):
        p.add_argument('--'+name,type=Path)
    p.add_argument('--output',type=Path,default=ROOT/'docs/engineering')
    p.add_argument('--interaction-m4',type=Path,help='separate corrected physical-key campaign for Model 4')
    p.add_argument('--session-z80pack',type=Path)
    p.add_argument('--session-trs80gp',type=Path)
    a=p.parse_args()
    if a.session_z80pack or a.session_trs80gp:
        assert a.session_z80pack and a.session_trs80gp and a.native_cpm
        collect(a.output,None,a.native_cpm,a.native_m4,{},sessions={'z80pack':a.session_z80pack,'trs80gp':a.session_trs80gp})
    else:
        assert all(getattr(a,n.replace('-','_')) for n in ('engine','native-cpm','native-m4','groups','large','interaction'))
        collect(a.output,a.engine,a.native_cpm,a.native_m4,{s:getattr(a,s) for s in ('groups','large','interaction')},a.interaction_m4)
