#!/usr/bin/env python3
"""Run assembled retry policy with injected single-attempt outcomes.

DC_TRY substitutes a controller outcome and captures submitted write bytes;
DC_ERR substitutes force-interrupt completion. The real retry and inversion
instructions execute. This is not an emulation of WD controller timing.
"""
from pathlib import Path
import re
from test_bios import Z80
from system_layout import LAYOUT
ROOT=Path(__file__).resolve().parents[1]
def main():
    listing=(ROOT/'build/system/disk.lst').read_text()
    syms={n:int(a,16) for a,n in re.findall(r'^([0-9a-fA-F]{4})\s+.*?\b(DC_\w+):',listing,re.M)}
    def word(v): return bytes((v&255,v>>8))
    cases=0
    for write in (False,True):
      for size in range(4):
       for inverted in (False,True):
        for statuses,attempts in [([0],1),([8,0],2),([4,16,0],3),([8,8,8],3),([1,0],2),([64],1),([8,64],2)]:
         c=Z80(b'');data=(ROOT/'build/system/disk.bin').read_bytes();base=LAYOUT['DISK']
         c.mem[base:base+len(data)]=data
         # Capture byte 0 of each submitted buffer, then return next status.
         stub=bytes([0x2a])+word(0x7100)+bytes([0x3a])+word(0x8000)+bytes([0x77,0x23,0x22])+word(0x7100)+bytes([0x2a])+word(0x7102)+bytes([0x7e,0x23,0x22])+word(0x7102)+bytes([0xb7,0xc9])
         c.mem[0x7000:0x7000+len(stub)]=stub
         c.mem[syms['DC_TRY']:syms['DC_TRY']+3]=bytes([0xc3,0,0x70])
         c.mem[syms['DC_ERR']]=0xc9
         c.setword(0x7100,0x7200);c.setword(0x7102,0x7300)
         c.mem[0x7300:0x7300+len(statuses)]=bytes(statuses)
         c.mem[syms['DC_FLAGS']]=0x10 if inverted else 0
         c.mem[syms['DC_SIZE']]=size
         original=bytes((i*7+0x35)&255 for i in range(128<<size))
         c.mem[0x8000:0x8000+len(original)]=original
         c.hl=0x8000;c.sp=0x6000
         c.run(syms['DC_WRITE' if write else 'DC_READ'],limit=60000)
         assert c.word(0x7102)==0x7300+attempts,(write,size,statuses)
         assert c.a==statuses[attempts-1] and c.z==(c.a==0)
         assert c.sp==0x6000
         assert c.mem[0x8000:0x8000+len(original)]==original
         expected=original[0]^(255 if write and inverted else 0)
         assert c.mem[0x7200:0x7200+attempts]==bytes([expected])*attempts
         cases+=1
    print(f'{cases} retry cases passed: recoverable/persistent errors, write protection, polarity, sizes, stack')
if __name__=='__main__': main()
