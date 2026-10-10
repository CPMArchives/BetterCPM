#!/usr/bin/env python3
"""Execute COPY unsigned decimal formatting across size/count boundaries."""
import re,tempfile
from pathlib import Path
from build_ccp import assemble
from test_bios import Z80
from test_disk_utilities import ROOT

def main():
 image=(ROOT/'build/utilities/COPY.COM').read_bytes()
 listing=(ROOT/'build/utilities/copy-transient.lst').read_text()
 def addr(n):return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+n+':',listing,re.M|re.I)[1],16)
 for value in [0,1,9,10,64,99,100,255,256,999,1024,65535,65536,999999,1000000,0xffffffff]:
  c=Z80(b'');c.mem[256:256+len(image)]=image
  c.mem[addr('CTR_NUM'):addr('CTR_NUM')+4]=value.to_bytes(4,'little')
  c.setword(0x6000,0x6100)
  stub=b'\xe5\x2a\x00\x60\x77\x23\x22\x00\x60\xe1\xc9'
  a=addr('BC_PCHAR');c.mem[a:a+len(stub)]=stub
  c.run(addr('CTR_DEC'),limit=100000)
  assert bytes(c.mem[0x6100:c.word(0x6000)]).decode()==str(value),value
 # Execute allocation scanning against synthetic physical directory entries.
 # This independently covers byte/word maps and different destination blocks.
 source=f"""        ORG 5000H
        LD A,C
        CP 31
        JR Z,DPB
        CP 26
        RET Z
        CP 17
        JR Z,FIRST
        LD A,(7300H)
        OR A
        JR Z,NEXT
        LD A,0FFH
        RET
DPB:    LD HL,7000H
        RET
FIRST:  XOR A
        LD (7300H),A
        LD HL,7100H
        LD DE,{addr('BC_DMA')}
        LD BC,128
        LDIR
        XOR A
        RET
NEXT:   LD A,1
        LD (7300H),A
        LD HL,7200H
        LD DE,{addr('BC_DMA')}
        LD BC,128
        LDIR
        LD A,2
        RET
        END
"""
 with tempfile.TemporaryDirectory() as temp:
  stub=assemble(Path.home()/'bin/z80asm',source,Path(temp)/'stub.bin',Path(temp)/'stub.lst',0x5000)
 for width,shift in [(1,3),(1,4),(2,4),(2,5),(2,7)]:
  c=Z80(b'');c.mem[256:256+len(image)]=image;c.mem[0x5000:0x5000+len(stub)]=stub
  c.mem[5:8]=b'\xc3\x00\x50';c.mem[addr('BC_CSELD')]=0xc9
  c.mem[0x7002]=shift;c.mem[0x7006]=0 if width==1 else 1
  values=[1,255] if width==1 else [1,256]
  for slot,blocks,base in [(0,values,0x7100),(2,[2],0x7200)]:
   for i,block in enumerate(blocks):c.mem[base+slot*32+16+i*width:base+slot*32+16+(i+1)*width]=block.to_bytes(width,'little')
  c.run(addr('CTR_ALLOC'),limit=100000)
  assert not c.carry and int.from_bytes(c.mem[addr('CTR_K'):addr('CTR_K')+4],'little')==3*(1<<(shift-3)),(width,shift)
 print('COPY byte/word allocation maps, block sizes and 32-bit decimal boundaries pass')

if __name__=='__main__':main()
