#!/usr/bin/env python3
"""Run resident feature hints before any file operation at relocated origins."""
import re,struct
from pathlib import Path
from test_bios import Z80
ROOT=Path(__file__).resolve().parents[1]
def execute(command,base,*,strict=False,hostile=False,details=None,claimed=True):
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
 data=command.encode('latin1');assert len(data)<=255
 c.mem[0x2000:0x2100]=bytes([0xA5])*256
 c.mem[0x2000:0x2000+len(data)]=data;c.de=0x2000;c.b=len(data)
 c.mem[0x5c:0x100]=bytes(range(0xa4))
 low=bytes(c.mem[0x5c:0x100]);tail=bytes(c.mem[0x2000:0x2100])
 c.sp=0xE900;c.mem[0xE800:0xE900]=bytes([0xA5])*256
 c.ix=0x1234;c.iy=0x5678
 before=bytes(c.mem[base:base+size]);output=[];calls=[]
 def io(port):
  calls.append(c.c)
  if c.c==9:
   p=c.de
   while c.mem[p]!=36:output.append(chr(c.mem[p]));p+=1
   if hostile:c.bc=0xa5a5;c.de=0x5a5a;c.hl=0x1234
   return 0
  if c.c==2:
   value=c.e;output.append(chr(value))
   if hostile:c.bc=0xa5a5;c.de=0x5a5a;c.hl=0x1234
   return value
  if strict:raise AssertionError(('non-console service during query/rejection',command,c.c))
  if c.c==25:return 0
  if c.c==32:return 2
  if c.c in (14,26):return 0
  if c.c==31:c.hl=0x1000;return 0
  if c.c in (17,18):return 255
  raise AssertionError(('file operation during rejected option',command,c.c))
 c.port_read=io;c.run(entry,limit=200000)
 assert c.carry==claimed,(command,'incorrect ownership')
 assert c.sp==0xE900,(command,'unbalanced stack',hex(c.sp))
 assert bytes(c.mem[0x2000:0x2100])==tail,(command,'command or guard changed')
 assert bytes(c.mem[0xE800:0xE880])==bytes([0xA5])*128,(command,'stack guard')
 if strict:
  assert bytes(c.mem[0x5c:0x100])==low,(command,'FCB/page-zero state changed')
  changed=[i for i,v in enumerate(c.mem[0xE800:0xE900]) if v!=0xA5]
  if details is not None:details['stack_bytes']=256-min(changed) if changed else 0
 if strict or 'Use :' in ''.join(output) or '/VER' in command:
  assert c.ix==0x1234 and c.iy==0x5678,(command,hex(c.ix),hex(c.iy))
 return ''.join(output),calls

def main():
 from utility_help import RESIDENT_SCREENS,text,resident_identification
 from utility_versions import banner
 count=0;peak=0
 for base in (0x4000,0x8101,0xA000):
  for name in RESIDENT_SCREENS:
   resident_title=banner(name,True)
   assert resident_title.endswith(', Resident RCP)'), resident_title
   assert 'Resident' not in banner(name), name
   expected=text(name,identity=resident_title,resident=True)
   assert len(expected.splitlines())<=23 and max(map(len,expected.splitlines()))<=79
   room=127-len(name)-1
   tails=['/H','/HELP','/h','/hElP',' /HELP  ','\t/H\t',
          '/H /HELP','/VER /HELP','/HELP /VER','FILE /HELP /BOGUS',
          '/BOGUS /VER /H','X'*(room-3)+' /H', '/HELP'+' '*(room-5)]
   for tail in tails:
    details={}
    out,calls=execute(name+' '+tail,base,strict=True,hostile=True,details=details)
    assert out==expected,(name,tail,out,expected)
    peak=max(peak,details['stack_bytes']);count+=1
   for tail in ('/VER','/ver','/HELPER /VER','/VER FILE /BOGUS','\t/VER\t'):
    out,_=execute(name+' '+tail,base,strict=True,hostile=True)
    assert out==resident_identification(name),(name,tail,out);count+=1
   for tail in ('/BOGUS','/HELPER','/HELP.X','/VER=1','/VERIFY','/','FILE /BOGUS'):
    out,_=execute(name+' '+tail,base,strict=True,hostile=True)
    assert out.startswith('Invalid usage.\r\n') and 'Use '+name+' /HELP for help.' in out,(name,tail,out)
    count+=1
  for name in ('ERA','TYPE','REN','COPY','MOVE','USER'):
   out,_=execute(name,base,strict=True,hostile=True)
   assert out.startswith('Invalid usage.\r\n') and 'Use '+name+' /HELP for help.' in out,(name,out)
   count+=1
  for command in ('USER 32','USER -1','USER 1 2','CLS EXTRA','VER FILE'):
   out,_=execute(command,base,strict=True,hostile=True)
   assert out.startswith('Invalid usage.\r\n') and ' /HELP for help.' in out,(command,out)
   count+=1
  for command in ('TYPE /P','COPY /O','MOVE /O','REN NEW=','ERA BAD*.X.Y'):
   out,calls=execute(command,base)
   assert ('Invalid usage.' in out or 'Invalid filespec.' in out) and ' /HELP for help.' in out,(command,out)
   assert set(calls)<={2,9,14,25,26,31,32},(command,calls)
   count+=1
  for command in ('DIRTY /HELP','COPYCAT /H','NOTRCP /VER','/HELP'):
   out,calls=execute(command,base,strict=True,hostile=True,claimed=False)
   assert out=='' and calls==[],(command,out,calls)
   count+=1
 print(f'PASS: {count} relocated resident help/version/rejection cases; hostile BDOS, FCB/tail/stack guards; query stack peak {peak} bytes')
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
   assert out==resident_identification(command),(command,out)
  for text in ('DIR /C=3','DIR /S=X','DIR /AAA','ERA /DRV','TYPE /CTLX','TYPE /BAD','DIR B3:F*A.TXT'):
   out,_=execute(text,base)
   assert 'Use :' not in out,(text,out)
 print('PASS: relocated hints, exact option tokens, /VER, malformed input and IX/IY preservation')
def transients():
 from test_utility_finalization import execute as query
 from test_utility_versions import expected_identification
 from utility_help import text
 count=0
 for name in ('DIR','USER','CLS','VER','COPY','MOVE'):
  for tail in ('/VER',' /ver  ','X /VER /BOGUS','/VER /VER','\t/VER\t','X'*122+' /VER'):
   actual,_=query(name,tail)
   assert actual==expected_identification(name),(name,tail,actual)
   count+=1
  # COPY retains its independently specified richer transient screen.
  expected=query(name,'/HELP')[0] if name=='COPY' else text(name)
  assert 'Resident' not in expected and 'Usage:' in expected
  for tail in ('/h',' /H  ','/ver /h /BOGUS','/VER /HELP','\t/h\t','/h /help','/h'+' '*125,'X'*124+' /h'):
   actual,_=query(name,tail)
   assert actual==expected,(name,tail,actual)
   count+=1
 print(f'PASS: {count} transient query/identity/alias cases; resident decoration absent')

if __name__=='__main__':
 main()
 transients()
