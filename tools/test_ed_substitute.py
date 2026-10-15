#!/usr/bin/env python3
"""S replacement semantics, combined scratch bound and partial overflow."""
from test_ed_buffer import context


def substitute(body,line,capacity=256):
    c,s,call,state,run=context(capacity)
    for byte in body:c.c=byte;assert not call('EB_PUT')[0]
    call('EB_TOP');return run(line)


def main():
    cases=[(b'one one',b'sone\x1atwo',b'two one',3,False),
           (b'one one',b'2sone\x1aX',b'X X',3,False),
           (b'one one',b'3sone\x1aX',b'X X',3,True),
           (b'one one',b'sone\x1a',b' one',0,False),
           (b'Mixed MIXED',b'Smixed\x1anew',b'Mixed NEW',9,False),
           (b'Mixed MIXED',b'Usmixed\x1anew',b'Mixed NEW',9,False),
           (b'abc',b'smissing\x1aX',b'abc',0,True),
           (b'abc',b'0sabc\x1aX',b'abc',0,False),
           (b'abc',b'-sabc\x1aX',b'abc',0,True),
           (b'A\r\nB',b'sA\x0cB\x1aX\x0cY',b'X\r\nY',4,False),
           (b'abc',b's\x1aX',b'Xabc',1,False)]
    for body,line,want,pos,bad in cases:
        result,state=substitute(body,line)
        assert result[0]==bad and state==(want,pos),(line,result,state)
    assert substitute(b'abc',b'sb\x1aLONG',4)==((True,ord('>')),(b'aLOc',3))
    assert substitute(b'x',b'0s'+b'a'*50+b'\x1a'+b'b'*49)[0]==(False,0)
    assert substitute(b'x',b'0s'+b'a'*50+b'\x1a'+b'b'*50)[0]==(True,ord('>'))
    assert substitute(b'x',b'sx\x1a\x00')[0]==(True,ord('?'))
    print('PASS: S counts, shrinking/growing/deleting, case, CRLF, empty pattern, scratch bound and partial overflow')


if __name__=='__main__':main()
