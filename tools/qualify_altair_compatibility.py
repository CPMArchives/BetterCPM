#!/usr/bin/env python3
"""Run pinned independent CP/M compatibility groups on real Altair guest media."""
import argparse
import hashlib
import json
from pathlib import Path
import os
import re
import shutil
import subprocess
from altair_media import image,DISKDEFS
from test_altair_system import Terminal

REVISION='a9a878fcd2e36698c7e856654a85847a004fdd20'
GROUPS=(('CPUTEST','/ALL',2),('ECOTEST','/GROUP:REQUIRED',1),
        ('DISKTEST','/SAFE',7),('CCPTEST','/GROUP:REQUIRED',12),
        ('ENTRYTST','/GROUP:REQUIRED',25),('BIOSTEST','/SAFE',5),
        ('ERRTEST','/SAFE',5),('DIRTEST','/SAFE',49),
        ('BDOSTEST','/GROUP:REQUIRED',56),('FILETEST','/GROUP:REQUIRED',68),
        ('RANDTEST','/SAFE',39))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--suite',type=Path,required=True)
    p.add_argument('--image-dir',type=Path,required=True)
    p.add_argument('--simulator',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--only',action='append')
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    src=a.image_dir.resolve();suite=a.suite.resolve()
    def blob(name):
        return subprocess.check_output(['git','-C',str(suite),'show',REVISION+':suite/'+name])
    hashes={n:h for h,n in (line.split() for line in blob('build/SHA256SUMS.txt').decode().splitlines() if line.strip())}
    names=subprocess.check_output(['git','-C',str(suite),'ls-tree','--name-only',REVISION+':suite/runtime-payload'],text=True).splitlines()
    payload=[(n,blob('runtime-payload/'+n)) for n in names if n.endswith(('.DAT','.CFG'))]
    full=[('BTFULL.DAT',bytes(127*128)+b'FULL-127'+bytes(120)),('BTREL.DAT',bytes(128)),
          ('BTFILL.DAT',bytes((224-2-16-1)*1024))]
    # Fill the directory as well as allocation space, respecting this format's
    # smaller 64-entry directory and sixteen-byte allocation maps.
    entries=sum(max(1,(len(d)+16383)//16384) for _,d in full)
    full.extend((f'F{i:07}.DAT',b'') for i in range(64-entries))
    report={'suite_revision':REVISION,'system_sha256':hashlib.sha256((src/'disks/drivea.dsk').read_bytes()).hexdigest(),
            'scope':'independent automatic groups; external/manual cards require separate accounting',
            'groups':{},'status':'RUNNING'}
    def save():(out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    for name,selector,expected in GROUPS:
        if a.only and name.lower() not in a.only:continue
        w=out/name.lower();w.mkdir();(w/'disks').mkdir()
        for n in ('system.conf','diskdefs'):shutil.copy2(src/n,w/n)
        program=blob('build/'+name+'.COM')
        assert hashlib.sha256(program).hexdigest()==hashes[name+'.COM']
        files=[(name+'.COM',program),*payload]
        if name=='BDOSTEST':files += [('BDSA.TMP',b''),('BDSB.TMP',b'')]
        if name=='RANDTEST':
            used=2+sum((len(d)+1023)//1024 for _,d in files)+sum((len(d)+1023)//1024 for n,d in files if n=='BTUSR.DAT')
            files.append(('RANDFILL.DAT',bytes((224-used-1)*1024)))
        mounts={'a':(src/'disks/drivea.dsk').read_bytes(),
                'b':image(bytes(20480),files),
                'c':image(bytes(20480),[('BTBFILE.DAT',(b'BFILE-000 '*15)[:128])]),
                'd':image(bytes(20480),full)}
        for letter,data in mounts.items():(w/f'disks/drive{letter}.dsk').write_bytes(data)
        print('Running',name,selector,flush=True)
        row={'status':'RUNNING','command':name+' '+selector,'expected_passes':expected,
             'program_sha256':hashes[name+'.COM']}
        report['groups'][name]=row;save()
        t=Terminal(a.simulator.resolve(),w)
        try:
            t.prompt();t.send('B:',drive='B')
            t.cursor=len(t.data);os.write(t.master,(name+' '+selector+'\r').encode())
            t.expect(r'Summary:\s*\d+ pass,\s*\d+ fail,\s*\d+ error',timeout=180)
            t.prompt('B')
            text=t.data.decode('latin1')
            summary=re.search(r'Summary:\s*(\d+) pass,\s*(\d+) fail,\s*(\d+) error',text)
            actual=tuple(map(int,summary.groups()))
            row.update(summary=list(actual),rows={m[1]:[m[2],m[3],m[4].strip()] for m in
                re.finditer(r'(?:^|\n)(\d{4})\s+([PFEOS?\-])\s+([RNXS])\s+([^\r\n]*)',text)})
            assert actual==(expected,0,0),(name,actual,expected)
            row['status']='PASS'
        except Exception as e:
            row.update(status='FAIL',error=str(e));report['status']='FAIL';save();raise
        finally:
            t.close();row['transcript_sha256']=hashlib.sha256(t.data).hexdigest();save()
        print(name,actual,'PASS',flush=True)
    report['status']='PASS';report['passes']=sum(x['summary'][0] for x in report['groups'].values());save()
    print('PASS',report['passes'],'independent automatic compatibility assertions',flush=True)


if __name__=='__main__':main()
