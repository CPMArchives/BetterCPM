#!/usr/bin/env python3
"""Integrated save-data drain across source, editing gap and output records."""
from test_ed_buffer import context


def setup(source,editing=b'',read_error=False,write_error=False):
    c,s,call,state,run=context(1024);reads=0;writes=[];dma=0;calls=[]
    padded=source+b'\x1a'*(128-len(source)%128)
    records=[padded[i:i+128] for i in range(0,len(padded),128)]
    c.mem[5:8]=bytes((0xdb,254,0xc9))
    def io(port):
        nonlocal reads,dma
        calls.append(c.c)
        if c.c==32:assert c.e in (3,7);return 0
        if c.c==26:dma=c.de;return 0
        if c.c==20:
            assert c.de==0x4800 and dma==s['ES_DATA'];reads+=1
            if read_error:return 2
            record=records.pop(0);c.mem[dma:dma+128]=record;return 0
        if c.c==21:
            assert c.de==0x4900 and dma==s['EW_DATA']
            if write_error:return 2
            writes.append(bytes(c.mem[dma:dma+128]));return 0
        raise AssertionError(('unexpected publication/other BDOS',c.c))
    c.port_read=io;c.hl=0x4800;c.a=7;call('ES_INIT')
    c.hl=0x4900;c.a=3;call('EW_INIT');call('EF_INIT')
    for byte in editing:c.c=byte;assert not call('EB_PUT')[0]
    return c,s,call,state,run,writes,calls


def main():
    for source,editing in [(b'',b''),(b'unread Mixed\r\n',b'EDIT\r\n'),
                           (b'x'*512,b'Y'*256),(b'abc\x1aignored',b'')]:
        c,s,call,state,run,writes,calls=setup(source,editing)
        assert call('EF_DRAIN')==(False,0) and state()==(b'',0)
        expected=editing+source.split(b'\x1a')[0]
        assert b''.join(writes)==expected+b'\x1a'*((-len(expected))%128)
        count=len(calls);assert call('EF_DRAIN')==(False,0) and len(calls)==count
        assert c.mem[s['EF_DONE']]==1
    # Prewritten output and previously appended source are not duplicated.
    c,s,call,state,run,writes,calls=setup(b'one\r\ntwo\r\nlast')
    assert not run(b'aW')[0][0]
    assert call('EF_DRAIN')==(False,0)
    assert b''.join(writes).rstrip(b'\x1a')==b'one\r\ntwo\r\nlast'
    # U affects appended text, not the unread tail copied at E.
    c,s,call,state,run,writes,calls=setup(b'Mixed\r\ntail')
    assert not run(b'Ua')[0][0]
    assert call('EF_DRAIN')==(False,0)
    assert b''.join(writes).rstrip(b'\x1a')==b'MIXED\r\ntail'
    c,s,call,state,run,writes,calls=setup(b'x',b'EDIT',read_error=True)
    assert call('EF_DRAIN')==(True,2) and not writes
    assert c.mem[s['EF_DONE']]==0 and c.mem[s['EF_ERROR']]==2
    c,s,call,state,run,writes,calls=setup(b'z'*200,write_error=True)
    assert call('EF_DRAIN')==(True,2)
    assert c.mem[s['EF_HAVE']]==1 and c.mem[s['EF_BYTE']]==ord('z')
    assert c.mem[s['ES_POS']]==1  # first byte of second source record is held
    count=len(calls);assert call('EF_DRAIN')==(True,2) and len(calls)==count
    print('PASS: integrated save drain, unread tail, prior A/W, case, padding, repeat finish and failure retention')


if __name__=='__main__':main()
