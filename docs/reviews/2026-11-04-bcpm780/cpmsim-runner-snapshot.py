from pathlib import Path
import sys,json,shutil,subprocess,hashlib
p=Path(__file__).resolve().parents[1];w=Path(__file__).resolve().parent/(sys.argv[2] if len(sys.argv)>2 else 'cpmsim');w.mkdir()
sys.path.insert(0,str(p/'licensing-review-20261103/review/tools'))
from test_z80pack_sysgen_install import session
from convert_fdf_image import dmk_to_raw
from fdf_format import select_fdf
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
base=p/'combined-media-qualification-20261103/systems/z80pack';report=json.loads((base/'report.json').read_text());original=base/report['image'];assert sha(original)==report['sha256']
simulator=p/'combined-media-qualification-20261103/fresh-runtime/z80pack/cpmsim/cpmsim'
config=Path(sys.argv[1]).resolve();disks=w/'disks';disks.mkdir();shutil.copy2(base/'diskdefs',w/'diskdefs')
for letter in 'abc':
 image=disks/f'drive{letter}.dsk';shutil.copy2(original,image)
 subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(image),'0:CONFIG.COM'],cwd=w,check=True,capture_output=True)
 subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),str(config),'0:CONFIG.COM'],cwd=w,check=True,capture_output=True)
A,B,C=[disks/f'drive{x}.dsk' for x in 'abc']
keep=w/'KEEP.TXT';keep.write_bytes(b'NORMALIZED BINDING INSTALL PRESERVES THIS FILE\r\n\x1a')
subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(C),str(keep),'0:KEEP.TXT'],cwd=w,check=True,capture_output=True)
m4base=p/'combined-media-qualification-20261103/systems/trs80gp';m4report=json.loads((m4base/'report.json').read_text());m4=m4base/m4report['image'];assert sha(m4)==m4report['sha256']
D=disks/'drived.dsk';D.write_bytes(dmk_to_raw(m4.read_bytes(),select_fdf(p/'licensing-review-20261103/review/metadata/DISK.FDF','MMI008')));D_before=sha(D)
fmt=select_fdf(p/'licensing-review-20261103/review/metadata/DISK.FDF','MMF017');reserved=fmt.reserved_records*128
C.write_bytes(b'\xa5'*reserved+C.read_bytes()[reserved:]);before=C.read_bytes();(w/'target-before.dsk').write_bytes(before)
prompt=b'A0>_ ';steps=[b'CONFIG /PHYSICAL=3 /TRACKS=80 /SIDES=2\r',b'CONFIG /LOGICAL=D /PHYSICAL=3 /FORMAT="BetterCP/M Model 4 System 780K"\r',b'DIR D:\r',b'TYPE D:README.TXT\r',b'CONFIG /LOGICAL=B /PHYSICAL=1 /FORMAT="California Computer Systems"\r',b'TYPE C:KEEP.TXT\r',b'SYSGEN A: B:INSTALL.SYS\r']
commands=[(x,prompt,60) for x in steps]+[(b'SYSGEN B:INSTALL.SYS C:\r',b'Proceed (Y/N)?',60),(b'Y',prompt,120),(b'BYE /Y\r',b'System halted',30)]
trace=session(simulator,disks,commands,w/'binding-install.bin')
assert trace.count(b'Disk configuration changed (until cold boot).')==3
assert b'Cannot apply' not in trace and b'Package exported and verified.' in trace and b'System installed and verified.' in trace
assert b'WELCOME' in trace.upper(),trace
assert b'NORMALIZED BINDING INSTALL PRESERVES THIS FILE' in trace
assert C.read_bytes()[reserved:]==before[reserved:] and sha(D)==D_before
coldw=w/'cold';(coldw/'disks').mkdir(parents=True);shutil.copy2(w/'diskdefs',coldw/'diskdefs');shutil.copy2(C,coldw/'disks/drivea.dsk')
cold=session(simulator,coldw/'disks',[(b'TYPE KEEP.TXT\r',prompt,60),(b'CONFIG /SHOW\r',prompt,60),(b'RSX LIST\r',prompt,60),(b'BYE /Y\r',b'System halted',30)],w/'cold-boot.bin')
assert b'NORMALIZED BINDING INSTALL PRESERVES THIS FILE' in cold and b'Saved disk-boot IOBYTE (decimal): 149' in cold
bootimage=coldw/'disks/drivea.dsk'
assert bootimage.read_bytes()[:reserved]==C.read_bytes()[:reserved]
for item in report['included']+[{'name':'KEEP.TXT','user':0}]:
 name=item['name']; paths=[]
 for label,image in [('installed',C),('cold',bootimage)]:
  out=w/(label+'-'+name);subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),f"{item.get('user',0)}:{name}",str(out)],cwd=w,check=True,capture_output=True);paths.append(out)
 assert paths[0].read_bytes()==paths[1].read_bytes(),name
subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(bootimage)],cwd=w,check=True,capture_output=True)
(w/'result.json').write_text(json.dumps({'status':'PASS','baseline_sha256':sha(original),'config_sha256':sha(config),'simulator_sha256':sha(simulator),'model4_baseline_sha256':sha(m4),'model4_raw_sha256':D_before,'installed_sha256':sha(C),'commands':[x[0].decode() for x in commands],'scope':'BCPM780 named D binding reads Model 4 System filesystem; native 332K SYSGEN export/install preserves complete populated filesystem; installed cold boot and sentinel read.'},indent=2))
print('PASS cpmsim named BCPM780 read and native installation')
