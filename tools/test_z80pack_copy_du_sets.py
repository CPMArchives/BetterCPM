#!/usr/bin/env python3
"""Qualify multi-DU COPY collection and whole-source-set safety."""
import argparse,shutil,subprocess,json,hashlib
from pathlib import Path
from test_disk_utilities import ROOT
from test_z80pack_sysgen_install import session

def main():
 p=argparse.ArgumentParser();p.add_argument('--image-dir',type=Path,required=True);p.add_argument('--report',type=Path,required=True);args=p.parse_args()
 work=args.report.resolve();work.mkdir(parents=True,exist_ok=False);shutil.copytree(args.image_dir/'disks',work/'disks');shutil.copy2(args.image_dir/'diskdefs',work/'diskdefs')
 disks={x:work/'disks'/f'drive{x}.dsk' for x in 'abcd'}
 def cpm(tool,disk,*values):subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disk),*map(str,values)],cwd=work,check=True)
 cpm('cpmrm',disks['a'],'0:*.COM')
 for name in ['COPY.COM','CPX.COM']:cpm('cpmcp',disks['a'],ROOT/'build/utilities'/name,'0:'+name)
 for d in 'bcd':disks[d].write_bytes(bytes([229])*len(disks[d].read_bytes()))
 def put(d,u,name,data):
  f=work/f'{d}-{u}-{name}';f.write_bytes(data);cpm('cpmcp',disks[d],f,f'{u}:{name}')
 expected={}
 for d,u in [('a',0),('a',5),('b',5),('b',6),('b',7),('c',3),('c',5),('c',6)]:
  name=f'{d.upper()}{u:02}.COM';data=(name.encode()*20).ljust(256,b'X');put(d,u,name,data);expected[name]=data
 for name in ['COPY.COM','CPX.COM']:
  data=(ROOT/'build/utilities'/name).read_bytes();expected[name]=data.ljust((len(data)+127)//128*128,b'\0')
 sim=Path.home()/'projects/git/z80pack/cpmsim/cpmsim';cases=[]
 def execute(cmd,label,unchanged=False):
  before={d:p.read_bytes() for d,p in disks.items()}
  text=session(sim,work/'disks',[(b'CPX UNLOAD RCP\r',b'A0>_ ',30),(cmd.encode()+b'\r',b'A0>_ ',120)],work/(label+'.txt'))
  for d in 'abc':assert disks[d].read_bytes()==before[d],(cmd,d)
  if unchanged:assert disks['d'].read_bytes()==before['d'],cmd
  cases.append(cmd);return text
 def contents(user,names):
  for name,data in names.items():
   f=work/('read-'+str(user)+'-'+name);cpm('cpmcp',disks['d'],f'{user}:{name}',f)
   assert f.read_bytes()==data,(user,name)
 text=execute('COPY /B [A0,B[5-7],C[3,5,6],5]:*.COM D3:','mixed')
 assert b'COPY DESTINATION CONFLICT' not in text and b'COPY source destination' not in text,text
 contents(3,expected)
 text=execute('COPY [A[-],B[-],C[-]]:*.COM D0: /B','all-users');contents(0,expected)
 # Equal names from distinct source DUs must reject even /O, before writes.
 put('b',5,'DUP.COM',b'B'*128);put('c',3,'DUP.COM',b'C'*128)
 text=execute('COPY [B5,C3]:DUP.COM D4: /O /B','duplicate',True);assert b'COPY DESTINATION CONFLICT' in text,text
 # A target that is itself a later source is forbidden, regardless of order.
 cpm('cpmrm',disks['b'],'5:DUP.COM');cpm('cpmrm',disks['c'],'3:DUP.COM')
 text=execute('COPY [B5,C3]:*.COM B5: /O /B','source-overlap',True);assert b'COPY DESTINATION CONFLICT' in text,text
 for i,cmd in enumerate(['COPY [B5,C[3,32]]:*.COM D5: /B','COPY B[*]:*.COM D5: /B','COPY B5:*.COM D[3,4]: /B']):
  text=execute(cmd,f'invalid-{i}',True);assert b'COPY source destination' in text,text
 text=execute('COPY [B5,P0]:*.COM D5: /B','unavailable',True);assert b'COPY SOURCE DRIVE UNAVAILABLE' in text,text
 # Global count, not per-DU count: reject the 65th distinct file before writes.
 for d in 'bc':disks[d].write_bytes(bytes([229])*len(disks[d].read_bytes()))
 for i in range(65):put('b' if i<60 else 'c',5,f'N{i:03}.COM',bytes([i])*128)
 text=execute('COPY [B5,C5]:*.COM D5: /B','capacity',True);assert b'COPY BATCH TOO LARGE' in text,text
 (work/'evidence.json').write_text(json.dumps({'result':'PASS','cases':cases,'sources_unchanged':True,'rejected_batches_destination_unchanged':True,'copy_sha256':hashlib.sha256((ROOT/'build/utilities/COPY.COM').read_bytes()).hexdigest()},indent=2)+'\n')
 print('COPY DU source sets, exact bytes, global conflict/overlap and capacity safety pass')
if __name__=='__main__':main()
