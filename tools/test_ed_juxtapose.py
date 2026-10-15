#!/usr/bin/env python3
"""J keeps both delimiters, inserts its middle text and removes the interval."""
from test_ed_substitute import substitute


def main():
    cases=[(b'BEGIN old END tail',b'jBEGIN\x1aNEW\x1aEND',b'BEGINNEWEND tail',8,False),
           (b'A old B A more B',b'2jA\x1aX\x1aB',b'AXB AXB',6,False),
           (b'A old B A more B',b'3jA\x1aX\x1aB',b'AXB AXB',6,True),
           (b'A old B',b'jA\x1a\x1aB',b'AB',1,False),
           (b'A old B',b'jA\x1aX\x1aZ',b'AX old B',2,True),
           (b'old B',b'jA\x1aX\x1aB',b'old B',0,True),
           (b'A old B',b'0jA\x1aX\x1aB',b'A old B',0,False),
           (b'aa AA old BB',b'Jaa\x1ax\x1abb',b'aa AAXBB',6,False),
           (b'A\r\nx\r\nB',b'jA\x1aNEW\x0c\x1aB',b'ANEW\r\nB',6,False)]
    for body,line,want,pos,bad in cases:
        result,state=substitute(body,line)
        assert result[0]==bad and state==(want,pos),(line,result,state)
    # Counted execution equals independent successive operations; a third
    # missing match must preserve the first two edits and report failure.
    body=b'A old B A more B'
    assert substitute(body,b'2jA\x1aX\x1aB')==substitute(body,b'jA\x1aX\x1aB\x1ajA\x1aX\x1aB')
    assert substitute(b'AxxxB',b'jA\x1aLONG\x1aB',6)==((True,ord('>')),(b'ALxxxB',2))
    assert substitute(b'A old B',b'-jA\x1aX\x1aB')[0]==(True,ord('?'))
    assert substitute(b'x',b'0j'+b'a'*33+b'\x1a'+b'b'*33+b'\x1a'+b'c'*33)[0]==(False,0)
    assert substitute(b'x',b'0j'+b'a'*33+b'\x1a'+b'b'*33+b'\x1a'+b'c'*34)[0]==(True,ord('>'))
    print('PASS: J delimiters/counts, middle insertion, retained end, partial failures, case, CRLF and scratch limit')


if __name__=='__main__':main()
