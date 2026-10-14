#!/usr/bin/env python3
"""Isolated size probe for scheduler detach and prepared publisher rebinding.
Run audit_monitor_hooks.py first. This does not implement metadata selection or
production transactions; it only checks that these two insertion points fit.
"""
import sys,re,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from build_rsx_runtime_overlays import source
from audit_monitor_memory import assemble
from system_layout import LAYOUT
out=root/'build/audit/monitor-efficiency/hooks-multiplex'
assemble(source('rsxmover.mac','RMBASE',0x7000),'mover-fixture',0x7000,out,Path('/Users/nathanael/bin/z80asm'))
s=source('rsxsched.mac','RSBASE',LAYOUT['CONFIG']+0x120)
d=assemble(s,'scheduler',LAYOUT['CONFIG']+0x120,out,Path('/Users/nathanael/bin/z80asm'))
assert len(d)<=0x310-0x120
fixture_source=re.sub(r'^RSBASE\s+EQU\s+.*$', 'RSBASE          EQU     07800H', s, flags=re.M)
assemble(fixture_source,'scheduler-fixture',0x7800,out,Path('/Users/nathanael/bin/z80asm'))
ls=(out/'bios.lst').read_text()
m=re.search(r'^([0-9a-f]{4})\s+.*\bMP_MON:',ls,re.M|re.I);assert m
cell=int(m[1],16)
s=source('r3pst.mac','RTBASE',LAYOUT['CONFIG']+0x38f)
d2=assemble(s,'publisher',LAYOUT['CONFIG']+0x38f,out,Path('/Users/nathanael/bin/z80asm'))
report={'scheduler_bytes':len(d),'scheduler_region_capacity':496,'publisher_bytes':len(d2),'commit_bytes_unchanged':1007,'commit_prefix_capacity':1012,'note':'Assembly size only; request offset 35 and transaction integration are prototypes.'}
(out/'binding-sizes.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
