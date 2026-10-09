#!/usr/bin/env python3
"""Native COPY source predicates, exact selection and filtered preflight."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from test_disk_utilities import ROOT
from test_z80pack_sysgen_install import session


def main():
    p=argparse.ArgumentParser();p.add_argument('--image-dir',type=Path,required=True);p.add_argument('--report',type=Path,required=True);args=p.parse_args()
    work=args.report.resolve();work.mkdir(parents=True,exist_ok=False)
    shutil.copytree(args.image_dir/'disks',work/'disks');shutil.copy2(args.image_dir/'diskdefs',work/'diskdefs')
    disks={d:work/'disks'/f'drive{d}.dsk' for d in 'abcd'}
    def cpm(tool,d,*values):
        subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disks[d]),*map(str,values)],cwd=work,check=True)
    cpm('cpmrm','a','0:COPY.COM');cpm('cpmcp','a',ROOT/'build/utilities/COPY.COM','0:COPY.COM')
    for d in 'bcd':disks[d].write_bytes(bytes([229])*len(disks[d].read_bytes()))
    data={}
    for state in range(8):
        name=f'F{state}.DAT';payload=bytes([state+48])*(33280 if state==7 else 128)
        f=work/name;f.write_bytes(payload);data[name]=payload;cpm('cpmcp','b',f,'1:'+name)
        flags=''.join(ch for bit,ch in [(1,'r'),(2,'s'),(4,'a')] if state&bit)
        if flags:cpm('cpmchattr','b',flags,'1:'+name)
    sim=Path.home()/'projects/git/z80pack/cpmsim/cpmsim';cases=[]
    def execute(command,label,unchanged=False):
        before={d:disks[d].read_bytes() for d in 'bcd'}
        text=session(sim,work/'disks',[(b'CPX UNLOAD RCP\r',b'A0>_ ',30),(command.encode()+b'\r',b'A0>_ ',120)],work/(label+'.txt'))
        assert disks['b'].read_bytes()==before['b'],command
        if unchanged:assert disks['d'].read_bytes()==before['d'],command
        cases.append(command);return text
    def check(user,selected):
        for state in range(8):
            name=f'F{state}.DAT';f=work/f'out-{user}-{name}'
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disks['d']),f'{user}:{name}',str(f)],cwd=work,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            assert f.exists()==(state in selected),(user,state)
            if f.exists():assert f.read_bytes()==data[name]
    for user,expression,selected in [
        (3,'$RO',{1,3,5,7}),(4,'$RW',{0,2,4,6}),
        (5,'$SYS',{2,3,6,7}),(6,'$DIR',{0,1,4,5}),
        (7,'$ARC',{4,5,6,7}),(8,'$ARC+!$SYS',{4,5}),
        (9,'$RO,$SYS',{1,2,3,5,6,7}),
        (10,'$R/O',{1,3,5,7}),(11,'$R/W',{0,2,4,6})]:
        command=f'COPY /B /V D{user}: = B1:*.DAT[{expression}]'
        text=execute(command,f'predicate-{user}')
        assert b'COPY source destination' not in text and b'VERIFY ERROR' not in text,command
        check(user,selected)
    text=execute('COPY /B B1:*.DAT[$RO+!$RO] D12:','empty',True)
    assert b'NO FILE' in text
    for i,expr in enumerate(['$WHL','$ARC+','','$RO,,!$SYS']):
        text=execute(f'COPY /B B1:*.DAT[{expr}] D12:',f'invalid-{i}',True)
        assert b'COPY source destination' in text
    # Same generated name, but only the ARC-marked DU survives filtering.
    f=work/'DUP.DAT';f.write_bytes(b'Q'*128)
    cpm('cpmcp','b',f,'2:DUP.DAT');cpm('cpmchattr','b','a','2:DUP.DAT')
    cpm('cpmcp','c',f,'2:DUP.DAT')
    text=execute('COPY /B [B2,C2]:*.DAT[$ARC] D13:','filtered-collision')
    assert b'COPY DESTINATION CONFLICT' not in text
    cpm('cpmchattr','c','a','2:DUP.DAT')
    text=execute('COPY /O /B [B2,C2]:*.DAT[$ARC] D14:','selected-collision',True)
    assert b'COPY DESTINATION CONFLICT' in text
    text=execute('COPY /B B1:F4.DAT[$ARC] B1:F4.DAT','selected-overlap',True)
    assert b'COPY DESTINATION CONFLICT' in text
    (work/'evidence.json').write_text(json.dumps({'result':'PASS','commands':cases,'copy_sha256':hashlib.sha256((ROOT/'build/utilities/COPY.COM').read_bytes()).hexdigest()},indent=2)+'\n')
    print('Native COPY source attributes, aliases, logical extents and filtered preflight pass')


if __name__=='__main__':main()
