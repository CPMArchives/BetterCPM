#!/usr/bin/env python3
"""Execute DIR's production name sorter and verify complete record identities."""
import itertools
import random
import re
from pathlib import Path
from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]

def main():
    image = (ROOT/'build/utilities/DIR.COM').read_bytes()
    listing = (ROOT/'build/utilities/dir-transient.lst').read_text()
    def addr(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
    names = [b'FOO     COM',b'A       TXT',b'FOO     ASM',b'AA      DAT']
    cases = [[],[names[0]]]+list(map(list,itertools.permutations(names)))
    cases += [names,sorted(names),sorted(names,reverse=True),[names[0]]*4]
    rng = random.Random(201)
    for length in (3,7,16,31,64):
        cases.append([rng.choice(names) for _ in range(length)])
    # Word-sized counts must not be truncated at 255. One displaced record
    # exercises every shrinking pass without a large random test cost.
    cases.append([f'F{i:07d}TXT'.encode() for i in range(1,260)]+[b'A       TXT'])
    for number,selected in enumerate(cases):
        c = Z80(b'')
        c.mem[256:256+len(image)] = image
        start = addr('DT_BUFFER')
        records = [name+bytes([i%256])+i.to_bytes(4,'little')+
                   (i*12345).to_bytes(4,'little')+(i+1).to_bytes(4,'little')
                   for i,name in enumerate(selected)]
        data = b''.join(records)
        c.mem[start-1] = 0x5a
        c.mem[start:start+len(data)] = data
        c.mem[start+len(data)] = 0xa5
        c.setword(addr('DT_FILES'),len(records))
        c.setword(addr('DT_END'),start+len(data))
        totals = bytes(range(12))
        c.mem[addr('DT_TOTAL'):addr('DT_TOTAL')+12] = totals
        c.run(addr('DN_SORT'),limit=15000000)
        actual = bytes(c.mem[start:start+len(data)])
        assert actual == b''.join(sorted(records,key=lambda record:record[:11])),number
        assert c.mem[start-1] == 0x5a and c.mem[start+len(data)] == 0xa5,number
        assert c.word(addr('DT_FILES')) == len(records)
        assert c.word(addr('DT_END')) == start+len(data)
        assert bytes(c.mem[addr('DT_TOTAL'):addr('DT_TOTAL')+12]) == totals
    print(f'DIR ascending name sort: {len(cases)} cases; record identity, stability and bounds pass')

if __name__ == '__main__':
    main()
