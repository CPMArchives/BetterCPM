#!/usr/bin/env python3
"""Create four-drive high-capacity fixtures; never overwrite working disks."""
from pathlib import Path
import argparse,json,shutil
from build_montezuma_extended_790k import build,verify,TRACK_LENGTH,LOGICAL_SECTOR_ORDER,DATA_MARK_OFFSET
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--output',type=Path,default=ROOT/'build/test-configurations/high-capacity')
 a=p.parse_args();out=a.output
 if out.exists():raise SystemExit(f'{out} exists; choose a new --output to preserve its disks')
 boot=ROOT/'build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk'
 verify(boot.read_bytes(),require_blank=False)
 out.mkdir(parents=True)
 shutil.copy2(boot,out/'drivea.dmk')
 blank=build();verify(blank)
 for letter in 'bcd':(out/f'drive{letter}.dmk').write_bytes(blank)
 # Flat images are in logical sector order for cpmtools, not cpmsim booting.
 for letter in 'abcd':
  image=(out/f'drive{letter}.dmk').read_bytes();raw=bytearray()
  for t in range(160):
   track=image[16+t*TRACK_LENGTH:16+(t+1)*TRACK_LENGTH]
   for i in LOGICAL_SECTOR_ORDER:
    ptr=int.from_bytes(track[i*2:i*2+2],'little')&0x3fff
    at=ptr+DATA_MARK_OFFSET+1;raw.extend(track[at:at+512])
  (out/f'drive{letter}.img').write_bytes(raw)
 definitions=''
 for name,reserved in [('system',4),('data',0)]:
  definitions+=f'diskdef bettercpm-{name}\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk {reserved}\n os 2.2\nend\n'
 (out/'diskdefs').write_text(definitions)
 manifest={'platform':'trs80gp Model 4','drives':[
  {'logical':'A','physical':0,'image':'drivea.dmk','format':'BetterCP/M SYSTEM 780K (MM Extended physical geometry)','bootable':True},
  *[{'logical':l.upper(),'physical':i,'image':f'drive{l}.dmk','format':'MM 80T DS DATA 800K','bootable':False} for i,l in enumerate('bcd',1)]],
  'sector_bytes':512,'cylinders':80,'sides':2,'sectors_per_side':10,'rsx_required':False,
  'z80pack':'A separate cpmsim platform adapter is required; these DMK images are not cpmsim boot media.'}
 (out/'configuration.json').write_text(json.dumps(manifest,indent=2)+'\n')
 # Launch from this directory; writes are confined to these working copies.
 from run_trs80_command import DEFAULT_EMULATOR
 launcher='#!/bin/sh\ncd -- "$(dirname -- "$0")" || exit 1\nexec '+"'"+str(DEFAULT_EMULATOR).replace("'","'\\''")+"'"+' -m4 -d0 drivea.dmk -d1 driveb.dmk -d2 drivec.dmk -d3 drived.dmk "$@"\n'
 (out/'launch-trs80.command').write_text(launcher);(out/'launch-trs80.command').chmod(0o755)
 print(out)
if __name__=='__main__':main()
