#!/usr/bin/env python3
"""Capture corrected release presentation on private Model 4 disks, one boot per case."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from trs80gp_launch import run
from run_trs80_command import key_args, DEFAULT_EMULATOR
from fdf_format import select_fdf
from convert_fdf_image import raw_to_dmk

CASES={
 'dir-empty':(':DIR D:\r',['D0: NO FILE','---- 796K FREE ----']),
 'crc40':('B:CRCKSUM A:STARTUP.SUB /40\r',['STARTUP','CRC32','KERM12','1 file calculated.']),
 'copy-help':(':COPY /HELP\r',['Usage: COPY','/BACKUP']),
 'compare-help':('C:COMPARE /VER /HELP /BOGUS\r',['Usage: COMPARE','/HELP']),
 'noah-help':('C:NOAH /HELP\r',['Usage: NOAH','/QUIET','/LIST']),
 'noah-add':('NOAH /ADD D:SMOKE.LBR A:STARTUP.SUB\r',['1 file added.'])}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--output',required=True,type=Path)
 p.add_argument('--images',type=Path,default=Path.home()/'projects/git/BetterCPM/Releases/model4')
 p.add_argument('--emulator',type=Path,default=DEFAULT_EMULATOR)
 p.add_argument('--only',choices=list(CASES))
 p.add_argument('--prepare-only',action='store_true')
 p.add_argument('--capture-review',action='store_true',help='Repeat COMPARE and NOAH captures to investigate raster/text discrepancies')
 a=p.parse_args();w=a.output.resolve();w.mkdir(parents=True,exist_ok=False)
 result={'status':'PREPARING','scope':'Automated text checks and saved screens; full layout review separate','cases':[]}
 def save():(w/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 save()
 try:
  names=['BetterCPM-Distribution-trs80gp-80T-DS-System.dmk','BetterCPM-Utilities-trs80gp-80T-DS-800K.dmk','BetterCPM-NOAH-trs80gp-80T-DS-800K.dmk']
  originals=[a.images.resolve()/n for n in names]
  result['images']=[{'source':str(f),'sha256':sha(f)} for f in originals];result['emulator_sha256']=sha(a.emulator)
  root=Path(__file__).resolve().parents[1]
  fmt=select_fdf(root/'metadata/DISK.FDF','Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)')
  blank=raw_to_dmk(b'\xe5'*fmt.image_bytes,fmt)
  for name,(text,expected) in CASES.items():
   if a.only and a.only!=name:continue
   if a.capture_review and name not in ('compare-help','noah-help'):continue
   folder=w/name;folder.mkdir();drives=[]
   for i,f in enumerate(originals):
    dest=folder/('drive'+str(i)+'.dmk');shutil.copyfile(f,dest);drives.append(dest)
   dest=folder/'drive3.dmk';dest.write_bytes(blank);drives.append(dest)
   cmd=[str(a.emulator),'-m4','-batch','-turbo','-ktx','-itime','18000']
   for i,f in enumerate(drives):cmd+=['-d'+str(i),str(f)]
   cmd+=['-iw','Type TYPE README.TXT for more','-id','6000']
   if name=='noah-add':
    cmd+=key_args('C:\r',delay=25)+['-iw','C0>','-id','6000']
   cmd+=key_args(text,delay=25)+['-id','30000','-it','-ics']
   if a.capture_review:
    cmd+=['-id','1000','-it','-ics','-id','5000','-it','-ics']
   cmd+=['-ix']
   case={'name':name,'command':cmd,'expected':expected,'status':'PREPARED'};result['cases'].append(case);save()
   if a.prepare_only:continue
   print('Running '+name,flush=True)
   try:
    run(cmd,cwd=folder,timeout=600)
    captures=sorted(folder.glob('trs80-text-*.bin'));assert len(captures)==(3 if a.capture_review else 1),'Unexpected result capture count'
    raw=captures[0].read_bytes()[:1920]
    output='\n'.join(bytes(c&127 for c in raw[i:i+80]).decode('ascii').rstrip() for i in range(0,len(raw),80))
    (folder/'screen.txt').write_text(output);case['observed']=output
    missing=[s for s in expected if s not in output];assert not missing,'Missing text: '+repr(missing)
    for i in [1,2]:assert sha(drives[i])==result['images'][i]['sha256'],'Utility disk changed'
    if name=='dir-empty':
     lines=output.splitlines();i=lines.index('D0: NO FILE');assert lines[i+1]=='---- 796K FREE ----','Footer not on adjacent row'
    case['status']='PASS_TEXT_CHECKS'
   except Exception as e:case['status']='FAIL';case['error']=str(e)
   save()
  assert all(sha(f)==r['sha256'] for f,r in zip(originals,result['images'])),'Original release image changed'
  result['status']='PREPARED_NOT_RUN' if a.prepare_only else ('PASS_TEXT_CHECKS' if all(c['status']=='PASS_TEXT_CHECKS' for c in result['cases']) else 'FAIL')
 except Exception as e:result['status']='FAIL';result['error']=str(e)
 save();print(result['status']+': '+str(w/'result.json'),flush=True)
 return 1 if result['status']=='FAIL' else 0

if __name__=='__main__':raise SystemExit(main())
