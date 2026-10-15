#!/usr/bin/env python3
"""First-command numeric Enter movement/type versus ignored trailing CR."""
from test_ed_buffer import context


def main():
    body=b'one\r\ntwo\r\nthree\r\nfour'
    cases=[(b'2',0,10,b'    3:  three\r\n'),(b'0',7,5,b'    2:  two\r\n'),
           (b'-1',17,10,b'    3:  three\r\n'),(b'-',7,0,b'    1:  one\r\n'),
           (b'#',0,len(body),b''),(b'B2',17,0,b''),(b'L0',0,5,b''),
           (b'\r',0,5,b'    2:  two\r\n')]
    for line,start,end,expected in cases:
        c,s,call,state,run=context(256);out=[]
        c.mem[5:8]=bytes((0xdb,254,0xc9))
        def io(port):
            if c.c==2:out.append(c.e);return 0
            assert c.c==11;return 0
        c.port_read=io
        for byte in body:c.c=byte;call('EB_PUT')
        call('EB_TOP')
        for _ in range(start):call('EB_RIGHT')
        assert run(line)==((False,0),(body,end)),line
        assert bytes(out)==expected,(line,bytes(out))
    print('PASS: signed/count/zero Enter, blank Enter and ignored CR after earlier commands')


if __name__=='__main__':main()
