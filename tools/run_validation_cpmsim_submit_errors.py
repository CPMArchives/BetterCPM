#!/usr/bin/env python3
"""Validate shipped SUBMIT bad-command and parameter-error queue cleanup."""
import argparse,json,shutil,subprocess
from pathlib import Path
from run_validation_cpmsim_ren import audit
from run_validation_returning import sha
from test_z80pack_attributes import directory
from test_z80pack_sysgen_install import session


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('baseline','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();w=a.output.resolve();w.mkdir(parents=True,exist_ok=False);base=a.baseline.resolve();r=json.loads((base/'report.json').read_text());(w/'disks').mkdir()
    image=w/'disks/drivea.dsk';shutil.copy2(base/r['image'],image);shutil.copy2(base/'diskdefs',w/'diskdefs');shutil.copy2(__file__,w/'executed-runner.py')
    for name,data in [('BAD.SUB',b'NOEXIST\r\nTYPE NEVER.TXT\r\n\x1a'),('PARM.SUB',b'TYPE $X\r\n\x1a'),('NEVER.TXT',b'SHOULD NOT EXECUTE\r\n\x1a')]:
        f=w/name;f.write_bytes(data);subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),str(f),'0:'+name],cwd=w,check=True,capture_output=True)
    sim=Path.home()/'projects/git/z80pack/cpmsim/cpmsim';traces=[]
    for name,expected in [('BAD',b'?'),('PARM',b'Parameter Error')]:
        trace=session(sim,w/'disks',[(f'SUBMIT {name}\r'.encode(),b'A0>_ ',30)],w/(name+'.txt'));assert expected in trace and b'SHOULD NOT EXECUTE' not in trace
        raw=directory(image,w/'diskdefs');assert not any(raw[i]<32 and bytes(x&127 for x in raw[i+1:i+12])==b'$$$     SUB' for i in range(0,len(raw),32));traces.append(name)
    shipped=audit(base,r,w,image)
    (w/'result.json').write_text(json.dumps({'status':'PASS','cases':traces,'runner_sha256':sha(Path(__file__)),'baseline_sha256':r['sha256'],'unchanged_shipped_files':shipped},indent=2)+'\n');print('PASS SUBMIT failure cleanup',w)

if __name__=='__main__':main()
