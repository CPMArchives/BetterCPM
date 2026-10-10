#!/usr/bin/env python3
"""Shared resident COPY/MOVE selection and no-mutation preflight on both platforms."""
import argparse,json,shutil,subprocess
from pathlib import Path
from test_disk_utilities import ROOT,medium,keys
from test_z80pack_sysgen_install import session
from test_sysgen_install import screen
from test_z80pack_attributes import directory
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run

def main():
 p=argparse.ArgumentParser();p.add_argument('--platform',choices=['z80pack','model4'],required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--image-dir',type=Path);a=p.parse_args()
 report=a.report.resolve();report.mkdir(exist_ok=False,parents=True)
 fixtures=[]
 def add(user,name,mask=0,size=129,seed=7):
  # Smallest useful multi-extent fixtures keep physical-floppy qualification bounded.
  if a.platform=='model4' and size==40000:size=17000
  fixtures.append((name,bytes((i*seed+user)%256 for i in range(size)),user,mask))
 add(1,'C1SYS.DAT',2);add(2,'C2ARC.DAT',4,40000)
 add(4,'M4.DAT',2);add(5,'M5.DAT',4,40000)
 add(6,'SAME.DAT');add(7,'SAME.DAT');add(8,'E8.DAT');add(9,'E9.DAT');add(10,'E9.DAT')
 add(11,'READ.DAT',1);add(12,'OVER.DAT',4,257);add(10,'OVER.DAT',0,129,3)
 add(13,'SELF.DAT');add(13,'ONE.DAT');add(14,'G1.DAT');add(15,'G2.DAT');add(13,'Q1.DAT');add(14,'H1.DAT');add(15,'H2.DAT')
 # Each change is (source DU/name, target DU/name, delete source?).
 cases=[
  ('COPY [A1,A2]:C*.DAT A[10,11]:','COPY source destination',[]),
  ('MOVE [A4,A5]:M*.DAT [A10,A11]:','COPY source destination',[]),
  ('COPY A1:C1SYS.DAT A10:F*A.DAT','COPY source destination',[]),
  ('COPY A1:C*B.DAT A10:','COPY source destination',[]),
  ('COPY [A1,E2]:C*.DAT A10:','INVALID DRIVE',[]),
  ('COPY [A1,A2]:C*.DAT A10:ONE.DAT','COPY source destination',[]),
  ('COPY A[6,7]:SAME.DAT A10: /O','Destination mapping collision.',[]),
  ('MOVE A[6,7]:SAME.DAT A10:','Destination mapping collision.',[]),
  ('COPY A[8,9]:E*.DAT A10:','FILE EXISTS',[]),
  ('COPY A13:SELF.DAT A13: /O','FILE EXISTS',[]),
  ('MOVE A11:READ.DAT A10:','READ ONLY',[]),
  ('COPY [A1,A2]:C*.DAT [A10,A10]:','',[(1,'C1SYS.DAT',10,'C1SYS.DAT',False),(2,'C2ARC.DAT',10,'C2ARC.DAT',False)]),
  ('MOVE [A4,5]:M*.DAT A10:','',[(4,'M4.DAT',10,'M4.DAT',True),(5,'M5.DAT',10,'M5.DAT',True)]),
  ('COPY A11:READ.DAT A10:','',[(11,'READ.DAT',10,'READ.DAT',False)]),
  ('COPY A12:OVER.DAT A10: /O','',[(12,'OVER.DAT',10,'OVER.DAT',False)]),
  ('COPY A13:SELF.DAT A13:NEW.DAT','',[(13,'SELF.DAT',13,'NEW.DAT',False)]),
  ('MOVE A10:MOVED.DAT:=A13:ONE.DAT','',[(13,'ONE.DAT',10,'MOVED.DAT',True)]),
  ('COPY A[-]:C*.DAT A10: /O','FILE EXISTS',[]),
  ('COPY A1:C1SYS.DAT[$RW+!$SYS] A10:','NO FILE',[]),
  ('COPY A1:C1SYS.DAT A10:READ.DAT /O','READ ONLY',[]),
  ('COPY [A14,A15,A3]:G*.DAT A3:','',[(14,'G1.DAT',3,'G1.DAT',False),(15,'G2.DAT',3,'G2.DAT',False)]),
  ('COPY A13:Q*.DAT A13:Q2.DAT /O','',[(13,'Q1.DAT',13,'Q2.DAT',False)]),
  ('MOVE [A14,A15,A4]:H*.DAT A4:','',[(14,'H1.DAT',4,'H1.DAT',True),(15,'H2.DAT',4,'H2.DAT',True)]),
  ('MOVE A13:Q2*.DAT A13:Q3.DAT','',[(13,'Q2.DAT',13,'Q3.DAT',True)])]
 def cpm(tool,*args):return subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(report/'disks/drivea.dsk'),*map(str,args)],cwd=report,check=True,stdout=subprocess.DEVNULL)
 observations=[]
 if a.platform=='z80pack':
  assert a.image_dir;shutil.copytree(a.image_dir/'disks',report/'disks');shutil.copy2(a.image_dir/'diskdefs',report/'diskdefs')
  cpm('cpmrm','0:RCP.CPX');cpm('cpmcp',ROOT/'build/cpx/RCP.CPX','0:RCP.CPX')
  for name,data,user,mask in fixtures:
   f=report/name;f.write_bytes(data);cpm('cpmcp',f,f'{user}:{name}')
   if mask:cpm('cpmchattr',''.join(flag for bit,flag in [(1,'r'),(2,'s'),(4,'a')] if mask&bit),f'{user}:{name}')
  for i,(cmd,wanted,changes) in enumerate(cases):
   before=(report/'disks/drivea.dsk').read_bytes()
   text=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',report/'disks',[(cmd.encode()+b'\r',b'A0>_ ',120)],report/f'case-{i}.txt').decode(errors='replace')
   assert wanted in text,(cmd,wanted,text)
   if wanted or not changes:assert (report/'disks/drivea.dsk').read_bytes()==before,cmd
   observations.append({'command':cmd,'result':'PASS'})
  raw=directory(report/'disks/drivea.dsk',report/'diskdefs')
 else:
  extras=[('SUBMIT.COM',(ROOT/'build/utilities/SUBMIT.COM').read_bytes()),*fixtures];script=[]
  for i,(cmd,_,_) in enumerate(cases):
   script += [cmd,f'CHECK{i}'];extras.append((f'CHECK{i}.COM',bytes.fromhex('110b010e09cd0500c30000')+f'\r\nCOPY MOVE CASE {i}\r\n$'.encode()))
  extras.append(('CASE.SUB',('\r\n'.join(script)+'\r\n').replace('$','$$').encode()+b'\x1a'))
  disk=report/'a.dmk';disk.write_bytes(medium(extras))
  invocation=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(disk),'-id','3000','-it']+keys('SUBMIT CASE\r')+['-itime','0']
  for i in range(len(cases)):invocation+=['-iw',f'COPY MOVE CASE {i}','-it']
  invocation+=['-id','3000','-it','-ix'];(report/'invocation.json').write_text(json.dumps(invocation))
  run(invocation,cwd=report,timeout=900,check=True)
  for i,(cmd,wanted,_) in enumerate(cases):
   text=screen(report/f'trs80-text-{i+1}.bin');assert wanted in text,(cmd,wanted,text);assert f'COPY MOVE CASE {i}' in text
   (report/f'case-{i}.txt').write_text(text);observations.append({'command':cmd,'result':'PASS'})
  from add_cpm_file_to_dmk import extract_raw
  from build_trs80_boot import FILESYSTEM_FIRST_SECTOR
  filesystem=extract_raw(disk.read_bytes())[FILESYSTEM_FIRST_SECTOR*512:]
  raw=filesystem[:4096]
 # Independent raw metadata: successful mappings preserved entry count/attrs;
 # rejected batches retained originals, and no cross-user relocation occurred.
 expected={}
 for name,data,user,mask in fixtures:expected[(user,name)]=(mask,data)
 for _,_,changes in cases:
  for user,name,target,new,erase in changes:
   expected[(target,new)]=expected[(user,name)]
   if erase:del expected[(user,name)]
 actual={}
 for pos in range(0,len(raw),32):
  e=raw[pos:pos+32]
  if e[0] not in (set(u for u,_ in expected)|set(u for _,_,u,_ in fixtures)):continue
  n=bytes(v&127 for v in e[1:9]).decode().rstrip()+'.'+bytes(v&127 for v in e[9:12]).decode().rstrip()
  mask=sum((e[9+i]>>7)<<i for i in range(3));actual.setdefault((e[0],n),[]).append((mask,e))
 assert set(actual)==set(expected),(set(actual),set(expected))
 for key,(mask,data) in expected.items():
  assert all(m==mask for m,_ in actual[key]),(key,mask,actual[key])
  if a.platform=='z80pack':
   f=report/'extracted.dat';cpm('cpmcp',f'{key[0]}:{key[1]}',f)
   content=f.read_bytes();assert len(data)<=len(content)<=((len(data)+127)&~127),key
   assert content[:len(data)]==data,key
 if a.platform=='model4':
  from test_model4_copy import files
  contents=files(filesystem)
  for (user,name),(_,data) in expected.items():
   stem,_,ext=name.partition('.')
   key=stem.ljust(8).encode()+ext.ljust(3).encode()
   content=contents[(user,key)][0]
   assert len(data)<=len(content)<=((len(data)+127)&~127),(user,name)
   assert content[:len(data)]==data,(user,name)
 (report/'evidence.json').write_text(json.dumps({'result':'PASS','platform':a.platform,'cases':observations},indent=2))
 print(f'Resident COPY/MOVE: {len(cases)} shared selection/preflight cases PASS on {a.platform}')
if __name__=='__main__':main()
