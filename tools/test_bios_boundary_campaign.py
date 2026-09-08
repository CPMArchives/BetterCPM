import sys,subprocess,shutil,json
from pathlib import Path
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'tools'))
from run_trs80_command import key_args,DEFAULT_EMULATOR
root=r/'build/compatibility/bios-boundary-repeat';root.mkdir(exist_ok=True)
blank=r/'build/compatibility/run-20260907-223215/d.dmk'
for item in [453,457]:
 w=root/str(item);w.mkdir(exist_ok=True)
 shutil.copy2(r/'build/compatibility/BetterCPM-Compatibility-Boundary.dmk',w/'a.dmk');shutil.copy2(blank,w/'d.dmk')
 args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(w/'a.dmk'),'-d3',str(w/'d.dmk'),'-id','3500']
 if item==453:args+=key_args('SETSYS\r')+['-iw','D SYSTEM READY','-id','6000','-it']
 args+=key_args(f'BIOSTEST /{item:04d}\r')+['-iw','Enter its configured drive letter','-it']+key_args('D')+['-iw','Continue (Y/N)?','-it']+key_args('Y')
 if item==457:
  args+=['-iw','0457 fault stage:','-it','-im','wp','3','on']+key_args('Y')+['-iw','Make the scratch disk writable again','-it','-im','wp','3','off']+key_args('Y')
 args+=['-id','6000','-it','-ix']
 try:subprocess.run(args,cwd=w,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=240,check=True)
 except subprocess.TimeoutExpired:print(item,'TIMEOUT',flush=True)
 screens=[]
 for p in sorted(w.glob('trs80-text-*.bin')):
  d=p.read_bytes()[:1920];screens.append('\n'.join(bytes(c&127 for c in d[i:i+80]).decode('ascii').rstrip() for i in range(0,1920,80)))
 (w/'screens.txt').write_text('\n\n--- SCREEN ---\n\n'.join(screens));print(item,screens[-1] if screens else 'NO SCREEN',flush=True)
