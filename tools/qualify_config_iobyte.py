#!/usr/bin/env python3
"""Real cpmsim cold-operand patch, live preservation and subsequent CRC inspection."""
import argparse,re,shutil,struct,subprocess,tempfile,json,zlib
from pathlib import Path
from build_ccp import assemble
from qualify_config_physical_cli import state_probe
from fdf_format import select_fdf
from build_z80pack_image import DEFAULT_FORMAT
from startup_record import build as startup
from system_layout import LAYOUT
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser();p.add_argument('--diskdefs',type=Path,required=True);a=p.parse_args()
 parent=ROOT/'build/config-iobyte';parent.mkdir(exist_ok=True);work=Path(tempfile.mkdtemp(prefix='run-',dir=parent))
 probe=state_probe(work)
 source=''' ORG 100H
 LD DE,MSG
 LD C,9
 CALL 5
 LD C,7
 CALL 5
 LD B,A
 RRCA
 RRCA
 RRCA
 RRCA
 CALL HEX
 LD A,B
 CALL HEX
 LD E,13
 LD C,2
 CALL 5
 RET
HEX: AND 15
 ADD A,'0'
 CP ':'
 JR C,OUT
 ADD A,7
OUT: PUSH BC
 LD E,A
 LD C,2
 CALL 5
 POP BC
 RET
MSG: DB 'IOBYTE=','$'
 END
'''
 get=assemble(Path.home()/'bin/z80asm',source,work/'IOGET.COM',work/'ioget.lst',256)
 fmt=select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT)
 def offset(n):
  t,i=divmod(n,fmt.spt);return t*fmt.raw_track_bytes+fmt.raw_record_map()[i]*128
 meta=(ROOT/'build/utilities/config-iobyte.inc').read_text();rows=[bytes(map(int,line.split('DB ')[1].split(','))) for line in meta.splitlines() if 'DB ' in line]
 desc=next(r for r in rows if int.from_bytes(r[:2],'little')==fmt.spt)
 record,within=desc[2:4];at=offset(record)+within
 results=[]
 for name in ('save','decline','corrupt','menu'):
  here=work/name;here.mkdir();disks=here/'disks';disks.mkdir();image=disks/'drivea.dsk'
  shutil.copy2(ROOT/'build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk',image)
  shutil.copy2(a.diskdefs,here/'diskdefs')
  subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(image),'0:CONFIG.COM'],cwd=here,check=True)
  for label,data in [('CONFIG.COM',(ROOT/'build/utilities/CONFIG.COM').read_bytes()),('STATE.COM',probe),('IOGET.COM',get)]:
   f=here/label;f.write_bytes(data);subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),str(f),'0:'+label],cwd=here,check=True)
  data=bytearray(image.read_bytes());bcst=startup('',system_base=LAYOUT['SYSTEM'])
  for i,n in enumerate((1,2)):data[offset(n):offset(n)+128]=bcst[i*128:(i+1)*128]
  assert zlib.crc32(data[offset(record):offset(record)+128])==int.from_bytes(desc[6:],'little')
  if name=='corrupt':data[offset(record)+120]^=1
  image.write_bytes(data);before=bytes(data)
  commands=[(b'STATE\r',b'A0>_ ',20),(b'IOGET\r',b'A0>_ ',20),
            (b'CONFIG /IOBYTE=85\r',b'Nothing changed.' if name=='corrupt' else b'(Y/N)? ',20)]
  if name!='corrupt':commands.append((b'Y' if name=='save' else b'N',b'A0>_ ',20))
  else:commands.append((b'',b'A0>_ ',20))
  if name=='menu':
   commands=[(b'STATE\r',b'A0>_ ',20),(b'IOGET\r',b'A0>_ ',20),(b'CONFIG\r',b'Your choice: [',20),
             (b'K',b'New disk-boot IOBYTE (decimal): ',20),(b'85\r',b'(Y/N)? ',20),
             (b'Y',b'Your choice: [',20),(b'\x03',b'A0>_ ',20)]
  commands += [(b'IOGET\r',b'A0>_ ',20),(b'STATE\r',b'A0>_ ',20)]
  if name in ('save','menu'):commands.append((b'CONFIG /SHOW\r',b'A0>_ ',30))
  commands.append((b'BYE\r',b'System halted',10))
  trace=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,commands,here/'transcript.bin')
  assert re.findall(rb'\rIOBYTE=([0-9A-F]{2})',trace)==[b'95',b'95'],trace
  states=re.findall(rb'STATE ([0-9A-F]{560})',trace);assert len(states)==2 and states[0]==states[1]
  expected=bytearray(before)
  if name in ('save','menu'):
   expected[at]=85;assert b'Cannot inspect' not in trace and b'Saved physical-drive profiles:' in trace,trace
  assert image.read_bytes()==bytes(expected),(name,'unexpected disk changes')
  if name in ('save','menu'):
   cold=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,[(b'IOGET\r',b'A0>_ ',20),(b'IOGET\r',b'A0>_ ',20),(b'BYE\r',b'System halted',10)],here/'cold.bin')
   assert re.findall(rb'\rIOBYTE=([0-9A-F]{2})',cold)==[b'55',b'55'],cold
   if name=='save':
    saveall=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,
     [(b'CONFIG /PHYSICAL=1 /SETTLE=20\r',b'A0>_ ',20),
      (b'CONFIG\r',b'Your choice: [',20),(b'H',b'Your choice: [',20),
      (b'B',b'(Y/N)? ',30),(b'Y',b'Push ENTER for menu.',30),
      (b'\r',b'Your choice: [',20),(b'\x03',b'A0>_ ',20),
      (b'BYE\r',b'System halted',10)],here/'saveall.bin')
    assert b'All current settings saved and verified.' in saveall,saveall
    final=image.read_bytes();assert final[at]==85,'save-all erased saved cold default'
    follow=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,
     [(b'IOGET\r',b'A0>_ ',20),(b'CONFIG /SHOW\r',b'A0>_ ',30),(b'BYE\r',b'System halted',10)],here/'saveall-cold.bin')
    assert re.findall(rb'\rIOBYTE=([0-9A-F]{2})',follow)==[b'55']
    assert b'Saved physical-drive profiles:' in follow and b'Cannot inspect' not in follow

  results.append({'case':name,'result':'PASS'})
 (work/'results.json').write_text(json.dumps(results,indent=2));print('PASS cpmsim saved IOBYTE, exact-byte save/decline/corruption rejection, live/warm preservation, cold restore and CRC inspection;',work)
if __name__=='__main__':main()
