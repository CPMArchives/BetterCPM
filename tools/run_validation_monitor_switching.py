#!/usr/bin/env python3
"""Switch all shipped personalities in one actual cpmsim session."""
import argparse,json,shutil
from pathlib import Path
from run_validation_cpmsim_monitors import audit
from run_validation_returning import sha
from test_z80pack_sysgen_install import session

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('baseline','output'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim');a=p.parse_args();w=a.output;w.mkdir(parents=True,exist_ok=False);report=json.loads((a.baseline/'report.json').read_text());original=a.baseline/report['image'];assert sha(original)==report['sha256'];disks=w/'disks';disks.mkdir();image=disks/'drivea.dsk';shutil.copy2(original,image);shutil.copy2(a.baseline/'diskdefs',w/'diskdefs');shutil.copy2(__file__,w/'executed-runner.py');prompt=b'A0>'
 steps=[(b'RSX LOAD ANSISCRN\r',prompt,30)]
 for name,program in [('ADM3A','ADMTST'),('VT52','VT52TST'),('ANSI','ANSITST')]:
  steps += [(f'RSX LOAD {name}\r'.encode(),prompt,30),(b'RSX LIST\r',prompt,30),(program.encode()+b'\r',b'Press a key to continue.',30)]
  count=3 if name=='ADM3A' else 2 if name=='VT52' else 1
  steps += [(b' ',b'Press a key to continue.',30)]*count
  if name=='ADM3A':steps += [(b' ',b'No ENTER is required.',30),(b'A:[]',b'ADMTST keyboard checks passed.',30)]
  else:steps += [(b' ',name.encode()+b' monitor exercise complete.',30)]
  steps += [(b'',prompt,30),(f'RSX UNLOAD {name}\r'.encode(),prompt,30)]
 steps += [(b'RSX UNLOAD ANSISCRN\r',prompt,30),(b'RSX LIST\r',b'TPA available: 53K',30),(b'',prompt,30),(b'BYE /Y\r',b'System halted',30)]
 trace=session(a.simulator,disks,steps,w/'transcript.bin')
 for name in ('ADM3A','VT52','ANSI'):assert name.encode()+b' : BDOS 255' in trace
 assert b'No MCON provider loaded' not in trace and b'No RSXs loaded' in trace and b'TPA available: 53K' in trace
 unchanged=audit(a.baseline,report,w,image)
 (w/'result.json').write_text(json.dumps({'status':'PASS','baseline_sha256':report['sha256'],'simulator_sha256':sha(a.simulator),'runner_sha256':sha(w/'executed-runner.py'),'unchanged_shipped_files':unchanged,'scope':'Single actual cpmsim session: ADM3A then VT52 then ANSI dedicated test completion with shared ANSISCRN retained between switches; complete unload/53K and file/filesystem audits. Not native switching or physical-terminal certification.'},indent=2)+'\n');print('PASS actual three-personality switching session',w)
if __name__=='__main__':main()
