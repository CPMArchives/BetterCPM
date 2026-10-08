#!/usr/bin/env python3
"""Execute COPY's exact-filespec validator in CPX and transient builds."""
import re
from pathlib import Path
from test_bios import Z80
from test_disk_utilities import ROOT


def main():
    valid = ['A', 'FILE', 'FILE.', 'FILE.COM', 'ABCDEFGH.COM', '12345678.123']
    invalid = ['', '.COM', 'ABCDEFGHI.COM', 'FILE.ABCD', 'FILE..COM',
               'F*X.DAT', 'F?.DAT', 'FILE:COM', 'FILE=COM', 'FILE COM',
               'FILE.COM EXTRA', 'FILE.\x01', 'FILE.\x7f']
    for binary_path, listing_path, origin in [
            ('build/cpx/rcp.bin', 'build/cpx/rcp.lst', 0x8000),
            ('build/utilities/COPY.COM', 'build/utilities/rcp-transient.lst', 0x100)]:
        binary = (ROOT / binary_path).read_bytes()
        listing = (ROOT / listing_path).read_text()
        entry = int(re.search(r'^([0-9a-f]{4})\s+.*?\bBC_CVALID:', listing, re.M | re.I)[1], 16)
        for text in valid + invalid:
            cpu = Z80(b'')
            cpu.mem[origin:origin + len(binary)] = binary
            cpu.mem[0x7000:0x7000 + len(text)] = text.encode('ascii')
            cpu.hl, cpu.b = 0x7000, len(text)
            before = bytes(cpu.mem)
            cpu.run(entry, limit=10000)
            assert cpu.carry == (text in invalid), (binary_path, text)
            # The routine only reads its operand; no FCB or code writes.
            assert cpu.mem[origin:origin + len(binary)] == before[origin:origin + len(binary)]
    print('COPY CPX/transient exact 8.3 boundaries and malformed operands passed')


if __name__ == '__main__':
    main()
