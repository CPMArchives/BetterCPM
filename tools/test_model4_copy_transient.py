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
 p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);p.add_argument('--resume',action='store_true');p.add_argument('--case',action='append',help='Run only named cases');p.add_argument('--small-fixtures',action='store_true',help='Use two records for S007; the separate large-file case remains required');a=p.parse_args()
 report=a.report.resolve();report.mkdir(parents=True,exist_ok=a.resume)
 binary=(ROOT/'build/utilities/COPY.COM').read_bytes();observations=[]
 (report/'harness.py').write_bytes(Path(__file__).read_bytes())
 source=[(f'S{i:03}.DAT',bytes([i])* (0 if i==0 else (256 if a.small_fixtures else 33280) if i==7 else 128),1,i) for i in range(8)]
 source += [('ONLY1.COM',b'1'*128,1),('ONLY3.COM',b'3'*128,3),('ONLY5.COM',b'5'*128,5),('DUP.COM',b'A'*128,1),('DUP.COM',b'B'*128,3)]
 def case(label,command,initial=(),response=(),image=None,source_files=None,source_arc_clear=(),script_lines=None,expected_prompt='A0'):
  selected_sources=source if source_files is None else source_files
  work=report/label
  if a.case and label not in a.case:return None
  if a.resume and (work/'passed.json').exists():
   info=json.loads((work/'passed.json').read_text());assert info['copy_sha256']==digest(binary)
   assert info.get('small_fixtures',False)==a.small_fixtures,'fixture size differs from saved case'
   observations.append(info);return None
  work.mkdir(exist_ok=a.resume)
  captures=list(work.glob('trs80-text-*'))
  if captures:
   prior=work/('previous-captures-'+str(time.time_ns()));prior.mkdir()
   for capture in list(work.iterdir()):
    if capture.is_file():shutil.move(str(capture),str(prior/capture.name))
  # SUBMIT's $$ escape passes literal attribute tokens. Brackets and ! cannot
  # currently be entered through the Model 4's ordinary keyboard translation.
  marker='FINISH '+label.upper().replace('-',' ')
  finish_command='A0:FINISH' if expected_prompt!='A0' else 'FINISH'
  script=('\r\n'.join(script_lines or ['COPY '+command])+ '\r\n'+finish_command+'\r\n').replace('$','$$').encode()+b'\x1a'
  # The marker appears only as output, never in SUBMIT's command echo.
  finish=b'\x11\x0b\x01\x0e\x09\xcd\x05\x00\xc3\x00\x00'+('\r\n'+marker+'\r\n$').encode()
  extras=[('COPY.COM',image or binary),('SUBMIT.COM',(ROOT/'build/utilities/SUBMIT.COM').read_bytes()),('CPX.COM',(ROOT/'build/utilities/CPX.COM').read_bytes()),('CASE.SUB',script),('FINISH.COM',finish),*selected_sources]
  adata=medium(extras);braw=bytearray(install_files([(0,'KEEP.DAT',b'KEEP'.ljust(128,b'!')), *[(u,n,d) for u,n,d,_ in initial]]))
  for u,n,d,mask in initial:
   for i in range(0,4096,32):
    if braw[i]==u and bytes(c&127 for c in braw[i+1:i+12])==key(n):
     for bit in range(3):braw[i+9+bit]|=128 if mask&(1<<bit) else 0
  bdata=build(braw)
  (work/'tested-copy.com').write_bytes(image or binary)
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
  assert texts and marker in texts[-1] and re.search(re.escape(expected_prompt)+r'>\s*$',texts[-1].rstrip()),texts
  araw=extract_raw((work/'a.dmk').read_bytes());after=files(extract_raw((work/'b.dmk').read_bytes()))
  assert araw[:OFF]==extract_raw(adata)[:OFF],label
  assert after[(0,key('KEEP.DAT'))][0]==b'KEEP'.ljust(128,b'!')
  original=files(extract_raw(adata)[OFF:]);current=files(araw[OFF:])
  for filekey,(data,entries) in original.items():
   if filekey[0]:
    assert current[filekey][0]==data,(label,filekey,'source content')
    cleared=label=='backup' and filekey[1].startswith(b'S00') or filekey[1] in {key(n) for n in source_arc_clear}
    expected=[state&3 if cleared else state for state in attrs(entries)]
    assert attrs(current[filekey][1])==expected,(label,filekey,'source attributes')
  return work,'\n'.join(texts),files(araw[OFF:]),after,bdata
 def passed(label,result,extra):
  if result is None:return
  work,text,src,dst,before=result
  info={'label':label,'command':json.loads((work/'invocation.json').read_text()),'copy_sha256':digest(binary),'tested_copy_sha256':digest((work/'tested-copy.com').read_bytes()),'small_fixtures':a.small_fixtures,'result':'PASS',**extra}
  (work/'passed.json').write_text(json.dumps(info,indent=2)+'\n');observations.append(info);print(label,'PASS',flush=True)
 def copied(result,user,selected,mask=lambda x:x,rename=lambda x:x):
  if result is None:return
  work,text,src,dst,before=result
  assert 'COPY source destination' not in text and 'INCOMPLETE' not in text,text
  for n,data,u,state in selected:
   actual,entries=dst[(user,key(rename(n)))];assert actual==data,(n,len(actual),len(data))
   assert all(x==mask(state) for x in attrs(entries)),(n,attrs(entries),mask(state))
 r=case('attributes','/B /V A1:S*.DAT B3:[$RW,!$ARC]');copied(r,3,source[:8],lambda x:x&2)
 if r:assert f'8 FILES COPIED [{14 if a.small_fixtures else 46}K]' in r[1] and f'[{2 if a.small_fixtures else 34}K]' in r[1],r[1]
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
 if r:assert 'FILE EXISTS' in r[1] and 'READ ONLY' in r[1] and f'6 FILES COPIED [{10 if a.small_fixtures else 42}K]' in r[1] and '2 FILES FAILED' in r[1],r[1]
 passed('batch-collision',r,{'batch_no_prompt':True,'readonly_never_overwritten':True})
 r=case('skip','/S /B A1:S*.DAT B8:',old)
 if r:assert '1 FILE SKIPPED' in r[1] and '1 FILE FAILED' in r[1] and f'6 FILES COPIED [{10 if a.small_fixtures else 42}K]' in r[1],r[1]
 passed('skip',r,{'skip_count_and_readonly_failure':True})
 r=case('no-match','/B A1:*.ZZZ B0:')
 if r:assert 'NO FILE' in r[1] and 'FILES COPIED' not in r[1] and (r[0]/'b.dmk').read_bytes()==r[4]
 passed('no-match',r,{'no_summary_or_writes':True})
 # Completion and recovery cases use small independent fixtures. The original
 # attributes case separately covers the unmodified binary over three extents.
 abc=[(n+'.DAT',n.encode()*256,1,4) for n in 'ABC']
 oldabc=[(8,n+'.DAT',b'OLD-'+n.encode()+bytes(251),0) for n in 'ABC']
 prompt=' [Destination exists. Overwrite? Y/N/O/S/R/?] '
 def pair(n,user=8):return f'A1:{n}.DAT -> B{user}:{n}.DAT'+prompt
 def exists(result,user,name,data=None,state=None):
  if result is None:return
  item=result[3].get((user,key(name)))
  if data is None:assert item is None,(user,name,item);return
  assert item and item[0]==data,(user,name,'contents')
  if state is not None:assert all(v==state for v in attrs(item[1])),(user,name,'attributes')
 def olddata(n):return b'OLD-'+n.encode()+bytes(251)
 r=case('interactive-choices','A1:*.DAT B8:',oldabc,
        [(pair('A'),'y'),(pair('B'),'N'),(pair('C'),'?'),
         ('Y - Yes  N - No','X'),(pair('C'),'Y')],source_files=abc)
 if r:
  exists(r,8,'A.DAT',b'A'*256,4);exists(r,8,'B.DAT',olddata('B'),0);exists(r,8,'C.DAT',b'C'*256,4)
  assert '2 FILES COPIED [4K]' in r[1] and '1 FILE SKIPPED' in r[1] and 'Y - Yes  N - No' in r[1]
 passed('interactive-choices',r,{'Y_N_help_invalid_response':True,'submit_remains_interactive':True})
 for label,choice in [('interactive-overwrite','O'),('interactive-skip','S')]:
  initial=oldabc+[(9,n+'.DAT',olddata(n),0) for n in 'ABC']
  r=case(label,'',initial,[(pair('A'),choice),(pair('A',9),'N'),(pair('B',9),'S')],
         source_files=abc,script_lines=['COPY A1:*.DAT B8:','COPY A1:*.DAT B9:'])
  if r:
   for n in 'ABC':
    exists(r,8,n+'.DAT',n.encode()*256 if choice=='O' else olddata(n),4 if choice=='O' else 0)
    exists(r,9,n+'.DAT',olddata(n),0)
   prompts={line.split(prompt.rstrip())[0] for line in r[1].splitlines() if prompt.rstrip() in line}
   assert len(prompts)==3,r[1]
  passed(label,r,{'session_choice':choice,'policy_resets_between_invocations':True})
 r=case('collision-abort','A1:*.DAT B8:',oldabc,[(pair('A'),'Y'),(pair('B'),'\x03')],source_files=abc)
 if r:
  exists(r,8,'A.DAT',b'A'*256,4)
  for n in 'BC':exists(r,8,n+'.DAT',olddata(n),0)
  assert 'COPY ABORTED' in r[1]
 passed('collision-abort',r,{'completed_file_retained':True,'later_destinations_preserved':True})
 protected=[(8,n+'.DAT',olddata(n),1 if n=='B' else 0) for n in 'ABC']
 r=case('overwrite-readonly','/O /B A1:*.DAT B8:[$RW]',protected,source_files=abc)
 if r:
  for n in 'AC':exists(r,8,n+'.DAT',n.encode()*256,4)
  exists(r,8,'B.DAT',olddata('B'),1)
  assert 'READ ONLY' in r[1] and '2 FILES COPIED [4K]' in r[1] and '1 FILE FAILED' in r[1]
 passed('overwrite-readonly',r,{'overwrite_and_destination_RW_never_override_readonly':True})
 r=case('backup-skip','/S /B /BACKUP A1:*.DAT B8:',oldabc[:1],source_files=abc,source_arc_clear=('B.DAT','C.DAT'))
 if r:
  exists(r,8,'A.DAT',olddata('A'),0)
  for n in 'BC':exists(r,8,n+'.DAT',n.encode()*256,0)
  assert '2 FILES COPIED [4K]' in r[1] and '1 FILE SKIPPED' in r[1]
 passed('backup-skip',r,{'skipped_source_arc_preserved':True})
 r=case('rename-validation','A1:*.DAT B8:',oldabc,
        [(pair('A'),'R'),('New Name: ','BAD*NAME.DAT\r'),
         ('Invalid filename.','B.DAT\r'),('COPY DESTINATION CONFLICT','NEW.DAT\r'),
         (pair('B'),'R'),('New Name: ','\r'),(pair('B'),'S')],source_files=abc)
 if r:
  exists(r,8,'NEW.DAT',b'A'*256,4)
  for n in 'ABC':exists(r,8,n+'.DAT',olddata(n),0)
  assert 'Invalid filename.' in r[1] and 'COPY DESTINATION CONFLICT' in r[1]
 passed('rename-validation',r,{'invalid_reprompt':True,'batch_conflict_rejected':True,'blank_returns_to_collision':True})
 r=case('rename-existing','A1:A.DAT B8:',oldabc+[(8,'NEW.DAT',b'EXIST'.ljust(256,b'!'),0)],
        [(pair('A'),'R'),('New Name: ','NEW.DAT\r'),
         ('A1:A.DAT -> B8:NEW.DAT'+prompt,'N')],source_files=abc)
 if r:
  exists(r,8,'A.DAT',olddata('A'),0);exists(r,8,'NEW.DAT',b'EXIST'.ljust(256,b'!'),0)
 passed('rename-existing',r,{'renamed_collision_reuses_prompt':True})
 r=case('rename-abort','A1:A.DAT B8:',oldabc,[(pair('A'),'R'),('New Name: ','\x03')],source_files=abc)
 if r:assert 'COPY ABORTED' in r[1] and (r[0]/'b.dmk').read_bytes()==r[4]
 passed('rename-abort',r,{'ctrl_c_aborts_entire_invocation':True})
 # Private fault probes alter only a call/return or polling gate. Actual media
 # operations and all production continuation/cleanup paths remain native.
 listing=(ROOT/'build/utilities/copy-transient.lst').read_text()
 def address(name):return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
 def fault(start,function,nth,status,cleanup=False):
  image=bytearray(binary);off=image.index(bytes([14,function,205,5,0]),address(start)-256)+2
  entry=256+len(image);counter=entry+19
  shim=b'\xcd\x05\x00\xf5\x21'+counter.to_bytes(2,'little')+bytes([0x34,0x7e,0xfe,nth,0x20,4,0xf1,0x3e,status,0xc9,0xf1,0xc9,0])
  assert len(shim)==20
  image[off:off+3]=b'\xcd'+entry.to_bytes(2,'little');image+=shim
  if cleanup:
   off=image.index(b'\x0e\x13\xcd\x05\x00',address('CVVDEL')-256)+2;image[off:off+3]=b'\x3e\xff\x00'
  return bytes(image)
 for label,start,function,nth,status,stop,cleanup in [
     ('fault-read','BC_CLOOP',20,5,4,False,False),
     ('fault-write','BC_CWRITE',21,4,255,False,False),
     ('fault-close','BC_CCLOSE',16,2,255,False,False),
     ('fault-full','BC_CWRITE',21,4,2,True,False),
     ('fault-cleanup','BC_CWRITE',21,4,255,True,True)]:
  r=case(label,'/B /BACKUP A1:*.DAT B8:',image=fault(start,function,nth,status,cleanup),
         source_files=abc,source_arc_clear=('A.DAT',) if stop else ('A.DAT','C.DAT'))
  if r:
   assert ('NO SPACE' if label=='fault-full' else 'READ ERROR' if label=='fault-read' else 'WRITE ERROR') in r[1],r[1]
   assert ('1 FILE COPIED [2K]' if stop else '2 FILES COPIED [4K]') in r[1] and '1 FILE FAILED' in r[1],r[1]
   exists(r,8,'A.DAT',b'A'*256,0)
   exists(r,8,'C.DAT',None if stop else b'C'*256,0)
   if cleanup:assert 'INCOMPLETE DESTINATION CLEANUP FAILED' in r[1] and (8,key('B.DAT')) in r[3]
   else:exists(r,8,'B.DAT')
  passed(label,r,{'controlled_fault':True,'stops':stop,'failed_cleanup':cleanup})
 def verify_image(once=False):
  image=bytearray(binary)
  if not once:image[address('CTVERIFY')-256:address('CTVERIFY')-254]=b'\x37\xc9';return bytes(image)
  call=image.index(b'\xcd'+address('CTVERIFY').to_bytes(2,'little'),address('CTVPOST')-256)
  entry=256+len(image);flag=entry+16
  shim=b'\xcd'+address('CTVERIFY').to_bytes(2,'little')+b'\xd8\x21'+flag.to_bytes(2,'little')+b'\x7e\xb7\xc8\x36\x00\x37\xc9\x00\x00\x01'
  assert len(shim)==17
  image[call+1:call+3]=entry.to_bytes(2,'little');return bytes(image+shim)
 r=case('verify-batch-failure','/B /V /BACKUP A1:*.DAT B8:',image=verify_image(),source_files=abc)
 if r:
  for n in 'ABC':exists(r,8,n+'.DAT')
  errors={line for line in r[1].splitlines() if ' [VERIFY ERROR]' in line}
  assert len(errors)==3 and '3 FILES FAILED' in r[1],r[1]
 passed('verify-batch-failure',r,{'verification_failure_continues':True,'source_arc_preserved':True})
 for label,reply in [('verify-skip','S'),('verify-abort','\x03')]:
  r=case(label,'/V /BACKUP A1:A.DAT B8:',response=[(' [VERIFY ERROR] R/S/? ','?'),
         ('R - Retry  S - Skip',reply)],image=verify_image(),source_files=abc)
  if r:
   exists(r,8,'A.DAT');assert 'R - Retry  S - Skip' in r[1]
   if reply=='\x03':assert 'COPY ABORTED' in r[1]
  passed(label,r,{'verification_help_and_cleanup':True})
 r=case('verify-retry','/V /BACKUP A1:A.DAT B8:',response=[(' [VERIFY ERROR] R/S/? ','R')],
        image=verify_image(True),source_files=abc,source_arc_clear=('A.DAT',))
 if r:exists(r,8,'A.DAT',b'A'*256,0)
 passed('verify-retry',r,{'verification_retry_uses_real_comparison':True,'backup_after_retry':True})
 for label,start in [('fault-destination-metadata','CTVATTR'),('fault-source-metadata','CTBPOST')]:
  image=bytearray(binary);off=image.index(b'\x0e\x1e\xcd\x05\x00',address(start)-256)+2;image[off:off+3]=b'\x3e\xff\x00'
  r=case(label,'/B /V /BACKUP A1:A.DAT B8:',image=bytes(image),source_files=abc)
  if r:
   exists(r,8,'A.DAT',b'A'*256)
   assert 'DATA COPIED; ATTRIBUTE STATUS INCOMPLETE' in r[1]
  passed(label,r,{'valid_data_retained':True,'source_arc_preserved':True})
 def cancel_image(phase):
  image=bytearray(binary);entry=256+len(image);flag=entry+29;message=entry+30
  word=lambda n:n.to_bytes(2,'little')
  code=b'\x21'+word(flag)+b'\x7e\xb7\xc8\x35\xca'+word(entry+13)+b'\xb7\xc9\x00'
  assert len(code)==13
  code+=b'\x11'+word(message)+b'\x0e\x09\xcd\x05\x00'
  code+=b'\xcd'+word(address('CTCHECK'))+b'\x30\xfb\xc9\x00\x00\x04READY$'
  assert code[29]==4
  call=address(phase)-256;assert image[call:call+3]==b'\xcd'+word(address('CTCHECK'))
  image[call+1:call+3]=word(entry);return bytes(image+code)
 for label,phase in [('cancel-transfer','BC_CLOOP'),('cancel-verification','CTVLOOP')]:
  command='/B /BACKUP '+('/V ' if phase=='CTVLOOP' else '')+'A1:*.DAT B8:'
  r=case(label,command,response=[('READY','\x03')],image=cancel_image(phase),source_files=abc,source_arc_clear=('A.DAT',),
         script_lines=['COPY '+command,'COPY /B A1:B.DAT B9:'])
  if r:
   exists(r,8,'A.DAT',b'A'*256,0)
   for n in 'BC':exists(r,8,n+'.DAT')
   assert 'COPY ABORTED' in r[1] and 'VERIFY ERROR' not in r[1]
   exists(r,9,'B.DAT',b'B'*256,4)
  passed(label,r,{'actual_ctrl_c':True,'completed_file_retained':True,'incomplete_destination_removed':True,'subsequent_copy_succeeds':True})
 r=case('caller-user31','',source_files=abc,script_lines=['A31:','A0:COPY /B A1:A.DAT B31:'],expected_prompt='A31')
 if r:exists(r,31,'A.DAT',b'A'*256,4)
 passed('caller-user31',r,{'caller_user31_restored':True,'destination_user31':True})
 for count in (64,65):
  label=f'capacity-{count}';fixtures=[(f'F{i:03}.DAT',b'',1,0) for i in range(count)]
  r=case(label,'/B A1:F*.DAT B8:',source_files=fixtures)
  if r:
   if count==65:assert 'COPY BATCH TOO LARGE' in r[1] and (r[0]/'b.dmk').read_bytes()==r[4]
   else:
    for n,data,_,mask in fixtures:exists(r,8,n,data,mask)
    assert '64 FILES COPIED [0K]' in r[1]
  passed(label,r,{'global_capacity':count,'overflow_before_writes':count==65})
 for label,initial in [('directory-full',[(0,f'D{i:03}.DAT',b'',0) for i in range(127)]),
                       ('allocation-full',[(0,'FULL.DAT',b'F'*(397*2048),0)])]:
  r=case(label,'/B A1:*.DAT B8:',initial,source_files=abc)
  if r:
   assert 'NO SPACE' in r[1] and '1 FILE FAILED' in r[1]
   for n in 'ABC':exists(r,8,n+'.DAT')
   before=files(extract_raw(r[4]))
   for filekey,(data,entries) in before.items():assert r[3][filekey]==(data,entries)
  passed(label,r,{'real_media_exhaustion':True,'ordinary_metadata_preserved':True})
 if a.case:assert {item['label'] for item in observations}==set(a.case),'unknown or incomplete requested case'
 (report/'evidence.json').write_text(json.dumps({'result':'PASS','observations':observations,'requested_cases':a.case,'small_fixtures':a.small_fixtures,'copy_sha256':digest(binary),'emulator_sha256':digest(DEFAULT_EMULATOR.read_bytes()),'input_method':'Native SUBMIT command files; literal dollar signs escaped as $$','keyboard_limitation':'Model 4 keyboard translation does not supply bracket/exclamation bytes; no core changes made'},indent=2)+'\n')
 print(f'Completed {len(observations)} selected transient COPY Model 4 cases: PASS')
if __name__=='__main__':main()
