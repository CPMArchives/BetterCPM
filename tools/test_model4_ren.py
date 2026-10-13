#!/usr/bin/env python3
"""Qualify transient REN on disposable Model 4 physical DMK media."""
import argparse,hashlib,json,re
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw
from build_source_disk import install_files
from build_montezuma_extended_790k import build
from test_disk_utilities import ROOT,medium,keys
from test_model4_copy import files
from test_sysgen_install import screen
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run

def main():
 p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 report=a.report.resolve();report.mkdir(parents=True,exist_ok=False)
 binary=(ROOT/'build/utilities/REN.COM').read_bytes();observations=[]
 fixtures=[(1,f'F{i}.DOC',bytes([i+40])*(20096 if i==7 else 256)) for i in range(8)]
 raw=bytearray(install_files(fixtures))
 for i in range(0,4096,32):
  if raw[i]==1:
   state=int(chr(raw[i+2]))
   for b in range(3):raw[i+9+b]|=128 if state&(1<<b) else 0
 original=build(raw)
 for label,command in [('dry',':REN /P /DRY B1:*.DOC *.TXT'),('protected',':REN /P B1:*.DOC *.TXT')]:
  work=report/label;work.mkdir();marker='REN FINISHED '+label.upper()
  script=(command+'\r\nFINISH\r\n').encode()+b'\x1a'
  finish=b'\x11\x0b\x01\x0e\x09\xcd\x05\x00\xc3\x00\x00'+('\r\n'+marker+'\r\n$').encode()
  adata=medium([('REN.COM',binary),('SUBMIT.COM',(ROOT/'build/utilities/SUBMIT.COM').read_bytes()),('CASE.SUB',script),('FINISH.COM',finish)])
  (work/'a.dmk').write_bytes(adata);(work/'b.dmk').write_bytes(original)
  cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(work/'a.dmk'),'-d1',str(work/'b.dmk'),'-id','3000','-it']
  cmd+=keys('SUBMIT CASE\r')+['-id','3000','-it','-itime','0','-iw',marker,'-id','1000','-it','-ix']
  (work/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n')
  run(cmd,cwd=work,timeout=180,check=True)
  captures=sorted(work.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1]));texts=[screen(p) for p in captures]
  for p,t in zip(captures,texts):p.with_suffix('.txt').write_text(t)
  assert texts and marker in texts[-1],texts
  current=files(extract_raw((work/'b.dmk').read_bytes()))
  if label=='dry':assert (work/'b.dmk').read_bytes()==original and any('Dry run only:' in t for t in texts)
  else:
   assert any('8 FILES RENAMED' in t for t in texts),texts
   for i,(_,name,payload) in enumerate(fixtures):
    key=(1,(name[:-3]+'TXT').partition('.')[0].ljust(8).encode()+b'TXT')
    data,entries=current[key];assert data==payload,(i,len(data))
    assert all(sum((e[9+b]>>7)<<b for b in range(3))==i for e in entries),(i,entries)
    assert (1,name.partition('.')[0].ljust(8).encode()+b'DOC') not in current
  observations.append({'case':label,'command':command,'result':'PASS'})
 (report/'evidence.json').write_text(json.dumps({'result':'PASS','ren_sha256':hashlib.sha256(binary).hexdigest(),'observations':observations},indent=2)+'\n')
 print('PASS: Model 4 REN /P all attributes, multi-extents, contents and dry-run media immutability')
if __name__=='__main__':main()
