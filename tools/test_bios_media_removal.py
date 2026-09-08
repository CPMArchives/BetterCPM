#!/usr/bin/env python3
"""Read a real scratch sector, eject media, and read another physical sector."""
from pathlib import Path
import subprocess,shutil,time,json
from run_trs80_command import key_args,DEFAULT_EMULATOR
R=Path(__file__).resolve().parents[1];W=R/'build/compatibility'/time.strftime('readerr-%Y%m%d-%H%M%S');W.mkdir()
shutil.copy2(R/'build/compatibility/probes/BetterCPM-Conformance-Probes.dmk',W/'a.dmk')
shutil.copy2(R/'build/compatibility/run-20260908-000734/d.dmk',W/'d.dmk')
a=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(W/'a.dmk'),'-d3',str(W/'d.dmk'),'-id','3500']+key_args('READERR\r')+['-iw','EJECT SCRATCH D','-it','-im','eject','3','1']+key_args('Y')+['-id','6000','-it','-ix']
subprocess.run(a,cwd=W,timeout=180,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
s=[]
for p in sorted(W.glob('trs80-text-*.bin')):
 d=p.read_bytes()[:1920];s.append('\n'.join(bytes(x&127 for x in d[i:i+80]).decode('ascii').rstrip() for i in range(0,1920,80)))
(W/'screens.txt').write_text('\n\n--- SCREEN ---\n\n'.join(s))
(W/'result.json').write_text(json.dumps({'passed':'0390 P R' in s[-1],'fixture':'Read sector 0 with media, eject D, read uncached logical sector 8'},indent=2))
print(W);print(s[-1])
