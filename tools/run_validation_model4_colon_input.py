#!/usr/bin/env python3
"""Bounded raw-key and CCP entry regression for the historical colon anomaly."""
import argparse,json,shutil,subprocess
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw,add_file,FILESYSTEM_FIRST_SECTOR,SECTOR_SIZE,DIRECTORY_ENTRIES
from build_montezuma_extended_790k import build
from build_ccp import assemble
from run_validation_model4 import audit_files
from run_validation_returning import sha
from run_trs80_command import DEFAULT_EMULATOR,key_args
from test_sysgen_install import screen
from trs80gp_launch import run

def probe():
 s=' ORG 100H\n'
 for delay in (12,25,60):
  s+=f''' LD DE,READY{delay}
 LD C,9
 CALL 5
 LD HL,BUFFER
 LD B,9
READ{delay}:
 PUSH BC
 PUSH HL
 LD E,0FFH
 LD C,6
 CALL 5
 POP HL
 POP BC
 OR A
 JR Z,READ{delay}
 LD (HL),A
 INC HL
 DJNZ READ{delay}
 LD DE,LABEL{delay}
 LD C,9
 CALL 5
 LD HL,BUFFER
 LD B,9
PRINT{delay}:
 PUSH BC
 PUSH HL
 LD A,(HL)
 CALL HEXBYTE
 POP HL
 POP BC
 INC HL
 DJNZ PRINT{delay}
 LD DE,NEWLINE
 LD C,9
 CALL 5
'''
 s+=''' LD DE,DONE
 LD C,9
 CALL 5
 LD C,0
 JP 5
HEXBYTE:
 PUSH AF
 RRCA
 RRCA
 RRCA
 RRCA
 AND 15
 CALL NIBBLE
 POP AF
 AND 15
 CALL NIBBLE
 LD E,32
 LD C,2
 JP 5
NIBBLE:
 ADD A,48
 CP 58
 JR C,DIGIT
 ADD A,7
DIGIT:
 LD E,A
 LD C,2
 JP 5
NEWLINE: DB 13,10,'$'
DONE: DB 'INPUT PHASES COMPLETE',13,10,'$'
BUFFER: DS 9
'''
 for delay in (12,25,60):s+=f"READY{delay}: DB 'INPUT{delay} READY',13,10,'$'\nLABEL{delay}: DB 'CAPTURE{delay} ','$'\n"
 return s+' END\n'

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('baseline','output'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--monitor',action='store_true');a=p.parse_args();w=a.output;w.mkdir(parents=True,exist_ok=False)
 report=json.loads((a.baseline/'report.json').read_text());original=a.baseline/report['image'];assert sha(original)==report['sha256'];raw=extract_raw(original.read_bytes())
 for i in range(DIRECTORY_ENTRIES):
  at=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE+i*32
  if raw[at]==0 and raw[at+1:at+12]==b'STARTUP SUB':raw[at]=229
 commands=[':VER /BANNER']+(['RSX LOAD M4SCRN','RSX LOAD ADM3A'] if a.monitor else [])+['KPROBE','IREADY']
 add_file(raw,'STARTUP.SUB',('\r\n'.join(commands)+'\r\n\x1a').encode())
 source=probe();(w/'probe.asm').write_text(source);code=assemble(Path.home()/'bin/z80asm',source,w/'KPROBE.COM',w/'probe.lst',0x100);add_file(raw,'KPROBE.COM',code)
 add_file(raw,'IREADY.COM',bytes.fromhex('110b010e09cd0500c30000')+b'CCP INPUT READY\r\n$')
 image=w/'a.dmk';image.write_bytes(build(bytes(raw)));shutil.copy2(__file__,w/'executed-runner.py')
 cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(image),'-itime','15000']
 for delay in (12,25,60):cmd+=['-iw',f'INPUT{delay} READY','-id','120']+key_args('A0:MEDIA\r',delay=delay)+['-iw',f'CAPTURE{delay}','-id','120','-it']
 cmd+=['-iw','CCP INPUT READY','-id','6000']+key_args('A0:VER /VER\r',delay=60)+['-iw','BetterCP/M VER 1.0','-id','6000','-it']
 cmd+=key_args('RSX LISX\x08T\r',delay=60)+['-iw','TPA available:','-id','6000','-it']
 if a.monitor:
  cmd+=key_args('RSX UNLOAD ADM3A\r',delay=60)+['-id','6000']+key_args('RSX UNLOAD M4SCRN\r',delay=60)+['-id','6000']+key_args('RSX LIST\r',delay=60)
 cmd+=['-iw','TPA available: 53K','-id','120','-it','-ix'];(w/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n');run(cmd,cwd=w,timeout=900)
 texts=[screen(f) for f in sorted(w.glob('trs80-text-*.bin'))]
 for i,t in enumerate(texts):(w/f'screen-{i}.txt').write_text(t+'\n')
 for delay in (12,25,60):assert any(f'CAPTURE{delay} 41 30 3A 4D 45 44 49 41 0D' in t for t in texts),(delay,texts)
 assert any('A0> A0:VER' in t or 'A0>A0:VER' in t for t in texts)
 assert any('A0>RSX LIST' in t for t in texts)
 assert 'No RSXs loaded' in texts[-1] and 'TPA available: 53K' in texts[-1]
 audit=audit_files(original,image,dict(report,included=[f for f in report['included'] if f['name']!='STARTUP.SUB']),w)
 assert extract_raw(original.read_bytes())[:20480]==extract_raw(image.read_bytes())[:20480]
 fs=subprocess.run(['fsck.cpm','-T','raw,pcw800','-f','bettercpm-default','-n',str(w/'file-audit/after.raw')],cwd=w/'file-audit',capture_output=True,check=True);(w/'filesystem.txt').write_bytes(fs.stdout+fs.stderr)
 assert sha(original)==report['sha256']
 (w/'result.json').write_text(json.dumps({'status':'PASS','monitor':a.monitor,'timings':[12,25,60],'expected_ascii_hex':'41303a4d454449410d','baseline_sha256':report['sha256'],'runner_sha256':sha(w/'executed-runner.py'),'probe_sha256':sha(w/'KPROBE.COM'),'emulator_sha256':sha(DEFAULT_EMULATOR),'file_audit':audit,'scope':'Native keyboard-matrix bytes at three timings, qualified CCP command, Backspace editing and warm return; bounded regression does not establish cause of historical intermittent anomaly or test macOS physical keyboard mappings.'},indent=2)+'\n');print('PASS native raw-key/CCP input regression',w)
if __name__=='__main__':main()
