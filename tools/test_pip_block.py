#!/usr/bin/env python3
"""DRI B XOFF handling preserves partial records and never pads mid-source."""
from test_pip_transfer import execute,key

def main():
 src=key(0,2,'SRC.TXT');dest=key(1,7,'DEST.TXT')
 for size in [0,1,127,128,129,300]:
  data=b'A'*size+b'\x13'+b'B'*130+b'\x13\x13C\x1a'
  out,fs,calls,writes=execute('B7:DEST.TXT=A2:SRC.TXT[BV]',{src:(data,0)})
  expected=b'A'*size+b'B'*130+b'C'
  assert out=='' and fs[dest][0]==expected.ljust(((len(expected)+127)//128)*128,b'\x1a'),(size,out)
  assert len(writes)==(len(expected)+127)//128
 data=bytes(range(256))
 out,fs,_,_=execute('B7:DEST.TXT=A2:SRC.TXT[BO]',{src:(data,0)})
 assert out=='' and fs[dest][0]==data[:26].replace(b'\x13',b'').ljust(128,b'\x1a')
 out,fs,_,_=execute('B7:DEST.TXT=INP:[BV]',{},input_bytes=b'A\x13B\x13\x1a',patch_in=True)
 assert out=='' and fs[dest][0]==b'AB'+b'\x1a'*126
 out,_,_,_=execute('CON:=INP:[B]',{},input_bytes=b'A\x13B\x1a',patch_in=True)
 assert out=='A\x13B'
 out,fs,_,_=execute('B7:DEST.TXT=A2:SRC.TXT[BE]',{src:(b'A\x13B\x1a',0)})
 assert out=='A\x13B\x1a' and fs[dest][0]==b'AB'+b'\x1a'*126
 out,fs,_,_=execute('B7:DEST.TXT=A2:SRC.TXT[BV]',{src:(b'A'*128+b'\x13'+b'B'*128+b'\x1a',0)},fail='write')
 assert 'DISK WRITE ERROR' in out and dest not in fs and key(1,7,'DEST.$$$') not in fs
 print('PASS: PIP B disk XOFF suppression, unpadded partial records, verification, devices, echo and failure cleanup')
if __name__=='__main__':main()
