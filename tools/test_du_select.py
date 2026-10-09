#!/usr/bin/env python3
"""Execute the shared DU include's conventional parser and bitmap iterator."""
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
 for text,error in [('B32:',2),('B999:',2),(':FOO',1),('Q:FOO',1),('B-1:',1),('B[1]:',3),('[A0,B1]:',3)]:
  c=Z80(b'');c.mem[0x200:0x200+len(image)]=image;c.mem[0x6000:0x6040]=bytes([255])*64;c.mem[0x7000:0x7000+len(text)]=text.encode();c.hl=0x7000;c.b=len(text);c.d=1;c.e=2;c.run(addr('DU_PARSE'),limit=10000)
  assert c.carry and c.a==error,(text,c.a)
  assert bytes(c.mem[0x6000:0x6040])==bytes(64)
 # Every bit must enumerate to its exact drive/user, once, including P31.
 c=Z80(b'');c.mem[0x200:0x200+len(image)]=image;c.mem[0x6000:0x6040]=bytes([255])*64;c.bc=0
 for i in range(512):
  c.run(addr('DU_NEXT'),limit=10000)
  assert not c.carry and (c.d,c.e)==divmod(i,32) and c.bc==i+1,(i,c.d,c.e,c.bc)
 c.run(addr('DU_NEXT'),limit=10000);assert c.carry and c.bc==512
 c.mem[0x6000:0x6040]=bytes(64);c.bc=0;c.run(addr('DU_NEXT'),limit=100000);assert c.carry and c.bc==512
 print(f'DU conventional parsing, failure atomicity and all 512 iterator positions pass ({len(image)} bytes)')
if __name__=='__main__':main()
