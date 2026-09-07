#!/usr/bin/env python3
"""Run real BDOS directory operations past entry 255, with RAM disk I/O."""
from pathlib import Path
import tempfile
import re
from build_ccp import assemble
from system_layout import LAYOUT as L
from test_bios import Z80
ROOT=Path(__file__).resolve().parents[1]

def main():
 for entries in (320,384):
  cpu=Z80((ROOT/'build/bios/bios.bin').read_bytes());cpu.sp=0x4000
  for file,key in [('bdos/bdos','BDOS'),('system/tables','TABLES'),('system/disk','DISK')]:
   data=(ROOT/'build'/f'{file}.bin').read_bytes();cpu.mem[L[key]:L[key]+len(data)]=data
  track=cpu.word(cpu.word(L['BIOS']+31)+2)
  sector=cpu.word(cpu.word(L['BIOS']+34)+2)
  dma=cpu.word(cpu.word(L['BIOS']+37)+2)
  source=f'''        ASEG
        ORG 9000H
READ:   CALL OFFSET
        LD DE,({dma})
        LD BC,128
        LDIR
        XOR A
        RET
WRITE:  CALL OFFSET
        EX DE,HL
        LD HL,({dma})
        LD BC,128
        LDIR
        XOR A
        RET
OFFSET: LD HL,({track})
        LD DE,2
        OR A
        SBC HL,DE
        LD B,L
        LD HL,({sector})
        LD DE,80
        INC B
PLUS:   DJNZ ADDTRK
        JR MULT
ADDTRK: ADD HL,DE
        JR PLUS
MULT:   ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        LD DE,6000H
        ADD HL,DE
        RET
        END
'''
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);code=assemble(Path.home()/'bin/z80asm',source,p/'io.bin',p/'io.lst',0x9000)
   write=int(re.search(r'^([0-9a-f]{4})\s+.*?WRITE:',(p/'io.lst').read_text(),re.M|re.I)[1],16)
  cpu.mem[0x9000:0x9000+len(code)]=code
  cpu.mem[L['BIOS']+39:L['BIOS']+42]=bytes([0xc3,0,0x90])
  cpu.mem[L['BIOS']+42:L['BIOS']+45]=bytes([0xc3,write&255,write>>8])
  dpb=L['TABLES']+17
  cpu.setword(dpb+7,entries-1);cpu.mem[dpb+9]=0xfc
  cpu.mem[0x6000:0x6000+entries*32]=bytes([0xe5])*(entries*32)
  for i in range(entries-1):
   at=0x6000+i*32
   cpu.mem[at:at+32]=bytes([0])+f'F{i:07d}TXT'.encode()+bytes(20)
  fcb=0x5000
  cpu.mem[fcb:fcb+36]=bytes([1])+b'LASTFILETXT'+bytes(24)
  def call(n):
   cpu.c=n;cpu.de=fcb;cpu.run(L['BDOS'],limit=1000000)
   assert cpu.sp==0x4000
   return cpu.a
  assert call(22)!=255, entries
  assert call(16)!=255, entries
  assert call(15)!=255, entries
  assert call(17)==3, entries
  at=0x6000+(entries-1)*32
  assert cpu.mem[at+1:at+12]==b'LASTFILETXT'
  cpu.mem[fcb+1:fcb+9]=b'FULLTEST'
  assert call(22)==255, entries
 print('PASS: create, close, open, search and full-directory rejection at entries 319 and 383')
if __name__=='__main__':main()
