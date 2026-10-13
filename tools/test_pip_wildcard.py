#!/usr/bin/env python3
"""DRI wildcard scan restarts, SYS admission, ARC propagation and failures."""
from test_pip_transfer import execute,key

def main():
    source={key(0,2,'ONE.DAT'):(b'one',0),key(0,2,'TWO.DAT'):(b'two',4),key(0,2,'THREE.DAT'):(b'system',6),key(0,2,'FOUR.DAT'):(b'ro',1),key(0,2,'MULTI.DAT'):(b'X'*33001,0),key(0,2,'OTHER.TXT'):(b'unselected',0)}
    for option in ['', '[V]','[RV]']:
        out,fs,calls,_=execute('B7:=A2:*.DAT'+option,source)
        admitted=[k for k in source if k[2].endswith(b'DAT') and ('R' in option or not source[k][1]&2)]
        for k in admitted:
            dest=(1,7,k[2]);payload,attr=source[k]
            assert fs[dest]==[payload.ljust((len(payload)+127)//128*128,b'\x1a'),attr]
        assert all(fs[k]==list(v) for k,v in source.items())
        assert out.count('COPYING -')==1 and out.count('MULTI.DAT')==1
        assert calls.count(17)>1 and 18 in calls
        assert key(1,7,'OTHER.TXT') not in fs
    out,fs,_,_=execute('B7:=A2:*.BAK',source)
    assert 'NOT FOUND' in out and fs=={k:list(v) for k,v in source.items()}
    out,fs,_,_=execute('B7:=A2:*.DAT[RV]',source,exm=1)
    assert out.count('MULTI.DAT')==1 and fs[key(1,7,'MULTI.DAT')][0].startswith(b'X'*33001)
    for command in ['A2:=A2:*.DAT','B7:=A2:*.DAT[X]']:
        out,fs,calls,_=execute(command,source)
        assert fs=={k:list(v) for k,v in source.items()} and not any(f in calls for f in (17,18,19,22,23))
    out,fs,_,_=execute('B7:=A2:*.DAT[V]',source,fail='verify')
    assert 'VERIFY ERROR' in out and not any(k[:2]==(1,7) for k in fs)
    protected={**source,key(1,7,'ONE.DAT'):(b'OLD',1)}
    out,fs,_,_=execute('B7:=A2:*.DAT[W]',protected)
    assert fs[key(1,7,'ONE.DAT')][0].startswith(b'one')
    out,fs,_,_=execute('B7:=A2:*.DAT[R]',source,fail='attributes')
    assert 'CANNOT SET DESTINATION ATTRIBUTES' in out
    assert key(1,7,'FOUR.DAT') in fs and key(1,7,'MULTI.DAT') not in fs
    assert all(fs[k]==list(v) for k,v in source.items())
    print('PASS: PIP wildcard restarted scans, mixed attributes, multi-extents, no-match and failure handling')

if __name__=='__main__':main()
