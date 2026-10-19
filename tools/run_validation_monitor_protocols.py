#!/usr/bin/env python3
"""Retain bounded monitor protocol checks against hash-matched release carriers."""
import argparse,contextlib,hashlib,importlib,io,json,shutil,sys
from pathlib import Path

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--cpmsim-build',type=Path,required=True);p.add_argument('--model4-build',type=Path,required=True)
 p.add_argument('--model4-baseline',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 report=json.loads((a.baseline/'report.json').read_text());included={x['name']:x['sha256'] for x in report['included']}
 included.update({x['name']:x['sha256'] for x in json.loads((a.model4_baseline/'report.json').read_text())['included']})
 carriers={'ADM3A.RSX':'monitor-development','VT52.RSX':'vt52-development','ANSI.RSX':'ansi-development','M4SCRN.RSX':'screen-backends','ANSISCRN.RSX':'screen-backends'}
 matched={}
 for name,folder in carriers.items():
  f=a.cpmsim_build/'build'/folder/name;assert sha(f)==included[name],name;matched[name]=sha(f)
  stem=name[:-4] if folder=='screen-backends' else name[:-4].lower()
  code=(f.parent/(stem+'.bin')).read_bytes();assert f.read_bytes()[512:512+len(code)]==code,name
 import test_screen_backends as backend
 backend.ROOT=a.cpmsim_build;backend.OUT=a.cpmsim_build/'build/screen-backends'
 original=backend.fixture
 def fixture(name,base,**kwargs):
  kwargs['model4_bios']=a.model4_build/'build/bios'
  kwargs['cpmsim_bios']=a.cpmsim_build/'build/z80pack'
  return original(name,base,**kwargs)
 backend.fixture=fixture
 results={}
 for name in ['test_adm3a_portable','test_vt52_rendering','test_ansi_portable']:
  mod=importlib.import_module(name);mod.ROOT=a.cpmsim_build
  if name=='test_vt52_rendering':mod.OUT=a.cpmsim_build/'build/vt52-development'
  source=Path(mod.__file__);shutil.copy2(source,a.output/source.name)
  log=io.StringIO();sys.argv=[name]
  with contextlib.redirect_stdout(log):
   if name=='test_ansi_portable':mod.main(production=True)
   else:mod.main()
  (a.output/(name+'.log')).write_text(log.getvalue());results[name]={'status':'PASS','source_sha256':sha(source)}
 from test_vt52_foundation import symbols
 bells={}
 for name,folder,stem,label in [('ADM3A','monitor-development','adm3a','AM_ENTRY'),('VT52','vt52-development','vt52','VT_ENTRY'),('ANSI','ansi-development','ansi','AN_ENTRY')]:
  cpu,old,cells,wire=fixture('ANSISCRN',0x6000)
  syms=backend.load(cpu,a.cpmsim_build/'build'/folder,stem,0x7000)
  cpu.setword(0x7000+12,cpu.backend_entry)
  entry=0x7000+syms[label]-0x8000
  cpu.a=4;cpu.run(entry,limit=300000);wire.clear()
  cpu.a=0;cpu.c=7;cpu.run(entry,limit=300000)
  assert bytes(wire)==b'\x07',(name,wire)
  bells[name]='07'
 results['host_bell_wire']={'status':'PASS','bytes':bells}
 shutil.copy2(__file__,a.output/'executed-runner.py')
 (a.output/'result.json').write_text(json.dumps({'status':'PASS','matched_release_carriers':matched,'tests':results,'runner_sha256':sha(Path(__file__)),'scope':'Assembled production personalities through relocated Model 4 and ANSI-host backends; CPU-model and software-terminal assertions, not native execution or physical-terminal observation.'},indent=2)+'\n')
 print('PASS bounded production monitor protocol checks',a.output)
if __name__=='__main__':main()
