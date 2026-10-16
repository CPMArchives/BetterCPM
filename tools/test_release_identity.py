#!/usr/bin/env python3
"""Execute the packed extension's release query and selector/frame regressions."""
from pathlib import Path
from system_layout import LAYOUT
from test_bios import Z80
from test_utility_versions import address
from version_metadata import rows

ROOT = Path(__file__).resolve().parents[1]


def main():
    image = (ROOT/'build/system/resident.bin').read_bytes()
    listing = (ROOT/'build/system/extensions.lst').read_text(errors='replace')
    entry = address(listing, 'EX_ENTRY')
    release = next(r['implementation_version'] for r in rows()
                   if r['component'] == 'BetterCP/M')
    for selector in (176, 177, 178, 179, 180, 182, 199, 200, 255):
        c = Z80(b'')
        c.mem[LAYOUT['SYSTEM']:LAYOUT['SYSTEM']+len(image)] = image
        # Controlled platform loader/cursor: no disk or physical device access.
        for offset in (54, 57, 60):
            at = LAYOUT['BIOS']+offset
            c.mem[at:at+3] = bytes((0x3e, 0xff, 0xc9))
        c.mem[LAYOUT['RSX_STATE']] = 0
        c.c, c.de, c.ix = selector, 0x7500, 0xA55A
        initial_sp = c.sp
        c.run(entry, limit=100000)
        assert c.sp == initial_sp and c.ix == 0xA55A, selector
        if selector == 180:
            assert bytes(c.mem[c.hl:c.hl+4]) == b'BV\x01\x03'
            pointer = c.word(c.hl+6)
            assert bytes(c.mem[pointer:pointer+len(release)+1]) == release.encode()+b'$'
        elif selector in (176, 177, 200, 255):
            assert c.a == 255, (selector, c.a)
        elif selector == 178:
            assert c.a == 1
        elif selector == 182:
            assert c.hl == 0 and c.mem[0x7500+19] == 1
        elif selector == 199:
            assert c.hl == 0
        elif selector == 179:
            assert c.a == 255
    assert len((ROOT/'build/system/extensions.bin').read_bytes()) <= (
        LAYOUT['DISK']-LAYOUT['EXTENSIONS'])
    print('PASS: packed release descriptor, extension selectors and preserved IX/SP')


if __name__ == '__main__':
    main()
