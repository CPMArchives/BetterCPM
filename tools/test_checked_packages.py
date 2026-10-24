#!/usr/bin/env python3
"""Execute checked package admission before destination activity."""
from pathlib import Path
import argparse,binascii,json,shutil,struct,subprocess,sys
p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('foreign',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=a.root.resolve();foreign=a.foreign.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(root/'tools'))
from checked_system_package import make,validate,crc,raw_payload,SIZE
from system_layout import LAYOUT as L
from test_bios import Z80
from build_z80pack_image import symbols,DEFAULT_FORMAT
from fdf_format import select_fdf
contract=json.loads((root/'build/z80pack/checked-package.json').read_text());good=(root/'build/z80pack/system-package/SYSTEM.SYS').read_bytes();other=(foreign/'build/z80pack/system-package/SYSTEM.SYS').read_bytes();sy=symbols(root/'build/utilities/sysgen.lst');program=(root/'build/utilities/SYSGEN.COM').read_bytes();results={}
def save(): (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
def cpu():
 c=Z80((root/'build/z80pack/bios.bin').read_bytes());d=(root/'build/z80pack/disk.bin').read_bytes();c.mem[L['DISK']:L['DISK']+len(d)]=d;c.mem[0x100:0x100+len(program)]=program;c.sp=0x3f00;return c
def seal(b,payload=False):
 b=bytearray(b)
 if payload:struct.pack_into('<H',b,96,crc(b[128:]))
 struct.pack_into('<H',b,126,crc(b[:126]));return bytes(b)
cases={'open-failure':good,'header-read-failure':good,'payload-read-failure':good,'close-failure':good,'valid':good,'foreign-profile':other,'truncated':good[:-128],'extra-record':good+bytes(128)}
for label,at in [('old-version',4),('base',8),('header-crc',120),('binding-header',16),('payload-crc',128+4096),('bootstrap',128+60*128),('second-stage',128+84*128),('ccp',128+108*128),('raw-private-id',128+contract['resident_id_offset'])]:
 b=bytearray(good);b[at]^=1
 if label in ('binding-header',):b=seal(b)
 if label in ('bootstrap','second-stage','ccp','raw-private-id'):b=seal(b,True)
 cases[label]=bytes(b)
b=bytearray(good);b[80]^=1;cases['foreign-id-resealed']=seal(b)
# Header and payload have agreeing CRCs, but their A: bindings disagree.
b=bytearray(good);b[128+contract['a_binding_offset']]^=1;cases['binding-payload-resealed']=seal(b,True)
if True:
 for label,data in cases.items():
  expected=label=='valid'
  try:validate(data,contract);accepted=True
  except ValueError:accepted=False
  assert accepted==(expected or label in ('open-failure','header-read-failure','payload-read-failure','close-failure')),('host',label)
  c=cpu();c.mem[5:8]=bytes((0xdb,254,0xc9));state={'dma':0,'record':0,'closed':0}
  def io(port):
   assert port&255==254
   if c.c==15:return 255 if label=='open-failure' else 0
   if c.c==26:state['dma']=c.de;return 0
   if c.c==20:
    n=state['record'];state['record']+=1
    if label=='header-read-failure' and n==0 or label=='payload-read-failure' and n==25:return 2
    b=data[n*128:(n+1)*128]
    if not b:return 1
    c.mem[state['dma']:state['dma']+128]=b;return 0
   if c.c==16:state['closed']+=1;return 255 if label=='close-failure' else 0
   raise AssertionError(('destination activity during package load',c.c))
  c.port_read=io;c.run(sy['LOADFILE'],limit=5000000);assert (c.a==0)==expected,('assembled',label,c.a)
  results['fixture-'+label]={'accepted':expected,'reads':state['record'],'closed':state['closed']};save();print('PASS package '+label,flush=True)
 # Disk-source admission normalizes only declared editable fields and restores
 # the buffered image exactly, including when admission fails.
 for label,payload,ok in [('matching',good[128:],True),('foreign',other[128:],False),('bad-stage',cases['second-stage'][128:],False)]:
  c=cpu();c.mem[0x4000:0x9000]=payload;c.run(sy['P11CHECK'],limit=3000000);assert c.z==ok and c.mem[0x4000:0x9000]==payload,label
  results['raw-'+label]={'accepted':ok,'payload_restored':True}
 b=bytearray(good[128:])
 for off,n in contract['masks']:b[off]^=1
 c=cpu();c.mem[0x4000:0x9000]=b;c.run(sy['P11CHECK'],limit=3000000);assert c.z and c.mem[0x4000:0x9000]==b
 results['raw-editable-fields']={'accepted':True,'payload_restored':True};edited_payload=bytes(b);save()
if True:
 for label in ('matching','missing','foreign'):
  c=cpu();c.mem[5:8]=bytes((0xdb,254,0xc9));c.mem[sy['DEST']]=1
  files={'RCP.CPX':(root/'build/cpx/RCP.CPX').read_bytes(),'R3PACK.RSX':(root/'build/system/R3PACK.RSX').read_bytes()}
  if label=='missing':del files['R3PACK.RSX']
  if label=='foreign':files['R3PACK.RSX']=(foreign/'build/system/R3PACK.RSX').read_bytes()
  state={'user':7,'dma':0,'file':None,'record':0}
  def io(port):
   assert port&255==254
   if c.c==32:
    if c.e!=255:state['user']=c.e
    return state['user']
   if c.c==15:
    assert state['user']==0 and c.mem[c.de]==2
    name=bytes(c.mem[c.de+1:c.de+9]).decode().strip()+'.'+bytes(c.mem[c.de+9:c.de+12]).decode().strip();state['file']=name;state['record']=0
    return 0 if name in files else 255
   if c.c==26:state['dma']=c.de;return 0
   if c.c==20:
    data=files[state['file']];n=state['record'];state['record']+=1;block=data[n*128:(n+1)*128]
    if not block:return 1
    c.mem[state['dma']:state['dma']+128]=block.ljust(128,b'\x1a');return 0
   if c.c==16:return 0
   raise AssertionError(('unexpected destination write',c.c))
  c.port_read=io;c.run(sy['P11FILES'],limit=5000000);assert c.z==(label=='matching') and state['user']==7,label
  results['destination-files-'+label]={'accepted':label=='matching','user_zero_checked':True,'caller_user_restored':7};save()

# Export must preserve allowed edits and regenerate the full package header.
for label,payload in [('matching',good[128:]),('edited',edited_payload)]:
 c=cpu();c.mem[0x4000:0x9000]=payload
 pos=contract['a_binding_offset']
 c.mem[sy['SOURCE']:sy['SOURCE']+64]=payload[pos:pos+64]
 c.run(sy['XHEADER'],limit=3000000);assert c.z
 c.run(sy['P11HEAD'],limit=3000000)
 package=bytes(c.mem[0x3100:0x3100+128])+bytes(c.mem[0x4000:0x9000])
 validate(package,contract)
 assert package[128:]==payload
 results['export-'+label]={'payload_preserved':True,'header_valid':True}
save()
print('PASS',len(results),'checked package/installer component cases')

# Build admission rejects changed guards and upstream bytes before composing.
from checked_system_package import guard_source
from build_checked_package import compose
from build_system_package import compose as legacy_compose
for name,operation in [('package-guard.inc',lambda:guard_source(root)),
                       ('checked-package.json',lambda:guard_source(root)),
                       ('command-loader/stage2.carrier',lambda:compose(Path.home()/'bin/z80asm'))]:
 path=root/'build/z80pack'/name;original=path.read_bytes()
 try:
  path.write_bytes(bytes((original[0]^1,))+original[1:])
  try:operation()
  except (ValueError,json.JSONDecodeError):pass
  else:raise AssertionError('accepted changed build input: '+name)
 finally:path.write_bytes(original)
 results['build-reject-'+name]={'rejected':True,'restored':True}
try:legacy_compose()
except ValueError:results['legacy-package-builder']={'rejected':True}
else:raise AssertionError('legacy package compose accepted a checked context')
save()
print('PASS',len(results),'package cases including generated-input refusals')
