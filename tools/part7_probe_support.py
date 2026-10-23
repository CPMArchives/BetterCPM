from __future__ import annotations
from pathlib import Path
import sys,shutil,re,json,subprocess,hashlib,os
base=Path(__file__).resolve().parents[1];root=Path(os.environ.get('P7_ROOT',str(base)))
sys.path.insert(0,str(root/'tools'))
from test_z80pack_sysgen_install import session
from build_ccp import assemble
from system_layout import LAYOUT as L
from fdf_format import select_fdf
from build_z80pack_image import DEFAULT_FORMAT
sim=Path(os.environ.get('BETTERCPM_ASSESSMENT_SIM','/tmp/bettercpm-assessment-part2-20261023/runtime-tools/cpmsim'))
fmt=select_fdf(root/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT)
out=root/'qualification';out.mkdir(exist_ok=True)
results=json.loads((out/'results.json').read_text()) if (out/'results.json').exists() else {}
def save(): (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
def case(name):
 w=out/name;(w/'disks').mkdir(parents=True,exist_ok=True)
 shutil.copy2(root/'assessment-media/diskdefs',w/'diskdefs')
 for c in 'abcd':shutil.copy2(root/'assessment-media/system.raw',w/'disks'/f'drive{c}.dsk')
 return w
def put(w,name,data,drive='a'):
 p=w/name;p.write_bytes(data)
 subprocess.run(['cpmcp','-f','bettercpm-default',str(w/'disks'/f'drive{drive}.dsk'),str(p),'0:'+name],cwd=w,check=True,capture_output=True)
 if name in ('FIT.COM','OVER.COM'):
  recovered=w/(name+'.readback')
  subprocess.run(['cpmcp','-f','bettercpm-default',str(w/'disks'/f'drive{drive}.dsk'),'0:'+name,str(recovered)],cwd=w,check=True,capture_output=True)
  assert recovered.read_bytes()==data
def asm(w,name,s):return assemble(Path.home()/'bin/z80asm','        ASEG\n        ORG 0100H\n'+s+'\n        END\n',w/(name+'.bin'),w/(name+'.lst'),0x100)
def run(w,commands,stem='transcript',initial=b'A0>_ '):
 steps=[(c.encode()+b'\r',b'A0>_ ',25) if isinstance(c,str) else c for c in commands]
 raw=session(sim,w/'disks',steps,w/(stem+'.bin'),initial_prompt=initial)
 t=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',raw.decode('ascii',errors='replace')).replace('\r','')
 (w/(stem+'.txt')).write_text(t)
 return t
def maps(t):
 t=re.sub(r'(?<!\n)([0-9A-F]{4}-[0-9A-F]{4} )',r'\n\1',t)
 t=t.replace('Maximum loadable COM:','\nMaximum loadable COM:')
 output=[]
 for b in t.split('BetterCP/M Memory Map')[1:]:
  b=b[:b.index(' bytes')+6]
  rows=[(int(h,16),int(l,16),int(n),owner) for h,l,n,owner in re.findall(r'([0-9A-F]{4})-([0-9A-F]{4}) +(\d+) ([^\n]+)',b)]
  assert rows[0][0]==65535 and rows[-1][:3]==(255,0,256)
  for i,(h,l,n,_) in enumerate(rows):
   assert h-l+1==n
   if i:assert rows[i-1][1]==h+1
  assert sum(x[2] for x in rows)==65536
  gate=next(x for x in rows if x[3]=='Dynamic CP/M gateway')
  maximum=int(re.search(r'Maximum loadable COM: (\d+)',b)[1]);assert maximum==(gate[1]-256)//128*128
  output.append({'maximum':maximum,'rows':rows})
 return output
