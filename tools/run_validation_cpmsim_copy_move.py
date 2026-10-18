#!/usr/bin/env python3
"""Validate shipped COPY and resident MOVE on disposable cpmsim disks."""
import argparse,json,shutil,subprocess
from pathlib import Path
from run_validation_cpmsim_ren import audit
from run_validation_returning import sha
from test_z80pack_attributes import directory
from test_z80pack_sysgen_install import session


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();base=a.baseline.resolve();w=a.output.resolve();w.mkdir(parents=True,exist_ok=False)
    report=json.loads((base/'report.json').read_text());(w/'disks').mkdir()
    disks={d:w/'disks'/('drive'+d+'.dsk') for d in 'abc'}
    for image in disks.values():shutil.copy2(base/report['image'],image)
    shutil.copy2(base/'diskdefs',w/'diskdefs');shutil.copy2(__file__,w/'executed-runner.py')
    def cpm(tool,d,*args):
        return subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disks[d]),*map(str,args)],cwd=w,check=True,capture_output=True)
    for d in 'bc':cpm('cpmrm',d,'0:*.*')
    def put(d,user,name,data,attrs=0):
        path=w/f'in-{d}-{user}-{name}';path.write_bytes(data);cpm('cpmcp',d,path,f'{user}:{name}')
        flags=''.join(ch for bit,ch in ((1,'r'),(2,'s'),(4,'a')) if attrs&bit)
        if flags:cpm('cpmchattr',d,flags,f'{user}:{name}')
    def rows(d,user,name):
        stem,ext=name.split('.');key=(stem.ljust(8)+ext.ljust(3)).encode();raw=directory(disks[d],w/'diskdefs')
        return [raw[i:i+32] for i in range(0,len(raw),32) if raw[i]==user and bytes(x&127 for x in raw[i+1:i+12])==key]
    def check(d,user,name,data,attrs=None):
        found=rows(d,user,name);assert found,(d,user,name)
        if attrs is not None:
            assert all(sum((r[9+i]>>7)<<i for i in range(3))==attrs for r in found),(name,attrs)
        out=w/f'out-{d}-{user}-{name}';cpm('cpmcp',d,f'{user}:{name}',out);assert out.read_bytes()==data,name
    sim=Path.home()/'projects/git/z80pack/cpmsim/cpmsim';commands=[]
    def execute(command):
        text=session(sim,w/'disks',[(command.encode()+b'\r',b'A0>_ ',120)],w/f'case-{len(commands):02}.txt')
        commands.append(command);return text
    # Binary records, multiple extents, zero length and all protected attributes.
    payloads={n:bytes((i*29+n)&255 for i in range(33280 if n==7 else 256)) for n in range(8)}
    for n,data in payloads.items():put('b',1,f'F{n}.DAT',data,n)
    before=disks['b'].read_bytes()
    execute('COPY B1:F7.DAT C1:EXACT.DAT');check('c',1,'EXACT.DAT',payloads[7],7)
    execute('COPY C2:ASSIGN.DAT=B1:F0.DAT');check('c',2,'ASSIGN.DAT',payloads[0],0)
    execute(':COPY /B /V B1:*.DAT C3:')
    for n,data in payloads.items():check('c',3,f'F{n}.DAT',data,n)
    assert disks['b'].read_bytes()==before,'COPY changed source'
    saved=disks['c'].read_bytes()
    text=execute(':COPY /B /S /V B1:*.DAT C3:');assert disks['c'].read_bytes()==saved,'skip changed destination'
    put('c',4,'REPLACE.DAT',b'Z'*128)
    execute(':COPY /B /O /V B1:F0.DAT C4:REPLACE.DAT');check('c',4,'REPLACE.DAT',payloads[0],0)
    saved=disks['c'].read_bytes()
    execute(':COPY /B /O B1:F0.DAT C3:F1.DAT');assert disks['c'].read_bytes()==saved,'overwrote RO target'
    savedb=disks['b'].read_bytes()
    execute(':COPY /B /O B1:F0.DAT B1:F0.DAT');assert disks['b'].read_bytes()==savedb,'self-copy changed source'
    execute(':COPY /B /V B1:*.DAT[$ARC+!$SYS] C5:')
    for n in (4,5):check('c',5,f'F{n}.DAT',payloads[n],n)
    assert not any(rows('c',5,f'F{n}.DAT') for n in (0,1,2,3,6,7))
    put('b',2,'EMPTY.DAT',b'')
    execute(':COPY /B /V B2:EMPTY.DAT C6:');check('c',6,'EMPTY.DAT',b'',0)
    saved={d:disks[d].read_bytes() for d in 'bc'}
    for command in (':COPY /B B1:F0.DAT C7: /BAD',':COPY /B B1:F0.DAT C7:TOOLONGNAME.DAT',':COPY /B [B1,E0]:*.DAT C7:'):
        execute(command)
        assert all(disks[d].read_bytes()==saved[d] for d in 'bc'),command
    put('b',8,'MOVE.DAT',b'M'*256,6)
    execute('MOVE B8:MOVE.DAT C8:MOVED.DAT');check('c',8,'MOVED.DAT',b'M'*256,6)
    assert not rows('b',8,'MOVE.DAT'),'successful MOVE retained source'
    put('b',9,'RO.DAT',b'R'*256,7)
    saved={d:disks[d].read_bytes() for d in 'bc'}
    text=execute('MOVE B9:RO.DAT C9:RO.DAT');assert b'READ ONLY' in text
    assert all(disks[d].read_bytes()==saved[d] for d in 'bc'),'RO MOVE changed media'
    check('b',9,'RO.DAT',b'R'*256,7);assert not rows('c',9,'RO.DAT')
    put('b',10,'KEEP.DAT',b'K'*128);put('c',10,'KEEP.DAT',b'T'*128)
    saved={d:disks[d].read_bytes() for d in 'bc'}
    execute('MOVE B10:KEEP.DAT C10:KEEP.DAT')
    assert all(disks[d].read_bytes()==saved[d] for d in 'bc'),'collision MOVE changed files'
    shipped=audit(base,report,w,disks['a'])
    for d in 'bc':
        result=subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(disks[d])],cwd=w,capture_output=True,check=True)
        (w/f'filesystem-{d}.txt').write_bytes(result.stdout+result.stderr)
    (w/'result.json').write_text(json.dumps({'status':'PASS','commands':commands,'runner_sha256':sha(Path(__file__)),'baseline_sha256':report['sha256'],'simulator_sha256':sha(sim),'unchanged_shipped_files':shipped},indent=2)+'\n')
    print('PASS shipped COPY/MOVE:',len(commands),'sessions',w)


if __name__=='__main__':main()
