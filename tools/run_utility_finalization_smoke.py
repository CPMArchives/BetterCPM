#!/usr/bin/env python3
"""Terminal-launched Model 4 utility checks on private media, with exact identities."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from trs80gp_launch import run
from run_trs80_command import key_args, DEFAULT_EMULATOR
from fdf_format import select_fdf
from build_z80pack_image import disk_definition
from convert_fdf_image import raw_to_dmk
from utility_versions import identities

ROOT=Path(__file__).resolve().parents[1]
NAMES=('STAT CPX RSX DIR USER CLS VER COPY MOVE ERA REN TYPE TIME DUP SYSGEN ED SUBMIT XSUB PIP '
       'DLINK DUMP DASM DSYM TED ADMTST VT52TST ANSITST SYSBUILD RESPACK RLMBUILD WARM '
       'DDT COMPARE CRCKSUM MD5SUM PATCH SEARCH SQ USQ CR UNCR LZH UNLZH').split()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--output',type=Path,required=True)
 p.add_argument('--images',type=Path,default=Path.home()/'projects/git/BetterCPM/Releases/model4')
 p.add_argument('--emulator',type=Path,default=DEFAULT_EMULATOR)
 p.add_argument('--prepare-only',action='store_true')
 p.add_argument('--only',choices=('all','managers','crcksum'),default='all')
 a=p.parse_args();w=a.output.resolve();w.mkdir(parents=True,exist_ok=False)
 result={'status':'PREPARING','scope':'Help/alias precedence and manager LIST only; not full operational qualification','cases':[]}
 def save():(w/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 save()
 try:
  files=[a.images/n for n in ('BetterCPM-Distribution-trs80gp-80T-DS-System.dmk','BetterCPM-NOAH-trs80gp-80T-DS-800K.dmk')]
  result['original_images']=[{'path':str(f.resolve()),'sha256':sha(f)} for f in files]
  result['emulator_sha256']=sha(a.emulator)
  fmt=select_fdf(ROOT/'third_party/montezuma/DISK-INT.FDF','Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)')
  (w/'diskdefs').write_text(disk_definition(fmt));raw=w/'utilities.raw';raw.write_bytes(b'\xe5'*fmt.image_bytes)
  result['components']={}
  selected=NAMES if a.only=='all' else (['CRCKSUM'] if a.only=='crcksum' else ['CPX','RSX','STAT'])
  for n in selected:
   f=ROOT/'build/utilities'/(n+'.COM')
   subprocess.run(['cpmcp','-T','raw','-f','bettercpm-mm-80t-ds-data',str(raw),str(f),'0:'+n+'.COM'],cwd=w,check=True,capture_output=True)
   result['components'][n]={'identity':identities()[n],'sha256':sha(f),'bytes':f.stat().st_size}
  companion=w/'companion.dmk';shutil.copy2(files[1],companion)
  b=w/'utilities.dmk';b.write_bytes(raw_to_dmk(raw.read_bytes(),fmt))
  result['private_utilities_sha256']=sha(b)
  subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-mm-80t-ds-data','-n',str(raw)],cwd=w,check=True,capture_output=True)
  cases=[(n.lower()+'-help','B:'+n+' /VER /h /BOGUS\r',['Usage: '+n,'/H /HELP']) for n in selected]
  if a.only!='crcksum':cases += [('cpx-list','B:CPX list  \r',['RCP.CPX','TPA available:']),('rsx-list','B:RSX list  \r',['TPA available:'])]
  for label,tail,expected in cases:
   folder=w/label;folder.mkdir();a_disk=folder/'system.dmk';shutil.copy2(files[0],a_disk)
   cmd=[str(a.emulator),'-m4','-batch','-turbo','-ktx','-itime','18000','-d0',str(a_disk),'-d1',str(b),'-d2',str(companion),'-iw','Type TYPE README.TXT for more','-id','6000']
   cmd+=key_args(tail,delay=25)+['-id','30000','-it','-ics','-id','1000','-ics','-ix']
   case={'name':label,'tail':tail,'command':cmd,'expected':expected,'status':'PREPARED'};result['cases'].append(case);save()
   if a.prepare_only:continue
   print('Running '+label,flush=True)
   try:
    run(cmd,cwd=folder,timeout=600)
    data=(folder/'trs80-text-0.bin').read_bytes()[:1920]
    text='\n'.join(bytes(c&127 for c in data[i:i+80]).decode('ascii').rstrip() for i in range(0,1920,80))
    (folder/'screen.txt').write_text(text);case['observed']=text
    assert all(x in text for x in expected),'Expected output missing'
    if label.endswith('-help'):
     version,revision=identities()[label[:-5].upper()]
     assert f'{label[:-5].upper()} {version} ({revision:03d}' in text,'Identity differs'
    assert sha(b)==result['private_utilities_sha256'],'Read-only utility disk changed'
    case['status']='PASS'
   except Exception as e:case['status']='FAIL';case['error']=str(e)
   save()
  assert all(sha(f)==r['sha256'] for f,r in zip(files,result['original_images'])),'Original images changed'
  result['status']='PREPARED_NOT_RUN' if a.prepare_only else ('PASS' if all(c['status']=='PASS' for c in result['cases']) else 'FAIL')
 except Exception as e:result['status']='FAIL';result['error']=str(e)
 save();print(result['status']+': '+str(w/'result.json'))
 return result['status']=='FAIL'

if __name__=='__main__':raise SystemExit(main())
