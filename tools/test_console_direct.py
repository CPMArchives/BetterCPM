import sys,subprocess,shutil,json
from pathlib import Path
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'tools'))
from run_trs80_command import key_args,DEFAULT_EMULATOR
w=r/'build/compatibility/console-pause/78';w.mkdir(exist_ok=True);shutil.copy2(r/'build/compatibility/BetterCPM-Compatibility-Console.dmk',w/'a.dmk')
a=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(w/'a.dmk'),'-id','3500']+key_args('CONSTEST /0078\r')+['-iw','Press any key to start the test:']+key_args('Z')+['-id','2','-it']+key_args('\x13')+['-id','300','-it','-ix']
subprocess.run(a,cwd=w,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=180,check=True)
s=[]
for p in sorted(w.glob('trs80-text-*.bin')):
 d=p.read_bytes()[:1920];s.append('\n'.join(bytes(c&127 for c in d[i:i+80]).decode('ascii').rstrip() for i in range(0,1920,80)))
(w/'screens.txt').write_text('\n\n--- SCREEN ---\n\n'.join(s))
good=len(s)==2 and 'Do OBSERVED' not in s[0] and 'Do OBSERVED' in s[1] and '...' in s[0]
(w/'result.json').write_text(json.dumps({'item':'0078','passed':good,'rule':'Inject Ctrl-S during dots; stream completes without a resume key.'},indent=2));print(good)
