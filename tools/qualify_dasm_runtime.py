#!/usr/bin/env python3
"""Measure the normal resident-profile active BDOS ceiling on both targets."""
import argparse,json,re,subprocess
from pathlib import Path
from dasm_native import campaign,DEFAULT_SYSTEM

SOURCE=''' ASEG
 ORG 100H
 LD DE,TITLE
 LD C,9
 CALL 5
 LD HL,(6)
 LD A,H
 CALL BYTE
 LD A,L
 CALL BYTE
 LD DE,TAIL
 LD C,9
 CALL 5
 RET
BYTE:
 PUSH AF
 RRCA
 RRCA
 RRCA
 RRCA
 CALL NIBBLE
 POP AF
NIBBLE:
 AND 15
 ADD A,'0'
 CP '9'+1
 JR C,CHAR
 ADD A,7
CHAR:
 PUSH BC
 PUSH DE
 PUSH HL
 LD E,A
 LD C,2
 CALL 5
 POP HL
 POP DE
 POP BC
 RET
TITLE: DB 'DASM ACTIVE CEILING ', '$'
TAIL: DB 'H',13,10,'$'
 END
'''

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--system',type=Path,default=DEFAULT_SYSTEM);p.add_argument('--utilities',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 source=a.output/'QTPA.MAC';source.write_text(SOURCE)
 subprocess.run([str(Path.home()/'bin/z80asm'),'-fb','-o'+str(a.output/'QTPA.COM'),str(source)],check=True,capture_output=True)
 image=(a.output/'QTPA.COM').read_bytes();report={'scope':'measured normal resident-profile active ceiling','platforms':{}}
 for platform in ('z80pack','trs80gp'):
  commands=['A:RSX LOAD ZPRTC','A:RSX LIST'] if platform=='z80pack' else ['RSX LIST']
  commands+=['QTPA','B:DASM /VER']
  log,out=campaign(platform,{'QTPA.COM':image},commands,a.output/platform,system=a.system,utilities=a.utilities)
  values=re.findall(rb'DASM ACTIVE CEILING ([0-9A-F]{4})H',log);assert values
  ceiling=int(values[-1],16);assert ceiling>=0xb810
  if platform=='trs80gp':assert b'M4SCRN' in log and b'ADM3A' in log
  else:assert b'ZPRTC' in log
  report['platforms'][platform]={'status':'PASS','active_ceiling':f'{ceiling:04X}','input_capacity':8192,'resident_profile':'M4SCRN+ADM3A' if platform=='trs80gp' else 'ZPRTC','execution_report':platform+'/execution.json'}
  (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',platform,'normal active ceiling',f'{ceiling:04X}',flush=True)
if __name__=='__main__':main()
