#!/usr/bin/env python3
"""Require native ZSM4/LINK parity for the shared DU include."""
import argparse,shutil,tempfile
from pathlib import Path
from build_ccp import assemble
from build_native_trs80 import blank,run
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--cpmsim',type=Path,required=True);p.add_argument('--system-disk',type=Path,required=True);p.add_argument('--disk-template',type=Path,required=True);p.add_argument('--tools',type=Path,required=True);a=p.parse_args()
 out=ROOT/'build/du-select';out.mkdir(parents=True,exist_ok=True)
 body='DU_MAP EQU 06000H\nDU_WORK EQU 06040H\n'+(ROOT/'src/utilities/common/duselect.inc').read_text()+'\n        END\n'
 expected=assemble(Path.home()/'bin/z80asm','        ORG 0100H\n'+body,out/'du-parity.bin',out/'du-parity.lst',0x100)
 with tempfile.TemporaryDirectory(prefix='du-native-') as temp:
  work=Path(temp);disks=work/'disks';disks.mkdir();shutil.copy2(a.system_disk,disks/'drivea.dsk')
  for drive in 'bcd':blank(a.disk_template,disks/f'drive{drive}.dsk')
  source=work/'DU.MAC';source.write_bytes(('        CSEG\n        .PHASE 0100H\n'+body.replace('        END\n','        .DEPHASE\n        END\n')).replace('\n','\r\n').encode()+b'\x1a')
  run('cpmcp','-f','ibm-3740',str(disks/'drivec.dsk'),str(source),'0:DU.MAC')
  for tool in ['ZSM4.COM','LINK.COM']:run('cpmcp','-f','ibm-3740',str(disks/'drived.dsk'),str(a.tools/tool),'0:'+tool)
  commands=f'''set timeout 60
spawn {a.cpmsim} -z -d {disks}
expect "A>"
send -- "B:\\r"
expect "B>"
send -- "D:ZSM4 DU=C:DU\\r"
expect -re {{Errors: +0}}
expect "B>"
send -- "D:LINK DU\\[A\\]\\r"
expect "CODE SIZE"
expect "B>"
send "\\034"
expect eof
'''
  result=run('expect','-c',commands,check=False);log=result.stdout+result.stderr;(out/'NATIVE-DU-BUILD.LOG').write_text(log)
  assert not result.returncode and 'CODE SIZE' in log,log
  target=work/'DU.COM';run('cpmcp','-f','ibm-3740',str(disks/'driveb.dsk'),'0:DU.COM',str(target))
  (out/'du-native.COM').write_bytes(target.read_bytes())
  assert target.read_bytes()[:len(expected)]==expected,'native/cross mismatch'
 print(f'DU include: {len(expected)} native byte-identical bytes')
if __name__=='__main__':main()
