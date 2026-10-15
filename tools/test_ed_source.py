#!/usr/bin/env python3
"""Record source state, sticky text/physical EOF and recoverable read errors."""
from test_ed_buffer import context


def stream(records):
    c,s,call,_,_=context();pending=list(records);calls=[];dma=0
    c.mem[5:8]=bytes((0xdb,254,0xc9))
    def io(port):
        nonlocal dma
        calls.append(c.c)
        if c.c==32:assert c.e==7;return 0
        if c.c==26:dma=c.de;return 0
        if c.c==20:
            assert c.de==0x4800 and dma==s['ES_DATA']
            item=pending.pop(0)
            if isinstance(item,int):return item
            assert len(item)==128;c.mem[dma:dma+128]=item;return 0
        raise AssertionError(('unexpected BDOS',c.c))
    c.port_read=io;c.hl=0x4800;c.a=7;call('ES_INIT')
    return c,s,call,calls,pending


def main():
    # A record boundary preserves every non-EOF byte, including NUL/high bit.
    body=bytes(x for x in range(256) if x!=26)+b'xy'
    padded=body+b'\x1a'*(384-len(body))
    c,s,call,calls,pending=stream([padded[i:i+128] for i in range(0,384,128)])
    for byte in body:assert call('ES_GET')==(False,byte)
    assert call('ES_GET')==(True,1);count=len(calls)
    for _ in range(3):assert call('ES_GET')==(True,1)
    assert len(calls)==count and not pending
    c,s,call,calls,pending=stream([b'a'*128,2,b'b'*128,1])
    for _ in range(128):assert call('ES_GET')==(False,97)
    assert call('ES_GET')==(True,2) and c.mem[s['ES_POS']]==128
    for _ in range(128):assert call('ES_GET')==(False,98)
    assert call('ES_GET')==(True,1);count=len(calls)
    assert call('ES_GET')==(True,1) and len(calls)==count
    # Reinitialization clears sticky EOF without changing the caller's FCB.
    before=bytes(c.mem[0x4800:0x4824]);c.hl=0x4800;c.a=7;call('ES_INIT')
    assert c.mem[s['ES_EOF']]==0 and c.mem[s['ES_POS']]==128
    assert bytes(c.mem[0x4800:0x4824])==before
    assert set(calls)=={20,26,32}
    print('PASS: source record boundaries, exact bytes, sticky EOF, read-error retry and reinitialization')


if __name__=='__main__':main()
