#!/usr/bin/env python3
"""Text extraction matches the pinned DRI one-character lookahead rules."""
from test_pip_transfer import execute,key
EOF='\x1a'
def main():
 src=key(0,2,'SRC.TXT');dest=key(1,7,'DEST.TXT')
 def copy(data,options,expected):
  out,fs,_,_=execute('B7:DEST.TXT=A2:SRC.TXT['+options+']',{src:(data,0)})
  assert out=='' and fs[dest][0]==expected.ljust(((len(expected)+127)//128)*128,b'\x1a'),(data,options,out,fs)
 copy(b'prefixSTARTmiddleQUITtail\x1a','SSTART'+EOF+'QQUIT'+EOF,b'STARTmiddleQUIT\r\n')
 copy(b'x'*126+b'ABCtail\x1a','SABC'+EOF,b'ABCtail')
 copy(b'x'*126+b'QUITtail\x1a','QQUIT'+EOF,b'x'*126+b'QUIT\r\n')
 copy(b'xxstartTAIL\x1a','USSTART'+EOF,b'STARTTAIL')
 copy(b'ababaXabaY\x1a','Saba'+EOF,b'ababaXabaY')
 copy(b'abc\x1a','S'+EOF,b'abc')
 copy(b'abc\x1a','Q'+EOF,b'\r\n')
 for data,options,message in [(b'none\x1a','SMISSING'+EOF,'START NOT FOUND'),(b'aabaX\x1a','Saba'+EOF,'START NOT FOUND'),(b'ABC\x1a','SABC'+EOF,'START NOT FOUND'),(b'QUIT\x1a','QQUIT'+EOF,'QUIT NOT FOUND')]:
  out,fs,_,_=execute('B7:DEST.TXT=A2:SRC.TXT['+options+']',{src:(data,0),dest:(b'old',0)})
  assert message in out and fs[dest]==[b'old',0] and key(1,7,'DEST.$$$') not in fs
 out,_,_,_=execute('CON:=INP:[SBEGIN'+EOF+'QEND'+EOF+']',{},input_bytes=b'xxBEGINbodyENDafter\x1a',patch_in=True)
 assert out=='BEGINbodyEND\r\n'
 out,fs,_,_=execute('B7:=A2:*.TXT[SSTART'+EOF+'QQUIT'+EOF+']',{src:(b'xxSTARTbodyQUITtail\x1a',5)})
 assert fs[key(1,7,'SRC.TXT')]==[b'STARTbodyQUIT\r\n'+b'\x1a'*113,5]
 two=key(2,3,'TWO.TXT')
 out,fs,_,_=execute('B7:DEST.TXT=A2:SRC.TXT[QEND'+EOF+'],C3:TWO.TXT[SSTART'+EOF+']',{src:(b'oneENDtail\x1a',0),two:(b'xxSTARTtwo\x1a',0)})
 assert fs[dest][0]==b'oneEND\r\nSTARTtwo'+b'\x1a'*112
 for tail in ['CON:=A2:SRC.COM[Sx'+EOF+']','B7:DEST.TXT=A2:SRC.TXT[OSx'+EOF+']']:
  out,_,calls,_=execute(tail,{src:(b'x\x1a',0)})
  assert 'not implemented' in out and not any(f in calls for f in (20,22,2))
 print('PASS: PIP text S/Q inclusion, lookahead, empty strings, record boundaries, source reset and missing-string cleanup')
if __name__=='__main__':main()
