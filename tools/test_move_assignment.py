#!/usr/bin/env python3
"""Check COPY/MOVE operand boundaries in real resident and transient code."""
import re
import struct
from pathlib import Path

from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]


def images():
    carrier = (ROOT / 'build/cpx/RCP.CPX').read_bytes()
    linked, size = struct.unpack_from('<HH', carrier, 10)
    count, _, payload, table = struct.unpack_from('<4H', carrier, 22)
    listing = (ROOT / 'build/cpx/rcp.lst').read_text()
    for base in (0x4000, 0x8101, 0xA000):
        image = bytearray(carrier[payload:payload + size])
        for i in range(count):
            offset = struct.unpack_from('<H', carrier, table + 2 * i)[0]
            value = struct.unpack_from('<H', image, offset)[0]
            struct.pack_into('<H', image, offset, (value + base - linked) & 65535)
        yield f'RCP at {base:04X}', image, listing, base, base - linked
    for name in ('COPY', 'MOVE'):
        listing_name = 'copy-transient.lst' if name == 'COPY' else 'rcp-transient.lst'
        yield name, (ROOT / f'build/utilities/{name}.COM').read_bytes(), (
            ROOT / 'build/utilities' / listing_name).read_text(), 0x100, 0


def main():
    count = 0
    for name, image, listing, base, delta in images():
        def address(symbol):
            return int(re.search(r'^([0-9a-f]{4})\s+.*?\b' + symbol + ':',
                                 listing, re.M | re.I)[1], 16) + delta
        for move in (False, True):
            for tail, destination, source in (
                ('B:MOVED.DAT=A:SOURCE.DAT', 'B:MOVED.DAT', 'A:SOURCE.DAT'),
                ('B3:=A0:README.TXT', 'B3:', 'A0:README.TXT'),
                ('B3:=A2:README.TXT', 'B3:', 'A2:README.TXT'),
                ('3:=A0:README.TXT', '3:', 'A0:README.TXT'),
                ('B:=A0:README.TXT', 'B:', 'A0:README.TXT'),
                ('[B3,B3]:=A0:README.TXT', '[B3,B3]:', 'A0:README.TXT'),
                ('A:SOURCE.DAT B:MOVED.DAT', 'B:MOVED.DAT', 'A:SOURCE.DAT'),
            ):
                cpu = Z80(b'')
                cpu.mem[base:base + len(image)] = image
                cpu.mem[5] = 0xC9  # Stop BDOS queries without accessing media.
                cpu.mem[address('BC_CPARSE')] = 0xC9
                cpu.mem[0x3000:0x3000 + len(tail)] = tail.encode()
                cpu.hl, cpu.b = 0x3000, len(tail)
                cpu.run(address('BC_MOVE' if move else 'BC_COPY'), limit=10000)
                for ptr, length, expected in (
                    ('BC_CDPTR', 'BC_CDLEN', destination),
                    ('BC_CSPTR', 'BC_CSLEN', source),
                ):
                    start = cpu.word(address(ptr))
                    size = cpu.mem[address(length)]
                    actual = bytes(cpu.mem[start:start + size]).decode()
                    assert actual == expected, (name, move, tail, ptr, actual, expected)
                count += 1
    print(f'{count} COPY/MOVE operand-boundary cases pass across resident relocation and transient builds')


if __name__ == '__main__':
    main()
