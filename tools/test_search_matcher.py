#!/usr/bin/env python3
"""Execute SEARCH's Z80 streaming core against independent byte/line oracles.

This is module verification, not a runnable utility or CP/M qualification.
"""
from pathlib import Path
import random
import re
from build_ccp import assemble
from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/search-core'


def compile_core():
    OUT.mkdir(parents=True, exist_ok=True)
    source = ('        ORG 0200H\n' +
              (ROOT/'src/utilities/search/matcher.inc').read_text() +
              (ROOT/'src/utilities/search/state.inc').read_text() +
              '\n        END\n')
    image = assemble(Path.home()/'bin/z80asm', source,
                     OUT/'matcher.bin', OUT/'matcher.lst', 0x200)
    listing = (OUT/'matcher.lst').read_text()
    names = {m[2]: int(m[1], 16) for m in re.finditer(
        r'^([0-9a-f]{4})\s+.*?\b(S[A-Z0-9]+):', listing, re.M | re.I)}
    return image, names


class Core:
    def __init__(self, image, names):
        self.c = Z80(b'')
        self.c.mem[0x200:0x200+len(image)] = image
        self.names = names
        self.guard = names['SFEND']
        self.c.mem[self.guard:self.guard+16] = bytes([0xA5])*16

    def call(self, name):
        sp = self.c.sp
        self.c.run(self.names[name], limit=100000)
        assert self.c.sp == sp, (name, 'stack imbalance')
        assert self.c.mem[self.guard:self.guard+16] == bytes([0xA5])*16

    def configure(self, pattern, flags=0):
        self.c.mem[0x7000:0x7000+len(pattern)] = pattern
        self.c.hl = 0x7000
        self.c.b = len(pattern)
        self.c.c = flags
        self.call('SCONFIG')
        assert bytes(self.c.mem[0x7000:0x7000+len(pattern)]) == pattern
        return self.c.a if self.c.carry else 0

    def read(self, name, size=4):
        p = self.names[name]
        return int.from_bytes(self.c.mem[p:p+size], 'little')

    def write(self, name, value, size=4):
        p = self.names[name]
        self.c.mem[p:p+size] = value.to_bytes(size, 'little')

    def feed(self, byte):
        self.c.a = byte
        self.call('SFEED')
        assert not self.c.carry, ('unexpected overflow', self.c.a)
        mask = self.c.a
        return (mask, self.read('STSTART') if mask & 1 else None,
                self.read('STLINE') if mask & 1 else None,
                self.read('SHSTART') if mask & 2 else None)


def fold(data):
    return bytes(b-32 if 97 <= b <= 122 else b for b in data)


def lines(data):
    # Independent lookahead oracle: a CR/LF pair belongs to the line it ends.
    result = []
    line = 1
    for i, b in enumerate(data):
        result.append(line)
        if b == 10 or (b == 13 and (i+1 == len(data) or data[i+1] != 10)):
            line += 1
    return result


def check(core, pattern, data, flags=0):
    assert core.configure(pattern, flags) == 0, (pattern, flags)
    text = None if flags & 2 else (fold(pattern) if flags & 4 else pattern)
    binary = None
    if not flags & 1:
        try:
            # Fixtures use the accepted strict notation, not Python's broader
            # whitespace decoder as the syntax acceptance oracle.
            binary = bytes.fromhex(pattern.decode('ascii'))
        except (ValueError, UnicodeDecodeError):
            pass
    source = fold(data) if flags & 4 else data
    line_numbers = lines(data)
    observed = []
    for end, byte in enumerate(data, 1):
        tm = text is not None and end >= len(text) and source[end-len(text):end] == text
        hm = binary is not None and end >= len(binary) and data[end-len(binary):end] == binary
        expected = (int(tm) | (int(hm) << 1), end-len(text) if tm else None,
                    line_numbers[end-len(text)] if tm else None,
                    end-len(binary) if hm else None)
        actual = core.feed(byte)
        assert actual == expected, (pattern, flags, end, actual, expected)
        if actual[0]:
            observed.append(actual)
    assert core.read('SPOS') == len(data)
    return observed


def main():
    image, names = compile_core()
    core = Core(image, names)
    for pattern, flags, error in [
        (b'', 0, 2), (b'A'*65, 0, 3), (b'41', 3, 1),
        (b'41', 8, 1), (b'41', 128, 1), (b'A'*128, 2, 1),
        (b'4', 2, 4), (b'41 4', 2, 4), (b'0x41', 2, 4),
        (b'41H', 2, 4), (b'41,42', 2, 4), (b' 41', 2, 4),
        (b'41 ', 2, 4), (b'41\t42', 2, 4), (b'4 1', 2, 4), (b'4142 43', 2, 4), (b'41 4243', 2, 4),
    ]:
        assert core.configure(pattern, flags) == error, (pattern, flags)
        assert core.read('STLEN', 1) == core.read('SHLEN', 1) == 0
    # Failed configurations cannot leak a previous valid matcher.
    assert core.configure(b'41') == 0
    assert core.configure(b'X', 2) == 4
    assert core.feed(ord('A'))[0] == 0

    check(core, b'4142', b'4142 AB 4142\r\n'+b'\x1a'*114)
    check(core, b'AAA', b'AAAAA')
    check(core, b'33', b'33333')  # Both modes overlap, with independent starts.
    check(core, b'AB', b'.'*65535+b'AB', 1)  # Real stream beyond 64 KiB.
    check(core, b'4142', b'4142 AB 4142', 1)
    check(core, b'41 42', b'AB 41 42 AB', 2)
    check(core, b'41  42', b'AB 41  42 AB')
    check(core, b'4a00', b'J\0j\0J\0', 6)
    check(core, b'hello', b'Hello hELLo HELLO hello', 4)
    check(core, b'hello', b'Hello hELLo HELLO hello')
    check(core, b'\xe1a', b'\xc1A\xe1A\xe1a', 5)
    check(core, b'1a', bytes(range(256))+b'\x1a'*128, 2)
    check(core, b'00', bytes(256), 2)
    for p in (b'X', b'\r', b'\n', b'\r\n', b'\nX', b'X\r\nX'):
        check(core, p, b'X\r\nX\rX\nX\r\r\nX\n\nX\r', 1)
    # Maximum window at every possible logical-record split, including overlap.
    pattern = b'A'*63+b'B'
    for split in range(1, 65):
        check(core, pattern, b'.'*(128-split)+pattern+pattern, 1)
    check(core, b'A'*64, b'A'*256, 1)
    # 126 HEX characters are the largest even test input accepted by this API;
    # a real command has less room because operands/delimiters share the tail.
    check(core, b'41'*63, b'A'*128, 2)
    rng = random.Random(524)
    for _ in range(25):
        data = bytes(rng.choice(b'ABCabc\r\n\0\x1a') for _ in range(180))
        start = rng.randrange(150)
        check(core, data[start:start+rng.randrange(1, 12)], data, 1 | (4 if rng.randrange(2) else 0))
    # Seed the documented wide positions to test carry propagation without
    # spending emulator time feeding thousands of uninteresting record bytes.
    assert core.configure(b'AB', 1) == 0
    core.write('SPOS', 65535)
    assert core.feed(65)[0] == 0
    assert core.feed(66)[1] == 65535
    assert core.read('SPOS') == 65537
    core.call('SRESET')
    assert core.feed(66)[0] == 0, 'partial match leaked across files'
    core.write('SLINE', 65535)
    core.feed(13)
    core.feed(10)
    assert core.read('SLINE') == 65536
    core.write('SPOS', 0xFFFFFFFF)
    core.c.a = 65
    core.call('SFEED')
    assert core.c.carry and core.c.a == 5
    assert core.read('SPOS') == 0xFFFFFFFF
    core.call('SFEED')
    assert core.c.carry and core.c.a == 5
    core.call('SRESET')
    core.write('SLINE', 0xFFFFFFFF)
    core.c.a = 10
    core.call('SFEED')
    assert core.c.carry and core.c.a == 5
    core.call('SRESET')
    assert core.read('SERROR', 1) == 0 and core.read('SLINE') == 1
    print(f'SEARCH matcher: configuration, independent dual-mode oracle, overlaps, '
          f'all 64 record splits, line attribution, reset and overflow pass ({len(image)} bytes including state)')


if __name__ == '__main__':
    main()
