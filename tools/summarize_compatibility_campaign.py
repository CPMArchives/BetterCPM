#!/usr/bin/env python3
"""Merge recorded suite rows and explicitly reviewed external verdicts.

Historical failures are retained unless a later executed result supersedes them.
Not-run rows never displace an executed result. This is a development inventory,
not a certification report.
"""
import json,csv,re
from pathlib import Path
r=Path(__file__).resolve().parents[1]; b=r/'build/compatibility'
c=list(csv.DictReader(open(r.parent/'cpm-compatibility/suite/design/case-to-executable-catalog.tsv'),delimiter='\t'))
rows={x['item']:x for x in json.loads((b/'ledger-results.json').read_text())}
for run in sorted(b.glob('run-*')):
 if run.name<'run-20260907-211115':continue
 for p in run.glob('*/rows.txt'):
  for line in p.read_text().splitlines():
   m=re.match(r'^(\d{4})\s+([PFO-])\s+([RNXS])\s+(.*)',line)
   if m and (m[2] in 'PFO' or m[1] not in rows):rows[m[1]]={'item':m[1],'status':m[2],'class':m[3],'detail':m[4],'evidence':str(p.relative_to(r))}
 for p in run.glob('*/screens.txt'):
  for m in re.finditer(r'LEDGER (\d{4})\n(?:(?!END_CASE).)*?RESULT (PASS|FAIL)\n(?:(?!END_CASE).)*?END_CASE',p.read_text(),re.S):
   rows[m[1]]={'item':m[1],'status':{'PASS':'P','FAIL':'F'}[m[2]],'detail':'Structured case report '+m[2],'evidence':str(p.relative_to(r))}
for i,v in json.loads((b/'fix-validation/fixed-items.json').read_text()).items():
 if i not in rows:rows[i]={'item':i,'status':'P','detail':'Validated repair','evidence':v['evidence']}
manual=b/'campaign-manual.json'
if manual.exists():
 for i,v in json.loads(manual.read_text()).items():
  rows[i]={'item':i,'status':v['result'],'detail':v['detail'],'evidence':v['evidence']}
full=[dict(x,**{'result':rows.get(x['ledger_entry'],{}).get('status','UNRECORDED'),'evidence':rows.get(x['ledger_entry'],{}).get('evidence',''),'detail':rows.get(x['ledger_entry'],{}).get('detail','')}) for x in c]
(b/'campaign-ledger.json').write_text(json.dumps(full,indent=2)+'\n')
pending=[x for x in full if x['classification']=='REQUIRED' and x['result']!='P']
from collections import Counter
print('Required:',Counter(x['result'] for x in full if x['classification']=='REQUIRED'))
print('Remaining:',len(pending))
(b/'campaign-pending.tsv').write_text('item\tutility\tresult\trequirement\n'+''.join(f"{x['ledger_entry']}\t{x['executable']}\t{x['result']}\t{x['requirement']}\n" for x in pending))
