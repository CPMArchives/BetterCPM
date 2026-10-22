#!/usr/bin/env python3
"""Qualify PIP's shared RO confirmation on private cpmsim/Model 4 media."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from test_disk_utilities import ROOT,medium
from test_z80pack_sysgen_install import session
from test_z80pack_attributes import directory
from test_model4_copy import files
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build
from run_trs80_command import DEFAULT_EMULATOR,key_args
from test_sysgen_install import screen
from trs80gp_launch import run
from utility_versions import banner
PROMPT='DESTINATION IS R/O, DELETE (Y/N)?'
PAYLOAD=b'S'*128;OLD=b'O'*128;OTHER=b'W'*128


def cpmsim(w,profile,binary):
 shutil.copytree(profile/'disks',w/'disks');shutil.copy2(profile/'diskdefs',w/'diskdefs')
 a=w/'disks/drivea.dsk';b=w/'disks/driveb.dsk'
 def cpm(tool,disk,*args):return subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disk),*map(str,args)],cwd=w,check=True,capture_output=True)
 subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(a),'0:PIP.COM'],cwd=w,capture_output=True)
 cpm('cpmcp',a,ROOT/'build/utilities/PIP.COM','0:PIP.COM')
 for name,data,ro in [('PUSRC.DAT',PAYLOAD,False),('PUOLD.DAT',OLD,True),('PUW.DAT',OTHER,True)]:
  p=w/name;p.write_bytes(data);cpm('cpmcp',b,p,'0:'+name)
  if ro:cpm('cpmchattr',b,'r','0:'+name)
 sim=Path.home()/'projects/git/z80pack/cpmsim/cpmsim';cases=[]
 def check(name,data,ro):
  p=w/('out-'+name);cpm('cpmcp',b,'0:'+name,p);assert p.read_bytes()==data,name
  stem,ext=name.split('.');key=(stem.ljust(8)+ext.ljust(3)).encode();raw=directory(b,w/'diskdefs')
  rows=[raw[i:i+32] for i in range(0,len(raw),32) if raw[i]==0 and bytes(x&127 for x in raw[i+1:i+12])==key]
  assert rows and all(bool(row[9]&128)==ro for row in rows),(name,ro)
 for label,answer in [('decline',b'N'),('invalid-declines',b'X'),('accept',b'y')]:
  text=session(sim,w/'disks',[(b'PIP B:PUOLD.DAT=B:PUSRC.DAT[V]\r',PROMPT.encode(),60),(answer,b'A0>_ ',60)],w/(label+'.txt'))
  assert text.count(PROMPT.encode())==1
  if label!='accept':assert b'**NOT DELETED**' in text
  check('PUOLD.DAT',PAYLOAD if label=='accept' else OLD,label!='accept')
  check('PUSRC.DAT',PAYLOAD,False);check('PUW.DAT',OTHER,True)
  cases.append(label)
 text=session(sim,w/'disks',[(b'PIP B:PUW.DAT=B:PUSRC.DAT[WV]\r',b'A0>_ ',60),(b'PIP /VER\r',b'A0>_ ',60)],w/'bypass.txt')
 assert PROMPT.encode() not in text and banner('PIP').encode() in text
 check('PUW.DAT',PAYLOAD,False);check('PUSRC.DAT',PAYLOAD,False)
 listing=cpm('cpmls',b).stdout.decode().lower();assert 'pu_old.$$$' not in listing and 'pu_w.$$$' not in listing
 fs=subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(b)],cwd=w,capture_output=True)
 (w/'filesystem.txt').write_bytes(fs.stdout+fs.stderr);assert fs.returncode==0
 return cases+['W-bypass','version','independent payload/RO checks after each decision','filesystem']


def model4(w,binary):
 raw=extract_raw(medium([('PIP.COM',binary),('PUSRC.DAT',PAYLOAD),('PUOLD.DAT',OLD),('PUW.DAT',OTHER)]))
 for i in range(20480,24576,32):
  if raw[i]==0 and bytes(x&127 for x in raw[i+1:i+12]) in (b'PUOLD   DAT',b'PUW     DAT'):raw[i+9]|=128
 before=files(raw[20480:]);(w/'before.raw').write_bytes(raw);disk=w/'a.dmk';disk.write_bytes(build(raw))
 stages=[];cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(disk),'-itime','30000','-id','5000']
 def command(text):cmd.extend(key_args('CLS\r',delay=25)+['-id','6000']+key_args(text+'\r',delay=25))
 def capture(name,marker):stages.append(name);cmd.extend(['-iw',marker,'-id','200','-it'])
 for label,answer in [('decline','N'),('invalid-declines','X'),('accept','Y')]:
  command('PIP PUOLD.DAT=PUSRC.DAT[V]');capture(label+'-question',PROMPT)
  cmd.extend(key_args(answer,delay=25))
  if label!='accept':capture(label,'**NOT DELETED**')
  else:stages.append(label);cmd+=['-id','12000','-it']
  cmd+=['-id','6000']
 command('PIP PUW.DAT=PUSRC.DAT[WV]');cmd+=['-id','12000','-it'];stages.append('W-bypass')
 cmd+=key_args('PIP /VER\r',delay=25);capture('version',banner('PIP'))
 cmd+=['-id','6000','-ix'];(w/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n')
 run(cmd,cwd=w,timeout=900,check=True)
 captures=sorted(w.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1]));assert len(captures)==len(stages)
 texts={n:screen(p) for n,p in zip(stages,captures)}
 for n,t in texts.items():(w/(n+'.txt')).write_text(t)
 assert PROMPT not in texts['W-bypass'] and 'A0>' in texts['accept']
 after=extract_raw(disk.read_bytes());(w/'after.raw').write_bytes(after);now=files(after[20480:])
 assert after[:20480]==raw[:20480]
 for k,(data,entries) in before.items():
  if k[1] in (b'PUOLD   DAT',b'PUW     DAT'):
   assert now[k][0]==PAYLOAD and all(not(row[9]&128) for row in now[k][1])
  else:assert now[k][0]==data,k
 assert not any(k[1].endswith(b'$$$') for k in now)
 (w/'diskdefs').write_text('diskdef bettercpm-default\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 4\n os 2.2\nend\n')
 fs=subprocess.run(['fsck.cpm','-T','raw,pcw800','-f','bettercpm-default','-n',str(w/'after.raw')],cwd=w,capture_output=True)
 (w/'filesystem.txt').write_bytes(fs.stdout+fs.stderr);assert fs.returncode==0
 return stages+['final payload/attributes, unchanged other files/system area, filesystem']


def main():
 p=argparse.ArgumentParser();p.add_argument('--platform',choices=['cpmsim','model4'],required=True);p.add_argument('--image-dir',type=Path);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 if a.platform=='cpmsim' and a.image_dir is None:p.error('--image-dir required for cpmsim')
 w=a.report.resolve();w.mkdir(parents=True,exist_ok=False);binary=(ROOT/'build/utilities/PIP.COM').read_bytes()
 cases=cpmsim(w,a.image_dir,binary) if a.platform=='cpmsim' else model4(w,binary)
 (w/'result.json').write_text(json.dumps({'result':'PASS','platform':a.platform,'pip_sha256':hashlib.sha256(binary).hexdigest(),'cases':cases},indent=2)+'\n')
 print('PASS:',a.platform,'PIP single-key RO approval, decline, W bypass and private-media checks')
if __name__=='__main__':main()
