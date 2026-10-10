#!/usr/bin/env python3
"""Execute the production DIR accumulator against independent directory fixtures."""
import re
from pathlib import Path
from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]

def main():
    image = (ROOT / 'build/utilities/DIR.COM').read_bytes()
    listing = (ROOT / 'build/utilities/dir-transient.lst').read_text()
    def addr(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b' + name + ':',
                             listing, re.M | re.I)[1], 16)
    count = 0
    for width, shift, exm in [(1,3,0), (1,4,1), (1,7,15),
                              (2,4,0), (2,5,1), (2,7,7)]:
        for blocks in [[], [1], [255], [1,255], list(range(1,17 if width == 1 else 9))]:
            for extent, rc in [(0,0), (0,128), (1,1), (exm,127), (31,128)]:
                c = Z80(b'')
                c.mem[256:256+len(image)] = image
                dpb, entry, total = 0x7000, 0x7100, 0x7200
                c.mem[dpb+2], c.mem[dpb+4], c.mem[dpb+6] = shift, exm, width-1
                c.mem[entry+12], c.mem[entry+15] = extent, rc
                for i, block in enumerate(blocks):
                    # Word maps include a nonzero high byte with a zero low byte.
                    if width == 2 and block == 255:
                        block = 256
                    start = entry+16+i*width
                    c.mem[start:start+width] = block.to_bytes(width, 'little')
                initial_alloc, initial_logical, initial_entries = 0xffff, 0xffffff, 0xffff
                initial = (initial_alloc.to_bytes(4,'little') +
                           initial_logical.to_bytes(4,'little') +
                           initial_entries.to_bytes(4,'little'))
                c.mem[total:total+12] = initial
                before_entry = bytes(c.mem[entry:entry+32])
                before_dpb = bytes(c.mem[dpb:dpb+15])
                for repetition in range(1,4):
                    c.hl = entry
                    c.d, c.e = dpb >> 8, dpb & 255
                    c.b, c.c = total >> 8, total & 255
                    c.run(addr('DM_ADD'), limit=10000)
                    actual = bytes(c.mem[total:total+12])
                    expected = ((initial_alloc+repetition*len(blocks)*(1<<shift)).to_bytes(4,'little') +
                                (initial_logical+repetition*((extent & exm)*128+rc)).to_bytes(4,'little') +
                                (initial_entries+repetition).to_bytes(4,'little'))
                    assert actual == expected, (width,shift,exm,blocks,extent,rc,actual,expected)
                    assert bytes(c.mem[entry:entry+32]) == before_entry
                    assert bytes(c.mem[dpb:dpb+15]) == before_dpb
                    count += 1
    # Count every physical entry, but apply the same SYS/predicate visibility rule.
    for mask, explicit, state in [(255,0,2),(255,0,0),(4,1,2),(1,1,2),(255,1,7)]:
        c = Z80(b'')
        c.mem[256:256+len(image)] = image
        entry, dpb = 0x7100, 0x7000
        c.setword(addr('BC_DIREP'),entry)
        c.setword(addr('DT_DPB'),dpb)
        c.mem[dpb+2] = 3
        c.mem[entry+16] = 1
        c.mem[entry+12],c.mem[entry+15] = 5,128
        for bit in range(3):
            c.mem[entry+9+bit] = 128 if state & (1<<bit) else 0
        c.mem[addr('FS_MASK')],c.mem[addr('OQ_LEN')] = mask,explicit
        c.mem[addr('DT_TOTAL'):addr('DT_TOTAL')+12] = bytes(12)
        c.run(addr('DT_FILTER'),limit=10000)
        matches = bool(mask & (1<<state))
        visible = matches and (explicit or not state & 2)
        assert c.carry == bool(visible)
        assert c.hl == entry or not matches
        assert c.word(addr('DT_TOTAL')+8) == int(bool(visible))
    print(f'DIR metrics: {count} accumulation cases and selected visibility gates pass')

if __name__ == '__main__':
    main()
