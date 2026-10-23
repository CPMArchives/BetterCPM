#!/usr/bin/env python3
"""Qualify freshly integrated Part 11 media without patching its system tracks."""
from pathlib import Path
import argparse,binascii,json,shutil,subprocess,sys
p=argparse.ArgumentParser(description=__doc__);p.add_argument('baseline',type=Path);p.add_argument('experiment',type=Path);p.add_argument('--smoke-only',action='store_true');a=p.parse_args()
root=a.baseline.resolve();out=a.experiment.resolve();out.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(root/'tools'))
import part7_probe_support as h
from assessment_checked_profiles import bound
h.out=out/'qualification';h.out.mkdir(exist_ok=True);h.results={}
meta=json.loads((root/'build/z80pack/checked-load.json').read_text());L=h.L
def putraw(b,record,data):
 for i,value in enumerate(data):
  rec=record+i//128;track,within=divmod(rec,h.fmt.spt);at=track*h.fmt.raw_track_bytes+h.fmt.raw_record_map()[within]*128+i%128;b[at]=value
def case(name,mode='streamed'):
 w=h.case(name)
 # HELLO is injected only into test copies, never the distribution manifest.
 h.put(w,'HELLO.CPX',(root/'build/cpx/HELLO.CPX').read_bytes())
 return w
def record(name,**kwargs):h.results[name]=kwargs;h.save();print('PASS '+name,flush=True)
w=case('streamed-smoke')
t=h.run(w,['STAT MEM','CPX LOAD HELLO','HELLO','CPX UNLOAD HELLO','STAT MEM'])
expected_tpa=(L['TPA']-256)//128*128
assert 'Hello from HELLO.CPX' in t and 'CPX?' not in t and all(m['maximum']==expected_tpa for m in h.maps(t))
record('streamed-smoke',unloaded_tpa=expected_tpa,hello_executed=True)
# Preserve the tested base image separately from per-campaign mutations.
shutil.copyfile(w/'disks/drivea.dsk',out/'system.raw');shutil.copyfile(root/'assessment-media/diskdefs',out/'diskdefs')
if a.smoke_only:raise SystemExit(0)
# Reuse the established patterned maximum-COM/return campaign on patched copies.
boundary_source=(root/'tools/qualify_part7_live.py').read_text().split("w=case('stateful')",1)[0]
boundary_source=boundary_source.split('from part7_probe_support import *\n',1)[1]
boundary_source=boundary_source.replace('57344',str(expected_tpa))
namespace=dict(vars(h));namespace['case']=case
exec(compile(boundary_source,'part7-boundary-on-part10','exec'),namespace)
for label,edit in [
 ('payload',lambda b:b.__setitem__(b.index(b'Hello from'),ord('J'))),
 ('public-id',lambda b:b.__setitem__(len(b)-18,1)),
 ('old-format',None),
 ('truncated-after-payload',lambda b:b.__delitem__(slice(640,None))),
 ('late-crc',lambda b:b.__setitem__(len(b)-1,b[-1]^1))]:
 w=case('streamed-'+label);bad=bytearray((root/'build/cpx/HELLO.CPX').read_bytes())
 if edit:edit(bad)
 else:bad=bytearray((root/'build/cpx/HELLO.CPX').read_bytes()[:-22]);bad[4]=1
 if label=='public-id':bad[-2:]=binascii.crc_hqx(bad[:-2],0xffff).to_bytes(2,'little')
 h.put(w,'BAD.CPX',bad,'b');h.put(w,'GOOD.CPX',(root/'build/cpx/HELLO.CPX').read_bytes(),'b')
 for n,path in [('STATEFUL.RSX','build/rsx/STATEFUL.RSX'),('STATTST.COM','build/utilities/STATTST.COM')]:h.put(w,n,(root/path).read_bytes())
 t=h.run(w,['RSX LOAD STATEFUL','STATTST INIT','STATTST MUTATE','PIP HELLO.CPX=B:BAD.CPX','CPX LOAD HELLO','STATTST CHECK','CPX UNLOAD HELLO','PIP HELLO.CPX=B:GOOD.CPX','CPX LOAD HELLO','HELLO','STATTST CHECK','CPX UNLOAD HELLO','RSX UNLOAD STATEFUL','STAT MEM'])
 assert 'CPX?' in t and 'Jello from' not in t and 'Hello from HELLO.CPX' in t and t.count('STATEFUL CHECK PASS')==2 and 'FAILED' not in t
 assert h.maps(t)[-1]['maximum']==expected_tpa
 record('streamed-'+label,rejected=True,rsx_state_checks=2,recovery=True,tpa=expected_tpa)
w=case('streamed-monitor')
t=h.run(w,['RSX LOAD ANSISCRN','STAT MEM',(b'RSX LOAD ADM3A\r',b'\x1b[7m \x1b[0m ',25),(b'STAT MEM\r',b'\x1b[7m \x1b[0m ',25),(b'RSX UNLOAD ADM3A\r',b'A0>_ ',25),'RSX UNLOAD ANSISCRN','STAT MEM'])
assert [m['maximum'] for m in h.maps(t)]==[expected_tpa-2560,expected_tpa-3072,expected_tpa]
record('streamed-monitor',tpa_screen_pair=expected_tpa-3072,unloaded_tpa=expected_tpa)
for label,record_number,offset in [('stage2-code',84,0),('stage2-id',84+2024//128,2024%128),('ccp',108+1024//128,0)]:
 w=case('bad-'+label);path=w/'disks/drivea.dsk';b=bytearray(path.read_bytes());track,within=divmod(record_number,h.fmt.spt);b[track*h.fmt.raw_track_bytes+h.fmt.raw_record_map()[within]*128+offset]^=1;path.write_bytes(b)
 raw=h.session(h.sim,w/'disks',[],w/'halt.bin',initial_prompt=b'!');assert b'A0>' not in raw
 record('bad-'+label,halt_before_prompt=True)
