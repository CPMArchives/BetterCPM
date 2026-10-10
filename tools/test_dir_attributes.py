#!/usr/bin/env python3
"""Execute DIR collection and reporting for all RO/SYS/ARC combinations."""
import re
from pathlib import Path
from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]
image = (ROOT / 'build/utilities/DIR.COM').read_bytes()
listing = (ROOT / 'build/utilities/dir-transient.lst').read_text()
def addr(name):
    return int(re.search(r'^([0-9a-f]{4})\s+.*?\b' + name + ':', listing, re.M | re.I)[1], 16)

for mask in range(8):
    c = Z80(b'')
    c.mem[256:256 + len(image)] = image
    buffer = addr('DT_BUFFER')
    c.setword(addr('DT_END'), buffer)
    c.setword(addr('DT_LIMIT'), buffer + 49)
    c.setword(addr('BC_DIREP'), 0x7100)
    c.setword(addr('DT_DPB'), 0x7000)
    entry = bytearray(32)
    entry[1:12] = b'FLAGS   TXT'
    for bit in range(3):
        if mask & (1 << bit):
            entry[9 + bit] |= 128
    c.mem[0x7100:0x7120] = entry
    c.run(addr('DT_STORE'), limit=10000)
    assert not c.carry and c.word(addr('DT_FILES')) == 1
    assert c.mem[buffer + 11] == mask
    assert bytes(c.mem[0x7100:0x7120]) == entry
    c.setword(addr('DT_SCAN'), buffer)
    c.mem[addr('BC_PRINT')] = 0xc9
    output = 0x6100
    c.setword(0x6000, output)
    stub = b'\xe5\x2a\x00\x60\x77\x23\x22\x00\x60\xe1\xc9'
    c.mem[addr('BC_PCHAR'):addr('BC_PCHAR') + len(stub)] = stub
    c.mem[addr('DT_SHOWATTR')] = 1
    c.run(addr('DT_ATTRIBUTES'), limit=10000)
    expected = ''.join(letter if mask & bit else '-' for bit, letter in [(2, 'S'), (1, 'R'), (4, 'A')])
    assert bytes(c.mem[output:c.word(0x6000)]).decode() == expected
    c.mem[addr('DT_SHOWATTR')] = 0
    c.setword(0x6000, output)
    c.run(addr('DT_ATTRIBUTES'), limit=10000)
    assert c.word(0x6000) == output
    # Additional physical entries stay one file; merge observed attribute bits.
    entry[12], entry[9], entry[10], entry[11] = 1, ord('T') | 128, ord('X') | 128, ord('T') | 128
    c.mem[0x7100:0x7120] = entry
    c.run(addr('DT_STORE'), limit=10000)
    assert not c.carry and c.word(addr('DT_FILES')) == 1
    assert c.mem[buffer + 11] == 7
print('Eight attribute masks, disabled display, immutable entries and extent aggregation passed')
