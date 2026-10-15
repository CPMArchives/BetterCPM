#!/usr/bin/env python3
"""Diagnostic spelling, recovery close attempt and safe caller-DU exit."""
from test_ed_buffer import context


def main():
    c,s,call,_,_=context();out=[];ops=[]
    c.mem[5:8]=bytes((0xdb,254,0xc9))
    def io(port):
        ops.append((c.c,c.e if c.c in (14,32) else c.de))
        if c.c==9:
            i=c.de
            while c.mem[i]!=36:out.append(c.mem[i]);i+=1
            return 0
        if c.c==16:assert c.de==s['FS_WORK'];return 255
        if c.c==1:return 13
        if c.c==2:out.append(c.e);return 0
        if c.c in (14,32,26):return 0
        raise AssertionError(('destructive/unexpected BDOS',c.c))
    c.port_read=io
    for name,value in [('EI_CDRV',2),('EI_CUSR',31),('EI_ODRV',1),('EI_OUSR',7)]:c.mem[s[name]]=value
    for reason,expected,close in [(1,b'FILE EXISTS, ERASE IT\r\n',False),
                                  (2,b'"SYSTEM" FILE NOT ACCESSIBLE\r\n',False),
                                  (3,b'DISK OR DIRECTORY FULL\r\n',True)]:
        out.clear();ops.clear();c.a=reason
        assert call('FD_SETUPERR')==(True,1) and bytes(out)==expected
        assert sum(n==16 for n,_ in ops)==int(close)
        assert ops[-3:]==[(14,2),(32,31),(26,128)]
    for new,ro,expected in [(0,0,b''),(1,0,b'NEW FILE\r\n'),(0,128,b'** FILE IS READ/ONLY **\r\n')]:
        out.clear();ops.clear();c.mem[s['FS_NEW']]=new;c.mem[s['FS_RO']]=ro
        assert call('FD_NOTES')==(False,0) and bytes(out)==expected
        assert all(n==9 for n,_ in ops)
    out.clear();ops.clear();c.a=2
    assert call('FD_FATAL')==(True,1) and c.mem[s['FD_STATUS']]==2
    assert [n for n,_ in ops]==[14,32,16,9,14,32,26]
    out.clear();ops.clear();c.mem[s['FQ_STAGE']]=1;c.mem[s['FP_STEP']]=1;c.mem[s['FS_RO']]=128;c.a=255
    assert call('FD_ACTIONERR')==(True,1)
    assert bytes(out)==b'\r\nBdos Err On A: File R/O\r\n'
    assert sum(n==1 for n,_ in ops)==1 and not any(n in (16,19,23) for n,_ in ops)
    for step in (1,2):
        out.clear();ops.clear();c.mem[s['FS_RO']]=0;c.mem[s['FP_STEP']]=step;c.a=255
        assert call('FD_ACTIONERR')==(True,1)
        assert bytes(out)==b'Rename failed. Edited text retained in work file.\r\n'
        assert c.mem[s['FD_STATUS']]==255
        assert [n for n,_ in ops]==[9,14,32,26]
        assert ops[-3:]==[(14,2),(32,31),(26,128)]
    # A failed initial work close is FINIS -> FERR: retry close once,
    # diagnose, then restore the caller DU/DMA without any renames.
    out.clear();ops.clear();c.mem[s['FP_STEP']]=0;c.a=255
    assert call('FD_ACTIONERR')==(True,1)
    assert bytes(out)==b'DISK OR DIRECTORY FULL\r\n'
    assert c.mem[s['FD_STATUS']]==255
    assert [n for n,_ in ops]==[14,32,16,9,14,32,26]
    print('PASS: stock setup diagnostics, NEW/RO notices, failed recovery close and caller DU/DMA exit')


if __name__=='__main__':main()
