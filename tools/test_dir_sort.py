#!/usr/bin/env python3
"""Execute DIR's production sorter and verify complete record identities."""
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
    runs=0
    for number,selected in enumerate(cases):
        modes=[('N',0)] if len(selected)>255 else [('N',0),('N',1),('T',0),('T',1),('Z',0),('Z',1),('U',0)]
        for mode,reverse in modes:
            c = Z80(b'')
            c.mem[256:256+len(image)] = image
            c.mem[addr('DT_UNIT')]=ord('E')  # Display units must not change allocated-space ordering.
            start = addr('DT_BUFFER')
            sizes=[0,8,256,65536,0x1000000,0xffffffff]
            records = [name+bytes([i%256])+sizes[i%len(sizes)].to_bytes(4,'little')+
                       (i*12345).to_bytes(4,'little')+(i+1).to_bytes(4,'little')
                       for i,name in enumerate(selected)]
            data = b''.join(records)
            c.mem[start-1] = 0x5a
            c.mem[start:start+len(data)] = data
            c.mem[start+len(data)] = 0xa5
            c.setword(addr('DT_FILES'),len(records))
            c.setword(addr('DT_END'),start+len(data))
            c.mem[addr('DN_MODE')],c.mem[addr('DN_REV')]=ord(mode),reverse
            totals = bytes(range(12))
            c.mem[addr('DT_TOTAL'):addr('DT_TOTAL')+12] = totals
            c.run(addr('DN_SORT'),limit=15000000)
            actual = bytes(c.mem[start:start+len(data)])
            if mode=='U':expected=records
            elif mode=='N':expected=sorted(records,key=lambda record:record[:11],reverse=bool(reverse))
            elif mode=='T':expected=sorted(records,key=lambda record:(
                tuple(-x if reverse else x for x in record[8:11]),record[:11]))
            else:expected=sorted(records,key=lambda record:(
                (-1 if reverse else 1)*int.from_bytes(record[12:16],'little'),record[:11]))
            assert actual == b''.join(expected),(number,mode,reverse)
            assert c.mem[start-1] == 0x5a and c.mem[start+len(data)] == 0xa5,number
            assert c.word(addr('DT_FILES')) == len(records)
            assert c.word(addr('DT_END')) == start+len(data)
            assert bytes(c.mem[addr('DT_TOTAL'):addr('DT_TOTAL')+12]) == totals
            runs+=1
    print(f'DIR sort modes: {runs} cases; record identity, stability and bounds pass')

if __name__ == '__main__':
    main()
