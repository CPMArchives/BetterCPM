#!/usr/bin/env python3
"""Production DIR grouping, bounded TPA buffer and allocated-size formatting."""
import re
from pathlib import Path
from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]

def main():
    image = (ROOT/'build/utilities/DIR.COM').read_bytes()
    listing = (ROOT/'build/utilities/dir-transient.lst').read_text()
    def addr(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
    c = Z80(b'')
    c.mem[256:256+len(image)] = image
    buffer = addr('DT_BUFFER')
    c.setword(addr('DT_END'),buffer)
    c.setword(addr('DT_FILES'),0)
    c.setword(addr('DT_LIMIT'),buffer+24*3+1)
    c.setword(addr('BC_DIREP'),0x7100)
    c.setword(addr('DT_DPB'),0x7000)
    c.mem[0x7002],c.mem[0x7004] = 4,1
    records = [('MULTI   DAT',3,128,[1,2]),('EMPTY   DAT',0,0,[]),
               ('MULTI   DAT',1,128,[3]),('THIRD   TXT',0,1,[4]),
               ('MULTI   DAT',5,7,[5])]
    before = bytes(c.mem[0x7000:0x700f])
    for name,ex,rc,blocks in records:
        entry = bytearray(32)
        entry[1:12] = name.encode()
        entry[9] |= 128   # attribute bits do not split the filename identity
        entry[12],entry[15] = ex,rc
        entry[16:16+len(blocks)] = bytes(blocks)
        c.mem[0x7100:0x7120] = entry
        c.run(addr('DT_STORE'),limit=10000)
        assert not c.carry
        assert bytes(c.mem[0x7100:0x7120]) == entry
        assert bytes(c.mem[0x7000:0x700f]) == before
    assert c.word(addr('DT_FILES')) == 3
    assert c.word(addr('DT_END')) == buffer+72
    def summary(index):
        start = buffer+index*24
        return (bytes(c.mem[start:start+11]).decode(),
                tuple(int.from_bytes(c.mem[start+12+i*4:start+16+i*4],'little')
                      for i in range(3)))
    assert all(c.mem[buffer+i*24+11]==1 for i in range(3))
    assert summary(0) == ('MULTI   DAT',(64,647,3))
    assert summary(1) == ('EMPTY   DAT',(0,0,1))
    assert summary(2) == ('THIRD   TXT',(16,1,1))
    saved = bytes(c.mem[buffer:buffer+96])
    c.mem[0x7101:0x710c] = b'FOURTH  TXT'
    c.run(addr('DT_STORE'),limit=10000)
    assert c.carry and c.word(addr('DT_FILES')) == 3
    assert bytes(c.mem[buffer:buffer+96]) == saved
    # The existing last file still aggregates when no new record can fit.
    c.mem[0x7101:0x710c] = b'THIRD   TXT'
    c.mem[0x710c],c.mem[0x710f] = 0,1
    c.run(addr('DT_STORE'),limit=10000)
    assert not c.carry and summary(2)[1] == (32,2,2)
    # Execute the production KiB conversion/decimal formatter without BDOS.
    output = 0x6100
    c.setword(0x6000,output)
    stub = b'\xe5\x2a\x00\x60\x77\x23\x22\x00\x60\xe1\xc9'
    c.mem[addr('BC_PCHAR'):addr('BC_PCHAR')+len(stub)] = stub
    for records in [0,8,16,320,65536,0xfffffff8]:
        c.mem[0x7300:0x7304] = records.to_bytes(4,'little')
        c.setword(0x6000,output)
        c.hl = 0x7300
        c.run(addr('DT_K'),limit=100000)
        assert bytes(c.mem[output:c.word(0x6000)]).decode() == str(records//8)
    print('DIR multi-extent grouping, buffer exhaustion and 32-bit KiB formatting pass')

if __name__ == '__main__':
    main()
