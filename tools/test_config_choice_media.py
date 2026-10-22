#!/usr/bin/env python3
"""CONFIG menu/drive/save-scope rejection on unchanged disposable media."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from test_disk_utilities import ROOT,medium
from test_z80pack_sysgen_install import session
from run_trs80_command import DEFAULT_EMULATOR,key_args
from test_sysgen_install import screen
from trs80gp_launch import run
STEPS=[('CONFIG\r','Configuration options:'),('Z','Configuration options:'),
 ('c','Disk drive selections'),('E','Disk drive selections'),('a','Type of drive (inches):'),
 ('\x03','Disk drive selections'),('\x03','Configuration options:'),
 ('S','Save startup defaults'),('X','Save startup defaults'),('\x03','Configuration options:')]
def main():
 p=argparse.ArgumentParser();p.add_argument('--platform',choices=['cpmsim','model4'],required=True);p.add_argument('--image-dir',type=Path);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 w=a.report.resolve();w.mkdir(parents=True,exist_ok=False)
 if a.platform=='cpmsim':
  if not a.image_dir:p.error('--image-dir required')
  shutil.copytree(a.image_dir/'disks',w/'disks');shutil.copy2(a.image_dir/'diskdefs',w/'diskdefs')
  disk=w/'disks/drivea.dsk'
  subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(disk),'0:CONFIG.COM'],cwd=w,capture_output=True)
  subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),str(ROOT/'build/utilities/CONFIG.COM'),'0:CONFIG.COM'],cwd=w,check=True,capture_output=True)
  before={x:x.read_bytes() for x in (w/'disks').glob('*.dsk')}
  ready=b'Your choice: [ ]\x08\x08'
  trace=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',w/'disks',[(key.encode(),ready,60) for key,_ in STEPS]+[(b'\x03',b'A0>_ ',30)],w/'session.txt')
  for _,marker in STEPS:assert marker.encode() in trace,marker
 else:
  disk=w/'a.dmk';disk.write_bytes(medium([]));other=w/'b.dmk';other.write_bytes(medium([]))
  before={x:x.read_bytes() for x in (disk,other)}
  cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(disk),'-d1',str(other),'-itime','30000','-id','5000']
  for key,marker in STEPS:
   visible={'Disk drive selections':'Number of drives: 4','Save startup defaults':'Save pending cold-boot changes only'}.get(marker,marker)
   cmd+=key_args(key,delay=25)+['-iw',visible,'-id','2000','-it']
  cmd+=key_args('\x03',delay=25)+['-id','6000','-it','-ix']
  (w/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n');run(cmd,cwd=w,timeout=600,check=True)
  captures=sorted(w.glob('trs80-text-*.bin'),key=lambda x:int(x.stem.rsplit('-',1)[1]));assert len(captures)==len(STEPS)+1
  for i,((_,marker),capture) in enumerate(zip(STEPS,captures)):
   text=screen(capture);(w/f'screen-{i}.txt').write_text(text);assert marker in text,(i,text)
  assert 'A0>' in screen(captures[-1])
 assert all(x.read_bytes()==data for x,data in before.items()),'menu operation changed media'
 report={'result':'PASS','platform':a.platform,'menu_stages':len(STEPS),'media_unchanged':True,'sha256':hashlib.sha256((ROOT/'build/utilities/CONFIG.COM').read_bytes()).hexdigest()}
 (w/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
if __name__=='__main__':main()
