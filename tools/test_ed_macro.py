#!/usr/bin/env python3
"""M repeat counts, continuous byte stream, case, interruption and stack exit."""
from test_ed_buffer import context


def macro(body,line,interrupt_after=None):
    c,s,call,state,run=context(256);polls=0;keys=[]
    c.mem[5:8]=bytes((0xdb,254,0xc9))
    def io(port):
        nonlocal polls
        if c.c==11:
            polls+=1;return 255 if interrupt_after is not None and polls>interrupt_after else 0
        if c.c==1:keys.append(1);return ord('x')
        raise AssertionError(('unexpected BDOS',c.c))
    c.port_read=io
    for byte in body:c.c=byte;assert not call('EB_PUT')[0]
    call('EB_TOP');result=run(line)
    assert c.mem[s['GM_ACTIVE']]==0
    assert not run(b'B')[0][0]  # no stale macro stream after an exit
    return result,keys


def main():
    cases=[(b'abcdef',b'2mC',b'abcdef',2,ord('#')),
           (b'',b'2miabc\x1a',b'abcabc',6,ord('#')),
           (b'',b'2Miabc\x1a',b'ABCABC',6,ord('#')),
           (b'',b'2miabc',b'abciabc',7,ord('#')),
           (b'one one',b'msone\x1aX\x1a',b'X X',3,ord('#')),
           (b'one one',b'1msone\x1aX\x1a',b'X X',3,ord('#')),
           (b'one one',b'0msone\x1aX\x1a',b'X X',3,ord('#')),
           (b'abc',b'2mmC',b'abc',0,ord('?')),
           (b'abc',b'-mC',b'abc',0,ord('?'))]
    for body,line,want,pos,flag in cases:
        (result,state),keys=macro(body,line)
        assert result==(True,flag) and state==(want,pos) and not keys,(line,result,state)
    assert macro(b'abc',b'm')[0]==((False,0),(b'abc',0))
    assert macro(b'abcdef',b'mC',interrupt_after=3)==(((True,ord('#')),(b'abcdef',3)),[1])
    print('PASS: M finite/unbounded counts, case, continuous strings, nested rejection, interruption and stack cleanup')


if __name__=='__main__':main()
