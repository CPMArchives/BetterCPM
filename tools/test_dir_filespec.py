#!/usr/bin/env python3
"""Prove malformed DIR operands are rejected before FCB expansion or BDOS I/O."""
import re
from build_rcp_transients import COMMANDS, symbol
from test_bios import Z80
from test_disk_utilities import ROOT


def main():
    for binary_name, listing_name, origin in [
            ('build/cpx/rcp.bin', 'build/cpx/rcp.lst', 0x8000),
            ('build/utilities/DIR.COM', 'build/utilities/rcp-transient.lst', 0x100)]:
        binary = (ROOT / binary_name).read_bytes()
        listing = (ROOT / listing_name).read_text()
        if origin == 0x100:
            # A call-site is not an entry label, even when the label has a comment.
            for command, entry_name in COMMANDS.items():
                if command == "COPY":
                    continue
                image = (ROOT / "build/utilities" / (command + ".COM")).read_bytes()
                target = image[21] | (image[22] << 8)
                assert target == symbol(ROOT / listing_name, entry_name)
                label = re.search(r"^([0-9a-f]{4})\s+.*?\b" + entry_name + ":", listing, re.M | re.I)
                assert target == int(label[1], 16), command
        def address(name):
            return int(re.search(r'^([0-9a-f]{4})\s+.*?\b' + name + ':', listing, re.M | re.I)[1], 16)
        for pattern in ['F*A.DAT', 'F**?.DAT', 'F?**?.DAT', 'F.**A',
                        'ABCDEFGHI.COM', 'FOO.ABCD', 'FOO..DAT']:
            cpu = Z80(b'')
            cpu.mem[origin:origin + len(binary)] = binary
            cpu.mem[address('BC_PRINT')] = 0xc9
            cpu.mem[address('BC_DURST')] = 0xc9
            cpu.mem[5] = 0x76  # Any BDOS call makes this test fail.
            fcb = address('BC_FCB')
            cpu.mem[fcb:fcb+36] = bytes([0xa5])*36
            cpu.mem[0x7000:0x7000+len(pattern)] = pattern.encode()
            cpu.hl, cpu.b = 0x7000, len(pattern)
            cpu.run(address('BC_DPARSE'), limit=10000)
            assert cpu.de == address('BC_IFSPEC'), (binary_name, pattern)
            assert bytes(cpu.mem[fcb:fcb+36]) == bytes([0xa5])*36
    print('Malformed DIR patterns reject before FCB expansion and BDOS search in both builds')


if __name__ == '__main__':
    main()
