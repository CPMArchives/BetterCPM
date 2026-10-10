#!/usr/bin/env python3
"""Native COPY report allocation, summaries and zero-count omission."""
import hashlib
import argparse,json,shutil,subprocess
from pathlib import Path
from test_disk_utilities import ROOT
from test_z80pack_sysgen_install import session

def main():
 p=argparse.ArgumentParser();p.add_argument('--image-dir',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 w=a.report.resolve();w.mkdir(parents=True,exist_ok=False);shutil.copytree(a.image_dir/'disks',w/'disks');shutil.copy2(a.image_dir/'diskdefs',w/'diskdefs')
 disks={x:w/'disks'/f'drive{x}.dsk' for x in 'abd'}
 def cpm(tool,x,*v):subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disks[x]),*map(str,v)],cwd=w,check=True)
 cpm('cpmrm','a','0:COPY.COM');cpm('cpmcp','a',ROOT/'build/utilities/COPY.COM','0:COPY.COM')
 for x in 'bd':disks[x].write_bytes(bytes([229])*len(disks[x].read_bytes()))
 for name,size in [('A',128),('B',128),('C',0),('BIG',33280)]:
  f=w/(name+'.DAT');f.write_bytes(b'X'*size);cpm('cpmcp','b',f,'1:'+f.name)
 old=w/'old.dat';old.write_bytes(b'Y'*33280)
 for name in ['A','B']:cpm('cpmcp','d',old,'0:'+name+'.DAT')
 cpm('cpmchattr','d','r','0:B.DAT')
 def execute(cmd,label):return session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',w/'disks',[(b'CPX UNLOAD RCP\r',b'A0>_ ',30),(cmd.encode()+b'\r',b'A0>_ ',120)],w/(label+'.txt'))
 t=execute('COPY /B /S B1:?.DAT D0:','mixed')
 assert b'B1:C.DAT -> D0:C.DAT [0K]' in t,t
 assert b'1 FILE COPIED [0K]' in t and b'1 FILE SKIPPED' in t and b'1 FILE FAILED' in t,t
 t=execute('COPY /B /O B1:A.DAT D0:','overwrite')
 assert b'B1:A.DAT -> D0:A.DAT [2K]' in t and b'FILES COPIED' not in t,t
 t=execute('COPY /B /V B1:*.DAT D2:','all')
 assert b'4 FILES COPIED [38K]' in t and b'B1:BIG.DAT -> D2:BIG.DAT [34K]' in t,t
 assert b'FILE SKIPPED' not in t and b'FILE FAILED' not in t,t
 t=execute('COPY /B B1:*.ZZZ D3:','no-match')
 assert b'NO FILE' in t and b'COPIED [' not in t and b'FILE FAILED' not in t,t
 (w/'evidence.json').write_text(json.dumps({'copy_sha256':hashlib.sha256((ROOT/'build/utilities/COPY.COM').read_bytes()).hexdigest(),'result':'PASS','empty_k':0,'one_record_k':2,'multi_extent_k':34,'mixed_summary':True,'overwrite_actual_allocation':True},indent=2)+'\n')
 print('Native COPY allocation, mixed summaries, overwrite and no-match reporting pass')
if __name__=='__main__':main()
