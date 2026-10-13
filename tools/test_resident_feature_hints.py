#!/usr/bin/env python3
"""Run resident feature hints before any file operation at relocated origins."""
import re,struct
from pathlib import Path
from test_bios import Z80
ROOT=Path(__file__).resolve().parents[1]
def execute(command,base):
 carrier=(ROOT/'build/cpx/RCP.CPX').read_bytes()
 linked,size=struct.unpack_from('<HH',carrier,10)
 count,_,payload,table=struct.unpack_from('<4H',carrier,22)
 data=bytearray(carrier[payload:payload+size])
 for i in range(count):
  off=struct.unpack_from('<H',carrier,table+2*i)[0]
  struct.pack_into('<H',data,off,(struct.unpack_from('<H',data,off)[0]+base-linked)&65535)
 listing=(ROOT/'build/cpx/rcp.lst').read_text()
 entry=int(re.search(r'^([0-9a-f]{4})\s+.*\bBC_COMMAND:',listing,re.M|re.I)[1],16)-linked+base
 c=Z80(b'');c.mem[base:base+size]=data;c.mem[5:8]=bytes((0xDB,254,0xC9))
 c.mem[0x2000:0x2000+len(command)]=command.encode();c.de=0x2000;c.b=len(command)
 c.ix=0x1234;c.iy=0x5678
 before=bytes(c.mem[base:base+size]);output=[];calls=[]
 def io(port):
  calls.append(c.c)
  if c.c==9:
   p=c.de
   while c.mem[p]!=36:output.append(chr(c.mem[p]));p+=1
   return 0
  if c.c==2:output.append(chr(c.e));return c.e
  if c.c==25:return 0
  if c.c==32:return 2
  if c.c in (14,26):return 0
  if c.c==31:c.hl=0x1000;return 0
  if c.c in (17,18):return 255
  raise AssertionError(('file operation during rejected option',command,c.c))
 c.port_read=io;c.run(entry,limit=200000)
 assert c.carry
 if 'Use :' in ''.join(output) or '/VER' in command:
  assert c.ix==0x1234 and c.iy==0x5678,(command,hex(c.ix),hex(c.iy))
 return ''.join(output),calls

def main():
 cases={'DIR':['/WHEREIS','/C=2','/S=N-','/Z=E','/A','/P'], 'ERA':['/D','/Y','/C','/R','/Q'],
        'TYPE':['/7','/CTL','/T'], 'REN':['/DRY','/QQ','/C','/P'], 'COPY':['/V','/B','/BACKUP']}
 for base in (0x4000,0x8101,0xA000):
  for command,options in cases.items():
   for option in options:
    for tail in (option+' B3:*.TXT', 'B3:*.TXT '+option):
     out,calls=execute(command+' '+tail,base)
     assert 'Use :'+command+'.' in out,(command,option,out)
     assert not any(f not in (2,9) for f in calls),(command,calls)
  for command in ('DIR','ERA','TYPE','REN','COPY','MOVE','USER','CLS','VER'):
   out,_=execute(command+' /VER',base)
   assert 'BetterCP/M '+command in out and 'Build 009' in out
  for text in ('DIR /C=3','DIR /S=X','DIR /AAA','ERA /DRV','TYPE /CTLX','TYPE /BAD','DIR B3:F*A.TXT'):
   out,_=execute(text,base)
   assert 'Use :' not in out,(text,out)
 print('PASS: relocated hints, exact option tokens, /VER, malformed input and IX/IY preservation')
if __name__=='__main__':main()
