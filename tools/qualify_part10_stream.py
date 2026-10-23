#!/usr/bin/env python3
"""Execute the streaming loader, including partial reads and publication guards."""
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
BAD:
 EX DE,HL
 LD HL,(PTR)
PARTIAL: LD BC,0
 LD A,B
 OR C
 JR Z,RETFAIL
 LDIR
RETFAIL: LD A,1
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
def run(data,name,fail=255,bound=None,allocation_override=None,partial=0):
 c=Z80((root/'build/z80pack/bios.bin').read_bytes());disk=(root/'build/z80pack/disk.bin').read_bytes();c.mem[L['DISK']:L['DISK']+len(disk)]=disk
 c.mem[0x500:0x500+len(image)]=image;c.mem[0x1000:0x7000]=b'\xa5'*0x6000
 c.mem[0x8000:0x8000+len(data)]=data;c.mem[0x7000:0x7000+len(stub)]=stub;c.mem[ss['FAILAT']+1]=fail;c.setword(ss['PARTIAL']+1,partial)
 c.mem[L['EXTENSIONS']+9:L['EXTENSIONS']+12]=b'\xc3\x00\x70';c.mem[L['DISK']+15:L['DISK']+18]=b'\xc3\x03\x70'
 c.mem[sy['CRFILE']]=int(name!='ccp.rlm');c.mem[sy['CRSLOT']]=108;c.setword(sy['CRMAGPTR'],sy['CRCCPMAG' if name=='ccp.rlm' else 'CRCPXMAG'])
 upper=L['TPA'] if bound is None else bound;c.setword(sy['CRBOUND'],upper);c.mem[sy['CRCOUNT']]=7;c.sp=0x1000
 allocation=allocation_override or next(x['allocation'] for x in rows if x['name']==name)
 c.mem[upper-allocation:upper]=b'\x5a'*allocation
 before=bytes(c.mem)
 c.run(sy['CRLOAD'],limit=3000000)
 # Code/state, reserved stack, header/input cache, prospective allocation and
 # controlled adapter state are the only regions allowed to change.
 allowed=((0x500,0x1680),(upper-allocation,upper),(0x7000,0x7000+len(stub)))
 assert all(before[i]==c.mem[i] or any(lo<=i<hi for lo,hi in allowed) for i in range(65536)),(name,'write outside unpublished/scratch regions')
 assert c.mem[0x1680:min(upper-allocation,0x7000)]==before[0x1680:min(upper-allocation,0x7000)]
 if c.a:assert c.word(sy['CRBOUND'])==upper,(name,'published rejected allocation')
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
  copied=min(size,max(0,(failure-1-header//128)*128))
  assert cc.mem[base:base+copied]==raw[header:header+copied],(name,failure,'partial payload differs')
  assert cc.mem[base+copied:base+row['allocation']]==b'\x5a'*(row['allocation']-copied),(name,failure,'write beyond successful reads')
 results.append([name,'all record failures rejected with exact unpublished payload prefix',row['records']])
 for pos in (0,table,header,header+size//2,header+size-1,len(raw)-22,len(raw)-3,len(raw)-1):
  b=bytearray(raw);b[pos]^=1;cc=run(b,name);assert cc.a!=0;results.append([name,'unsealed corruption rejected',pos])
 # A valid CRC must not hide a foreign private ID or invalid public declaration.
 for pos in range(len(raw)-18,len(raw)-2):
  b=bytearray(raw);b[pos]^=1;cc=run(reseal(b),name);assert cc.a!=0
 results.append([name,'each ID-byte mutation rejected even with recomputed CRC',16])
 # A disk/file read may alter its buffer before reporting failure. No byte
 # of that unsuccessful record may reach the prospective payload.
 for failure in sorted({header//128+1,min(row['records'],header//128+2),row['records']}):
  for partial in (1,63,127,128):
   cc=run(raw,name,fail=failure,partial=partial);assert cc.a!=0
   copied=min(size,max(0,(failure-1-header//128)*128))
   assert cc.mem[base:base+copied]==raw[header:header+copied]
   assert cc.mem[base+copied:base+row['allocation']]==b'\x5a'*(row['allocation']-copied)
 results.append([name,'failed reads that changed 1/63/127/128 buffer bytes never publish those bytes'])
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
 print('PASS streamed carrier '+name,flush=True)
# Synthetic carriers exercise every accepted header size and record-boundary
# cases, including binding and CRC words split across physical records.
for hs in (512,1024,1536):
 for size in (10,107,108,127,128,129,235,256,257):
  for commands in (0,1,17):
   b=bytearray(hs);b[:10]=b'BCPX'+bytes((2,1,1,0,0,0))
   allocation=(size+255)//256*256
   payload=bytes((i*37+11)&255 for i in range(size))
   for at,v in ((10,0x100),(12,size),(14,allocation),(16,8),(18,65535),(20,65535),(22,1),(24,hs),(26,hs),(28,48),(30,hs+size),(44,sum(payload)&65535),(48,size-2)):
    struct.pack_into('<H',b,at,v)
   b[42]=commands;b+=payload+bytes(commands*8)+b'BP'+bytes((2,0))+bytes(18);b=reseal(b)
   cc=run(b,'HELLO.CPX',bound=0x1680+allocation,allocation_override=allocation);assert cc.a==0,(hs,size,commands,cc.a)
   assert cc.mem[ss['COUNT']]==(len(b)+127)//128
   base=0x1680;expected=bytearray(payload);v=int.from_bytes(expected[-2:],'little');expected[-2:]=((v+base-0x100)&65535).to_bytes(2,'little');expected[2:8]=(base+8).to_bytes(2,'little')+bytes(4)
   assert cc.mem[base:base+size]==expected,(hs,size,commands)
results.append(['synthetic carriers','three header sizes, short payloads, metadata and split trailers',81])
(out/'fixture-results.json').write_text(json.dumps(results,indent=2)+'\n')
print('PASS streaming loader: exact-record failures, integrity, identity, placement and relocation')
