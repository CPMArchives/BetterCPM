#!/usr/bin/env python3
"""MOUNT and R/W regression on real BetterCP/M with a full-size FDF image."""
import argparse,sys,shutil,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_z80pack_sysgen_install import session
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--baseline',type=Path,required=True)
parser.add_argument('--simulator',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();a=args.baseline.resolve();w=args.output.resolve()
d=w/'disks';d.mkdir(parents=True,exist_ok=False)
image=a/json.loads((a/'report.json').read_text())['image']
before=hashlib.sha256(image.read_bytes()).hexdigest()
shutil.copy2(image,d/'drivea.dsk')
for letter in 'bcd':shutil.copy2(a/'work-image',d/('drive'+letter+'.dsk'))
shutil.copy2(a/'work-image',w/'New Image.dsk');(w/'Input.txt').write_bytes(b'Host transfer with MOUNT\r\n')
commands=[]
def cmd(s,expected=b'A0>_ '):commands.append((s.encode()+b'\r',expected,30))
for s in ['MOUNT /VER','R /VER','W /VER','MOUNT /U','MOUNT /L [A,B]:','MOUNT B: "New Image.dsk"','DIR B:','R Input.txt B:PROBE.TXT','W B:PROBE.TXT Output.txt'] :cmd(s)
cmd('MOUNT /U [A,B]:',b'[y/N] ');commands.append((b'n',b'A0>_ ',30))
for s in ['MOUNT /L B:','DIR B:','MOUNT /U B:','MOUNT /L B:','MOUNT B: "New Image.dsk"','TYPE B:PROBE.TXT']:cmd(s)
cmd('BYE /Y',b'System halted')
text=session(args.simulator.resolve(),d,commands,w/'transcript.txt')
assert b'Operation cancelled. No changes made.' in text
assert b'B: empty' in text
assert b'R 1.0 (005-dev)' in text and b'W 1.0 (005-dev)' in text
assert b'Host transfer with MOUNT' in text
assert (w/'Output.txt').read_bytes()==(w/'Input.txt').read_bytes()
assert b'BDOS Error' not in text and b'Disk R/O' not in text and b'Cannot open' not in text
assert hashlib.sha256(image.read_bytes()).hexdigest()==before
report={'status':'PASS','source_commit':json.loads((a/'report.json').read_text())['source']['revision'],'system_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'transcript_sha256':hashlib.sha256(text).hexdigest(),'scope':'Actual BetterCP/M System disk: MOUNT help/version, explicit selector errors, live replacement, listing, A: cancel, eject/reinsert, directory reads, and R/W transfer on mounted image.'}
(w/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
