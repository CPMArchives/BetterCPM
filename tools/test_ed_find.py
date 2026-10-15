#!/usr/bin/env python3
"""Literal F search semantics, counts, case and bounded string collection."""
from test_ed_buffer import context


def main():
    cases=[(b'fabc',False,b'abc ABC abc',3),(b'Fabc',False,b'abc ABC abc',7),
           (b'2fabc',False,b'abc ABC abc',11),(b'3fabc',True,b'abc ABC abc',11),
           (b'fnone',True,b'abc ABC abc',0),(b'0fabc',False,b'abc ABC abc',0),
           (b'-fabc',True,b'abc ABC abc',0),(b'Ufabc',False,b'abc ABC abc',7),
           (b'fA\x0cB',False,b'A\r\nB',4),(b'f',False,b'abc',0),
           (b'f',True,b'',0),(b'fabc',True,b'ab',0)]
    for line,bad,body,pos in cases:
        c,s,call,state,run=context(256)
        for byte in body:c.c=byte;assert not call('EB_PUT')[0]
        call('EB_TOP');result,actual=run(line)
        assert result[0]==bad and actual==(body,pos),(line,result,actual)
    c,s,call,state,run=context(256)
    assert not run(b'iabcabc\x1aB3C')[0][0]
    assert run(b'fabc\x1ai!\x1a')[1]==(b'abcabc!',7)
    assert run(b'Bf\x00')[0]==(True,ord('?'))
    assert run(b'B0f'+b'x'*99)[0]==(False,0)
    assert run(b'B0f'+b'x'*100)[0]==(True,ord('>'))
    assert run(b'B0f'+b'x'*98+b'\x0c')[0]==(True,ord('>'))
    print('PASS: literal F counts/case, cursor preservation, delimiters, CRLF, NUL and scratch overflow')


if __name__=='__main__':main()
