#!/usr/bin/env python3
"""DRI pre-transformation echo and shared formatting-state semantics."""
from test_pip_transfer import execute,key

def main():
 src=key(0,2,'SRC.TXT');dest=key(1,7,'DEST.TXT')
 out,fs,_,_=execute('B7:DEST.TXT=A2:SRC.TXT[EU]',{src:(b'Abc\x1a',0)})
 assert out=='Abc\x1a' and fs[dest][0]==b'ABC'+b'\x1a'*125
 out,fs,_,_=execute('B7:DEST.TXT=A2:SRC.TXT[ET8]',{src:(b'A\tB\x1a',0)})
 assert out=='A'+' '*6+'B\x1a' and fs[dest][0]==b'A'+b' '*8+b'B'+b'\x1a'*118
 out,fs,_,_=execute('B7:DEST.TXT=A2:SRC.TXT[EN]',{src:(b'A\r\nB\x1a',0)})
 assert out=='     1: A\r\n     3: B\x1a' and fs[dest][0]==b'A\r     2: \nB'+b'\x1a'*116
 out,fs,_,_=execute('B7:DEST.TXT=INP:[EZU]',{},input_bytes=b'a\xe2\x9a',patch_in=True)
 assert out.encode('latin1')==b'a\xe2\x9a' and fs[dest][0]==b'AB'+b'\x1a'*126
 out,fs,_,_=execute('B7:DEST.TXT=A2:SRC.TXT[ESBEGIN\x1aQEND\x1a]',{src:(b'xxBEGINbodyENDafter\x1a',0)})
 assert out=='xxBEGINbodyENDa' and fs[dest][0]==b'BEGINbodyEND\r\n'+b'\x1a'*114
 out,_,_,_=execute('CON:=A2:SRC.TXT[E]',{src:(b'AB\x1a',0)})
 assert out=='AABB\x1a'
 print('PASS: PIP raw echo, EOF/lookahead echo, parity/case order and shared tab/number state')
if __name__=='__main__':main()
