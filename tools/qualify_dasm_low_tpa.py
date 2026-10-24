#!/usr/bin/env python3
"""Native startup refusal at a real lowered BDOS vector, with resident canary."""
import argparse,json
from pathlib import Path
from build_dasm import build
from dasm_native import campaign,DEFAULT_SYSTEM
from dasm_script_harness import scripted

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--system',type=Path,default=DEFAULT_SYSTEM);p.add_argument('--utilities',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--platforms',nargs='+',default=['z80pack','trs80gp']);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 image=build(Path.home()/'bin/z80asm',a.output/'cross');report={'scope':'native insufficient TPA refusal; normal/reduced successful capacity covered by corpus','platforms':{}}
 for platform in a.platforms:
  files={'QLOW.COM':scripted(image,['G'],ceiling=0xb100)}
  log,out=campaign(platform,files,['QLOW'],a.output/platform,system=a.system,utilities=a.utilities,utility_files={'DASM.COM':image})
  assert b'insufficient' in log.lower() and b'B100' in log and b'B200' in log,log[-2000:]
  assert b'DASM RESIDENT CANARY PASS' in log and b'DASM RESIDENT CANARY FAIL' not in log
  report['platforms'][platform]={'status':'PASS','active_ceiling':'B100','required_ceiling':'B200','resident_canary':True,'execution_report':platform+'/execution.json'}
  (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',platform,'insufficient TPA startup refusal and resident canary',flush=True)
if __name__=='__main__':main()
