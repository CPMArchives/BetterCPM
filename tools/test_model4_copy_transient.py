#!/usr/bin/env python3
"""Qualify completed transient COPY on Model 4, using native SUBMIT syntax input."""
import argparse,hashlib,json,re,shutil,time
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw
from build_source_disk import install_files
from build_montezuma_extended_790k import build
from build_trs80_boot import FILESYSTEM_FIRST_SECTOR
from run_trs80_command import DEFAULT_EMULATOR
from test_disk_utilities import ROOT,medium,keys
from test_sysgen_install import screen
from test_model4_copy import files
from trs80gp_launch import run

OFF=FILESYSTEM_FIRST_SECTOR*512

def digest(data):return hashlib.sha256(data).hexdigest()
def key(name):return name.partition('.')[0].ljust(8).encode()+name.partition('.')[2].ljust(3).encode()
def attrs(entries):return [sum((e[9+i]>>7)<<i for i in range(3)) for e in entries]
def main():
 p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);p.add_argument('--resume',action='store_true');p.add_argument('--case',action='append',help='Run only named cases');a=p.parse_args()
 report=a.report.resolve();report.mkdir(parents=True,exist_ok=a.resume)
 binary=(ROOT/'build/utilities/COPY.COM').read_bytes();observations=[]
 source=[(f'S{i:03}.DAT',bytes([i])* (0 if i==0 else 33280 if i==7 else 128),1,i) for i in range(8)]
 source += [('ONLY1.COM',b'1'*128,1),('ONLY3.COM',b'3'*128,3),('ONLY5.COM',b'5'*128,5),('DUP.COM',b'A'*128,1),('DUP.COM',b'B'*128,3)]
 def case(label,command,initial=(),response=(),image=None):
  work=report/label
  if a.case and label not in a.case:return None
  if a.resume and (work/'passed.json').exists():
   info=json.loads((work/'passed.json').read_text());assert info['copy_sha256']==digest(binary)
   observations.append(info);return None
  work.mkdir(exist_ok=a.resume)
  captures=list(work.glob('trs80-text-*'))
  if captures:
   prior=work/('previous-captures-'+str(time.time_ns()));prior.mkdir()
   for capture in captures:shutil.move(str(capture),str(prior/capture.name))
  # SUBMIT's $$ escape passes literal attribute tokens. Brackets and ! cannot
  # currently be entered through the Model 4's ordinary keyboard translation.
  marker='FINISH '+label.upper().replace('-',' ')
  script=('COPY '+command+'\r\nFINISH\r\n').replace('$','$$').encode()+b'\x1a'
  # The marker appears only as output, never in SUBMIT's command echo.
  finish=b'\x11\x0b\x01\x0e\x09\xcd\x05\x00\xc3\x00\x00'+('\r\n'+marker+'\r\n$').encode()
  extras=[('COPY.COM',image or binary),('SUBMIT.COM',(ROOT/'build/utilities/SUBMIT.COM').read_bytes()),('CPX.COM',(ROOT/'build/utilities/CPX.COM').read_bytes()),('CASE.SUB',script),('FINISH.COM',finish),*source]
  adata=medium(extras);braw=bytearray(install_files([(0,'KEEP.DAT',b'KEEP'.ljust(128,b'!')), *[(u,n,d) for u,n,d,_ in initial]]))
  for u,n,d,mask in initial:
   for i in range(0,4096,32):
    if braw[i]==u and bytes(c&127 for c in braw[i+1:i+12])==key(n):
     for bit in range(3):braw[i+9+bit]|=128 if mask&(1<<bit) else 0
  bdata=build(braw)
  (work/'before-a.dmk').write_bytes(adata);(work/'before-b.dmk').write_bytes(bdata)
  (work/'a.dmk').write_bytes(adata);(work/'b.dmk').write_bytes(bdata)
  cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(work/'a.dmk'),'-d1',str(work/'b.dmk'),'-id','3000','-it']
  cmd+=keys('CPX UNLOAD RCP\r')+['-id','3000','-it']
  cmd+=keys('SUBMIT CASE\r')+['-id','3000','-it','-itime','0','-iw',response[0][0] if response else marker,'-id','300','-it']
  for index,(wait,reply) in enumerate(response):
   nextwait=response[index+1][0] if index+1<len(response) else marker
   cmd+=keys(reply)+['-itime','0','-iw',nextwait,'-id','300','-it']
  cmd+=['-id','3000','-it','-ix']
  (work/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n')
  run(cmd,cwd=work,timeout=1800,check=True)
  texts=[]
  for f in sorted(work.glob('trs80-text-*.bin'),key=lambda f:int(f.stem.rsplit('-',1)[1])):
   t=screen(f);f.with_suffix('.txt').write_text(t);texts.append(t)
  assert texts and marker in texts[-1] and re.search(r'A0>\s*$',texts[-1].rstrip()),texts
  araw=extract_raw((work/'a.dmk').read_bytes());after=files(extract_raw((work/'b.dmk').read_bytes()))
  assert araw[:OFF]==extract_raw(adata)[:OFF],label
  assert after[(0,key('KEEP.DAT'))][0]==b'KEEP'.ljust(128,b'!')
  original=files(extract_raw(adata)[OFF:]);current=files(araw[OFF:])
  for filekey,(data,entries) in original.items():
   if filekey[0] and label!='backup':
    assert current[filekey][0]==data,(label,filekey,'source content')
    assert attrs(current[filekey][1])==attrs(entries),(label,filekey,'source attributes')
  return work,'\n'.join(texts),files(araw[OFF:]),after,bdata
 def passed(label,result,extra):
  if result is None:return
  work,text,src,dst,before=result
  info={'label':label,'command':json.loads((work/'invocation.json').read_text()),'copy_sha256':digest(binary),'result':'PASS',**extra}
  (work/'passed.json').write_text(json.dumps(info,indent=2)+'\n');observations.append(info);print(label,'PASS',flush=True)
 def copied(result,user,selected,mask=lambda x:x,rename=lambda x:x):
  if result is None:return
  work,text,src,dst,before=result
  assert 'COPY source destination' not in text and 'INCOMPLETE' not in text,text
  for n,data,u,state in selected:
   actual,entries=dst[(user,key(rename(n)))];assert actual==data,(n,len(actual),len(data))
   assert all(x==mask(state) for x in attrs(entries)),(n,attrs(entries),mask(state))
 r=case('attributes','/B /V A1:S*.DAT B3:[$RW,!$ARC]');copied(r,3,source[:8],lambda x:x&2)
 if r:assert '8 FILES COPIED [46K]' in r[1] and '[34K]' in r[1],r[1]
 passed('attributes',r,{'all_attributes':True,'multi_extent_allocation':True})
 r=case('predicates','/B /V A1:S*.DAT[$ARC+!$SYS] B4:');copied(r,4,[source[4],source[5]])
 if r:assert '2 FILES COPIED [4K]' in r[1] and len([k for k in r[3] if k[0]==4])==2,r[1]
 passed('predicates',r,{'predicate_precedence':True})
 r=case('backup','/B /V /BACKUP A1:S*.DAT B5:[$ARC]');copied(r,5,source[:8],lambda x:x&3)
 if r:
  for n,data,u,state in source[:8]:assert r[2][(u,key(n))][0]==data and all(x==state&3 for x in attrs(r[2][(u,key(n))][1]))
 passed('backup',r,{'source_destination_arc_cleared':True,'other_attributes_preserved':True})
 # Every remaining case gets its own source media, preserving ordinary attributes.
 r=case('du-sets','/B [A[1,3],5]:ONLY*.COM B6:')
 if r:
  for n,data,u in source[8:11]:assert r[3][(6,key(n))][0]==data
  assert '3 FILES COPIED [6K]' in r[1],r[1]
 passed('du-sets',r,{'nested_selector_and_inherited_drive':True})
 r=case('mapping','/B /V B7:X?*.BAK=A1:S***.DAT');copied(r,7,source[:8],rename=lambda n:'X'+n[1:4]+'.BAK')
 passed('mapping',r,{'positional_substitution_and_star_collapse':True})
 r=case('duplicate','/O /B [A1,A3]:DUP.COM B6:')
 if r:assert 'COPY DESTINATION CONFLICT' in r[1] and (r[0]/'b.dmk').read_bytes()==r[4]
 passed('duplicate',r,{'preflight_before_destination_mutation':True})
 r=case('overlap','/O /B A1:S*.DAT A1:')
 if r:assert 'COPY DESTINATION CONFLICT' in r[1]
 passed('overlap',r,{'selected_source_overlap_rejected':True})
 for label,command in [('bad-wild','/B A1:S*A.DAT B0:'),('bad-user','/B A[1,32]:S*.DAT B0:'),('bad-dest','/B A1:S*.DAT B[3,4]:'),('bad-attrs','/B A1:S*.DAT B0:[$RO,$RW]'),('bad-option','/BACKUPX /B A1:S*.DAT B0:')]:
  r=case(label,command)
  if r:assert 'COPY source destination' in r[1] and (r[0]/'b.dmk').read_bytes()==r[4],r[1]
  passed(label,r,{'invalid_before_writes':True})
 old=[(8,'S001.DAT',b'OLD'.ljust(128,b'!'),0),(8,'S002.DAT',b'RO'.ljust(128,b'!'),1)]
 r=case('batch-collision','/B A1:S*.DAT B8:',old)
 if r:assert 'FILE EXISTS' in r[1] and 'READ ONLY' in r[1] and '6 FILES COPIED [42K]' in r[1] and '2 FILES FAILED' in r[1],r[1]
 passed('batch-collision',r,{'batch_no_prompt':True,'readonly_never_overwritten':True})
 r=case('skip','/S /B A1:S*.DAT B8:',old)
 if r:assert '1 FILE SKIPPED' in r[1] and '1 FILE FAILED' in r[1] and '6 FILES COPIED [42K]' in r[1],r[1]
 passed('skip',r,{'skip_count_and_readonly_failure':True})
 r=case('no-match','/B A1:*.ZZZ B0:')
 if r:assert 'NO FILE' in r[1] and 'FILES COPIED' not in r[1] and (r[0]/'b.dmk').read_bytes()==r[4]
 passed('no-match',r,{'no_summary_or_writes':True})
 if a.case:assert {item['label'] for item in observations}==set(a.case),'unknown or incomplete requested case'
 (report/'evidence.json').write_text(json.dumps({'result':'PASS','observations':observations,'requested_cases':a.case,'copy_sha256':digest(binary),'emulator_sha256':digest(DEFAULT_EMULATOR.read_bytes()),'input_method':'Native SUBMIT command files; literal dollar signs escaped as $$','keyboard_limitation':'Model 4 keyboard translation does not supply bracket/exclamation bytes; no core changes made'},indent=2)+'\n')
 print(f'Completed {len(observations)} selected transient COPY Model 4 cases: PASS')
if __name__=='__main__':main()
