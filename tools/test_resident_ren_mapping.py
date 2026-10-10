#!/usr/bin/env python3
"""Exercise positional REN mapping, invalid concrete names and fixed points."""
from pathlib import Path
import re
from test_bios import Z80
ROOT=Path(__file__).resolve().parents[1]
def main():
 image=(ROOT/'build/cpx/rcp.bin').read_bytes();listing=(ROOT/'build/cpx/rcp.lst').read_text()
 def addr(n):return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+n+':',listing,re.M|re.I)[1],16)
 cases=[(b'FOOBAR  COM',b'X???????BAK',b'XOOBAR  BAK'),(b'F       DOC',b'????????TXT',b'F       TXT'),(b'FOO     DOC',b'FOO     DOC',b'FOO     DOC'),(b'A       DOC',b'??X     TXT',None),(b'FOO     DOC',b'        TXT',None),(b'FOO     DOC',b'F_O     ???',b'F_O     DOC')]
 for old,template,new in cases:
  c=Z80(b'');c.mem[0x8000:0x8000+len(image)]=image;c.mem[5]=0x76
  c.mem[0x6000:0x600b]=old;c.mem[addr('RF_TEMP')+1:addr('RF_TEMP')+12]=template;c.hl=0x6000;c.run(addr('RF_MAP'),10000)
  assert c.carry==(new is None),(old,template,c.carry)
  if new is not None:
   assert bytes(c.mem[addr('RF_NAME'):addr('RF_NAME')+11])==new
   c.mem[0x6000:0x600b]=new;c.hl=0x6000;c.run(addr('RF_MAP'),10000)
   assert not c.carry and bytes(c.mem[addr('RF_NAME'):addr('RF_NAME')+11])==new,'mapping must be idempotent'
 print('Resident REN positional mapping, invalid-name rejection and fixed points PASS')
if __name__=='__main__':main()
