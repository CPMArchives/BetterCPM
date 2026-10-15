#!/usr/bin/env python3
"""R exact library names, source-DU inheritance and independent record state."""
from test_ed_buffer import context


def read(command,body=b'Mixed\r\n\0z\x1aignored',key=(2,7,b'HEADER  LIB'),capacity=512,read_status=0):
    c,s,call,state,run=context(capacity);drive=0;user=0;index=0;ops=[]
    original=b'\3CASE    TXT'+b'\0'*24
    c.mem[s['EI_FCB']:s['EI_FCB']+36]=original
    c.mem[s['EI_SDRV']]=2;c.mem[s['EI_SUSR']]=7
    c.mem[s['EI_CDRV']]=0;c.mem[s['EI_CUSR']]=0
    c.mem[5:8]=bytes((0xdb,254,0xc9))
    def io(port):
        nonlocal drive,user,index
        ops.append(c.c)
        if c.c==14:drive=c.e;return 0
        if c.c==32:user=c.e;return 0
        if c.c==26:assert c.de==s['GR_DATA'];return 0
        if c.c==15:
            f=c.de;assert f==s['GR_FCB'] and c.mem[f]==drive+1
            actual=(drive,user,bytes(c.mem[f+1:f+12]));index=0
            return 0 if actual==key else 255
        if c.c==20:
            assert c.de==s['GR_FCB']
            if read_status:return read_status
            padded=body+b'\x1a'*(128-len(body)%128)
            record=padded[index:index+128];index+=128
            if not record:return 1
            c.mem[s['GR_DATA']:s['GR_DATA']+128]=record;return 0
        raise AssertionError(('unexpected main-stream/destructive BDOS',c.c))
    c.port_read=io
    assert not run(b'ipreSUF\x1aB3C')[0][0]
    result=run(command)
    assert bytes(c.mem[s['EI_FCB']:s['EI_FCB']+36])==original
    assert c.mem[s['EI_CDRV']]==0 and c.mem[s['EI_CUSR']]==0
    return result,ops


def main():
    assert read(b'rheader')[0]==((False,0),(b'preMixed\r\n\0zSUF',12))
    assert read(b'Rheader')[0]==((False,0),(b'preMIXED\r\n\0ZSUF',12))
    assert read(b'Urheader')[0]==((False,0),(b'preMIXED\r\n\0ZSUF',12))
    assert read(b'rB19:header.lib',key=(1,19,b'HEADER  LIB'))[0][0]==(False,0)
    assert read(b'r19:header.txt',key=(0,19,b'HEADER  TXT'))[0][0]==(False,0)
    assert read(b'rB:header',key=(1,0,b'HEADER  LIB'))[0][0]==(False,0)
    assert read(b'r',key=(2,7,b'X$$$$$$$LIB'))[0][0]==(False,0)
    assert read(b'rheader\x1ai!\x1a')[0][1]==(b'preMixed\r\n\0z!SUF',13)
    assert read(b'rmissing')[0][0]==(True,ord('O'))
    for command in (b'1rheader',b'0rheader',b'-rheader',b'rB[-]:header',b'rB19:',b'r*.LIB'):
        result,ops=read(command);assert result[0]==(True,ord('?')) and not ops,(command,result,ops)
    assert read(b'r'+b'x'*17)[0][0]==(True,ord('#'))
    assert read(b'rheader',body=b'x'*200)[0][1]==(b'pre'+b'x'*200+b'SUF',203)
    assert read(b'rheader',body=b'long',capacity=8)[0]==((True,ord('>')),(b'preloSUF',5))
    assert read(b'rheader',read_status=2)[0]==((False,0),(b'preSUF',3))
    print('PASS: R record insertion/case, DU/default LIB, original filespec preservation, errors and overflow')


if __name__=='__main__':main()
