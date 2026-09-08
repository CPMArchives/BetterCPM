import sys,subprocess,json,shutil
from pathlib import Path
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'tools'))
from run_trs80_command import key_args,DEFAULT_EMULATOR
out=r/'build/compatibility/console-pause';out.mkdir(exist_ok=True)
for item,needle in [(63,'Function-2 scrolling-control stream'),(64,'Function-9 scrolling-control stream')]:
 w=out/str(item);w.mkdir(exist_ok=True);shutil.copy2(r/'build/compatibility/BetterCPM-Compatibility-Console.dmk',w/'a.dmk')
 args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(w/'a.dmk'),'-id','3500']+key_args(f'CONSTEST /{item:04d}\r')
 args+=['-iw',needle]+key_args('\x13')+['-id','100','-it','-id','100','-it']+key_args('X')+['-id','300','-it','-ix']
 try:subprocess.run(args,cwd=w,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=80,check=True)
 except subprocess.TimeoutExpired:print(item,'TIMEOUT',flush=True);continue
 screens=[]
 for p in sorted(w.glob('trs80-text-*.bin')):
  d=p.read_bytes()[:1920];screens.append('\n'.join(bytes(c&127 for c in d[i:i+80]).decode('ascii').rstrip() for i in range(0,1920,80)))
 (w/'screens.txt').write_text('\n\n--- SCREEN ---\n\n'.join(screens))
 good=len(screens)==3 and screens[0]==screens[1] and 'Do OBSERVED' not in screens[0] and 'Do OBSERVED' in screens[2]
 (w/'result.json').write_text(json.dumps({'item':f'{item:04d}','passed':good,'rule':'Two identical paused screens before resume; confirmation reached only after X.'},indent=2))
 print(item,good,flush=True)
