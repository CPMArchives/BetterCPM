#!/usr/bin/env python3
"""Initial line/type commands, verification and display controls without disk I/O."""
from test_ed_buffer import context


def main():
    c,s,call,text,run=context(512);output=[];calls=[];ready=[False]
    c.mem[5:8]=bytes((0xdb,254,0xc9))
    def io(port):
        calls.append(c.c)
        if c.c==2:output.append(c.e);return 0
        if c.c==11:return 255 if ready[0] else 0
        if c.c==1:ready[0]=False;return ord('x')
        raise AssertionError(('unexpected BDOS',c.c))
    c.port_read=io
    def check(line,expected,cursor):
        output.clear();before=text()[0];(bad,flag),state=run(line)
        assert not bad,(line,flag)
        assert bytes(output)==expected,(line,bytes(output),expected)
        assert state==(before,cursor),(line,state)
    assert not run(b'ione\x0ctwo\x0cthree\x1aB')[0][0]
    check(b'T',b'    1:  one\r\n',0)
    check(b'2T',b'    1:  one\r\n    2:  two\r\n',0)
    check(b'0T',b'',0)
    check(b'L2C0T',b'    2:  tw',7)
    check(b'-T',b'    1:  one\r\n    2:  tw',7)
    check(b'B-V#T',b'one\r\ntwo\r\nthree',0)
    check(b'V#T',b'    1:  one\r\n    2:  two\r\n    3:  three',0)
    output.clear();ready[0]=True
    assert run(b'T')[0]==(True,ord('#'))
    assert text()[1]==0 and bytes(output)==b'    1:  '
    assert calls[-2:]==[11,1]
    assert run(b'0V')[0]==(True,2) # console caller formats memory report later
    c2,s2,_,_,run2=context(64);c2.mem[5:8]=bytes((0xdb,254,0xc9));out=[]
    def io2(port):
        if c2.c==2:out.append(c2.e);return 0
        assert c2.c==11;return 0
    c2.port_read=io2
    assert not run2(b'iA\tB\x01\x1aB-VT')[0][0]
    assert bytes(out)==b'A       B^A'
    print('PASS: signed line ranges, nonmoving T, V/-V, line numbers, tabs/control display and output interruption')


if __name__=='__main__':main()
