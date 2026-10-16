#!/usr/bin/env python3
"""Actual Model 4 boot operand save, live preservation and next-cold restore."""
import tempfile
from pathlib import Path
from build_ccp import assemble
from test_disk_utilities import ROOT,medium
from test_config_sysgen import logical
from run_trs80_command import DEFAULT_EMULATOR,key_args
from trs80gp_launch import run

def main():
 parent=ROOT/'build/test-results/config-iobyte-model4';parent.mkdir(parents=True,exist_ok=True)
 work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));extras=[]
 for value in (0x95,0x55):
  stem=f'IO{value:02X}';source=f''' ORG 100H
 LD C,7
 CALL 5
 CP {value}
 LD DE,BAD
 JR NZ,SHOW
 LD A,(3)
 CP {value}
 JR NZ,SHOW
 LD DE,GOOD
SHOW: LD C,9
 CALL 5
 RET
GOOD: DB '{stem} PASS','$'
BAD: DB '{stem} FAIL','$'
 END
'''
  extras.append((stem+'.COM',assemble(Path.home()/'bin/z80asm',source,work/(stem+'.COM'),work/(stem+'.lst'),256)))
 original=medium(extras);image=work/'a.dmk';image.write_bytes(original)
 args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(image),'-id','2500']
 for command,capture in [('IO95\r',True),('CONFIG /IOBYTE=85\r',False),('Y',True),('IO95\r',True)]:
  args+=key_args(command)+['-id','18000' if command.startswith('CONFIG') or command=='Y' else '4000']
  if capture:args+=['-it']
 args+=['-ix'];run(args,cwd=work,check=True,timeout=110)
 def text(n):
  raw=(work/f'trs80-text-{n}.bin').read_bytes()[:1920]
  return '\n'.join(bytes(c&127 for c in raw[i:i+80]).decode('ascii').rstrip() for i in range(0,1920,80))
 assert 'IO95 PASS' in text(0),text(0)
 assert 'Disk-boot IOBYTE saved; live unchanged.' in text(1),text(1)
 assert 'IO95 PASS' in text(2),text(2)
 before=logical(original);after=logical(image.read_bytes());expected=bytearray(before);expected[513]=0x55
 assert after==bytes(expected),'save changed another logical disk byte'
 cold=work/'cold';cold.mkdir()
 args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(image),'-id','2500']+key_args('IO55\r')+['-id','5000','-it','-ix']
 run(args,cwd=cold,check=True,timeout=40)
 raw=(cold/'trs80-text-0.bin').read_bytes();screen=bytes(c&127 for c in raw).decode('ascii')
 assert 'IO55 PASS' in screen,screen
 assert logical(image.read_bytes())==after,'cold boot wrote saved default'
 print('PASS Model 4 exact boot operand save, live preservation, cold restore and warm preservation;',work)
if __name__=='__main__':main()
