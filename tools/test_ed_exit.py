#!/usr/bin/env python3
"""Full BetterCP/M DU selection plus stock CCP packed-byte/DMA restoration."""
from test_ed_buffer import context


def main():
    c,s,call,_,_=context();ops=[]
    c.mem[5:8]=bytes((0xdb,254,0xc9))
    def io(port):
        assert c.c in (14,32,26),c.c
        ops.append((c.c,c.de if c.c==26 else c.e));return 0
    c.port_read=io
    for drive in range(16):
        for user in range(32):
            ops.clear();c.mem[s['FQ_DRIVE']]=drive;c.a=user
            assert call('FQ_LEAVE')==(False,1)
            assert ops==[(14,drive),(32,user),(26,128)]
            assert c.mem[4]==((user&15)<<4)|drive
    print('PASS: exit selects all 16 drives/32 users, restores DMA and prepares legacy CCP boot byte')


if __name__=='__main__':main()
