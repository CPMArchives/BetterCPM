#!/usr/bin/env python3
"""DRI case/parity ordering across disk, device and wildcard paths."""
from test_pip_transfer import execute,key

def transform(data,options):
 result=bytearray()
 for value in data:
  if 'Z' in options:value&=127
  if 'U' in options and 97<=value<=122:value-=32
  elif 'U' not in options and 'L' in options and 65<=value<=90:value+=32
  result.append(value)
 return bytes(result)

def main():
 src=key(0,2,'SRC.COM');dest=key(1,7,'DEST.COM')
 data=bytes(range(256))
 for option in ['U','L','UL','Z','ZU','ZL','ZUL']:
  out,fs,_,_=execute('B7:DEST.COM=A2:SRC.COM[OV'+option+']',{src:(data,0)})
  assert out=='' and fs[dest][0]==transform(data,option),(option,out)
 text=key(0,2,'SRC.TXT');data=b'aZ\xe1\x9aAFTER'
 out,fs,_,_=execute('B7:DEST.TXT=A2:SRC.TXT[ZU]',{text:(data,0)})
 assert fs[key(1,7,'DEST.TXT')][0]==b'AZA'+b'\x1a'*125
 out,_,_,_=execute('CON:=A2:SRC.TXT[L]',{text:(b'Az\x1a',0)})
 assert out=='az'
 for dev in ['CON','RDR','INP']:
  out,fs,_,_=execute('B7:DEST.TXT='+dev+':[ZU]',{},input_bytes=b'aZ\xe1\x9a',patch_in=True)
  assert out=='' and fs[key(1,7,'DEST.TXT')][0]==b'AZA'+b'\x1a'*125
 one=key(0,2,'ONE.TXT');two=key(2,3,'TWO.TXT')
 out,fs,_,_=execute('B7:DEST.TXT=A2:ONE.TXT[U],C3:TWO.TXT[L]',{one:(b'one\x1a',0),two:(b'TWO\x1a',0)})
 assert fs[key(1,7,'DEST.TXT')][0]==b'ONEtwo'+b'\x1a'*122
 out,fs,_,_=execute('B7:=A2:*.TXT[UZ]',{one:(b'one\x1a',5)})
 assert fs[key(1,7,'ONE.TXT')]==[b'ONE'+b'\x1a'*125,5]
 out,_,_,_=execute('LST:=INP:[L],EOF:,NUL:',{},input_bytes=b'ABC\x1a',patch_in=True)
 assert out.encode()==b'abc\x1a'+bytes(40)
 print('PASS: PIP U/L/Z ASCII bounds, precedence, parity EOF, binary records, mixed sources and wildcard attributes')
if __name__=='__main__':main()
