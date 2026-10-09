#!/usr/bin/env python3
"""Qualify STAT extended-DU inspection on disposable media."""
import argparse,shutil,subprocess,json,hashlib
from pathlib import Path
from test_disk_utilities import ROOT
from test_z80pack_sysgen_install import session

def main():
 p=argparse.ArgumentParser();p.add_argument('--image-dir',type=Path,required=True);p.add_argument('--report',type=Path,required=True);args=p.parse_args()
 work=args.report.resolve();work.mkdir(parents=True,exist_ok=False);shutil.copytree(args.image_dir/'disks',work/'disks');shutil.copy2(args.image_dir/'diskdefs',work/'diskdefs')
 disks={x:work/'disks'/f'drive{x}.dsk' for x in 'abc'}
 def cpm(tool,disk,*values):subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disk),*map(str,values)],cwd=work,check=True)
 cpm('cpmrm',disks['a'],'0:STAT.COM','0:RSXTEST.COM','0:RSX2TST.COM');cpm('cpmcp',disks['a'],ROOT/'build/utilities/STAT.COM','0:STAT.COM')
 for drive in 'bc':disks[drive].write_bytes(bytes([229])*len(disks[drive].read_bytes()))
 for drive,user,name,size in [('a',0,'FIRST.DAT',128),('b',3,'SAME.DAT',128),('b',5,'SAME.DAT',256),('b',31,'LAST.DAT',20000),('c',3,'THIRD.DAT',128),('c',5,'FIFTH.DAT',128),('c',7,'SEVENTH.DAT',128),('c',11,'ELEVEN.DAT',128)]:
  f=work/f'{drive}-{user}-{name}';f.write_bytes(bytes(size));cpm('cpmcp',disks[drive],f,f'{user}:{name}')
 sim=Path.home()/'projects/git/z80pack/cpmsim/cpmsim'
 observations=[]
 def check(cmd,required,forbidden=(),caller='A0'):
  steps=[]
  if caller!='A0':steps.append((caller.encode()+b':\r',caller.encode()+b'>_ ',30))
  steps.append((cmd.encode()+b'\r',caller.encode()+b'>_ ',60))
  before={p:p.read_bytes() for p in disks.values()}
  text=session(sim,work/'disks',steps,work/f'case-{len(observations)}.txt')
  def rendered(x):
   if x.endswith('.DAT'):
    du,name=x.split(':');stem,ext=name.split('.');return (du+':'+stem.ljust(8)+'.'+ext).encode()
   return x.encode()
  for x in required:assert rendered(x) in text,(cmd,x,text)
  for x in forbidden:assert rendered(x) not in text,(cmd,x,text)
  assert all(p.read_bytes()==data for p,data in before.items()),cmd
  observations.append(cmd);return text
 t=check('STAT B[3,5]:*.DAT',['B3:SAME.DAT','B5:SAME.DAT'])
 assert t.count(b'B3:SAME    .DAT')==1 and t.count(b'B5:SAME    .DAT')==1
 t=check('STAT B[5-3,3,5]:*.DAT $S',['B3:SAME.DAT','B5:SAME.DAT','B4:','File Not Found'])
 assert t.count(b'B3:SAME    .DAT')==1 and t.count(b'B5:SAME    .DAT')==1
 check('STAT B[31-]:*.DAT',['B31:LAST.DAT'])
 check('A0:STAT [A0,C[3,5,7-11],5]:*.DAT',['A0:FIRST.DAT','B5:SAME.DAT','C3:THIRD.DAT','C5:FIFTH.DAT','C7:SEVENTH.DAT','C11:ELEVEN.DAT'],caller='B2')
 check('STAT [P0,B3]:*.DAT',['B3:SAME.DAT','P0: unavailable'])
 for cmd in ['STAT [B3,B[5,32]]:*.DAT','STAT B[*]:*.DAT','STAT B[3]:*.DAT $R/O','STAT B[3]:DSK:','STAT B[3]:','STAT B[3]:=R/O']:
  check(cmd,['Invalid STAT command'],['B3:SAME.DAT'])
 check('STAT B3:*.DAT',['B:SAME.DAT'],['B3:SAME.DAT'])
 (work/'evidence.json').write_text(json.dumps({'result':'PASS','cases':observations,'media_unchanged':True,'stat_sha256':hashlib.sha256((ROOT/'build/utilities/STAT.COM').read_bytes()).hexdigest()},indent=2)+'\n')
 print('STAT DU sets, inheritance, read-only scope, continuation and caller restoration pass')
if __name__=='__main__':main()
