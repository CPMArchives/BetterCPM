#!/usr/bin/env python3
"""Private one-shot faults qualify COPY cleanup, continuation and stop rules."""
import argparse,json,re,shutil,subprocess
from pathlib import Path
from test_disk_utilities import ROOT
from test_z80pack_sysgen_install import session

def main():
 p=argparse.ArgumentParser();p.add_argument('--image-dir',type=Path,required=True);p.add_argument('--report',type=Path,required=True);args=p.parse_args()
 w=args.report.resolve();w.mkdir(parents=True,exist_ok=False)
 base=(ROOT/'build/utilities/COPY.COM').read_bytes();listing=(ROOT/'build/utilities/copy-transient.lst').read_text()
 def addr(n):return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+n+':',listing,re.M|re.I)[1],16)
 results=[]
 for label,start,function,nth,status,stop,cleanup in [('read','BC_CLOOP',20,5,4,False,False),('write','BC_CWRITE',21,4,255,False,False),('close','BC_CCLOSE',16,2,255,False,False),('full','BC_CWRITE',21,4,2,True,False),('cleanup','BC_CWRITE',21,4,255,True,True)]:
  d=w/label;d.mkdir();shutil.copytree(args.image_dir/'disks',d/'disks');shutil.copy2(args.image_dir/'diskdefs',d/'diskdefs')
  disks={x:d/'disks'/f'drive{x}.dsk' for x in 'abd'}
  def cpm(tool,x,*v):subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disks[x]),*map(str,v)],cwd=d,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  for x in 'bd':disks[x].write_bytes(bytes([229])*len(disks[x].read_bytes()))
  for name in 'ABC':
   f=d/(name+'.DAT');f.write_bytes(name.encode()*256);cpm('cpmcp','b',f,'1:'+f.name);cpm('cpmchattr','b','a','1:'+f.name)
  image=bytearray(base);off=image.index(bytes([14,function,205,5,0]),addr(start)-256)+2
  entry=256+len(image);counter=entry+19
  shim=b'\xcd\x05\x00\xf5\x21'+counter.to_bytes(2,'little')+bytes([0x34,0x7e,0xfe,nth,0x20,4,0xf1,0x3e,status,0xc9,0xf1,0xc9,0])
  assert len(shim)==20
  image[off:off+3]=b'\xcd'+entry.to_bytes(2,'little');image+=shim
  if cleanup:
   off=image.index(b'\x0e\x13\xcd\x05\x00',addr('CVVDEL')-256)+2;image[off:off+3]=b'\x3e\xff\x00'
  f=d/'COPY.COM';f.write_bytes(image);cpm('cpmrm','a','0:COPY.COM');cpm('cpmcp','a',f,'0:COPY.COM')
  t=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',d/'disks',[(b'CPX UNLOAD RCP\r',b'A0>_ ',30),(b'COPY /B /BACKUP B1:*.DAT D0:\r',b'A0>_ ',90)],d/'transcript.txt')
  assert (b'NO SPACE' if label=='full' else b'READ ERROR' if label=='read' else b'WRITE ERROR') in t,(label,t)
  if cleanup:assert b'INCOMPLETE DESTINATION CLEANUP FAILED' in t
  for name,exists in [('A',True),('B',cleanup),('C',not stop)]:
   f=d/('out-'+name);cpm('cpmcp','d','0:'+name+'.DAT',f);assert f.exists()==exists,(label,name)
   if exists and name!='B':assert f.read_bytes()==name.encode()*256
  raw=disks['b'].read_bytes();directory=b''.join(raw[6*18*256+s*256:6*18*256+(s+1)*256] for s in [0,4,8,12,16,2,6,10])
  for name,arc in [('A',False),('B',True),('C',stop)]:
   entries=[directory[i:i+32] for i in range(0,len(directory),32) if directory[i]==1 and bytes(c&127 for c in directory[i+1:i+12])==name.encode()+b'       DAT']
   assert entries and all(bool(e[11]&128)==arc for e in entries),(label,name)
  results.append(label)
 (w/'evidence.json').write_text(json.dumps({'result':'PASS','controlled_faults':results,'caller_du_restored':True},indent=2)+'\n')
 print('Native COPY read/write/close continuation, disk-full stop and cleanup failure pass')
if __name__=='__main__':main()
