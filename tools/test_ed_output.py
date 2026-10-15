#!/usr/bin/env python3
"""Work-file records: padding, boundaries, finalization and latched failures."""
from test_ed_buffer import context


def output(fail_at=None,status=1,capacity=64):
    c,s,call,_,_=context(capacity);records=[];calls=[];dma=0;attempts=0
    c.mem[5:8]=bytes((0xdb,254,0xc9))
    def io(port):
        nonlocal dma,attempts
        calls.append(c.c)
        if c.c==32:assert c.e==3;return 0
        if c.c==26:dma=c.de;return 0
        if c.c==21:
            assert c.de==0x4800 and dma==s['EW_DATA']
            attempts+=1
            if attempts==fail_at:return status
            records.append(bytes(c.mem[dma:dma+128]));return 0
        raise AssertionError(('unexpected BDOS',c.c))
    c.port_read=io;c.hl=0x4800;c.a=3;assert call('EW_INIT')==(False,0)
    def put(byte):c.c=byte;return call('EW_PUT')
    return c,s,call,put,records,calls


def main():
    for length in (0,1,127,128,129,255,256,257,1024):
        c,s,call,put,records,calls=output()
        body=bytes(i%256 for i in range(length))
        for byte in body:assert put(byte)==(False,0)
        assert call('EW_FIN')==(False,0)
        padding=(-length)%128
        assert b''.join(records)==body+b'\x1a'*padding
        assert c.mem[s['EW_PAD']]==padding
        count=len(calls);assert not call('EW_FIN')[0] and len(calls)==count
        assert put(88)==(True,255) and len(calls)==count
        assert set(calls)<={21,26,32}
    for status in (1,2,255):
        c,s,call,put,records,calls=output(1,status)
        for byte in range(128):assert put(byte)==(False,0)
        assert put(99)==(True,status) and not records
        assert c.mem[s['EW_POS']]==128
        assert bytes(c.mem[s['EW_DATA']:s['EW_DATA']+128])==bytes(range(128))
        count=len(calls)
        assert put(100)==(True,status) and call('EW_FIN')==(True,status)
        assert len(calls)==count  # never retry an uncertain sequential write
        c.hl=0x4800;c.a=3;call('EW_INIT')
        assert c.mem[s['EW_BAD']]==0 and c.mem[s['EW_POS']]==0
    c,s,call,put,records,calls=output(1,2)
    assert put(65)==(False,0) and call('EW_FIN')==(True,2)
    assert c.mem[s['EW_PAD']]==127 and c.mem[s['EW_SEAL']]==0
    count=len(calls);assert call('EW_FIN')==(True,2) and len(calls)==count
    print('PASS: output record boundaries, exact bytes, final padding, sealed stream and latched write failures')


if __name__=='__main__':main()
