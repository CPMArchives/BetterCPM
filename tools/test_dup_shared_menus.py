#!/usr/bin/env python3
"""DUP menu/drive compatibility and confirmation isolation across contexts."""
import hashlib,json
from functools import lru_cache
from pathlib import Path
from build_dup import expanded_source
from build_ccp import assemble
from test_bios import Z80
from test_utility_versions import address
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/dup-menu-input'
@lru_cache(maxsize=2)
def positions(ls):return {n:address(ls,n) for n in ('CHOICE','DP_MENU','DP_ASK','ASKDRV','HASREV','DFASK','DCMODE','DCNEXT','DCFIRST','DCSECOND','UC_COUNT','UC_LIST','UC_DEF','UY_LIST','DU_MODE','DU_MLIST','DU_DLIST')}

def invoke(image,ls,entry,keys,reverse=0,cpu=None):
 p=positions(ls);c=cpu or Z80(b'')
 if cpu is None:c.mem[256:256+len(image)]=image;c.mem[5:8]=b'\xdb\xf4\xc9'
 c.mem[p['HASREV']]=reverse;c.hl=p['DFASK'];pending=list(keys);out=[];reads=[]
 def io(port):
  assert port&255==244
  if c.c==6:
   assert c.e==255 and pending,'unexpected input'
   value=pending.pop(0);reads.append(value)
  else:
   assert c.c in (2,178),c.c
   out.append((c.c,c.e));value=0
  c.bc=0xbcbc;c.de=0xdede;c.hl=0xeeee;c.ix=0xaaaa
  return value
 c.port_read=io;sp=c.sp;c.run(p[entry],limit=150000);assert c.sp==sp
 return c,(c.a,tuple(out),pending,reads)

def main():
 OUT.mkdir(parents=True,exist_ok=True);text=expanded_source()
 text=text.replace('CALL DP_MENU','CALL CHOICE').replace('CALL DP_DRIVE','CALL CHOICE')
 a=text.index('CHOICE:');b=text.index('; A = unsigned byte',a)
 text=text[:a]+(ROOT/'tools/fixtures/dup-legacy-choice.inc').read_text()+text[b:]
 (OUT/'legacy-expanded.mac').write_text(text)
 old=assemble(Path.home()/'bin/z80asm',text,OUT/'legacy.bin',OUT/'legacy.lst',256);oldls=(OUT/'legacy.lst').read_text()
 image=(ROOT/'build/utilities/DUP.COM').read_bytes();ls=(ROOT/'build/utilities/dup.lst').read_text();p=positions(ls);cases=0
 for reverse in (0,1):
  for key in range(256):
   keys=bytes([key])+b'B!'
   for before,after in [('CHOICE','DP_MENU'),('ASKDRV','ASKDRV')]:
    c,a=invoke(old,oldls,before,keys,reverse);n,b=invoke(image,ls,after,keys,reverse)
    assert a==b,(reverse,key,after,a,b)
    if after=='ASKDRV':assert (c.carry,c.z)==(n.carry,n.z)
    assert n.mem[p['UC_COUNT']]==2 and n.word(p['UC_LIST'])==p['UY_LIST'] and n.mem[p['UC_DEF']]==0 and n.mem[p['DU_MODE']]==0
    cases+=1
 # Reuse one controller instance through menus, invalid drive and approvals.
 c=None
 for entry,key,expected in [('DP_MENU',b'A',65),('ASKDRV',b'B',1),('DP_ASK',b'N',78),('DP_MENU',b'Y',89),('DP_ASK',b'X',0),('ASKDRV',b'\r',255),('DP_ASK',b'Y',89)]:
  c,r=invoke(image,ls,entry,key+b'!',cpu=c);assert r[0]==expected and r[2]==[33],(entry,r)
 # Invalid menu configuration aborts without reading, never reuses last A.
 for field,entry in [('DU_MLIST','DP_MENU'),('DU_DLIST','ASKDRV')]:
  c=Z80(b'');c.mem[256:256+len(image)]=image;c.mem[5:8]=b'\xdb\xf4\xc9';c.mem[p[field]]=0
  c,r=invoke(image,ls,entry,b'',cpu=c);assert r[0]==(3 if entry=='DP_MENU' else 255) and not r[3]
  c,r=invoke(image,ls,'DP_ASK',b'N!',cpu=c);assert r[0]==78 and r[2]==[33]
 # CLI drive selection must remain completely noninteractive.
 for mode in (1,2,3):
  c=Z80(b'');c.mem[256:256+len(image)]=image;c.mem[p['DCMODE']]=mode;c.mem[p['DCFIRST']]=1;c.mem[p['DCSECOND']]=3
  for expected in (1,3):
   c,r=invoke(image,ls,'ASKDRV',b'',cpu=c);assert r==(expected,(),[],[]),r
 (OUT/'results.json').write_text(json.dumps({'result':'PASS','differential_cases':cases,'context_sequence_cases':7,'malformed_menu_cases':2,'noninteractive_modes':3,'dup_sha256':hashlib.sha256(image).hexdigest(),'bytes':len(image)},indent=2)+'\n')
 print(f'PASS: {cases} DUP menu/drive comparisons, mixed-context confirmation isolation, malformed menus and CLI bypass')
if __name__=='__main__':main()
