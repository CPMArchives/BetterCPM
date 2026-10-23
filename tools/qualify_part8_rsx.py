#!/usr/bin/env python3
"""Execute the migrated carrier/metadata validators with rejection invariants."""
from pathlib import Path
import json,struct,sys
import test_rsxcarrier as fixture
from test_bios import Z80
from system_layout import LAYOUT as L
ROOT=Path(__file__).resolve().parents[1]
class ResidentCPU(Z80):
 def __init__(self,_):
  super().__init__((ROOT/'build/z80pack/bios.bin').read_bytes())
  b=(ROOT/'build/z80pack/disk.bin').read_bytes();self.mem[L['DISK']:L['DISK']+len(b)]=b
 def run(self,address,limit=1000):super().run(address,max(limit,500000))
fixture.Z80=ResidentCPU
cases=[]
def reject(data,metadata=False):
 c,before=fixture.phase_one(bytes(data),name=bytes(data[32:40]));phase=1
 if c.a==0 and metadata:
  before=fixture.phase_two(c,len(data));phase=2
 assert c.a!=0,('unexpected admission',phase)
 assert bytes(c.mem[fixture.FACTS:fixture.FACTS+26])==before,('facts changed on failure',phase)
for p in sorted((ROOT/'build/rsx').glob('*.RSX')):
 b=p.read_bytes()
 if p.stem in ('M4SCRN','FREHDCLK'):
  reject(b);cases.append([p.name,'unmigrated platform artifact rejected']);continue
 c,_=fixture.phase_one(b,name=b[32:40]);assert c.a==0,p.name
 cases.append([p.name,'binding accepted'])
 # Platform-specific metadata may reject a Model 4 monitor on cpmsim.
 if p.stem in ('HELLO','ECHO','STATEFUL'):
  fixture.phase_two(c,len(b));assert c.a==0,p.name
b=(ROOT/'build/rsx/STATEFUL.RSX').read_bytes();m=int.from_bytes(b[30:32],'little');rec=m+12
damaged=bytearray(b);damaged[512]^=1;reject(damaged);cases.append(['payload checksum rejection'])
for pos,val in [(4,2),(rec,5),(rec+1,17),(rec+2,0),(rec+2,2),(rec+3,2)]:
 bad=bytearray(b);bad[pos]=val;reject(bad);cases.append(['fixed binding rejection',pos,val])
for i in range(16):
 bad=bytearray(b);bad[rec+4+i]^=1;reject(bad);cases.append(['foreign-ID byte',i])
for end in range(rec,rec+20):reject(b[:end]);cases.append(['truncated binding',end-rec])
bad=bytearray(b);bad[m+4]=1;reject(bad,True);cases.append(['old BMET rejected'])
bad=bytearray(b);bad[rec:rec]=bad[rec:rec+20];bad[m+7]+=1;struct.pack_into('<H',bad,m+8,int.from_bytes(bad[m+8:m+10],'little')+20);reject(bad,True);cases.append(['duplicate binding rejected'])
pub=(ROOT/'build/rsx/HELLO.RSX').read_bytes();pr=int.from_bytes(pub[30:32],'little')+12
for i in range(16):
 bad=bytearray(pub);bad[pr+4+i]=1;reject(bad);cases.append(['nonzero public-ID byte',i])
if len(sys.argv)>1:
 foreign=Path(sys.argv[1]);reject((foreign/'STATEFUL.RSX').read_bytes());c,_=fixture.phase_one((foreign/'HELLO.RSX').read_bytes(),name=b'HELLO   ');assert c.a==0
 cases.append(['foreign private rejected / public accepted'])
(ROOT/'assessment-build-logs/part8-rsx-tests.json').write_text(json.dumps(cases,indent=2)+'\n')
print('PASS RSX v3 binding/metadata, malformed/missing/duplicate records, unchanged facts on failure')
