#!/usr/bin/env python3
"""REN name-field compatibility: raw editor events and full rename workflows."""
import hashlib,json
from pathlib import Path
from build_ccp import assemble
from build_ren import expanded_source
from test_bios import Z80
from test_ren_core import ROOT,run
from test_utility_versions import address
OUT=ROOT/'build/ren-shared-name'


def module_checks(image,listing):
 at=lambda n:address(listing,n)
 cases=0
 # Real linked engine, caller-owned bytes guarded on both ends, across limits.
 for cap in (1,31,255):
  raw,ls=MODULES[cap]
  positions={n:address(ls,n) for n in ('UA_BUF','UA_INIT','UA_KEY','UA_LEN','UA_FULL')}
  addr=positions.__getitem__
  for prefix in (b'',b'X'*cap,b'X'*(cap+1),b'X'*(cap+1)+b'\x08'):
   for key in range(256):
    # Isolated shared module supports 255-byte capacity; REN itself uses 31.
    c=Z80(b'');c.mem[256:256+len(raw)]=raw
    guard=addr('UA_BUF');c.mem[guard-1]=0xa5;c.mem[guard+cap]=0x5a
    c.a=cap;c.run(addr('UA_INIT'));assert c.a==0 and not c.carry
    expected=bytearray();full=0
    for ch in prefix+bytes([key]):
     if ch==3:event=2
     elif ch==13:event=1
     elif ch in (8,127):
      if expected:expected.pop()
      event=0
     elif ch==21:expected.clear();full=0;event=0
     elif len(expected)==cap:full=1;event=5
     else:expected.append(ch);event=0
     c.a=ch;c.run(addr('UA_KEY'))
     assert (c.a,c.carry)==(event,False),(cap,key,ch,c.a,event)
     assert c.mem[addr('UA_LEN')]==len(expected) and c.mem[addr('UA_FULL')]==full
     assert bytes(c.mem[guard:guard+len(expected)])==bytes(expected)
     assert c.mem[guard-1]==0xa5 and c.mem[guard+cap]==0x5a
    cases+=1
 # Actual REN binding aliases its existing buffer/state, with no extra text area.
 c=Z80(b'');c.mem[256:256+len(image)]=image;c.a=31;c.run(at('UA_INIT'))
 for ch in b'X'*32+b'\x08':c.a=ch;c.run(at('UA_KEY'))
 assert c.mem[at('R_ILEN')]==30 and c.mem[at('R_IFULL')]==1
 c.a=0;c.run(at('UA_INIT'));assert c.a==7 and not c.carry
 assert c.mem[at('R_ILEN')]==30 and c.mem[at('R_IFULL')]==1
 c.a=31;c.run(at('UA_INIT'));assert c.a==0 and not c.carry
 assert c.mem[at('R_ILEN')]==0 and c.mem[at('R_IFULL')]==0
 return cases

MODULES={}
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 events=(ROOT/'src/utilities/common/ui/events.inc').read_text()
 engine=(ROOT/'src/utilities/common/ui/append.inc').read_text()
 for cap in (1,31,255):
  source='        ASEG\n        ORG 0100H\n'+events+engine+f'\nUA_MAX: DB 0\nUA_LEN: DB 0\nUA_FULL: DB 0\n DB 0\nUA_BUF: DS {cap}\n DB 0\n END\n'
  raw=assemble(Path.home()/'bin/z80asm',source,OUT/f'append-{cap}.bin',OUT/f'append-{cap}.lst',256)
  MODULES[cap]=(raw,(OUT/f'append-{cap}.lst').read_text())
 image=(ROOT/'build/utilities/REN.COM').read_bytes();listing=(ROOT/'build/utilities/ren.lst').read_text()
 event_cases=module_checks(image,listing)
 source=expanded_source().replace('        CSEG\n','        ASEG\n').replace('        .PHASE  0103H\n','        ORG 0103H\n').replace('        .DEPHASE\n','')
 start=source.index('        LD A,31\n        CALL UA_INIT',source.index('R_NEWPROM:'));end=source.index('R_INEND:',start)
 source=source[:start]+(ROOT/'tools/fixtures/ren-legacy-name.inc').read_text()+source[end:]
 (OUT/'legacy-expanded.mac').write_text(source)
 baseline=b'\xc3\x03\x01'+assemble(Path.home()/'bin/z80asm',source,OUT/'legacy.bin',OUT/'legacy.lst',0x103)
 cases=[('byte-'+str(k),'N'+chr(k)+'\rS\rS') for k in range(256)]
 cases += [
  ('lowercase','Nnew.txt\r'),('backspace','Nnew.txz\x08t\r'),('del','Nnew.txz\x7ft\r'),
  ('clear','Nbad*name\x15new.txt\r'),('blank','N\rS'),('cancel','N\x03'),
  ('overflow','N'+'X'*32+'\rnew.txt\r'),
  ('sticky-overflow','N'+'X'*32+'\x08'*28+'\rnew.txt\r'),
  ('overflow-clear','N'+'X'*32+'\x15new.txt\r'),
  ('invalid-retry','Nbad*.txt\rnew.txt\r'),('esc-not-cancel','N\x1b\rnew.txt\r'),
  ('empty-backspace','N\x08\x7fnew.txt\r')]
 for name,responses in cases:
  outcomes=[]
  for binary in (baseline,image):
   files={(1,1,b'FOO     DOC'):4,(1,1,b'FOO     TXT'):0}
   mutations,text=run('B1:FOO.DOC FOO.TXT',files,responses,image=binary)
   outcomes.append((mutations,text,files))
  assert outcomes[0]==outcomes[1],(name,outcomes)
 (OUT/'results.json').write_text(json.dumps({'result':'PASS','module_cases':event_cases,'differential_workflows':len(cases),'ren_sha256':hashlib.sha256(image).hexdigest(),'bytes':len(image)},indent=2)+'\n')
 print(f'PASS: {event_cases} guarded append-engine sequences and {len(cases)} complete legacy name-field comparisons')
if __name__=='__main__':main()
