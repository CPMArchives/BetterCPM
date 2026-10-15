#!/usr/bin/env python3
"""Interactive insert semantics and control state, without a file engine."""
from test_ed_buffer import context


def insert(keys,upper=False,initial=b'',capacity=256):
    c,s,call,text,run=context(capacity);output=[]
    c.mem[5:8]=bytes((0xdb,254,0xc9))
    def io(port):
        if c.c==2:output.append(c.e);return 0
        if c.c==11:return 0
        raise AssertionError(('unexpected BDOS',c.c))
    c.port_read=io
    if initial:assert not run(b'i'+initial+b'\x1a')[0][0]
    assert run(b'I' if upper else b'i')[0]==(True,1)
    assert call('IN_START')==(False,0)
    for key in keys:
        c.c=key;bad,flag=call('IN_FEED')
        if bad:return (bad,flag),text(),bytes(output)
    return (False,flag),text(),bytes(output)


def main():
    cases=[(b'abc\rdef\x1a',b'abc\r\ndef'),(b'abc\ndef\x1a',b'abc\ndef'),
           (b'abc\x15def\x1a',b'def'),(b'abc\x18def\x1a',b'def'),
           (b'abc\x7fd\x1a',b'abd'),(b'abc\x08d\x1a',b'abd'),
           (b'abc\x12d\x1a',b'abcd'),(b'A\tB\x1a',b'A\tB'),
           (b'A\x0cB\x1a',b'A\r\nB'),(b'\x08a\x1a',b'a'),
           (b'abc\rdef\x15gh\x1a',b'abc\r\ngh'),
           (b'ab\tX\x08\x08Q\x1a',b'abQ'),(b'\x00abc\x1a',b'abc'),
           (b'A\x05B\x1a',b'A\x05B'),(b'abc\r\x7fX\x1a',b'abc\rX')]
    for keys,want in cases:
        result,state,_=insert(keys)
        assert result==(False,1) and state==(want,len(want)),(keys,result,state)
    assert insert(b'Mixed\x1a',upper=True)[1]==(b'MIXED',5)
    assert insert(b'xy\x15Z\x1a',initial=b'OLD')[1]==(b'Z',1)
    assert insert(b'ab\rc\x1a',capacity=3)[:2]==((True,ord('>')),(b'ab\r',3))
    assert insert(b'\x7f')[:2]==((True,ord('?')),(b'',0))
    print('PASS: interactive insert, CR/LF, case, NUL/control data, ^U/^X/^R/^H/DEL and partial overflow')


if __name__=='__main__':main()
