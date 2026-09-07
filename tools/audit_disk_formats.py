#!/usr/bin/env python3
"""Audit all 112 definitions against the compiled BIOS and loaded FDF.RSX.

Only overlay fetch and disk reset are stubbed; no disk I/O is performed.
Acceptance is not a claim of compatibility with a physical drive.
"""
import sys,struct,json
from pathlib import Path
r=Path(__file__).resolve().parents[1]
from test_fdf_rsx import cpu_at
from test_disk_utilities import records
from system_layout import LAYOUT as L
rows=records()
for f in json.loads((r/'metadata/mm-builtin-formats.json').read_text())['formats']:
 p=f['parameters'];rows.append((f['name'],bytes([1])+struct.pack('<HBBBHHBBHH',*p[:10])+bytes((p[12],p[10],p[11],p[13]))+bytes(f['sector_ids']).ljust(32,b'\0')+bytes(12)))
accepted=[];rejected=[]
for name,bind in rows:
 c=cpu_at(0x8000)
 for f,a in [('bios/bios',L['BIOS']),('system/disk',L['DISK']),('system/config',L['CONFIG']),('system/tables',L['TABLES'])]:
  b=(r/'build'/f'{f}.bin').read_bytes();c.mem[a:a+len(b)]=b
 c.mem[L['BIOS']+57:L['BIOS']+59]=bytes([0xaf,0xc9])
 c.mem[5:8]=bytes([0xc3,4,0x80])
 c.mem[0x9000:0x9050]=bytes([1,1])+bind[1:]+bytes(15)
 c.de=0x9000;c.b=4
 c.run(L['DISK'],limit=30000)
 (rejected if c.a else accepted).append((name,c.a))
assert len(rows)==112
assert len(accepted)==107 and len(rejected)==5, (accepted,rejected)
print('Compiled BIOS validator: ACCEPT',len(accepted),'REJECT',len(rejected))
print(*rejected,sep='\n')
