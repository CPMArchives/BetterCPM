#!/usr/bin/env python3
"""Exercise the supplied P2DOS carrier on private copies of prepared System media."""
from pathlib import Path
import argparse,shutil,json,hashlib,subprocess
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--image-dir',type=Path,required=True)
parser.add_argument('--simulator',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
repo=Path(__file__).resolve().parents[1]
from test_z80pack_clock_lifecycle import PROBE
from build_ccp import assemble
from test_z80pack_sysgen_install import session
work=args.output.resolve();work.mkdir(parents=True,exist_ok=False);disks=work/'disks';disks.mkdir()
image=args.image_dir.resolve();report=json.loads((image/'report.json').read_text());source=image/report['image'];before=hashlib.sha256(source.read_bytes()).hexdigest()
assert before==report['sha256'] and report['target']=='z80pack'
p2dos=next(x for x in report['included'] if x['name']=='P2DOS.RSX')
shutil.copy2(source,disks/'drivea.dsk')
for name in ['driveb.dsk','drivec.dsk','drived.dsk']:shutil.copy2(image/'work-image',disks/name)
shutil.copy2(image/'diskdefs',work/'diskdefs')
readback=work/'P2DOS.readback'
subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disks/'drivea.dsk'),'0:P2DOS.RSX',str(readback)],cwd=work,check=True)
data=readback.read_bytes();body=data[:p2dos['bytes']]
assert hashlib.sha256(body).hexdigest()==p2dos['sha256']
assert set(data[p2dos['bytes']:]) <= {0,26}
(work/'CLKPROB.MAC').write_text(PROBE);probe=work/'CLKPROB.COM';assemble(Path.home()/'bin/z80asm',PROBE,probe,work/'CLKPROB.lst',0x100)
subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disks/'driveb.dsk'),str(probe),'0:CLKPROB.COM'],cwd=work,check=True)
commands=[('B:CLKPROB 2','abi'),('RSX LOAD ZPRTC',None),('RSX LOAD P2DOS',None),('B:CLKPROB 0','abi'),('TIME',None),('B:CLKPROB 0','abi'),('RSX UNLOAD ZPRTC',None),('B:CLKPROB 1','abi'),('RSX LIST','resident'),('RSX LOAD ZPRTC',None),('B:CLKPROB 0','abi'),('RSX UNLOAD P2DOS',None),('B:CLKPROB 2','abi')]
sim=args.simulator.resolve()
out=session(sim,disks,[(c.encode()+b'\r',b'A0>_ ',20) for c,_ in commands],work/'transcript.txt')
cursor=0
for c,kind in commands:
 start=out.index(c.encode(),cursor);end=out.index(b'A0>_ ',start);block=out[start:end];cursor=end
 if kind=='abi':assert b'CLOCK ABI PASS' in block and b'CLOCK ABI FAIL' not in block,(c,block)
 if kind=='resident':assert b'P2DOS' in block and b'ZPRTC' not in block,block
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
summary={'status':'PASS','input_image_sha256':before,'p2dos_sha256':p2dos['sha256'],'probe_sha256':hashlib.sha256(probe.read_bytes()).hexdigest(),'simulator_sha256':hashlib.sha256(sim.read_bytes()).hexdigest(),'simulator_mode':'ordinary RAM mode; record the selected runtime/qualification environment separately','commands':commands,'scope':'Supplied A0 P2DOS: absent/loaded/provider-unloaded/replaced/unloaded results; GET/SET A/HL, DE/SP/IX/IY and failed-GET atomicity. Transient JP0 returns exercise warm reconstruction. Private disks only; not Model 4 runtime or public-package acceptance.'}
(work/'results.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
