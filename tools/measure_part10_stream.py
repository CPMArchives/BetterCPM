#!/usr/bin/env python3
"""Compare successful CRLOAD runner dispatch counts and fixture stack use.

Counts functional-runner dispatches, not Z80 T-states or wall time. The runner
executes block instructions such as LDIR in one dispatch. Interrupts and
physical disk latency are absent. The same read adapter is used.
"""
from pathlib import Path
import argparse,inspect,json,sys,textwrap
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('baseline',type=Path);p.add_argument('reference',type=Path);p.add_argument('experiment',type=Path);a=p.parse_args()
sys.path.insert(0,str(a.baseline.resolve()/'tools'))
from test_bios import Z80
source=textwrap.dedent(inspect.getsource(Z80.run)).replace('for _ in range(limit):','self.instructions = 0\n    for _ in range(limit):\n        self.instructions += 1')
ns=dict(Z80.run.__globals__);exec(compile(source,'counted-z80-runner','exec'),ns);Z80.run=ns['run']
original_push=Z80.push
def push(self,v):
 original_push(self,v);self.minimum_sp=min(getattr(self,'minimum_sp',65535),self.sp)
Z80.push=push
root=Path(__file__).resolve().parents[1];results={}
for label,script,stage in [('full_staging','qualify_part9_stage.py',a.reference),('streaming','qualify_part10_stream.py',a.experiment)]:
 sys.argv=[script,str(a.baseline),str(stage)]
 prelude=(root/'tools'/script).read_text().split('for row in rows:',1)[0]
 context={'__name__':'measurement_fixture','__file__':str(root/'tools'/script)}
 exec(compile(prelude,script,'exec'),context)
 results[label]={}
 for name in ('ccp.rlm','RCP.CPX','HELLO.CPX'):
  c=context['run']((stage/name).read_bytes(),name);assert c.a==0
  results[label][name]={'runner_dispatches':c.instructions,'fixture_stack_bytes':4096-c.minimum_sp,'minimum_sp':c.minimum_sp}
for name in results['streaming']:
 results['streaming'][name]['dispatch_ratio']=round(results['streaming'][name]['runner_dispatches']/results['full_staging'][name]['runner_dispatches'],4)
(a.experiment/'instruction-measurements.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
