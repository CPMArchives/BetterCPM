#!/usr/bin/env python3
"""DIR WHEREIS campaigns on isolated cpmsim or Model 4 media.
cpmsim --image-dir points to a qualified workspace containing disks/ and diskdefs.
"""
import argparse,sys,shutil,subprocess
from pathlib import Path
from test_z80pack_sysgen_install import session
from test_disk_utilities import medium,keys
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run
root=Path(__file__).resolve().parents[1]
def cpmsim(args):
 w=args.report.resolve();w.mkdir(exist_ok=False,parents=True);s=args.image_dir.resolve()
 if not (w/'disks').exists():shutil.copytree(s/'disks',w/'disks');shutil.copy2(s/'diskdefs',w/'diskdefs')
 d=w/'disks/drivea.dsk'
 for n,p in [('DIR.COM',root/'build/utilities/DIR.COM'),('RCP.CPX',root/'build/cpx/RCP.CPX')]:
  subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(d),'0:'+n],cwd=w,check=False,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(d),str(p),'0:'+n],cwd=w,check=True)
 (w/'ED.COM').write_bytes(b'fixture only')
 for disk,user in [(d,0),(d,2),(w/'disks/driveb.dsk',3)]:
  subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(disk),str(user)+':ED.COM'],cwd=w,check=False,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),str(w/'ED.COM'),str(user)+':ED.COM'],cwd=w,check=True)
 subprocess.run(['cpmchattr','-T','raw','-f','bettercpm-default',str(d),'s','0:ED.COM'],cwd=w,check=True)
 before={p:p.read_bytes() for p in (w/'disks').glob('drive?.dsk')}
 cmds=['DIR /WHEREIS ED.COM',':DIR /WHEREIS A3:*.TXT',':DIR /WHEREIS ED.COM',':DIR /WHEREIS B:ED.COM',':DIR /WHEREIS B[-]:ED.COM',':DIR /WHEREIS A0:ED.COM[$SYS]',':DIR /WHEREIS A3:*.TXT /A',':DIR /VER']
 t=session(args.cpmsim,w/'disks',[(c.encode()+b'\r',b'A0>_ ',60) for c in cmds],w/'transcript.txt')
 for expected in [b'DIR: Use :DIR.',b'A0:ED.COM',b'A2:ED.COM',b'B3:ED.COM',b'DIR: No matches found.',b'Invalid option.',b'Build 003']:assert expected in t,(expected,t[-4000:])
 assert all(p.read_bytes()==data for p,data in before.items())
 print('PASS: cpmsim WHEREIS scope, SYS, normal validation, version and unchanged media')

def model4(args):
 w=args.report.resolve();w.mkdir(exist_ok=False,parents=True)
 image=medium([('DIR.COM',(root/'build/utilities/DIR.COM').read_bytes()),('ED.COM',b'fixture')]);(w/'a.dmk').write_bytes(image)
 a=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(w/'a.dmk'),'-id','5000']
 for c,delay in [('CLS',1000),('DIR /WHEREIS ED.COM',1500),(':DIR /WHEREIS A0:ED.COM',6000),(':DIR /WHEREIS A0:MISSING.COM',6000),(':DIR /WHEREIS A0:ED.COM /A',6000),(':DIR /VER',5000),(':DIR /VER',5000)]:
  a+=keys(c+'\r')+['-id',str(delay),'-it']
 a+=['-ix'];run(a,cwd=w,check=True,timeout=180)
 texts=[]
 for p in sorted(w.glob('trs80-text-*.bin')):
  raw=p.read_bytes()[:1920];texts.append('\n'.join(bytes(c&127 for c in raw[i:i+80]).decode('ascii').rstrip() for i in range(0,1920,80)))
 out='\n'.join(texts);(w/'screens.txt').write_text(out)
 for expected in ['DIR: Use :DIR.','A0:ED.COM','1 MATCH','DIR: No matches found.','Invalid option.','Build 003']:assert expected in out,(expected,out)
 assert (w/'a.dmk').read_bytes()==image
 print('PASS: Model 4 WHEREIS, resident hint, validation, version and unchanged disk')

def main():
 p=argparse.ArgumentParser();p.add_argument('--platform',choices=['z80pack','model4'],required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--image-dir',type=Path)
 p.add_argument('--cpmsim',type=Path,default=Path('/Users/nathanael/projects/git/z80pack/cpmsim/cpmsim'));args=p.parse_args()
 if args.platform=='z80pack':
  if not args.image_dir:p.error('--image-dir is required for z80pack')
  cpmsim(args)
 else:model4(args)
if __name__=='__main__':main()
