#!/usr/bin/env python3
"""REN shared choices on private native Model 4 media, with payload audit."""
import argparse,hashlib,json,subprocess
from test_disk_utilities import ROOT,medium
from test_model4_copy import files
from add_cpm_file_to_dmk import extract_raw
from run_trs80_command import DEFAULT_EMULATOR,key_args
from test_sysgen_install import screen
from trs80gp_launch import run
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 w=a.report.resolve();w.mkdir(parents=True,exist_ok=False)
 binary=(ROOT/'build/utilities/REN.COM').read_bytes()
 disk=w/'a.dmk';disk.write_bytes(medium([('REN.COM',binary),('FIRST.DAT',b'ORIGINAL SOURCE\r\n'),('TAKEN.DAT',b'EXISTING TARGET\r\n')]))
 raw=extract_raw(disk.read_bytes());before=files(raw[20480:]);(w/'before.raw').write_bytes(raw)
 stages=[];cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(disk),'-itime','30000','-id','5000']
 def capture(name,marker):
  stages.append(name);cmd.extend(['-iw',marker,'-id','120','-it'])
 def command(text):
  cmd.extend(key_args('CLS\r',delay=25)+['-id','6000']+key_args(text+'\r',delay=25))
 command(':REN /C FIRST.DAT NEW.DAT');capture('confirm','Rename? Y/N')
 cmd+=['-ik','6','2','-id','25','-ik','6','0','-id','25']+key_args('\rX',delay=25)+['-id','500','-it'];stages.append('invalid')
 cmd+=key_args('N',delay=25);capture('decline','1 SKIPPED')
 cmd+=['-id','6000'];command(':REN /C FIRST.DAT NEW.DAT');capture('cancel-question','Rename? Y/N')
 cmd+=key_args('\x03',delay=25)+['-id','6000','-it'];stages.append('cancel')
 command(':REN /C FIRST.DAT TAKEN.DAT');capture('collision','File exists. N/S/A/?')
 cmd+=key_args('?',delay=25);capture('help','N New name, S Skip file, A Abort remainder.')
 cmd+=key_args('N',delay=25);capture('name','New name?')
 cmd+=key_args('NEW.DAT\r',delay=25);capture('replacement','Rename? Y/N')
 cmd+=key_args('Y',delay=25);capture('renamed','1 FILES RENAMED')
 cmd+=['-id','6000','-it','-ix'];stages.append('returned')
 (w/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n');run(cmd,cwd=w,timeout=900,check=True)
 caps=sorted(w.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1]));assert len(caps)==len(stages)
 texts={n:screen(p) for n,p in zip(stages,caps)}
 for n,t in texts.items():(w/(n+'.txt')).write_text(t)
 assert 'Rename? Y/N' in texts['invalid'] and '1 SKIPPED' not in texts['invalid']
 assert 'A0>' in texts['cancel'] and 'A0>' in texts['returned']
 assert 'FIRST.DAT -> NEW.DAT' in texts['replacement']
 after=extract_raw(disk.read_bytes());(w/'after.raw').write_bytes(after);now=files(after[20480:])
 assert (0,b'FIRST   DAT') not in now and now[0,b'NEW     DAT'][0]==before[0,b'FIRST   DAT'][0]
 for k,(payload,entries) in before.items():
  if k!=(0,b'FIRST   DAT'):assert now[k][0]==payload,k
 assert after[:20480]==raw[:20480]
 (w/'diskdefs').write_text('diskdef bettercpm-default\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 4\n os 2.2\nend\n')
 fs=subprocess.run(['fsck.cpm','-T','raw,pcw800','-f','bettercpm-default','-n',str(w/'after.raw')],cwd=w,capture_output=True,text=True)
 (w/'filesystem.txt').write_text(fs.stdout+fs.stderr);assert fs.returncode==0
 (w/'result.json').write_text(json.dumps({'result':'PASS','ren_sha256':hashlib.sha256(binary).hexdigest(),'stages':stages,'scope':'native confirmation, invalid ESC/Enter/X, decline, Ctrl-C, collision/help, replacement name, authorization; unchanged other payloads/system records, clean filesystem. Fault recovery choices are CPU-qualified.'},indent=2)+'\n')
 print('PASS: native Model 4 REN shared choices and independent file/media audit')
if __name__=='__main__':main()
