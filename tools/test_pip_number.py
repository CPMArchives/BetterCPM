#!/usr/bin/env python3
"""DRI numbered lines and pagination, shared with tabs and output limits."""
from test_pip_transfer import execute,key

def main():
 src=key(0,2,'SRC.TXT');dest=key(1,7,'DEST.TXT')
 cases=[('N',b'     1: A\r\n     2: B\r\n'),('N2',b'000001\tA\r\n000002\tB\r\n'),
        ('P2',b'\x0cA\r\nB\r\n'),('NP2T8',b'\x0c     1: A\r\n     2: B\r\n')]
 for option,expected in cases:
  out,fs,_,_=execute('B7:DEST.TXT=A2:SRC.TXT['+option+']',{src:(b'A\r\nB\r\n\x1a',0)})
  assert out=='' and fs[dest][0]==expected.ljust(128,b'\x1a'),(option,out,fs[dest])
  out,_,_,_=execute('LST:=A2:SRC.TXT['+option+']',{src:(b'A\r\nB\r\n\x1a',0)})
  assert out.encode()==expected,(option,out)
 out,_,_,_=execute('CON:=INP:[NP2]',{},input_bytes=b'A\nB\nC\x1a',patch_in=True)
 assert out=='\x0c     1: A\n     2: B\n\x0c     3: C'
 two=key(2,3,'TWO.TXT')
 out,_,_,_=execute('CON:=A2:SRC.TXT[N],C3:TWO.TXT[N]',{src:(b'A\r\n\x1a',0),two:(b'B\x1a',0)})
 assert out=='     1: A\r\n     2: B'
 out,_,_,_=execute('CON:=A2:SRC.TXT[N]',{src:((b'x\r\n'*101)+b'\x1a',0)})
 assert '    99: x' in out and '   100: x' in out and '   101: x' in out
 out,_,_,_=execute('CON:=A2:SRC.TXT[NP2F]',{src:(b'\x0cA\r\nB\r\nC\x1a',0)})
 assert out=='\x0c     1: A\r\n     2: B\r\n\x0c     3: C'
 print('PASS: PIP line numbers, page ejects, numbering continuity, decimal carry and formatting interaction')
if __name__=='__main__':main()
