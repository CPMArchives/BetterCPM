#!/usr/bin/env python3
"""DUP menu/drive input and refusal on private cpmsim/Model 4 media."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from test_disk_utilities import ROOT,medium
from test_z80pack_sysgen_install import session
from run_trs80_command import DEFAULT_EMULATOR,key_args
from test_sysgen_install import screen
from trs80gp_launch import run
MENU='[ A ] Format a disk'
DRIVE='Choose logical drive [ A - D ], or ^C to return.'
CONFIRM='Format this disk? [Y/N]'
SOURCE='Source logical drive [ A - D ]'

def cpmsim(w,profile):
 shutil.copytree(profile/'disks',w/'disks');shutil.copy2(profile/'diskdefs',w/'diskdefs')
 a=w/'disks/drivea.dsk';b=w/'disks/driveb.dsk'
 subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(a),'0:DUP.COM'],cwd=w,check=True,capture_output=True)
 subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(a),str(ROOT/'build/utilities/DUP.COM'),'0:DUP.COM'],cwd=w,check=True,capture_output=True)
 beforea=a.read_bytes();beforeb=b.read_bytes()
 # Wait for the completed choice field, not an earlier heading. Cooked
 # output can intercept Ctrl-C before KEY starts polling for the answer.
 ready=b'Your choice: [ ]\x08\x08'
 steps=[(b'DUP\r',ready,60),(b'X',ready,30),
        (b'a',ready,30),(b'E',ready,30),
        (b'A',ready,30),(b'\x03',ready,30),
        (b'A',ready,30),(b'b',CONFIRM.encode()+b' ',60),
        (b'N',ready,30),(b'A',ready,30),
        (b'B',CONFIRM.encode()+b' ',60),(b'X',ready,30),
        (b'\x03',b'A0>_ ',30)]
 text=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',w/'disks',steps,w/'session.txt')
 assert text.count(CONFIRM.encode())==2 and b'Formatting cylinder' not in text
 assert a.read_bytes()==beforea and b.read_bytes()==beforeb
 return ['invalid menu redisplay','lowercase operation/drive','invalid drive returns menu','drive Ctrl-C returns menu','N/X decline destructive approval after selections','main Ctrl-C exits','both disk images unchanged']

def model4(w):
 a=w/'a.dmk';b=w/'b.dmk';a.write_bytes(medium([('DUP.COM',(ROOT/'build/utilities/DUP.COM').read_bytes())]));b.write_bytes(medium([]))
 beforea=a.read_bytes();beforeb=b.read_bytes();stages=[]
 cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(a),'-d1',str(b),'-itime','30000','-id','5000']
 def keys(text):cmd.extend(key_args(text,delay=25))
 def snap(label,marker=None):
  if marker:cmd.extend(['-iw',marker])
  cmd.extend(['-id','2000','-it']);stages.append(label)
 keys('DUP\r');snap('main',MENU)
 keys('X');snap('invalid-main')
 keys('a');snap('drive',DRIVE)
 keys('E');snap('invalid-drive')
 keys('A');snap('drive-again',DRIVE)
 keys('\x03');snap('drive-cancel')
 keys('A');snap('drive-target',DRIVE)
 keys('b');snap('approval',CONFIRM)
 keys('N');snap('declined',MENU)
 keys('A');snap('drive-target-again',DRIVE)
 keys('B');snap('approval-again',CONFIRM)
 keys('X');snap('invalid-declines',MENU)
 keys('\x03');cmd+=['-id','6000','-it','-ix'];stages.append('returned')
 (w/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n');run(cmd,cwd=w,timeout=900,check=True)
 captures=sorted(w.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1]));assert len(captures)==len(stages)
 texts={n:screen(p) for n,p in zip(stages,captures)}
 for n,t in texts.items():(w/(n+'.txt')).write_text(t)
 for n in ['invalid-main','invalid-drive','drive-cancel','declined','invalid-declines']:assert MENU in texts[n],(n,texts[n])
 for n in ['approval','approval-again']:assert CONFIRM in texts[n],(n,texts[n])
 assert 'A0>' in texts['returned']
 assert a.read_bytes()==beforea and b.read_bytes()==beforeb,'menu/refusal modified disk'
 return stages+['both physical disk images unchanged']

def main():
 p=argparse.ArgumentParser();p.add_argument('--platform',choices=['cpmsim','model4'],required=True);p.add_argument('--image-dir',type=Path);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 if a.platform=='cpmsim' and a.image_dir is None:p.error('--image-dir required')
 w=a.report.resolve();w.mkdir(parents=True,exist_ok=False)
 cases=cpmsim(w,a.image_dir) if a.platform=='cpmsim' else model4(w)
 (w/'result.json').write_text(json.dumps({'result':'PASS','platform':a.platform,'dup_sha256':hashlib.sha256((ROOT/'build/utilities/DUP.COM').read_bytes()).hexdigest(),'cases':cases},indent=2)+'\n')
 print('PASS:',a.platform,'DUP menus, drive selection, confirmation isolation and unchanged media')
if __name__=='__main__':main()
