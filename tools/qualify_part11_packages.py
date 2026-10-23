#!/usr/bin/env python3
"""Execute package admission and live checked SYSGEN installation/refusal."""
from pathlib import Path
import argparse,binascii,json,shutil,struct,subprocess,sys
p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('foreign',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--fixtures-only',action='store_true');p.add_argument('--live-only',action='store_true');a=p.parse_args()
root=a.root.resolve();foreign=a.foreign.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(root/'tools'))
from checked_system_package import make,validate,crc,raw_payload,SIZE
from system_layout import LAYOUT as L
from test_bios import Z80
from build_z80pack_image import symbols,DEFAULT_FORMAT
from fdf_format import select_fdf
from test_z80pack_sysgen_install import session
contract=json.loads((root/'build/z80pack/checked-package.json').read_text());good=(root/'assessment-media/SYSTEM.SYS').read_bytes();other=(foreign/'assessment-media/SYSTEM.SYS').read_bytes();sy=symbols(root/'build/utilities/sysgen.lst');program=(root/'build/utilities/SYSGEN.COM').read_bytes();results={}
def save(): (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
def cpu():
 c=Z80((root/'build/z80pack/bios.bin').read_bytes());d=(root/'build/z80pack/disk.bin').read_bytes();c.mem[L['DISK']:L['DISK']+len(d)]=d;c.mem[0x100:0x100+len(program)]=program;c.sp=0x3f00;return c
def seal(b,payload=False):
 b=bytearray(b)
 if payload:struct.pack_into('<H',b,96,crc(b[128:]))
 struct.pack_into('<H',b,126,crc(b[:126]));return bytes(b)
cases={'valid':good,'foreign-profile':other,'truncated':good[:-128],'extra-record':good+bytes(128)}
for label,at in [('old-version',4),('base',8),('header-crc',120),('binding-header',16),('payload-crc',128+4096),('bootstrap',128+60*128),('second-stage',128+84*128),('ccp',128+108*128),('raw-private-id',128+contract['resident_id_offset'])]:
 b=bytearray(good);b[at]^=1
 if label in ('binding-header',):b=seal(b)
 if label in ('bootstrap','second-stage','ccp','raw-private-id'):b=seal(b,True)
 cases[label]=bytes(b)
b=bytearray(good);b[80]^=1;cases['foreign-id-resealed']=seal(b)
# Header and payload have agreeing CRCs, but their A: bindings disagree.
b=bytearray(good);b[128+contract['a_binding_offset']]^=1;cases['binding-payload-resealed']=seal(b,True)
if not a.live_only:
 for label,data in cases.items():
  expected=label=='valid'
  try:validate(data,contract);accepted=True
  except ValueError:accepted=False
  assert accepted==expected,('host',label)
  c=cpu();c.mem[5:8]=bytes((0xdb,254,0xc9));state={'dma':0,'record':0,'closed':0}
  def io(port):
   assert port&255==254
   if c.c==15:return 0
   if c.c==26:state['dma']=c.de;return 0
   if c.c==20:
    n=state['record'];state['record']+=1;b=data[n*128:(n+1)*128]
    if not b:return 1
    c.mem[state['dma']:state['dma']+128]=b;return 0
   if c.c==16:state['closed']+=1;return 0
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
 results['raw-editable-fields']={'accepted':True,'payload_restored':True};save()
if not a.live_only:
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
if a.fixtures_only:raise SystemExit(0)
fmt=select_fdf(root/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT);sim=Path('/tmp/bettercpm-assessment-part2-20261023/runtime-tools/cpmsim')
def put(w,drive,name,data):
 path=w/name;path.write_bytes(data);disk=w/'disks'/('drive'+drive+'.dsk')
 subprocess.run(['cpmrm','-f','bettercpm-default',str(disk),'0:'+name],cwd=w,capture_output=True)
 subprocess.run(['cpmcp','-f','bettercpm-default',str(disk),str(path),'0:'+name],cwd=w,check=True,capture_output=True)
def case(name):
 w=out/name;(w/'disks').mkdir(parents=True,exist_ok=True);shutil.copyfile(root/'assessment-media/diskdefs',w/'diskdefs')
 for d in 'abcd':shutil.copyfile(root/'assessment-media/system.raw',w/'disks'/f'drive{d}.dsk')
 # Avoid SUBMIT's temporary-file writes obscuring preservation comparisons.
 from startup_record import build
 startup=build(':VER /BANNER',system_base=L['SYSTEM'])
 for d in 'abcd':
  path=w/'disks'/f'drive{d}.dsk';b=bytearray(path.read_bytes())
  for i in range(2):
   rec=i+1;tr,j=divmod(rec,fmt.spt);at=tr*fmt.raw_track_bytes+fmt.raw_record_map()[j]*128;b[at:at+128]=startup[i*128:(i+1)*128]
  path.write_bytes(b)
 put(w,'b','KEEP.TXT',b'PART 11 PRESERVE THIS FILE\r\n');return w
def run(w,commands,name='transcript'):
 return session(sim,w/'disks',commands,w/(name+'.txt'))
def prompt(command):return (command.encode()+b'\r',b'A0>_ ',60)
def record(name,**kw):results[name]=kw;save();print('PASS '+name,flush=True)
# Both package and disk-source installation preserve existing files and produce
# a target that boots with its already-matching command/runtime file inventory.
for mode in ('package-install','disk-install'):
 w=case(mode)
 if mode=='package-install':put(w,'a','SYSTEM.SYS',good)
 target=w/'disks/driveb.dsk';before=target.read_bytes();command='SYSGEN SYSTEM.SYS B:' if mode=='package-install' else 'SYSGEN A: B:'
 t=run(w,[(command.encode()+b'\r',b'Proceed (Y/N)?',60),(b'Y',b'A0>_ ',90)])
 assert b'System installed and verified.' in t,t[-1500:]
 after=target.read_bytes();assert after[fmt.reserved_records*128:]==before[fmt.reserved_records*128:]
 shutil.copyfile(target,w/'disks/drivea.dsk');cold=run(w,[prompt('STAT MEM')],'cold-boot')
 expected=(L['TPA']-256)//128*128;assert f'Maximum loadable COM: {expected}'.encode() in cold
 record(mode,filesystem_unchanged=True,cold_boot=True,tpa=expected)
# Live export must recreate both the exact source payload and its v2 checks.
w=case('export');t=run(w,[prompt('SYSGEN A: B:EXPORTED.SYS')]);assert b'Package exported and verified.' in t
exported=w/'EXPORTED.SYS';subprocess.run(['cpmcp','-f','bettercpm-default',str(w/'disks/driveb.dsk'),'0:EXPORTED.SYS',str(exported)],cwd=w,check=True,capture_output=True)
assert exported.read_bytes()==make(raw_payload(root,w/'disks/drivea.dsk'),contract)
record('export',exact_host_package=True)
for label in ('foreign-profile','foreign-id-resealed','old-version','truncated','binding-header','binding-payload-resealed','second-stage'):
 w=case('reject-'+label);put(w,'a','BAD.SYS',cases[label]);target=w/'disks/driveb.dsk';before=target.read_bytes()
 t=run(w,[prompt('SYSGEN BAD.SYS B:')]);assert b'system package is invalid' in t and target.read_bytes()==before,(label,t[-1000:])
 record('reject-'+label,target_unchanged=True)
for label in ('missing-rcp','foreign-rcp','foreign-pack'):
 w=case(label);target=w/'disks/driveb.dsk'
 if label=='missing-rcp':subprocess.run(['cpmrm','-f','bettercpm-default',str(target),'0:RCP.CPX'],cwd=w,check=True)
 else:
  name,rel=('RCP.CPX','build/cpx/RCP.CPX') if label=='foreign-rcp' else ('R3PACK.RSX','build/system/R3PACK.RSX');put(w,'b',name,(foreign/rel).read_bytes())
 before=target.read_bytes();t=run(w,[(b'SYSGEN A: B:\r',b'Proceed (Y/N)?',60),(b'Y',b'A0>_ ',90)])
 assert b'Matching RCP.CPX and R3PACK.RSX required' in t and target.read_bytes()==before,(label,t[-1500:])
 record(label,target_unchanged=True)
print('PASS package/install/export/mixed-version campaign',flush=True)
# Refuse a foreign disk-source contract before any destination write, too.
w=case('foreign-disk-source');shutil.copyfile(foreign/'assessment-media/system.raw',w/'disks/drivec.dsk');target=w/'disks/driveb.dsk';before=target.read_bytes()
t=run(w,[(b'SYSGEN C: B:\r',b'Proceed (Y/N)?',60),(b'Y',b'A0>_ ',90)])
assert b'system package is invalid' in t and target.read_bytes()==before
record('foreign-disk-source',target_unchanged=True)
w=case('decline');before=(w/'disks/driveb.dsk').read_bytes()
t=run(w,[(b'SYSGEN A: B:\r',b'Proceed (Y/N)?',60),(b'N',b'A0>_ ',60)])
assert (w/'disks/driveb.dsk').read_bytes()==before
record('decline',target_unchanged=True)
