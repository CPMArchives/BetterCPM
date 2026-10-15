#!/usr/bin/env python3
"""Console A/W disk failures invoke recovery, not ordinary BREAK handling."""
from test_ed_buffer import context


def case(command):
    c,s,call,state,run=context(256);output=[];ops=[]
    c.mem[5:8]=bytes((0xdb,254,0xc9))
    def io(port):
        ops.append(c.c)
        if c.c==10:
            c.mem[c.de+1]=len(command);c.mem[c.de+2:c.de+2+len(command)]=command
            return 0
        if c.c==2:output.append(c.e);return 0
        if c.c==9:
            p=c.de
            while c.mem[p]!=36:output.append(c.mem[p]);p+=1
            return 0
        if c.c in (14,26,32):return 0
        if c.c in (20,21):return 2
        if c.c==16:return 255
        raise AssertionError(('unexpected destructive/console BDOS',c.c))
    c.port_read=io
    for name,value in [('EI_CDRV',2),('EI_CUSR',31),('EI_ODRV',1),('EI_OUSR',3)]:c.mem[s[name]]=value
    c.hl=s['FS_SOURCE'];c.a=7;call('ES_INIT')
    c.hl=s['FS_WORK'];c.a=3;call('EW_INIT')
    if command==b'w':
        for _ in range(128):c.c=65;assert not call('EW_PUT')[0]
        assert not run(b'itext\x1a')[0][0]
    assert call('EU_READ')==(True,1)
    assert b'DISK OR DIRECTORY FULL\r\n' in bytes(output)
    assert b'BREAK' not in bytes(output)
    assert ops.count(16)==1 and c.mem[s['FD_STATUS']]==2
    if command==b'w':assert state()==(b'text',0)  # first unaccepted byte survives
    # A later ordinary command must not inherit the previous disk error.
    output.clear();assert not run(b'B')[0][0]
    assert c.mem[s['EC_IOERR']]==0
    return ops


def main():
    assert 20 in case(b'a')
    assert 21 in case(b'w')
    print('PASS: ordinary A/W failures close recovery output, diagnose and exit without BREAK or destructive cleanup')


if __name__=='__main__':main()
