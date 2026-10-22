#!/usr/bin/env python3
"""CONFIG menu byte compatibility, strict caller approvals and malformed state."""
import hashlib,json
from pathlib import Path
from build_config import expanded_source
from build_ccp import assemble
from test_bios import Z80
from test_utility_versions import address
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/config-choice-input'
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 source=expanded_source().replace('CALL CC_PICK','CALL KEY').replace('CALL CC_ASK','CALL KEY')
 old=assemble(Path.home()/'bin/z80asm',source,OUT/'legacy.bin',OUT/'legacy.lst',256)
 image=(ROOT/'build/utilities/CONFIG.COM').read_bytes();ls=(ROOT/'build/utilities/config.lst').read_text();oldls=(OUT/'legacy.lst').read_text()
 def invoke(data,listing,entry,keys,rev=0,c=None):
  at=lambda name:address(listing,name)
  if c is None:c=Z80(b'');c.mem[256:256+len(data)]=data;c.mem[5:8]=b'\xdb\xf4\xc9'
  c.mem[at('HASREV')]=rev;queue=list(keys);out=[];reads=[]
  def io(port):
   assert port&255==244
   if c.c==6 and c.e==255:assert queue;value=queue.pop(0);reads.append(value)
   else:assert c.c in (2,178);out.append((c.c,c.e));value=0
   c.bc=0xbcbc;c.de=0xdede;c.hl=0xeeee;c.ix=0xaaaa
   return value
  c.port_read=io;sp=c.sp;c.run(at(entry),limit=200000);assert c.sp==sp
  return c,(c.a,out,queue,reads)
 cases=0
 for reverse in (0,1):
  for key in range(256):
   keys=bytes([key])+b'B!'
   _,before=invoke(old,oldls,'CHOICE',keys,reverse)
   c,after=invoke(image,ls,'CHOICE',keys,reverse);assert before==after,(reverse,key,before,after);cases+=1
 for key in range(256):
  keys=bytes([key])+b'N!'
  _,before=invoke(old,oldls,'KEY',keys)
  _,after=invoke(image,ls,'CC_ASK',keys);assert before==after,(key,before,after)
 c=None
 for entry,keys,value in [('CHOICE',b'A',65),('CC_ASK',b'N',78),('CHOICE',b'Y',89),('CC_ASK',b'X',88),('CC_PICK',b'0',48),('CC_ASK',b'y',89)]:
  c,r=invoke(image,ls,entry,keys+b'!',c=c);assert r[0]==value and r[2]==[33]
 for field,value in [('UC_COUNT',0),('UC_LIST',0),('UC_DEF',88),('CC_TOKEN',0)]:
  c=Z80(b'');c.mem[256:256+len(image)]=image;c.mem[5:8]=b'\xdb\xf4\xc9';at=lambda n:address(ls,n)
  if field=='UC_LIST':c.setword(at(field),value)
  else:c.mem[at(field)]=value
  c,r=invoke(image,ls,'CC_ASK',b'',c=c);assert r==(3,[],[],[]),(field,r)
 assert len(image)<=0x3d00
 # Both platform validation and boot-IOBYTE records must remain linked.
 assert address(ls,'SGVEND')-address(ls,'SGVALID')==40
 io=address(ls,'IO_VALID')-256
 assert image[io:io+2]==bytes([80,0]) and image[io+10:io+12]==bytes([128,0]) and image[io+20:io+22]==bytes(2)
 report={'result':'PASS','menu_cases':cases,'approval_cases':256,'mixed_context_cases':6,'malformed_cases':4,'bytes':len(image),'stack_gap_bytes':0x3d00-len(image),'sha256':hashlib.sha256(image).hexdigest()}
 (OUT/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
if __name__=='__main__':main()
