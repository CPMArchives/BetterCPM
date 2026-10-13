#!/usr/bin/env python3
"""Staged text-device input, special sources and injected disk failures."""
from test_pip_transfer import execute,key

def main():
 dest=key(1,7,'DEST.DAT');temp=key(1,7,'DEST.$$$')
 for device in ['CON','RDR','INP']:
  for size in [0,1,127,128,129,300]:
   data=b'x'*size
   out,fs,calls,_=execute('B7:DEST.DAT='+device+':[V]',{},input_bytes=data+b'\x1a',patch_in=True)
   expected=data.ljust(((size+127)//128)*128,b'\x1a')
   assert out=='' and fs[dest]==[expected,0] and temp not in fs,(device,size,out,fs)
   assert 20 not in calls
 out,fs,_,_=execute('B7:DEST.DAT=RDR:',{},input_bytes=b'\xc1\x9a')
 assert fs[dest][0]==b'A'+b'\x1a'*127
 for device,prefix in [('NUL',bytes(40)),('EOF',b'\x1a')]:
  out,fs,calls,_=execute('B7:DEST.DAT='+device+':',{})
  assert out=='' and fs[dest][0]==prefix.ljust(128,b'\x1a') and not any(f in calls for f in (1,3))
 out,fs,_,_=execute('B7:DEST.DAT=INP:',{})
 assert out=='' and fs[dest]==[b'',0]
 for tail in ['B7:DEST.DAT=CON:[O]','B7:=CON:','B7:DEST.DAT=PTR:']:
  out,fs,calls,_=execute(tail,{dest:(b'old',0)})
  assert ('not implemented' in out or 'INVALID FORMAT' in out or 'DEVICE UNAVAILABLE' in out) and fs[dest]==[b'old',0]
  assert not any(f in calls for f in (1,3,19,22,23))
 out,fs,calls,_=execute('B7:DEST.DAT=NUL:[W]',{dest:(b'old',1)})
 assert fs[dest][0]==bytes(40)+b'\x1a'*88 and 1 not in calls
 out,fs,calls,_=execute('B7:DEST.DAT=NUL:',{dest:(b'old',1)},answer='N')
 assert fs[dest]==[b'old',1] and temp not in fs and 1 in calls
 for failure in ['write','verify','close','rename']:
  out,fs,_,_=execute('B7:DEST.DAT=CON:[V]',{dest:(b'old',0)},fail=failure,input_bytes=b'x'*300+b'\x1a')
  assert out
  if failure=='rename':assert dest not in fs
  else:assert fs[dest]==[b'old',0]
  assert (temp in fs)==(failure=='rename'),(failure,out,fs)
 print('PASS: PIP CON/RDR/INP text input, NUL/EOF, boundaries, verification and guarded disk failures')
if __name__=='__main__':main()
