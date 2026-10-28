#!/usr/bin/env python3
"""Check corrected quick references from exact packaged BetterCP/M disks."""
from pathlib import Path
import argparse,hashlib,json,shutil
from test_z80pack_sysgen_install import session
from utility_help import text
from build_dump import version_text
ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--image-dir',type=Path,required=True);p.add_argument('--utilities',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
 a=p.parse_args();w=a.report.resolve();w.mkdir(parents=True,exist_ok=False)
 shutil.copytree(a.image_dir/'disks',w/'disks');shutil.copy2(a.image_dir/'diskdefs',w/'diskdefs')
 for letter,name in [('b','BetterCPM-Utilities-z80pack-332K.dsk'),('c','BetterCPM-NOAH-z80pack-332K.dsk')]:
  (w/f'disks/drive{letter}.dsk').write_bytes((a.utilities/name).read_bytes())
 before={f:sha(f.read_bytes()) for f in (w/'disks').glob('drive*.dsk')}
 steps=[]
 for name in ('DUMP','DASM','DSYM','TED'):
  for tail in ('/HELP','/VER /HELP /BOGUS','/VER'):
   steps.append((f'B0:{name} {tail}\r'.encode(),b'A0>_ ',20))
 output=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',w/'disks',steps,w/'transcript.txt').decode()
 for name in ('DUMP','DASM','DSYM','TED'):
  expected=text(name,version_text().splitlines()[0] if name=='DUMP' else None)
  assert output.count(expected)==2,(name,output)
 assert all(sha(f.read_bytes())==h for f,h in before.items())
 record={'status':'PASS','scope':'Exact packaged HELP/VER and HELP precedence for DUMP/DASM/DSYM/TED; every mounted disk unchanged','binaries':{name:sha((ROOT/f'build/utilities/{name}.COM').read_bytes()) for name in ('DUMP','DASM','DSYM','TED')},'volumes':{f.name:h for f,h in before.items()}}
 (w/'evidence.json').write_text(json.dumps(record,indent=2)+'\n')
 print('Packaged HELP/VER, query precedence and mounted-media immutability: PASS')

if __name__=='__main__':main()
