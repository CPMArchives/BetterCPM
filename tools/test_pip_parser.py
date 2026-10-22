#!/usr/bin/env python3
"""Historical assignment/concatenation framing, string delimiters and pure version."""
import re,struct,hashlib,json
from pathlib import Path
from test_bios import Z80,SENTINEL
from utility_versions import banner
ROOT=Path(__file__).resolve().parents[1]
def cpu():
 c=Z80(b'');data=(ROOT/'build/pip-development/PIP.COM').read_bytes();c.mem[256:256+len(data)]=data
 return c
def addr(label):
 text=(ROOT/'build/pip-development/pip.lst').read_text()
 return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+label+':',text,re.M|re.I)[1],16)
def scan(text):
 c=cpu();c.mem[0x6000:0x6000+len(text)]=text.encode();c.hl=0x6000;c.b=len(text)
 c.run(addr('PP_PARSE'),limit=100000)
 out=[]
 for i in range(c.mem[addr('PP_COUNT')]):
  p=addr('PP_SPANS')+3*i;start=c.mem[p]|c.mem[p+1]<<8;length=c.mem[p+2];out.append(bytes(c.mem[start:start+length]).decode())
 assert bytes(c.mem[0x6000:0x6000+len(text)])==text.encode()
 return c.carry,out
def invocation(text,keys=()):
 c=cpu();c.mem[0:3]=bytes((0xC3,SENTINEL&255,SENTINEL>>8));c.mem[0x80]=len(text);c.mem[0x81:0x81+len(text)]=text.encode();c.mem[5:8]=bytes((0xDB,254,0xC9));output=[];calls=[];lines=iter(keys);state={'drive':1,'user':7}
 def io(port):
  calls.append(c.c)
  if c.c==180:c.hl=0;return 0
  if c.c==11:return 0
  if c.c==0:c.pc=SENTINEL;return 0
  if c.c==25:return state['drive']
  if c.c==32:
   if c.e!=255:state['user']=c.e
   return state['user']
  if c.c==14:state['drive']=c.e;return 0
  if c.c==26:return 0
  if c.c==15:return 255
  if c.c==10:
   line=next(lines);c.mem[c.de+1]=len(line);c.mem[c.de+2:c.de+2+len(line)]=line.encode();return 0
  if c.c==9:
   p=c.de
   while c.mem[p]!=36:output.append(chr(c.mem[p]));p+=1
   return 0
  raise AssertionError(('unexpected/mutating BDOS',c.c))
 c.port_read=io;c.run(256,limit=100000)
 assert state=={'drive':1,'user':7}
 return ''.join(output),calls
def main():
 cases={'B:=A:*.COM':['B:','A:*.COM'], ' NEW.TXT = A3:ONE.TXT, B7:TWO.TXT ':['NEW.TXT','A3:ONE.TXT','B7:TWO.TXT'],
        'LST:=X.ASM[NT8U]':['LST:','X.ASM[NT8U]'], 'D=F[Sfoo, bar=[]\x1aQend\x1a],G':['D','F[Sfoo, bar=[]\x1aQend\x1a]','G'],
        'B:_A:F.COM':['B:','A:F.COM']}
 for text,expected in cases.items():
  bad,parts=scan(text);assert not bad and parts==expected,(text,bad,parts)
 for text in ['', 'A B','A=','A=,B','A,B=C','A=B=C','A=B[V','A=B]','A=B[Sunterminated]','A=B[[V]]']:
  bad,parts=scan(text);assert bad and not parts,(text,parts)
 tail='A='+','.join('B' for _ in range(63));assert len(tail)==127
 bad,parts=scan(tail);assert not bad and len(parts)==64
 out,calls=invocation('/VER');assert banner('PIP') in out and calls==[9],(out,calls)
 out,calls=invocation('A=B[Shello /VER, world\x1a]');assert 'NO FILE' in out and 'Invalid /VER' not in out
 out,calls=invocation('A=B /VER');assert 'Invalid /VER usage.' in out and calls==[9]
 out,calls=invocation('',keys=['PRN:=CON:','BAD','']);assert out.count('*')==3 and 'DEVICE UNAVAILABLE' in out and 'INVALID FORMAT' in out
 data=(ROOT/'build/pip-development/PIP.COM').read_bytes();assert data[3:10]==bytes((0xC9,0,0,0xC9,0,0,0x1A))
 info=json.loads((ROOT/'third_party/dri-pip/provenance.json').read_text());assert hashlib.sha256((ROOT/'third_party/dri-pip/pip.plm').read_bytes()).hexdigest()==info['sha256']
 print('PASS: PIP assignment, concatenation, extraction delimiters, full tail, interactive loop, pure /VER and provenance')
if __name__=='__main__':main()
