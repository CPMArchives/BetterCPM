#!/usr/bin/env python3
"""Candidate command carrier format and executed Z80 record-gate experiments."""
from pathlib import Path
import json,struct,sys
from build_ccp import assemble
from test_bios import Z80
from build_z80pack_rom_boot import z80pack_reloader_source
from build_z80pack_image import normalized
from system_layout import LAYOUT as L
from part8_carrier_formats import candidate,inspect
ROOT=Path(__file__).resolve().parents[1]
profile=json.loads((ROOT/'assessment-profile.json').read_text());identity=profile['compatibility_id']
out=ROOT/'assessment-command-candidates';out.mkdir(exist_ok=True)
rows=[]
for rel in ('build/ccp/ccp.rlm','build/cpx/RCP.CPX','build/cpx/HELLO.CPX'):
 p=ROOT/rel;old=p.read_bytes();new=candidate(old,identity);facts=inspect(new,identity)
 assert len(new)==len(old)+20
 (out/p.name).write_bytes(new)
 variants=[old,new[:-1],new+bytes(1)]
 off=facts['binding_offset']
 for pos in (0,1,2,3,4,19):
  bad=bytearray(new);bad[off+pos]^=0x80;variants.append(bytes(bad))
 for b in variants:
  try:inspect(b,identity)
  except (ValueError,struct.error,IndexError):pass
  else:raise AssertionError('accepted malformed command carrier')
 rows.append({'name':p.name,'old_bytes':len(old),'new_bytes':len(new),'old_records':(len(old)+127)//128,'new_records':(len(new)+127)//128,**facts})
s=(ROOT/'src/system/part8-record-gate.mac').read_text().replace('; @part8-binding@',(ROOT/'src/system/part8-binding.inc').read_text())
gate=assemble(Path.home()/'bin/z80asm',s,out/'record-gate.bin',out/'record-gate.lst',0x8000)
reload=z80pack_reloader_source((ROOT/'src/platform/trs80m4/ccprelod.mac').read_text())
body=s[s.index('PG_ENTRY:'):s.rindex('        END')]
trial=normalized(reload).replace('        END',body+'        END')
combined=assemble(Path.home()/'bin/z80asm',trial,out/'naive-reloader.bin',out/'naive-reloader.lst',L['RELOADER'])
assert len(combined)>L['RELOADER_CAPACITY']
results=[]
def run(rec,available=20,kind=0,address=0x5200):
 c=Z80((ROOT/'build/z80pack/bios.bin').read_bytes());disk=(ROOT/'build/z80pack/disk.bin').read_bytes();c.mem[L['DISK']:L['DISK']+len(disk)]=disk
 c.mem[0x8000:0x8000+len(gate)]=gate
 if address+len(rec)<=65536:c.mem[address:address+len(rec)]=rec
 c.hl=address;c.bc=available;c.a=kind;c.sp=0x6000;c.run(0x8000,limit=10000);assert c.sp==0x6000
 return c.a
private=b'BP\1\1'+bytes.fromhex(identity);public=b'BP\1\0'+bytes(16)
assert run(private)==0 and run(private,kind=1)==0 and run(public)==0 and run(public,kind=1)!=0
for available in range(20):assert run(private,available=available)!=0
for rec in (private,public):
 for i in range(20):
  b=bytearray(rec);b[i]^=0x80;assert run(b)!=0;results.append(['record-mutation',rec[3],i])
assert run(private,address=65520)!=0
assert run(private,kind=2)!=0
report={'carriers':rows,'z80_gate_bytes':len(gate),'z80_record_mutation_rejections':results,'short_record_rejections':20,'ccp_public_rejected':True,'wrap_rejected':True,'reloader_bytes':len((ROOT/'build/z80pack/reloader.bin').read_bytes()),'reloader_capacity':L['RELOADER_CAPACITY'],'naive_combined_bytes':len(combined),'integration':'candidate gate only; CPX/CCP runtime loader unchanged'}
(out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='z80_record_mutation_rejections'}))
