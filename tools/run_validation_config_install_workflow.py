#!/usr/bin/env python3
"""Save CONFIG, export its system, install on populated media and cold boot it."""
import argparse,json,shutil,subprocess
from pathlib import Path
from run_validation_cpmsim_monitors import audit
from run_validation_returning import sha
from test_z80pack_sysgen_install import session
from fdf_format import select_fdf
from build_z80pack_image import DEFAULT_FORMAT
from build_ccp import assemble
from startup_record import parse
from system_layout import LAYOUT
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('baseline','output'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim');a=p.parse_args();w=a.output;w.mkdir(parents=True,exist_ok=False);report=json.loads((a.baseline/'report.json').read_text());original=a.baseline/report['image'];assert sha(original)==report['sha256'];disks=w/'disks';disks.mkdir();shutil.copy2(a.baseline/'diskdefs',w/'diskdefs');shutil.copy2(__file__,w/'executed-runner.py')
 for letter in 'abc':shutil.copy2(original,disks/f'drive{letter}.dsk')
 A,B,C=[disks/f'drive{x}.dsk' for x in 'abc'];subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(B),'0:*.*'],cwd=w,check=True,capture_output=True)
 def put(image,user,name,data):
  f=w/name;f.write_bytes(data);subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),str(f),f'{user}:{name}'],cwd=w,check=True,capture_output=True)
 for value in (0x95,0x55):
  text=f" ORG 100H\n LD A,(3)\n CP {value}\n JR NZ,BAD\n LD DE,OK\n JR PRINT\nBAD: LD DE,FAIL\nPRINT: LD C,9\n CALL 5\n RET\nOK: DB 'LIVE IOBYTE {value:02X} PASS',13,10,'$'\nFAIL: DB 'IOBYTE CHECK FAIL',13,10,'$'\n END\n";(w/f'io{value:02x}.asm').write_text(text);code=assemble(Path.home()/'bin/z80asm',text,w/f'IO{value:02X}.COM',w/f'io{value:02x}.lst',0x100)
  for image in (A,C):put(image,0,f'IO{value:02X}.COM',code)
 sentinel=b'INSTALLED WORKFLOW SENTINEL\r\n\x1a';put(C,7,'KEEP.TXT',sentinel)
 fmt=select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT);reserved=fmt.reserved_records*128
 def offset(i):
  tr,within=divmod(i,fmt.spt);return tr*fmt.raw_track_bytes+fmt.raw_record_map()[within]*128
 def payload(data):return b''.join(data[offset(i):offset(i)+128] for i in range(160))
 C.write_bytes(b'\xa5'*reserved+C.read_bytes()[reserved:]);beforeC=C.read_bytes();(w/'target-before.dsk').write_bytes(beforeC);(w/'source-before.dsk').write_bytes(A.read_bytes())
 prompt=b'A0>_ '
 steps=[(b'IO95\r',prompt,30),(b'CONFIG /STARTUP="VER /VER"\r',b'(Y/N)? ',30),(b'Y',prompt,60),(b'CONFIG /IOBYTE=85\r',b'(Y/N)? ',30),(b'Y',prompt,60),(b'IO95\r',prompt,30),(b'CONFIG /SHOW\r',prompt,60),(b'SYSGEN A: B:LIB090.SYS\r',prompt,90),(b'SYSGEN B:LIB090.SYS C:\r',b'Proceed (Y/N)?',30),(b'Y',prompt,90),(b'BYE /Y\r',b'System halted',30)]
 trace=session(a.simulator,disks,steps,w/'save-export-install.bin');assert trace.count(b'LIVE IOBYTE 95 PASS')==2 and b'IOBYTE CHECK FAIL' not in trace;assert b'Disk-boot IOBYTE saved; live unchanged.' in trace and b'Package exported and verified.' in trace and b'System installed and verified.' in trace
 actual=A.read_bytes();startup=b''.join(actual[offset(i):offset(i)+128] for i in (1,2));assert parse(startup,system_base=LAYOUT['SYSTEM'])=='VER /VER'
 package=w/'LIB090-exported.SYS';subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(B),'0:LIB090.SYS',str(package)],cwd=w,check=True,capture_output=True);data=package.read_bytes();assert len(data)==20608 and data[:8]==b'BCSY\x01\x01\xa0\x00' and data[128:]==payload(actual)
 assert C.read_bytes()[reserved:]==beforeC[reserved:];(w/'installed.dsk').write_bytes(C.read_bytes());boot=w/'reboot';(boot/'disks').mkdir(parents=True);shutil.copy2(w/'diskdefs',boot/'diskdefs');bootimage=boot/'disks/drivea.dsk';shutil.copy2(C,bootimage)
 cold=session(a.simulator,boot/'disks',[(b'IO55\r',prompt,30),(b'CONFIG /SHOW\r',prompt,60),(b'TYPE A7:KEEP.TXT\r',prompt,30),(b'BYE /Y\r',b'System halted',30)],w/'installed-cold-boot.bin')
 assert b'BetterCP/M VER 1.0 (Resident, RCP Build ' in cold and b'LIVE IOBYTE 55 PASS' in cold and b'IOBYTE CHECK FAIL' not in cold and b'INSTALLED WORKFLOW SENTINEL' in cold;assert bootimage.read_bytes()==C.read_bytes(),'read-only installed boot changed media'
 shipped=audit(a.baseline,report,w,A)
 for label,image in [('package',B),('installed',C),('reboot',bootimage)]:
  fs=subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(image)],cwd=w,capture_output=True,check=True);(w/(label+'-filesystem.txt')).write_bytes(fs.stdout+fs.stderr)
 assert sha(original)==report['sha256']
 (w/'result.json').write_text(json.dumps({'status':'PASS','baseline_sha256':report['sha256'],'simulator_sha256':sha(a.simulator),'runner_sha256':sha(w/'executed-runner.py'),'package_sha256':sha(package),'installed_sha256':sha(C),'unchanged_shipped_files':shipped,'scope':'Actual CONFIG startup/IOBYTE save (live unchanged), named SYSGEN export of exact configured payload, confirmed install with complete destination filesystem preserved, installed cold boot restores startup and IOBYTE55, sentinel and read-only boot media preserved.'},indent=2)+'\n');print('PASS integrated CONFIG export/install/cold-boot workflow',w)
if __name__=='__main__':main()
