#!/usr/bin/env python3
"""Execute the shared DU scope parser and canonical bitmap iterator."""
import re
from pathlib import Path
from build_ccp import assemble
from test_bios import Z80
ROOT=Path(__file__).resolve().parents[1]
def main():
 out=ROOT/'build/du-select';out.mkdir(parents=True,exist_ok=True)
 source='        ORG 0200H\nDU_MAP EQU 06000H\nDU_WORK EQU 06040H\n'+(ROOT/'src/utilities/common/duselect.inc').read_text()+'\n        END\n'
 image=assemble(Path.home()/'bin/z80asm',source,out/'du.bin',out/'du.lst',0x200)
 listing=(out/'du.lst').read_text()
 def addr(name):return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
 for text,drv,usr,remaining in [('*.COM',1,2,'*.COM'),('B:',1,2,''),('b31:*.DAT',1,31,'*.DAT'),('5:FOO',1,5,'FOO'),('P00:',15,0,''),('',1,2,''),('FOO.DAT',1,2,'FOO.DAT')]:
  c=Z80(b'');c.mem[0x200:0x200+len(image)]=image;c.mem[0x7000:0x7000+len(text)]=text.encode();c.hl=0x7000;c.b=len(text);c.d=1;c.e=2
  c.run(addr('DU_PARSE'),limit=10000)
  assert not c.carry,(text,c.a)
  assert bytes(c.mem[c.hl:c.hl+c.b]).decode()==remaining,text
  expected=bytearray(64);expected[drv*4+usr//8]=1<<(usr%8)
  assert bytes(c.mem[0x6000:0x6040])==expected,text
 for text,error in [('B32:',2),('B999:',2),(':FOO',1),('Q:FOO',1),('B-1:',1)]:
  c=Z80(b'');c.mem[0x200:0x200+len(image)]=image;c.mem[0x6000:0x6040]=bytes([255])*64;c.mem[0x7000:0x7000+len(text)]=text.encode();c.hl=0x7000;c.b=len(text);c.d=1;c.e=2;c.run(addr('DU_PARSE'),limit=10000)
  assert c.carry and c.a==error,(text,c.a)
  assert bytes(c.mem[0x6000:0x6040])==bytes(64)
 # Grammar cases use explicit expected sets rather than the parser algorithm.
 def parse(text):
  c=Z80(b'');c.mem[0x200:0x200+len(image)]=image;c.mem[0x6000:0x6040]=bytes([255])*64
  c.mem[0x7000:0x7000+len(text)]=text.encode();c.hl=0x7000;c.b=len(text);c.d=1;c.e=2
  c.run(addr('DU_PARSE'),limit=100000)
  assert bytes(c.mem[0x7000:0x7000+len(text)]).decode()==text
  return c
 def bitmap(pairs):
  result=bytearray(64)
  for d,u in pairs:result[d*4+u//8]|=1<<(u%8)
  return bytes(result)
 valid=[('B[1]:*.COM',[(1,1)],'*.COM'),('B[3,5,7-11]:',[(1,u) for u in [3,5,7,8,9,10,11]],''),
  ('[A0,C[3,5,7-11],5]:F?*.DAT',[(0,0),(1,5)]+[(2,u) for u in [3,5,7,8,9,10,11]],'F?*.DAT'),
  ('[A,B4,C]:',[(0,2),(1,4),(2,2)],''),('B[-]:',[(1,u) for u in range(32)],''),
  ('B[-4,8-]:',[(1,u) for u in list(range(5))+list(range(8,32))],''),
  ('B[5-12,11,4-8]:',[(1,u) for u in range(4,13)],''),
  ('[A0,B[2,4],C[3-8],D5]:',[(0,0),(1,2),(1,4)]+[(2,u) for u in range(3,9)]+[(3,5)],''),
  ('[b09,B[9,4,11,2],5]:',[(1,u) for u in [2,4,5,9,11]],'')]
 for text,pairs,tail in valid:
  c=parse(text);assert not c.carry,(text,c.a,c.hl-0x7000)
  assert bytes(c.mem[0x6000:0x6040])==bitmap(pairs),text
  assert bytes(c.mem[c.hl:c.hl+c.b]).decode()==tail,text
 for form in ['A5:','A[5]:','[A5]:','A[5-5]:','[A[5]]:','[A[5-5]]:']:
  c=parse(form);assert not c.carry and bytes(c.mem[0x6000:0x6040])==bitmap([(0,5)]),form
 for lo in range(32):
  for hi in range(32):
   text=f'B[{lo}-{hi}]:';c=parse(text)
   assert not c.carry and bytes(c.mem[0x6000:0x6040])==bitmap([(1,u) for u in range(min(lo,hi),max(lo,hi)+1)]),text
 bad=['B[,3,5]:','B[5,9,]:','B[3,,5]:','B[,]:','B[]:','[,A0,B3]:','[A0,B3,]:','[A0,,B3]:',
  'B[32]:','[[A0,B4],C]:','[A,[B,C],D]:','B[*]:','B[1--2]:','B[1-2-3]:','B[1 2]:','[A0, 5]:',
  'B[1]:X','B[1]','[A0','B[-','B[000]:','B[+1]:','B[1,]:','[5,]:','[32]:','B[2,[3]]:','[A0,B[1,32]]:','[A0,B[1],]:','B[01,02,003]:','B[1]:FOO:']
 # The filename belongs to the caller: X is legal here; only scope is parsed.
 bad.remove('B[1]:X')
 bad.remove('B[1]:FOO:') # Filename validation is outside this library.
 for text in ['[A0,C[3,5,7-11],5]:','B[3,5,7-11]:']:
  for cut in range(1,len(text)):
   prefix=text[:cut]
   if '[' in prefix:
    c=parse(prefix);assert c.carry and bytes(c.mem[0x6000:0x6040])==bytes(64),prefix
 for text in bad:
  c=parse(text);assert c.carry,(text,c.a)
  assert bytes(c.mem[0x6000:0x6040])==bytes(64),text
  assert 0<=c.hl-0x7000<=len(text),(text,c.hl)
 # Every bit must enumerate to its exact drive/user, once, including P31.
 c=Z80(b'');c.mem[0x200:0x200+len(image)]=image;c.mem[0x6000:0x6040]=bytes([255])*64;c.bc=0
 for i in range(512):
  c.run(addr('DU_NEXT'),limit=10000)
  assert not c.carry and (c.d,c.e)==divmod(i,32) and c.bc==i+1,(i,c.d,c.e,c.bc)
 c.run(addr('DU_NEXT'),limit=10000);assert c.carry and c.bc==512
 c.mem[0x6000:0x6040]=bytes(64);c.bc=0;c.run(addr('DU_NEXT'),limit=100000);assert c.carry and c.bc==512
 print(f'DU single/compound scopes, 1024 ranges, atomic errors and 512 iterator positions pass ({len(image)} bytes)')
if __name__=='__main__':main()
