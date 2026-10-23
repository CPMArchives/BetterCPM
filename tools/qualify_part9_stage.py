#!/usr/bin/env python3
"""Execute the staged loader, including read failures and pre-publication gates."""
from pathlib import Path
import argparse,binascii,json,struct,sys
p=argparse.ArgumentParser(description=__doc__);p.add_argument('baseline',type=Path);p.add_argument('experiment',type=Path);a=p.parse_args()
root=a.baseline.resolve();out=a.experiment.resolve();sys.path.insert(0,str(root/'tools'))
from build_ccp import assemble
from build_z80pack_image import symbols
from system_layout import LAYOUT as L
from test_bios import Z80
sy=symbols(out/'stage2.lst');image=(out/'stage2.bin').read_bytes()
# Single-record adapters; they deliberately fail without reporting success for
# any unread part of a record. The assembled production-facing reader is used.
adapter=''' ASEG
 ORG 07000H
 JP FILE
 JP RAW
FILE:
 PUSH BC
 POP HL
RAW:
 LD A,(COUNT)
 INC A
 LD (COUNT),A
FAILAT: CP 255
 JR Z,BAD
 EX DE,HL
 LD HL,(PTR)
 LD BC,128
 LDIR
 LD (PTR),HL
 EX DE,HL
 XOR A
 RET
BAD: LD A,1
 OR A
 RET
COUNT: DB 0
PTR: DW 08000H
 END
'''
stub=assemble(Path.home()/'bin/z80asm',adapter,out/'record-adapter.bin',out/'record-adapter.lst',0x7000);ss=symbols(out/'record-adapter.lst')
rows=json.loads((out/'results.json').read_text())['carriers'];results=[]
def reseal(b):
 b=bytearray(b);struct.pack_into('<H',b,len(b)-2,binascii.crc_hqx(b[:-2],0xffff));return b
def run(data,name,fail=255,bound=None):
 c=Z80((root/'build/z80pack/bios.bin').read_bytes());disk=(root/'build/z80pack/disk.bin').read_bytes();c.mem[L['DISK']:L['DISK']+len(disk)]=disk
 c.mem[0x500:0x500+len(image)]=image;c.mem[0x1000:0x7000]=b'\xa5'*0x6000
 c.mem[0x8000:0x8000+len(data)]=data;c.mem[0x7000:0x7000+len(stub)]=stub;c.mem[ss['FAILAT']+1]=fail
 c.mem[L['EXTENSIONS']+9:L['EXTENSIONS']+12]=b'\xc3\x00\x70';c.mem[L['DISK']+15:L['DISK']+18]=b'\xc3\x03\x70'
 c.mem[sy['CRFILE']]=int(name!='ccp.rlm');c.mem[sy['CRSLOT']]=108;c.setword(sy['CRMAGPTR'],sy['CRCCPMAG' if name=='ccp.rlm' else 'CRCPXMAG'])
 upper=L['TPA'] if bound is None else bound;c.setword(sy['CRBOUND'],upper);c.mem[sy['CRCOUNT']]=7;c.sp=0x1000
 allocation=next(x['allocation'] for x in rows if x['name']==name)
 c.mem[upper-allocation:upper]=b'\x5a'*allocation
 c.run(sy['CRLOAD'],limit=2000000)
 assert c.sp==0x1000 and c.mem[sy['CRCOUNT']]==7
 return c
for row in rows:
 name=row['name'];raw=(out/name).read_bytes();original=(root/('build/ccp/' if name=='ccp.rlm' else 'build/cpx/')/name).read_bytes()
 c=run(raw,name);assert c.a==0,(name,c.a)
 header=1024 if name=='ccp.rlm' else int.from_bytes(raw[24:26],'little');size=int.from_bytes(raw[8:10] if name=='ccp.rlm' else raw[12:14],'little')
 linked=int.from_bytes(raw[6:8] if name=='ccp.rlm' else raw[10:12],'little');nrel=int.from_bytes(raw[14:16] if name=='ccp.rlm' else raw[22:24],'little');table=16 if name=='ccp.rlm' else 48;base=c.word(sy['CRBASE'])
 expected=bytearray(original[header:header+size])
 for i in range(nrel):
  at=int.from_bytes(raw[table+2*i:table+2*i+2],'little');v=int.from_bytes(expected[at:at+2],'little');expected[at:at+2]=((v+base-linked)&65535).to_bytes(2,'little')
 if name!='ccp.rlm':
  for at in (16,18,20):
   v=int.from_bytes(raw[at:at+2],'little');expected[2+at-16:4+at-16]=(0 if v==65535 else base+v).to_bytes(2,'little')
 assert c.mem[base:base+size]==expected,name
 assert c.mem[ss['COUNT']]==row['records'];results.append([name,'matching payload and relocations',row['records']])
 for bound,ok in ((row['required_upper_boundary'],True),(row['required_upper_boundary']-1,False)):
  cc=run(raw,name,bound=bound);assert (cc.a==0)==ok,(name,bound,cc.a);results.append([name,'staging boundary',bound,ok])
 # Every required physical record failing is rejected, not padded with stale RAM.
 for failure in range(1,row['records']+1):
  cc=run(raw,name,fail=failure);assert cc.a!=0 and cc.word(sy['CRBOUND'])==L['TPA']
  assert cc.mem[base:base+row['allocation']]==b'\x5a'*row['allocation'],(name,failure,'destination modified')
 results.append([name,'all record failures rejected before destination write',row['records']])
 for pos in (0,table,header,header+size//2,header+size-1,len(raw)-22,len(raw)-3,len(raw)-1):
  b=bytearray(raw);b[pos]^=1;cc=run(b,name);assert cc.a!=0 and cc.mem[base:base+row['allocation']]==b'\x5a'*row['allocation'];results.append([name,'unsealed corruption rejected',pos])
 # A valid CRC must not hide a foreign private ID or invalid public declaration.
 for pos in range(len(raw)-18,len(raw)-2):
  b=bytearray(raw);b[pos]^=1;cc=run(reseal(b),name);assert cc.a!=0 and cc.mem[base:base+row['allocation']]==b'\x5a'*row['allocation']
 results.append([name,'each ID-byte mutation rejected even with recomputed CRC',16])
 # Structurally invalid relocation must be rejected before any copying occurs.
 b=bytearray(raw);struct.pack_into('<H',b,table,size-1);cc=run(reseal(b),name);assert cc.a!=0 and cc.mem[base:base+row['allocation']]==b'\x5a'*row['allocation']
 if nrel>1:
  b=bytearray(raw);b[table+2:table+4]=b[table:table+2];cc=run(reseal(b),name);assert cc.a!=0
 results.append([name,'invalid and duplicate relocation offsets rejected'])
 if name!='ccp.rlm':
  b=bytearray(raw);b[44]^=1;cc=run(reseal(b),name);assert cc.a!=0;results.append([name,'stale payload checksum rejected despite valid carrier CRC'])
  invalid_fields=[(6,2),(8,1),(12,0),(14,0),(16,size),(18,size),(20,size),(22,0x8000),(24,256),(26,512 if header!=512 else 1024),(28,49),(30,header+size+1)]
 else:
  invalid_fields=[(8,0),(10,0),(12,1),(14,0x8000)]
 for offset,value in invalid_fields:
  b=bytearray(raw);struct.pack_into('<H',b,offset,value);cc=run(reseal(b),name);assert cc.a!=0,(name,offset,value)
  assert cc.mem[base:base+row['allocation']]==b'\x5a'*row['allocation'];results.append([name,'invalid header with valid CRC rejected',offset,value])
 for offset,value in ((len(raw)-20,3),(len(raw)-19,2)):
  b=bytearray(raw);b[offset]=value;cc=run(reseal(b),name);assert cc.a!=0
 if name=='ccp.rlm':
  b=bytearray(raw);b[-19]=0;b[-18:-2]=bytes(16);cc=run(reseal(b),name);assert cc.a!=0;results.append([name,'public CCP rejected with valid CRC'])
 print('PASS staged carrier '+name,flush=True)
(out/'fixture-results.json').write_text(json.dumps(results,indent=2)+'\n')
print('PASS staged loader: exact-record failures, integrity, identity, placement and relocation')
