#!/usr/bin/env python3
"""Execute resident private-ID/CRC gates and raw read-failure paths."""
from pathlib import Path
import binascii, json, struct, tempfile
from build_ccp import assemble
from system_layout import LAYOUT as L, SYMBOLS as S
from test_bios import Z80
from assessment_checked_profiles import bound
ROOT=Path(__file__).resolve().parents[1]
meta=json.loads((ROOT/'build/z80pack/checked-load.json').read_text());sy=meta['symbols']
results=[]
def cpu():
 c=Z80((ROOT/'build/z80pack/bios.bin').read_bytes())
 d=(ROOT/'build/z80pack/disk.bin').read_bytes();c.mem[L['DISK']:L['DISK']+len(d)]=d;c.sp=0x5F00
 return c
ctl=bound((ROOT/'build/z80pack/config.bin').read_bytes().ljust(1024,b'\0'),ROOT)
ent=(ROOT/'build/system/R3ENTRY.RSX').read_bytes()
rel=bound((ROOT/'build/z80pack/reloader.bin').read_bytes().ljust(L['RELOADER_CAPACITY'],b'\0')+(ROOT/'build/z80pack/rsxselect.bin').read_bytes().ljust(1024-L['RELOADER_CAPACITY'],b'\0'),ROOT)
for kind,payload,label in [('reloader',rel,'Z_EREL'),('control',ctl,'Z_ECTL'),('entry',ent,'Z_EENT')]:
 expected=meta['checksums'][label];assert binascii.crc_hqx(payload,0xffff)==expected
 for off in [None,0,511,999,1000,1015,1023]:
  data=bytearray(payload)
  if off is not None:data[off]^=1
  c=cpu();c.mem[0x4000:0x4400]=data;c.de=0x4000;c.hl=expected;c.run(sy['Z_VERIFY'],limit=200000)
  assert (c.a==0)==(off is None),(kind,off,c.a)
  assert c.sp==0x5F00
  results.append([kind,'match' if off is None else 'corrupt',off])
 # A checksum that deliberately agrees with a foreign ID still cannot pass.
 bad=bytearray(payload);bad[1000]^=1
 c=cpu();c.mem[0x4000:0x4400]=bad;c.de=0x4000;c.hl=binascii.crc_hqx(bad,0xffff);c.run(sy['Z_VERIFY'],limit=200000);assert c.a!=0
 results.append([kind,'foreign ID with matching CRC rejected'])
with tempfile.TemporaryDirectory() as td:
 w=Path(td)
 for count,status in [(0,1),(128,1),(896,1),(1023,1),(1024,0)]:
  source=f''' ASEG
 ORG 05000H
 EX DE,HL
 LD HL,04000H
 LD BC,{count}
'''+(' LDIR\n' if count else '')+f' LD A,{status}\n OR A\n RET\n END\n'
  stub=assemble(Path.home()/'bin/z80asm',source,w/'stub.bin',w/'stub.lst',0x5000)
  for path,payload in [('PL_RSXLOAD',ent),('PL_OVLOAD',ctl)]:
   c=cpu();c.mem[0x5000:0x5000+len(stub)]=stub;c.mem[0x4000:0x4400]=payload
   c.mem[L['DISK']+15:L['DISK']+18]=b'\xc3\x00\x50'
   c.mem[L['RSX']:L['RSX']+1024]=b'\xA5'*1024;c.a=0;c.run(sy[path],limit=200000)
   assert (c.a==0)==(status==0),(path,count)
   assert c.mem[L['RSX']:L['RSX']+1021]==b'\xA5'*1021
   results.append([path,count,status,'manager preserved'])
# Disk-free restore: no disk adapter is executable and a cached resolver exists.
c=cpu();c.mem[0x6000:0x63F4]=bytes(i%256 for i in range(1012));c.setword(S['LY_CBACK'],0x6000)
c.mem[L['DISK']+15:L['DISK']+18]=b'\x76'*3
c.mem[L['RSX']:L['RSX']+1024]=b'\xA5'*1024;c.a=3;c.run(sy['PL_RSXLOAD'],limit=20000)
assert c.a==0 and c.mem[L['RSX']:L['RSX']+1012]==c.mem[0x6000:0x63F4]
assert c.mem[L['RSX']+1012:L['RSX']+1024]==b'\xA5'*12
results.append(['restore','no disk code reachable','frame/gateway preserved'])
(ROOT/'assessment-build-logs/raw-tests.json').write_text(json.dumps(results,indent=2)+'\n')
print('PASS: raw identity/CRC, partial reads, manager preservation and disk-free restore')
