#!/usr/bin/env python3
"""Resident REN selection, mapping and no-mutation preflight on both platforms."""
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
 def add(user,name,mask=0,size=129):fixtures.append((name,bytes((i*7+user)%256 for i in range(size)),user,mask))
 for u in [3,5]:
  add(u,'BATCH1.DOC',2);add(u,'BATCH2.DOC',4,40000)
  add(u,'DUP1.DOC');add(u,'DUP2.DOC')
  add(u,'LATER.DOC')
 add(5,'TAKEN.TXT');add(3,'FOOBAR.DOC');add(3,'ONE.DOC')
 add(3,'RO1.DOC',1);add(3,'RO2.DOC',0);add(3,'OV1.DOC');add(3,'OV2.DOC')
 cases=[
  ('REN A3:BAD.TXT=A3:ONE.DOC','Invalid filespec.',{}),
  ('REN A[-]:*.TXT=A3:ONE.DOC','Invalid filespec.',{}),
  ('REN *.TXT=A[3,5]:F*A.DOC','Invalid filespec.',{}),
  ('REN KEEP.TXT=A0:MISSING.DOC','NO FILE',{}),
  ('REN NEW.TXT_A3:ONE.DOC','',{(3,'ONE.DOC'):'NEW.TXT'}),
  ('REN *.TXT=[A3,5]:BATCH*.DOC','',{(u,n):n.replace('.DOC','.TXT') for u in [3,5] for n in ['BATCH1.DOC','BATCH2.DOC']}),
  ('REN SAME.TXT=A[3,5]:DUP*.DOC','Rename mapping collision.',{}),
  ('REN TAKEN.TXT=A[3,5]:LATER.DOC','FILE EXISTS',{}),
  ('REN OV2.DOC=A3:OV*.DOC','FILE EXISTS',{}),
  ('REN *.TXT=A3:RO*.DOC','Read only.',{}),
  ('REN X?***.BAK=A3:FOOBAR.DOC','',{(3,'FOOBAR.DOC'):'XOOBAR.BAK'}),
  ('REN *.TXT=A3:RO*.DOC[$RW]','',{(3,'RO2.DOC'):'RO2.TXT'}),
  ('REN SAME.TXT=A[3,5]:LATER.DOC','',{(u,'LATER.DOC'):'SAME.TXT' for u in [3,5]}),
  ('REN *.TXT=A[3,5]:*.TXT','',{}),
  ('REN B2:NEW.TXT=A3:NEW.TXT','Invalid filespec.',{}),
  ('REN NEW.TXT=[A3,E5]:NEW.TXT','INVALID DRIVE',{})]
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
   script += [cmd,f'CHECK{i}'];extras.append((f'CHECK{i}.COM',bytes.fromhex('110b010e09cd0500c30000')+f'\r\nREN CASE {i}\r\n$'.encode()))
  extras.append(('CASE.SUB',('\r\n'.join(script)+'\r\n').replace('$','$$').encode()+b'\x1a'))
  disk=report/'a.dmk';disk.write_bytes(medium(extras))
  invocation=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(disk),'-id','3000','-it']+keys('SUBMIT CASE\r')+['-itime','0']
  for i in range(len(cases)):invocation+=['-iw',f'REN CASE {i}','-it']
  invocation+=['-id','3000','-it','-ix'];(report/'invocation.json').write_text(json.dumps(invocation))
  run(invocation,cwd=report,timeout=900,check=True)
  for i,(cmd,wanted,_) in enumerate(cases):
   text=screen(report/f'trs80-text-{i+1}.bin');assert wanted in text,(cmd,wanted,text);assert f'REN CASE {i}' in text
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
  for key,new in changes.items():expected[(key[0],new)]=expected.pop(key)
 actual={}
 for pos in range(0,len(raw),32):
  e=raw[pos:pos+32]
  if e[0] not in [3,5]:continue
  n=bytes(v&127 for v in e[1:9]).decode().rstrip()+'.'+bytes(v&127 for v in e[9:12]).decode().rstrip()
  mask=sum((e[9+i]>>7)<<i for i in range(3));actual.setdefault((e[0],n),[]).append((mask,e))
 assert set(actual)==set(expected),(set(actual),set(expected))
 for key,(mask,data) in expected.items():
  assert all(m==mask for m,_ in actual[key]),(key,mask,actual[key])
  if a.platform=='z80pack':
   f=report/'extracted.dat';cpm('cpmcp',f'{key[0]}:{key[1]}',f);assert f.read_bytes()[:len(data)]==data,key
 if a.platform=='model4':
  from test_model4_copy import files
  contents=files(filesystem)
  for (user,name),(_,data) in expected.items():
   stem,_,ext=name.partition('.')
   key=stem.ljust(8).encode()+ext.ljust(3).encode()
   assert contents[(user,key)][0][:len(data)]==data,(user,name)
 (report/'evidence.json').write_text(json.dumps({'result':'PASS','platform':a.platform,'cases':observations},indent=2))
 print(f'Resident REN: {len(cases)} selection/mapping/preflight cases PASS on {a.platform}')
if __name__=='__main__':main()
