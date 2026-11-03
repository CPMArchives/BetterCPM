#!/usr/bin/env python3
"""Run the reviewed native conformance groups from a working desktop Terminal."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from trs80gp_launch import require_launch_services

ROOT=Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--suite',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--audit-blockers',type=Path,
                   help='Also resume a previously prepared audit-blocker packet in this batch')
    a=p.parse_args()
    baseline=a.baseline.resolve();suite=a.suite.resolve();output=a.output.resolve()
    output.mkdir(parents=True,exist_ok=False)
    report=json.loads((baseline/'report.json').read_text())
    image=baseline/report['image'];assert sha(image)==report['sha256']
    assert report['target']=='trs80gp'
    revision=subprocess.check_output(['git','-C',str(suite),'rev-parse','HEAD'],text=True).strip()
    assert revision=='a9a878fcd2e36698c7e856654a85847a004fdd20'
    for line in (suite/'suite/build/SHA256SUMS.txt').read_text().splitlines():
        value,name=line.split();assert sha(suite/'suite/build'/name)==value
    result={'status':'RUNNING','candidate_commit':report['source']['revision'],
            'baseline_sha256':sha(image),'suite_revision':revision,'runs':[],
            'runner_sha256':sha(Path(__file__)),
            'audit_blockers_packet':str(a.audit_blockers.resolve()) if a.audit_blockers else None,
            'scope':'Reviewed native returning groups only. Not all 627 cards; exclusions, devices and other external procedures remain separate.'}
    def save():(output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    save()
    try:
        require_launch_services()
        jobs=[('run_validation_model4.py',['--group',g],g) for g in ('small','ccp','bios-error')]
        jobs += [('run_validation_model4_directory.py',['--program',n],n.lower())
                 for n in ('DIRTEST','BDOSTEST','FILETEST','RANDTEST')]
        if a.audit_blockers:
            jobs.append(('test_audit_blockers_model4.py',
                         ['--resume','--output',str(a.audit_blockers.resolve())],
                         'audit-blockers'))
        for tool,args,name in jobs:
            print('Running',name,flush=True)
            cmd=[sys.executable,str(ROOT/'tools'/tool),'--baseline',str(baseline),
                 '--suite',str(suite),'--output',str(output/name)]+args
            if name=='audit-blockers':cmd=[sys.executable,str(ROOT/'tools'/tool)]+args
            with (output/(name+'.log')).open('w') as log:
                run=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            result['runs'].append({'name':name,'exit_code':run.returncode,'command':cmd})
            save()
        assert sha(image)==result['baseline_sha256'],'Reference image changed'
        result['status']='PASS_SELECTED_GROUPS' if all(r['exit_code']==0 for r in result['runs']) else 'FAIL'
    except Exception as error:
        result['status']='BLOCKED_OR_INCOMPLETE';result['error']=str(error)
    save();print(result['status']+': '+str(output/'result.json'))
    return result['status']!='PASS_SELECTED_GROUPS'


if __name__=='__main__':raise SystemExit(main())
