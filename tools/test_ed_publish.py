#!/usr/bin/env python3
"""Publication primitive ordering and preservation at each failure boundary."""
from test_ed_buffer import context


def trial(failure=None,done=True,readonly=False):
    c,s,call,_,_=context();drive=0;user=0;ops=[]
    src=(1,7,b'CASE    TXT');temp=(2,3,b'CASE    $$$')
    live={src:b'OLD',temp:b'NEW'}
    c.mem[s['EI_FCB']:s['EI_FCB']+36]=b'\0CASE    TXT'+b'\0'*24
    c.mem[s['FS_WORK']:s['FS_WORK']+36]=b'\3CASE    $$$'+b'\0'*24
    c.mem[s['FS_WORK']+13]=117  # must not publish ISIS-II unused-byte metadata
    c.mem[s['FS_RO']]=128 if readonly else 0
    for name,value in [('EI_SDRV',1),('EI_SUSR',7),('EI_ODRV',2),('EI_OUSR',3),('EF_DONE',int(done))]:c.mem[s[name]]=value
    c.mem[5:8]=bytes((0xdb,254,0xc9))
    def io(port):
        nonlocal drive,user
        if c.c==14:drive=c.e;return 0
        if c.c==32:user=c.e;return 0
        assert c.c in (16,23),c.c
        f=c.de;key=(drive,user,bytes(c.mem[f+1:f+12]))
        assert c.mem[f]==drive+1
        if c.c==16:
            assert c.mem[f+13]==0;ops.append(('close',key))
        else:
            target=(drive,user,bytes(c.mem[f+17:f+28]));ops.append(('rename',key,target))
        if len(ops)==failure:return 255
        if c.c==23:
            assert key in live and target not in live
            live[target]=live.pop(key)
        return 0
    c.port_read=io;call('FP_INIT');result=call('FP_COMMIT')
    return c,s,call,result,ops,live


def main():
    src=(1,7,b'CASE    TXT');bak=(1,7,b'CASE    BAK');temp=(2,3,b'CASE    $$$');dest=(2,3,b'CASE    TXT')
    c,s,call,result,ops,live=trial()
    assert result==(False,0) and live=={bak:b'OLD',dest:b'NEW'}
    assert ops==[('close',temp),('rename',src,bak),('rename',temp,dest)]
    assert c.mem[s['FP_STEP']]==3
    assert call('FP_COMMIT')==(True,254) and len(ops)==3
    for failure,expected in [(1,{src:b'OLD',temp:b'NEW'}),(2,{src:b'OLD',temp:b'NEW'}),(3,{bak:b'OLD',temp:b'NEW'})]:
        c,s,call,result,ops,live=trial(failure)
        assert result==(True,255) and live==expected and len(ops)==failure
        assert c.mem[s['FP_STEP']]==failure-1
        assert call('FP_COMMIT')==(True,254) and len(ops)==failure
    c,s,call,result,ops,live=trial(done=False)
    assert result==(True,254) and not ops
    c,s,call,result,ops,live=trial(readonly=True)
    assert result==(True,255) and ops==[('close',temp)]
    assert live=={src:b'OLD',temp:b'NEW'} and c.mem[s['FP_STEP']]==1
    print('PASS: close/source backup/output publication order, S1 normalization and each failure boundary')


if __name__=='__main__':main()
