#!/usr/bin/env python3
"""SYSGEN destination KEY compatibility and confirmation-context isolation."""
import hashlib,json
from pathlib import Path
from test_bios import Z80
from test_utility_versions import address
ROOT=Path(__file__).resolve().parents[1]
def main():
 image=(ROOT/'build/utilities/SYSGEN.COM').read_bytes()
 listing=(ROOT/'build/utilities/sysgen.lst').read_text();at=lambda n:address(listing,n)
 def invoke(entry,keys,c=None):
  if c is None:
   c=Z80(b'');c.mem[256:256+len(image)]=image;c.mem[5:8]=b'\xdb\xf4\xc9'
  pending=list(keys);reads=[]
  def io(port):
   assert port&255==244 and c.c==6 and c.e==255 and pending
   value=pending.pop(0);reads.append(value)
   c.bc=0xbcbc;c.de=0xdede;c.hl=0xeeee;c.ix=0xaaaa
   return value
  c.port_read=io;sp=c.sp;c.run(at(entry),limit=100000);assert c.sp==sp
  return c,(c.a,pending,reads)
 for key in range(256):
  _,old=invoke('KEY',bytes([key])+b'B!')
  c,new=invoke('SG_DRIVE',bytes([key])+b'B!');assert new==old,(key,old,new)
  assert c.word(at('UC_LIST'))==at('UY_LIST') and c.mem[at('UC_COUNT')]==2
  assert c.mem[at('UC_DEF')]==0 and c.mem[at('SG_MODE')]==0
 c=None
 for entry,key,value in [('SG_DRIVE',b'b',66),('SG_ASK',b'N',78),('SG_DRIVE',b'Y',89),('SG_ASK',b'X',0),('SG_DRIVE',b'\x03',3),('SG_ASK',b'Y',89)]:
  c,r=invoke(entry,key+b'!',c);assert r[0]==value and r[1]==[33],r
 c=Z80(b'');c.mem[256:256+len(image)]=image;c.mem[5:8]=b'\xdb\xf4\xc9';c.mem[at('SG_LIST')]=0;c.mem[at('SG_RAW')]=66
 c,r=invoke('SG_DRIVE',b'',c);assert r==(3,[],[])
 c,r=invoke('SG_ASK',b'N!',c);assert r[0]==78
 source=(ROOT/'src/utilities/sysgen.mac').read_text()
 assert 'CALL PUTS\n        CALL SG_DRIVE\n        CP 3\n        JP Z,0' in source
 report={'result':'PASS','key_comparisons':256,'context_cases':6,'malformed_selection_cases':1,'bytes':len(image),'sha256':hashlib.sha256(image).hexdigest()}
 (ROOT/'build/utilities/sysgen-shared-destination.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
if __name__=='__main__':main()
