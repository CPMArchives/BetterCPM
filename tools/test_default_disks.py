#!/usr/bin/env python3
"""Boot the high-capacity profile and read/write the end of all data disks."""
from pathlib import Path
import tempfile,subprocess
from build_ccp import assemble
from system_layout import LAYOUT as L
from test_disk_utilities import medium,keys
from run_trs80_command import DEFAULT_EMULATOR
ROOT=Path(__file__).resolve().parents[1]

def main():
 with tempfile.TemporaryDirectory(prefix='bettercpm-default-disks-') as tmp:
  w=Path(tmp)
  source='''        ASEG
        ORG 100H
        LD SP,4000H
        LD A,1
        LD (DRIVE),A
NEXT:   LD A,(DRIVE)
        LD C,A
        CALL SEL
        LD A,H
        OR L
        JP Z,FAIL
        LD BC,159
        CALL TRACK
        LD BC,39
        CALL SECTOR
        LD BC,3000H
        CALL DMA
        CALL READ
        OR A
        JP NZ,FAIL
        LD HL,3000H
        LD B,128
FILL:   LD A,(HL)
        CP 0E5H
        JP NZ,FAIL
        LD (HL),05AH
        INC HL
        DJNZ FILL
        LD C,0
        CALL WRITE
        OR A
        JP NZ,FAIL
        CALL READ
        OR A
        JP NZ,FAIL
        LD HL,3000H
        LD B,128
CHECK:  LD A,(HL)
        CP 05AH
        JP NZ,FAIL
        INC HL
        DJNZ CHECK
        LD A,(DRIVE)
        INC A
        LD (DRIVE),A
        CP 4
        JR C,NEXT
        LD DE,OK
        JR REPORT
FAIL:   LD DE,BAD
REPORT: LD C,9
        CALL 5
        JP 0
OK:     DB 'THREE 800K DATA DRIVES READ WRITE PASS',13,10,'$'
BAD:    DB 'DEFAULT DRIVE TEST FAILED',13,10,'$'
DRIVE:  DB 0
'''
  for name,offset in [('SEL',27),('TRACK',30),('SECTOR',33),('DMA',36),('READ',39),('WRITE',42)]:
   source+=f'{name} EQU {L["BIOS"]+offset}\n'
  code=assemble(Path.home()/'bin/z80asm',source,w/'DEFTEST.COM',w/'probe.lst',0x100)
  original=medium([('DEFTEST.COM',code)])
  (w/'drivea.dmk').write_bytes(original)
  profile=ROOT/'build/test-configurations/high-capacity'
  for l in 'bcd':(w/f'drive{l}.dmk').write_bytes((profile/f'drive{l}.dmk').read_bytes())
  args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo']
  for i,l in enumerate('abcd'):args += [f'-d{i}',str(w/f'drive{l}.dmk')]
  args+=['-id','3500']+keys('DEFTEST\r')+['-id','12000','-it','-ix']
  subprocess.run(args,cwd=w,check=True,timeout=180)
  raw=next(w.glob('trs80-text-*.bin')).read_bytes()[:1920]
  text='\n'.join(bytes(c&127 for c in raw[i:i+80]).decode('ascii').rstrip() for i in range(0,1920,80))
  (ROOT/'build/test-configurations/high-capacity/verification.txt').write_text(text+'\n')
  assert 'THREE 800K DATA DRIVES READ WRITE PASS' in text,text
  assert 'A0>' in text,text
  assert (w/'drivea.dmk').read_bytes()==original
  print('PASS: boots 780K system; reads and writes final 128-byte record of each 800K data disk; returns to A; system disk unchanged.')
if __name__=='__main__':main()
