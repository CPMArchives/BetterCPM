#!/usr/bin/env python3
"""Compare complete REN workflows with retained pre-migration choice reads."""
import hashlib,json
from pathlib import Path
from build_ccp import assemble
from build_ren import expanded_source
from test_ren_core import run,ROOT
OUT=ROOT/'build/ren-shared-input'

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 source=expanded_source().replace('        CSEG\n','        ASEG\n').replace('        .PHASE  0103H\n','        ORG 0103H\n').replace('        .DEPHASE\n','')
 legacy=json.loads((ROOT/'tools/fixtures/ren-legacy-choice.json').read_text())
 for call,name in [('RU_YN','confirmation'),('RU_COL','collision'),('RU_FAIL','recovery')]:
  anchor='        CALL '+call+'\n';assert source.count(anchor)==1
  source=source.replace(anchor,legacy[name]+'\n')
 (OUT/'legacy-expanded.mac').write_text(source)
 baseline=b'\xc3\x03\x01'+assemble(Path.home()/'bin/z80asm',source,OUT/'legacy.bin',OUT/'legacy.lst',0x103)
 current=(ROOT/'build/utilities/REN.COM').read_bytes()
 listing=(ROOT/'build/utilities/ren.lst').read_text()
 import re
 for symbol in ('EDITNEW','UP_RUN','UW_LEFT','UR_DRAW'):
  assert not re.search(r'\b'+symbol+r':',listing),symbol
 name=(1,1,b'FOO     DOC');target=(1,1,b'FOO     TXT')
 count=0
 for key in range(256):
  for kind in ('confirmation','collision','recovery'):
   files={name:0};tail='B1:FOO.DOC FOO.TXT';options={}
   if kind=='confirmation':tail='/C '+tail;fallback='N'
   elif kind=='collision':files[target]=4;fallback='S\rS'
   else:options['rename_failures']={name:2};fallback='SS'
   response=chr(key)+fallback
   outcomes=[]
   for image in (baseline,current):
    fixture=files.copy();kw={k:v.copy() if isinstance(v,dict) else v for k,v in options.items()}
    changes,text=run(tail,fixture,response,image=image,**kw)
    outcomes.append((changes,text,fixture))
   assert outcomes[0]==outcomes[1],(key,kind,outcomes)
   count+=1
 (OUT/'results.json').write_text(json.dumps({'result':'PASS','differential_workflows':count,'ren_sha256':hashlib.sha256(current).hexdigest(),'bytes':len(current)},indent=2)+'\n')
 print(f'PASS: {count} complete REN choice workflows match retained legacy behavior')
if __name__=='__main__':main()
