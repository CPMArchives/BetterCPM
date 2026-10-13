#!/usr/bin/env python3
"""Disk concatenation text boundaries, object sources and staged failures."""
from test_pip_transfer import execute,key

def main():
    a=key(0,2,'ONE.TXT');b=key(2,3,'TWO.TXT');d=key(1,7,'DEST.TXT');t=key(1,7,'DEST.$$$')
    for first,second in [(b'one\x1aignored',b'two\x1atail'),(b'',b'two\x1a'),(b'one\x1a',b''),(b'',b''),(b'A'*256+b'\x1a',b'B'*256+b'\x1a'),(b'A'*16387+b'\x1a',b'B'*17003+b'\x1a'),(b'\xffhi\x1a',b'\x80there\x1a')]:
        files={a:(first,0),b:(second,0),d:(b'OLD',0)}
        content=first.split(b'\x1a')[0]+second.split(b'\x1a')[0]
        expected=content.ljust((len(content)+127)//128*128,b'\x1a')
        out,fs,_,_=execute('B7:DEST.TXT=A2:ONE.TXT[V],C3:TWO.TXT[V]',files,unused=(-len(content))%128)
        assert fs[d]==[expected,0] and t not in fs and fs[a]==[first,0] and fs[b]==[second,0],out
    obj=key(0,2,'ONE.COM')
    first=b'\x00\x1a\xff';second=b'text\x1atail'
    for source in ['A2:ONE.COM','A2:ONE.TXT[O]']:
        k=obj if 'COM' in source else a
        files={k:(first,0),b:(second,0),d:(b'OLD',0)}
        content=first.ljust(128,b'\x1a')+b'text';expected=content.ljust(256,b'\x1a')
        out,fs,_,_=execute('B7:DEST.TXT='+source+',C3:TWO.TXT',files,unused=124)
        assert fs[d][0]==expected,out
    files={a:(b'one\x1a',0),b:(b'two\x1a',2),d:(b'OLD',0)}
    out,fs,_,_=execute('B7:DEST.TXT=A2:ONE.TXT,C3:TWO.TXT',files)
    assert 'NO FILE' in out and fs[d]==[b'OLD',0] and t not in fs
    out,fs,_,_=execute('B7:DEST.TXT=A2:ONE.TXT,C3:TWO.TXT[R]',files,unused=122)
    assert fs[d][0].startswith(b'onetwo') and fs[b][1]==2
    for late in ['C3:MISSING.TXT','B7:DEST.$$$','B7:DEST.TXT','C3:TWO.TXT[N]']:
        out,fs,_,_=execute('B7:DEST.TXT=A2:ONE.TXT,'+late,files)
        assert fs[d]==[b'OLD',0] and t not in fs and fs[a]==[b'one\x1a',0],out
    for failure in ['verify','verify_read','write','close']:
        files={a:(b'A'*130+b'\x1a',0),b:(b'B'*130+b'\x1a',0),d:(b'OLD',0)}
        out,fs,_,_=execute('B7:DEST.TXT=A2:ONE.TXT[V],C3:TWO.TXT[V]',files,fail=failure)
        assert fs[d]==[b'OLD',0] and t not in fs,(failure,out)
    files={a:(b'one\x1a',0),b:(b'two\x1a',0),d:(b'OLD',1)}
    out,fs,calls,_=execute('B7:DEST.TXT=A2:ONE.TXT,C3:TWO.TXT[W]',files,unused=122)
    assert fs[d][0].startswith(b'onetwo') and 1 not in calls
    print('PASS: PIP text/object concatenation, mixed DUs, partial/full records, multi-extents and guarded failure cleanup')

if __name__=='__main__':main()
