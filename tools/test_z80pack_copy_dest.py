#!/usr/bin/env python3
"""Native destination qualifiers and read-only protection with raw metadata."""
import hashlib
import argparse,json,shutil,subprocess
from pathlib import Path
from test_disk_utilities import ROOT
from test_z80pack_sysgen_install import session


def main():
 p=argparse.ArgumentParser();p.add_argument('--image-dir',type=Path,required=True);p.add_argument('--report',type=Path,required=True);args=p.parse_args()
 w=args.report.resolve();w.mkdir(parents=True,exist_ok=False);shutil.copytree(args.image_dir/'disks',w/'disks');shutil.copy2(args.image_dir/'diskdefs',w/'diskdefs')
 disks={x:w/'disks'/f'drive{x}.dsk' for x in 'abd'}
 def cpm(tool,d,*v):subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disks[d]),*map(str,v)],cwd=w,check=True)
 cpm('cpmrm','a','0:COPY.COM');cpm('cpmcp','a',ROOT/'build/utilities/COPY.COM','0:COPY.COM')
 for d in 'bd':disks[d].write_bytes(bytes([229])*len(disks[d].read_bytes()))
 payloads={}
 for state in range(8):
  f=w/f'F{state}.DAT';f.write_bytes(bytes([state+48])*(33280 if state==7 else 128));payloads[state]=f.read_bytes();cpm('cpmcp','b',f,'1:'+f.name)
  flags=''.join(c for bit,c in [(1,'r'),(2,'s'),(4,'a')] if state&bit)
  if flags:cpm('cpmchattr','b',flags,'1:'+f.name)
 sim=Path.home()/'projects/git/z80pack/cpmsim/cpmsim';commands=[]
 def execute(cmd,label,unchanged=False):
  before={d:disks[d].read_bytes() for d in 'bd'}
  t=session(sim,w/'disks',[(b'CPX UNLOAD RCP\r',b'A0>_ ',30),(cmd.encode()+b'\r',b'A0>_ ',120)],w/(label+'.txt'))
  assert disks['b'].read_bytes()==before['b']
  if unchanged:assert disks['d'].read_bytes()==before['d']
  commands.append(cmd);return t
 def entries():
  raw=disks['d'].read_bytes();directory=b''.join(raw[6*18*256+n*256:6*18*256+(n+1)*256] for n in [0,4,8,12,16,2,6,10])
  return [directory[i:i+32] for i in range(0,len(directory),32)]
 for user,qual,expected in [(3,'$RW,!$ARC',lambda x:x&2),(4,'$RO,$SYS,$ARC',lambda x:7),(5,'$DIR',lambda x:x&5)]:
  cmd=f'COPY /B /V D{user}:[{qual}] = B1:*.DAT';t=execute(cmd,f'overrides-{user}')
  assert b'COPY source destination' not in t and b'VERIFY ERROR' not in t
  for state in range(8):
   f=w/f'out-{user}-{state}';cpm('cpmcp','d',f'{user}:F{state}.DAT',f);assert f.read_bytes()==payloads[state]
   found=[e for e in entries() if e[0]==user and bytes(c&127 for c in e[1:12])==f'F{state}'.ljust(8).encode()+b'DAT']
   assert found and all(sum(1<<i for i in range(3) if e[9+i]&128)==expected(state) for e in found),(user,state)
 t=execute('COPY /V /B B1:*.DAT[$ARC] D6:*.BAK[$R/W,$DIR,!$ARC]','both-qualifiers')
 assert b'COPY source destination' not in t
 for state in range(4,8):
  f=w/f'rename-{state}';cpm('cpmcp','d',f'6:F{state}.BAK',f);assert f.read_bytes()==payloads[state]
  found=[e for e in entries() if e[0]==6 and bytes(c&127 for c in e[1:12])==f'F{state}'.ljust(8).encode()+b'BAK']
  assert found and all(not any(e[i]&128 for i in (9,10,11)) for e in found)
 for i,q in enumerate(['$RO,$RW','$SYS,$DIR','$ARC,!$ARC','$RO+$SYS','$RO,,','$WHL']):
  t=execute(f'COPY /B B1:*.DAT D7:[{q}]',f'invalid-{i}',True);assert b'COPY source destination' in t
 f=w/'old.dat';f.write_bytes(b'OLD'.ljust(128,b'X'));cpm('cpmcp','d',f,'7:F0.DAT');cpm('cpmchattr','d','r','7:F0.DAT')
 t=execute('COPY /O /B B1:F0.DAT D7:[$RW]','read-only',True);assert b'READ ONLY' in t
 (w/'evidence.json').write_text(json.dumps({'copy_sha256':hashlib.sha256((ROOT/'build/utilities/COPY.COM').read_bytes()).hexdigest(),'result':'PASS','commands':commands,'raw_attributes_verified':True,'source_media_unchanged':True},indent=2)+'\n')
 print('Native COPY destination overrides, qualifier orders, raw extents and read-only protection pass')


if __name__=='__main__':main()
