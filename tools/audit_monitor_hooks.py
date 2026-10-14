#!/usr/bin/env python3
"""Assemble the production BIOS hooks privately for lifecycle binding probes.

This never publishes images or installs a provider. Production RSX transaction
integration must precede binding a real monitor.
"""
from pathlib import Path
import json
import argparse
root=Path(__file__).resolve().parents[1]
from audit_monitor_memory import assemble
from system_layout import LAYOUT,expand_layout
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--assembler',type=Path,default=Path('/Users/nathanael/bin/z80asm'))
args=parser.parse_args()
source=(root/'src/bios/bios.mac').read_text()
# The multiplex candidate is now production source. Retain a reproducible
# isolated assembly for binding probes without reapplying dispatch transforms.
from audit_iobyte_routing import monitor_hooks
s=monitor_hooks(source)
out=root/'build/audit/monitor-efficiency/hooks-multiplex'
out.mkdir(parents=True,exist_ok=True)
for filename,p in [('biosplat.inc',root/'src/bios/biosplat.inc'),('m4cons.inc',root/'src/platform/trs80m4/m4cons.inc'),('m4scroll.inc',root/'src/platform/trs80m4/m4scroll.inc'),('reload.inc',root/'src/platform/trs80m4/reload.inc')]:
 (out/filename).write_text(expand_layout(p.read_text()))
data=assemble(s,'bios',LAYOUT['BIOS'],out,args.assembler)
rows=[dict(profile='multiplex',bytes=len(data),growth=len(data)-693,directory=str(out))]
print(json.dumps(rows,indent=2))
(root/'build/audit/monitor-efficiency/hooks.json').write_text(json.dumps(rows,indent=2)+'\n')
