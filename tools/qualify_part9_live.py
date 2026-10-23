#!/usr/bin/env python3
"""Live cpmsim proof images; preserve the pinned Part 8 build unchanged."""
from pathlib import Path
import argparse,binascii,json,shutil,subprocess,sys
p=argparse.ArgumentParser(description=__doc__);p.add_argument('baseline',type=Path);p.add_argument('experiment',type=Path);p.add_argument('--compact',type=Path);p.add_argument('--smoke-only',action='store_true');a=p.parse_args()
root=a.baseline.resolve();out=a.experiment.resolve();sys.path.insert(0,str(root/'tools'))
import part7_probe_support as h
from assessment_checked_profiles import bound
h.out=out/'qualification';h.out.mkdir(exist_ok=True);h.results={}
meta=json.loads((root/'build/z80pack/checked-load.json').read_text());L=h.L
def putraw(b,record,data):
 for i,value in enumerate(data):
  rec=record+i//128;track,within=divmod(rec,h.fmt.spt);at=track*h.fmt.raw_track_bytes+h.fmt.raw_record_map()[within]*128+i%128;b[at]=value
def patch(path,mode):
 b=bytearray(path.read_bytes())
 if mode=='staged':
  first=(out/'stage1.carrier').read_bytes();putraw(b,84,(out/'stage2.carrier').read_bytes());putraw(b,108,(out/'ccp.rlm').read_bytes().ljust(13*512,b'\0'))
 else:
  first=bound((a.compact/'compact.bin').read_bytes().ljust(L['RELOADER_CAPACITY'],b'\0')+(root/'build/z80pack/rsxselect.bin').read_bytes().ljust(1024-L['RELOADER_CAPACITY'],b'\0'),root)
 putraw(b,60,first)
 # Only the expected first-stage CRC operand changes in the protected resident.
 offset=meta['symbols']['Z_EREL']+1-L['SYSTEM'];rec=8+offset//128
 checksum=binascii.crc_hqx(first,0xffff).to_bytes(2,'little')
 for i,value in enumerate(checksum):
  off=offset+i;track,within=divmod(8+off//128,h.fmt.spt);b[track*h.fmt.raw_track_bytes+h.fmt.raw_record_map()[within]*128+off%128]=value
 path.write_bytes(b)
def case(name,mode='staged'):
 w=h.case(name)
 for c in 'abcd':patch(w/'disks'/f'drive{c}.dsk',mode)
 if mode=='staged':
  for n in ('RCP.CPX','HELLO.CPX'):
   subprocess.run(['cpmrm','-f','bettercpm-default',str(w/'disks/drivea.dsk'),'0:'+n],cwd=w,check=True,capture_output=True)
   h.put(w,n,(out/n).read_bytes())
 return w
def record(name,**kwargs):h.results[name]=kwargs;h.save();print('PASS '+name,flush=True)
w=case('staged-smoke')
t=h.run(w,['STAT MEM','CPX LOAD HELLO','HELLO','CPX UNLOAD HELLO','STAT MEM'])
expected_tpa=(L['TPA']-256)//128*128
assert 'Hello from HELLO.CPX' in t and 'CPX?' not in t and all(m['maximum']==expected_tpa for m in h.maps(t))
record('staged-smoke',unloaded_tpa=expected_tpa,hello_executed=True)
# Preserve the tested base image separately from per-campaign mutations.
shutil.copyfile(w/'disks/drivea.dsk',out/'system.raw');shutil.copyfile(root/'assessment-media/diskdefs',out/'diskdefs')
if a.smoke_only:raise SystemExit(0)
# Reuse the established patterned maximum-COM/return campaign on patched copies.
boundary_source=(root/'tools/qualify_part7_live.py').read_text().split("w=case('stateful')",1)[0]
boundary_source=boundary_source.split('from part7_probe_support import *\n',1)[1]
namespace=dict(vars(h));namespace['case']=case
exec(compile(boundary_source,'part7-boundary-on-part9','exec'),namespace)
if a.compact:
 w=case('compact-checksum','compact');bad=bytearray((root/'build/cpx/HELLO.CPX').read_bytes());bad[bad.index(b'Hello from')]=ord('J');h.put(w,'BAD.CPX',bad,'b');h.put(w,'GOOD.CPX',(root/'build/cpx/HELLO.CPX').read_bytes(),'b')
 t=h.run(w,['PIP HELLO.CPX=B:BAD.CPX','CPX LOAD HELLO','HELLO','CPX UNLOAD HELLO','PIP HELLO.CPX=B:GOOD.CPX','CPX LOAD HELLO','HELLO','CPX UNLOAD HELLO','STAT MEM'])
 assert 'CPX?' in t and 'Jello from' not in t and 'Hello from HELLO.CPX' in t and h.maps(t)[-1]['maximum']==57344
 record('compact-checksum',stale_checksum_rejected=True,recovery=True,tpa=57344)
for label,edit in [
 ('payload',lambda b:b.__setitem__(b.index(b'Hello from'),ord('J'))),
 ('public-id',lambda b:b.__setitem__(len(b)-18,1)),
 ('old-format',None),
 ('truncated',lambda b:b.__delitem__(slice(512,None)))]:
 w=case('staged-'+label);bad=bytearray((out/'HELLO.CPX').read_bytes())
 if edit:edit(bad)
 else:bad=bytearray((root/'build/cpx/HELLO.CPX').read_bytes())
 if label=='public-id':bad[-2:]=binascii.crc_hqx(bad[:-2],0xffff).to_bytes(2,'little')
 h.put(w,'BAD.CPX',bad,'b');h.put(w,'GOOD.CPX',(out/'HELLO.CPX').read_bytes(),'b')
 for n,path in [('STATEFUL.RSX','build/rsx/STATEFUL.RSX'),('STATTST.COM','build/utilities/STATTST.COM')]:h.put(w,n,(root/path).read_bytes())
 t=h.run(w,['RSX LOAD STATEFUL','STATTST INIT','STATTST MUTATE','PIP HELLO.CPX=B:BAD.CPX','CPX LOAD HELLO','STATTST CHECK','CPX UNLOAD HELLO','PIP HELLO.CPX=B:GOOD.CPX','CPX LOAD HELLO','HELLO','STATTST CHECK','CPX UNLOAD HELLO','RSX UNLOAD STATEFUL','STAT MEM'])
 assert 'CPX?' in t and 'Jello from' not in t and 'Hello from HELLO.CPX' in t and t.count('STATEFUL CHECK PASS')==2 and 'FAILED' not in t
 assert h.maps(t)[-1]['maximum']==57344
 record('staged-'+label,rejected=True,rsx_state_checks=2,recovery=True,tpa=57344)
w=case('staged-monitor')
t=h.run(w,['RSX LOAD ANSISCRN','STAT MEM',(b'RSX LOAD ADM3A\r',b'\x1b[7m \x1b[0m ',25),(b'STAT MEM\r',b'\x1b[7m \x1b[0m ',25),(b'RSX UNLOAD ADM3A\r',b'A0>_ ',25),'RSX UNLOAD ANSISCRN','STAT MEM'])
assert [m['maximum'] for m in h.maps(t)]==[54784,54272,57344]
record('staged-monitor',tpa_screen_pair=54272,unloaded_tpa=57344)
for label,record_number,offset in [('stage2-code',84,0),('stage2-id',84+2024//128,2024%128),('ccp',108+1024//128,0)]:
 w=case('bad-'+label);path=w/'disks/drivea.dsk';b=bytearray(path.read_bytes());track,within=divmod(record_number,h.fmt.spt);b[track*h.fmt.raw_track_bytes+h.fmt.raw_record_map()[within]*128+offset]^=1;path.write_bytes(b)
 raw=h.session(h.sim,w/'disks',[],w/'halt.bin',initial_prompt=b'!');assert b'A0>' not in raw
 record('bad-'+label,halt_before_prompt=True)
