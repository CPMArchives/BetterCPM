#!/usr/bin/env python3
"""Collect fresh exact-image DDT/toolchain gates and unchanged TED/DASM refreshes."""
import argparse
import hashlib
import json
from pathlib import Path
from refresh_utilities_acceptance import archive_evidence,refresh
from toolchain_distribution import companions
from search_source import ROOT

sha=lambda data:hashlib.sha256(data).hexdigest()


def collect(plan,output):
    output.mkdir(parents=True,exist_ok=True)
    inventory=Path(plan['inventory']);audit=json.loads(inventory.read_text())
    assert audit['status']=='PASS'
    for kind in ('TED','DASM'):
        folders={target:Path(plan[kind][target]) for target in ('z80pack','trs80gp')}
        refresh(kind,ROOT/f'docs/engineering/{kind}-Qualification.json',inventory,folders,
            output/(kind+'-Utilities-Refresh.json'),Path(plan['TED-native-z80pack']) if kind=='TED' else None)
    ddt={'ddt_utilities_acceptance':'PASS','whole_utilities_disk':'PROVISIONAL','platforms':{}}
    for target in ('z80pack','trs80gp'):
        folder=Path(plan['DDT'][target]);r=json.loads((folder/'report.json').read_text())
        assert r['ddt_utilities_acceptance']=='PASS' and r['sources_unchanged']
        p=r['platforms'][target]
        assert p['status']=='PASS' and p['utilities_unchanged'] and p['debuggee_unchanged']
        assert p['utilities_sha256']==audit['platforms'][target]['image_sha256']
        assert r['ddt_sha256']==audit['platforms'][target]['files_sha256']['DDT.COM']
        if 'ddt_sha256' in ddt:assert ddt['ddt_sha256']==r['ddt_sha256']
        ddt['ddt_sha256']=r['ddt_sha256'];ddt['platforms'][target]=p
    ddt['evidence_archive']=archive_evidence(output/'DDT-Utilities-Refresh-Evidence.tar.gz',
        {target:Path(plan['DDT'][target])/target for target in ('z80pack','trs80gp')})
    (output/'DDT-Utilities-Refresh.json').write_text(json.dumps(ddt,indent=2)+'\n')
    tools={'status':'PASS','scope':'Fresh native packaged PROBE and six codec builds on both exact media pairs',
        'tools_sha256':{name:sha((ROOT/path).read_bytes()) for name,path in
            [('ZSM4.COM','third_party/zsm4/ZSM4.COM'),('LINK.COM','third_party/dri-link/LINK.COM')]},
        'companions_sha256':{name:sha(data) for name,data in companions(ROOT).items()},'platforms':{}}
    for target in ('z80pack','trs80gp'):
        folder=Path(plan['toolchain'][target]);r=json.loads((folder/'report.json').read_text())
        assert r['status']=='PASS'
        p=r['platforms'][target]
        assert p['status']=='PASS' and set(p['cases'])=={'PROBE','SQ','USQ','CR','UNCR','LZH','UNLZH'}
        assert all(case['status']=='PASS' for case in p['cases'].values())
        assert p['utilities_sha256']==audit['platforms'][target]['image_sha256']
        system_audit=json.loads((folder/'system-audit.json').read_text())
        assert set(system_audit)=={target+'/'+name for name in p['cases']}
        assert all(row['status']=='PASS' and row['shipped_files_unchanged'] for row in system_audit.values())
        tools['platforms'][target]={**p,'system_audit_status':'PASS',
            'system_audit_sha256':sha((folder/'system-audit.json').read_bytes()),
            'runner_sha256':r['runner_sha256']}
    tools['evidence_archive']=archive_evidence(output/'Toolchain-Utilities-Refresh-Evidence.tar.gz',
        {target:Path(plan['toolchain'][target]) for target in ('z80pack','trs80gp')})
    (output/'Toolchain-Utilities-Refresh.json').write_text(json.dumps(tools,indent=2)+'\n')
    print('PASS fresh DDT/toolchain and unchanged TED/DASM paired-media refresh receipts')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign-map',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    collect(json.loads(args.campaign_map.read_text()),args.output)
