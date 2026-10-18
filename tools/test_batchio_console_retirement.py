#!/usr/bin/env python3
"""EOF and malformed queues preserve Function-10 callers; only Function 0 retires."""
import re
from pathlib import Path
from test_bios import Z80
ROOT=Path(__file__).resolve().parents[1]


def main():
    binary=(ROOT/'build/rsx/batchio.bin').read_bytes();listing=(ROOT/'build/rsx/batchio.lst').read_text()
    def addr(n):return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+n+':',listing,re.M|re.I)[1],16)
    for failure in ('absent','empty','read','oversize','close'):
        malformed=failure!='absent'
        c=Z80(b'');c.mem[0x8000:0x8000+len(binary)]=binary;c.setword(addr('BI_NEXT'),0x7000)
        c.mem[0x7000:0x7003]=bytes((0xdb,254,0xc9));c.mem[0:3]=bytes.fromhex('c3ffff')
        c.mem[0x100:0x5000]=b'G'*(0x5000-0x100);original=bytes(c.mem[0x100:0x5000]);c.mem[0x6000]=20;active=[False]
        c.mem[addr('BI_FRESH')]=0;calls=[];state={'user':31,'dma':0x6500}
        def io(port):
            f=c.c;calls.append(f)
            if f==32:
                old=state['user']
                if c.e!=255:state['user']=c.e
                return old
            if f==26:state['dma']=c.de;return 0
            if f==15:
                if active[0]:c.mem[addr('BI_SUBRC')]=2;return 0
                if malformed:c.mem[addr('BI_SUBRC')]=0 if failure=='empty' else (2 if failure=='close' else 1);return 0
                return 255
            if f==20:
                if failure=='read' and not active[0]:return 2
                c.mem[addr('BI_BUFFER'):addr('BI_BUFFER')+4]=(b'\x7eNEW' if failure=='oversize' and not active[0] else b'\x03NEW');return 0
            if f==16:return 255 if failure=='close' and not active[0] else 3
            if f in (9,19):return 0
            if f==10:
                assert c.de==0x6000 and state=={'user':31,'dma':0x6500}
                c.mem[0x6001]=7;c.mem[0x6002:0x6009]=b'CONSOLE';return 0
            if f in (0,177):return 0
            raise AssertionError(('unexpected call',f))
        c.port_read=io;c.c=0;c.run(addr('BI_DISPATCH'),limit=100000);assert calls==[0];calls.clear()
        c.setword(addr('BI_UDMA'),0x6500);c.c=10;c.de=0x6000
        c.run(addr('BI_DISPATCH'),limit=100000)
        assert c.mem[0x6001:0x6009]==b'\x07CONSOLE'
        assert bytes(c.mem[0x100:0x5000])==original and 177 not in calls
        assert (19 in calls)==malformed and c.mem[addr('BI_IDLE')]==1
        # The application now explicitly requests warm boot; retirement may
        # consume its workspace only at this boundary.
        c.c=0;c.run(addr('BI_DISPATCH'),limit=100000)
        assert calls[-1]==177
        # A later valid stream must rearm batching rather than retire on its
        # next explicit Function 0 just because console fallback occurred earlier.
        active[0]=True;c.c=10;c.de=0x6000;c.run(addr('BI_DISPATCH'),limit=100000)
        assert c.mem[0x6001:0x6005]==b'\x03NEW' and c.mem[addr('BI_IDLE')]==0
        c.c=0;c.run(addr('BI_DISPATCH'),limit=100000);assert calls[-1]==0
    print('PASS BATCHIO console EOF/malformed recovery, application/DU/DMA preservation and Function-0-only retirement')

if __name__=='__main__':main()
