#!/usr/bin/env python3
"""Execute first-stage admission with partial reads and foreign/corrupt stages."""
from pathlib import Path
import argparse,binascii,json,sys
p=argparse.ArgumentParser(description=__doc__);p.add_argument('baseline',type=Path);p.add_argument('experiment',type=Path);a=p.parse_args()
root=a.baseline.resolve();out=a.experiment.resolve();sys.path.insert(0,str(root/'tools'))
from build_ccp import assemble
from build_z80pack_image import symbols
from system_layout import LAYOUT as L
from test_bios import Z80
first=(out/'stage1.bin').read_bytes();sy=symbols(out/'stage1.lst')
identity=bytes.fromhex(json.loads((root/'assessment-profile.json').read_text())['compatibility_id'])
# An instrumented stage records that control crossed the admission boundary.
payload=bytes((0x3e,42,0xd3,3,0x76)).ljust(2024,b'\0')+identity+bytes(8)
class Stop(Exception):pass
def trial(data,count=2048,status=0,expected=None):
 c=Z80((root/'build/z80pack/bios.bin').read_bytes());d=(root/'build/z80pack/disk.bin').read_bytes();c.mem[L['DISK']:L['DISK']+len(d)]=d
 c.mem[0x100:0x100+len(first)]=first;c.setword(sy['P9_EXPECT']+1,binascii.crc_hqx(payload,0xffff) if expected is None else expected)
 c.mem[0x500:0xd00]=b'\xa5'*2048;c.mem[0x4000:0x4800]=data
 src=' ASEG\n ORG 07000H\n EX DE,HL\n LD HL,04000H\n'+(f' LD BC,{count}\n LDIR\n' if count else '')+f' LD A,{status}\n OR A\n RET\n END\n'
 stub=assemble(Path.home()/'bin/z80asm',src,out/'bootstrap-read.bin',out/'bootstrap-read.lst',0x7000)
 c.mem[0x7000:0x7000+len(stub)]=stub;c.mem[L['DISK']+15:L['DISK']+18]=b'\xc3\x00\x70'
 signals=[]
 def write(port,value):
  signals.append([port&255,value]);raise Stop()
 c.port_write=write
 try:c.run(0x100,limit=500000)
 except Stop:pass
 assert len(signals)==1
 return signals[0]==[3,42]
results=[]
assert trial(payload);results.append(['matching verified stage entered'])
for count in range(0,2048,128):
 assert not trial(payload,count=count,status=1);results.append(['partial read rejected',count])
for offset in (0,511,1023,2023,2024,2039,2047):
 b=bytearray(payload);b[offset]^=1;assert not trial(b);results.append(['corrupt stage rejected',offset])
b=bytearray(payload);b[2024]^=1;assert not trial(b,expected=binascii.crc_hqx(b,0xffff));results.append(['foreign identity rejected with matching expected CRC'])
(out/'bootstrap-results.json').write_text(json.dumps(results,indent=2)+'\n');print('PASS second-stage admission and partial reads')
