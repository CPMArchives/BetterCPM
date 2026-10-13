#!/usr/bin/env python3
"""DRI T/F/D output behavior and column tracking across sources."""
from test_pip_transfer import execute,key

def main():
 src=key(0,2,'SRC.TXT');dest=key(1,7,'DEST.TXT')
 cases=[(b'A\tB\r\nC\tD\x1a','T8',b'A'+b' '*7+b'B\r\nC'+b' '*7+b'D'),
        (b'\tA\tB\x1a','T4',b' '*4+b'A'+b' '*3+b'B'),
        (b'A\tB\x1a','T0',b'A\tB'),
        (b'A\x0cB\r\n\x0cC\x1a','F',b'AB\r\nC'),
        (b'ABCDEFG\r\nHIJKL\x1a','D3',b'ABC\r\nHIJ'),
        (b'A\tB\r\nC\tD\x1a','T8D4',b'A   \r\nC   '),
        (b'ABC\nDEF\rGHI\x1a','D4',b'ABC\nD\rGHI')]
 for data,options,expected in cases:
  out,fs,_,_=execute('B7:DEST.TXT=A2:SRC.TXT[V'+options+']',{src:(data,0)})
  assert out=='' and fs[dest][0]==expected.ljust(128,b'\x1a'),(options,out,fs[dest])
  out,_,_,_=execute('LST:=A2:SRC.TXT['+options+']',{src:(data,0)})
  assert out.encode()==expected,(options,out)
 two=key(2,3,'TWO.TXT')
 out,fs,_,_=execute('B7:DEST.TXT=A2:SRC.TXT,C3:TWO.TXT[T8]',{src:(b'ABC\x1a',0),two:(b'\tZ\x1a',0)})
 assert fs[dest][0]==b'ABC'+b' '*5+b'Z'+b'\x1a'*119
 out,_,_,_=execute('CON:=INP:[FT4]',{},input_bytes=b'A\x0c\tB\x1a',patch_in=True)
 assert out=='A   B'
 out,fs,_,_=execute('B7:=A2:*.TXT[T4F]',{src:(b'A\x0c\tB\x1a',5)})
 assert fs[key(1,7,'SRC.TXT')]==[b'A   B'+b'\x1a'*123,5]
 out,fs,_,_=execute('B7:DEST.TXT=A2:SRC.TXT[T255]',{src:(b'\tX\x1a',0)})
 assert fs[dest][0]==b' '*255+b'X'
 out,fs,_,_=execute('B7:DEST.TXT=A2:SRC.TXT[T8]',{src:(b'\t'*40+b'\x1a',0)},fail='write')
 assert 'DISK WRITE ERROR' in out and dest not in fs and key(1,7,'DEST.$$$') not in fs
 print('PASS: PIP tab stops, form filtering, line limits, column continuity, long expansions and failure cleanup')
if __name__=='__main__':main()
