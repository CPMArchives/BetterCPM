#!/usr/bin/env python3
"""Execute WHEREIS with BIOS directory fixtures and explicit recoverable failures."""
import re,struct
from pathlib import Path
from test_bios import Z80,SENTINEL
ROOT=Path(__file__).resolve().parents[1]
def execute(tail,rows,configured=(0,1),read_fail=(),open_fail=(),ceiling=0xD501):
 c=Z80(b'');image=(ROOT/'build/utilities/DIR.COM').read_bytes();c.mem[256:256+len(image)]=image
 c.mem[0:3]=bytes((0xC3,SENTINEL&255,SENTINEL>>8));c.setword(1,0x7003);c.setword(6,ceiling)
 c.mem[5]=0xDB;c.mem[6]=254;c.mem[7]=0xC9
 # BDOS trap cannot overlap the public ceiling pointer; use an indirect jump.
 c.mem[5:8]=bytes((0xC3,ceiling&255,ceiling>>8));c.mem[ceiling:ceiling+3]=bytes((0xDB,254,0xC9))
 c.mem[0x80]=len(tail);c.mem[0x81:0x81+len(tail)]=tail.encode()
 for offset,port in ((27,201),(30,202),(33,203),(36,204),(39,205),(48,206)):
  c.mem[0x7000+offset:0x7003+offset]=bytes((0xDB,port,0xC9))
 c.setword(0x720A,0x7300)
 dpb=struct.pack('<HBBBHHBBHH',16,4,15,0,255,63,0xC0,0,16,2)
 c.mem[0x7300:0x730F]=dpb
 state={'drive':0,'track':2,'sector':0,'dma':0x80};out=[];calls=[];reads=[]
 def io(port):
  port&=255
  if port==201:
   state['drive']=c.c;c.hl=0 if c.c in open_fail else 0x7200;return 0
  if port==202:state['track']=c.bc;return 0
  if port==203:state['sector']=c.bc;return 0
  if port==204:state['dma']=c.bc;return 0
  if port==206:c.hl=c.bc;return 0
  if port==205:
   rec=(state['track']-2)*16+state['sector'];drive=state['drive'];reads.append((drive,rec))
   if (drive,rec) in read_fail:return 1
   raw=b''.join(rows.get(drive,())).ljust(2048,b'\xe5');p=128*rec
   c.mem[state['dma']:state['dma']+128]=raw[p:p+128];return 0
  assert port==254
  calls.append(c.c)
  if c.c==0:c.pc=SENTINEL;return 0
  if c.c==25:return 0
  if c.c==32:return 2
  if c.c in (14,26):return 0
  if c.c==181:
   drive=c.mem[c.de];c.mem[c.de+1:c.de+65]=bytes((drive if drive in configured else 255,))+bytes(63);return 0
  if c.c==2:
   value=c.e;out.append(chr(value));c.hl=0xDEAD;c.bc=0xBEEF;return value
  if c.c==9:
   p=c.de
   while c.mem[p]!=36:out.append(chr(c.mem[p]));p+=1
   return 0
  raise AssertionError(('unexpected BDOS file operation',c.c,tail))
 c.port_read=io;c.run(256,limit=5000000)
 return ''.join(out),calls,reads,state

def row(user,name,attr=0,extent=0):
 stem,_,ext=name.partition('.');r=bytearray(32);r[0]=user;r[1:12]=(stem.ljust(8)+ext.ljust(3)).encode();r[12]=extent
 for bit in range(3):r[9+bit]|=((attr>>bit)&1)<<7
 return bytes(r)
def main():
 rows={0:[row(0,'ED.COM',2),row(0,'ED.COM',2,1),row(2,'ED.COM'),row(31,'LAST.COM')],1:[row(2,'ED.COM'),row(3,'FOO.COM',4),row(3,'FOO.COM',4,2)]}
 out,calls,reads,s=execute('/WHEREIS ED.COM',rows)
 assert out=='\r\nA0:ED.COM\r\nA2:ED.COM\r\nB2:ED.COM\r\n3 MATCHES\r\n',out
 assert len(reads)==32 and s['drive']==0 and s['dma']==0x80
 for tail,expected in [('B:ED.COM /WHEREIS','B2:ED.COM'),('/WHEREIS B[-]:*.COM[$ARC]','B3:FOO.COM'),('/WHEREIS [B3,A31]:*.COM','A31:LAST.COM')]:
  out,_,_,_=execute(tail,rows);assert expected in out,out
 out,_,_,_=execute('/WHEREIS MISSING.COM',rows,read_fail=((1,0),))
 assert 'directory read error.' in out and out.endswith('DIR: No matches found.\r\nSearch incomplete.\r\n'),out
 out,_,_,_=execute('/WHEREIS ED.COM',rows,read_fail=((1,1),))
 assert 'A0:ED.COM' in out and 'B2:ED.COM' not in out and out.endswith('Search incomplete.\r\n'),out
 out,_,_,_=execute('/WHEREIS C[-]:ED.COM',rows)
 assert out.count('unavailable.')==1 and 'Search incomplete.' in out,out
 for tail in ['/WHEREIS','/WHEREIS ED.COM PIP.COM','/WHEREIS /A ED.COM','/P ED.COM /WHEREIS','/WHEREIS /C=2 ED.COM','/WHEREIS ED.COM /VER','/WHEREISX ED.COM','/WHEREIS B:F*A.COM']:
  out,calls,reads,_=execute(tail,rows);assert 'Invalid' in out and not reads,(tail,out)
 out,_,_,_=execute('/WHEREIS ED.COM',rows,ceiling=0x5000)
 assert 'capacity exceeded.' in out and 'Search incomplete.' in out,out
 print('PASS: WHEREIS global/explicit inheritance, predicates, extents, order, bounded memory and recoverable errors')
if __name__=='__main__':main()
