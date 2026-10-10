#!/usr/bin/env python3
"""Native backup ARC updates with raw metadata."""
import hashlib
import argparse,json,shutil,subprocess,re
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
  if '/BACKUP' not in cmd:assert disks['b'].read_bytes()==before['b']
  if unchanged:assert disks['d'].read_bytes()==before['d']
  commands.append(cmd);return t
 def entries():
  raw=disks['d'].read_bytes();directory=b''.join(raw[6*18*256+n*256:6*18*256+(n+1)*256] for n in [0,4,8,12,16,2,6,10])
  return [directory[i:i+32] for i in range(0,len(directory),32)]
 for user,cmd in [(3,'COPY /BACKUP /B /V B1:*.DAT D3:[$ARC]'),(4,'COPY /B /V B1:*.DAT D4: /BACKUP')]:
  t=execute(cmd,f'backup-{user}')
  assert b'COPY source destination' not in t and b'INCOMPLETE' not in t
  assert b'8 FILES COPIED [48K]' in t and b'[34K]' in t,t
  for state in range(8):
   f=w/f'out-{user}-{state}';cpm('cpmcp','d',f'{user}:F{state}.DAT',f);assert f.read_bytes()==payloads[state]
   found=[e for e in entries() if e[0]==user and bytes(c&127 for c in e[1:12])==f'F{state}'.ljust(8).encode()+b'DAT']
   assert found and all(sum(1<<i for i in range(3) if e[9+i]&128)==(state&3) for e in found),(user,state)
  raw=disks['b'].read_bytes();directory=b''.join(raw[6*18*256+n*256:6*18*256+(n+1)*256] for n in [0,4,8,12,16,2,6,10])
  for state in range(8):
   found=[directory[i:i+32] for i in range(0,len(directory),32) if directory[i]==1 and bytes(c&127 for c in directory[i+1:i+12])==f'F{state}'.ljust(8).encode()+b'DAT']
   assert found and all(sum(1<<i for i in range(3) if e[9+i]&128)==(state&3) for e in found)
 for i,cmd in enumerate(['COPY /BACKUPX /B B1:*.DAT D7:','COPY /B B1:*.DAT D7: /BACKUPX','COPY /BACKUP /B B1:*.DAT D7:[$ARC,!$ARC]']):
  t=execute(cmd,f'invalid-{i}',True);assert b'COPY source destination' in t
 # Controlled metadata failures use private binaries, never the released image.
 base=(ROOT/'build/utilities/COPY.COM').read_bytes()
 listing=(ROOT/'build/utilities/copy-transient.lst').read_text()
 def addr(name):return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
 for user,label,start in [(8,'destination-metadata','CTVATTR'),(9,'source-metadata','CTBPOST')]:
  cpm('cpmchattr','b','a','1:F4.DAT')
  before=disks['b'].read_bytes()
  image=bytearray(base);off=image.index(b'\x0e\x1e\xcd\x05\x00',addr(start)-256)+2
  image[off:off+3]=b'\x3e\xff\x00'
  binary=w/(label+'.com');binary.write_bytes(image)
  cpm('cpmrm','a','0:COPY.COM');cpm('cpmcp','a',binary,'0:COPY.COM')
  t=execute(f'COPY /B /V /BACKUP B1:F4.DAT D{user}:',label)
  assert b'DATA COPIED; ATTRIBUTE STATUS INCOMPLETE' in t
  assert disks['b'].read_bytes()==before
  f=w/(label+'.dat');cpm('cpmcp','d',f'{user}:F4.DAT',f);assert f.read_bytes()==payloads[4]
 cpm('cpmrm','a','0:COPY.COM');cpm('cpmcp','a',ROOT/'build/utilities/COPY.COM','0:COPY.COM')
 # A skipped collision and a failed verification never clear source ARC.
 before=disks['b'].read_bytes()
 execute('COPY /B /S /BACKUP B1:F4.DAT D3:','skip')
 assert disks['b'].read_bytes()==before
 image=bytearray(base);off=addr('CTVERIFY')-256;image[off:off+2]=b'\x37\xc9'
 binary=w/'verify-failure.com';binary.write_bytes(image)
 cpm('cpmrm','a','0:COPY.COM');cpm('cpmcp','a',binary,'0:COPY.COM')
 t=execute('COPY /B /V /BACKUP B1:F4.DAT D10:','verify-failure')
 assert disks['b'].read_bytes()==before and b'VERIFY ERROR' in t
 assert not any(e[0]==10 for e in entries())
 (w/'evidence.json').write_text(json.dumps({'copy_sha256':hashlib.sha256((ROOT/'build/utilities/COPY.COM').read_bytes()).hexdigest(),'result':'PASS','commands':commands,'raw_attributes_verified':True,'source_arc_cleared_only':True},indent=2)+'\n')
 print('Native COPY backup, option orders, read-only sources and raw extents pass')


if __name__=='__main__':main()
