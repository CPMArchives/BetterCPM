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


def collect(output,engine,native_cpm,native_m4,installed,interaction_m4=None):
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
    if interaction_m4:campaigns['installed-interaction-trs80gp']=interaction_m4
    for label,folder in campaigns.items():
        for p in sorted(folder.rglob('*')):
            if p.is_file():files['campaigns/'+label+'/'+str(p.relative_to(folder))]=p.read_bytes()
    eng=json.loads((engine/'report.json').read_text());assert eng['status']=='PASS'
    platforms={}
    for target,native in [('z80pack',native_cpm),('trs80gp',native_m4)]:
        n=json.loads((native/'report.json').read_text())
        assert n['payload_sha256']==payload and n['platforms'][target]['status']=='PASS'
        assert n['platforms'][target]['native_cross_parity']
        assert eng['platforms'][target]['status']=='PASS'
        proofs={}
        for scenario,folder in installed.items():
            if target=='trs80gp' and scenario=='interaction' and interaction_m4:folder=interaction_m4
            r=json.loads((folder/'report.json').read_text())
            e=json.loads((folder/target/'execution.json').read_text())
            assert r['installed'] and r['payload_sha256']==payload
            assert r['platforms'][target]['status']=='PASS'
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
        platforms[target]={'status':'PASS','system_sha256':system,'utilities_sha256':utilities,
                           'native_cross_parity':True,'scenarios':proofs}
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
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--output',type=Path,default=ROOT/'docs/engineering')
    p.add_argument('--interaction-m4',type=Path,help='separate corrected physical-key campaign for Model 4')
    a=p.parse_args()
    collect(a.output,a.engine,a.native_cpm,a.native_m4,{s:getattr(a,s) for s in ('groups','large','interaction')},a.interaction_m4)
