#!/usr/bin/env python3
"""Reject structurally invalid/unreadable SYSTEM packages before installation."""
from pathlib import Path
from build_system_package import compose
from test_utility_versions import address, runner
ROOT = Path(__file__).resolve().parents[1]


def main():
    image = (ROOT / 'build/utilities/SYSGEN.COM').read_bytes()
    listing = (ROOT / 'build/utilities/sysgen.lst').read_text()
    package, _ = compose()
    cases = ('valid', 'open', 'header-read', 'magic', 'version', 'size', 'base', 'short', 'extra', 'payload-read')
    for case in cases:
        data = bytearray(package)
        for name, offset in (('magic',0),('version',4),('size',6),('base',8)):
            if case == name: data[offset] ^= 1
        if case == 'short': data = data[:-128]
        if case == 'extra': data += bytes(128)
        cpu = runner(image); cpu.mem[5:8] = bytes((0xDB,254,0xC9))
        state = {'dma': 0, 'record': 0, 'closed': 0}
        def io(port):
            assert port & 255 == 254
            if cpu.c == 15: return 255 if case == 'open' else 0
            if cpu.c == 26: state['dma'] = cpu.de; return 0
            if cpu.c == 20:
                n = state['record']; state['record'] += 1
                if case == 'header-read' and n == 0 or case == 'payload-read' and n == 25: return 2
                block = data[n*128:(n+1)*128]
                if not block: return 1
                assert len(block) == 128
                cpu.mem[state['dma']:state['dma']+128] = block
                return 0
            if cpu.c == 16: state['closed'] += 1; return 0
            raise AssertionError(('unexpected service/destination activity',cpu.c))
        cpu.port_read = io
        cpu.run(address(listing,'LOADFILE'),limit=2000000)
        assert cpu.a == (0 if case == 'valid' else 2), (case,cpu.a)
        if case == 'valid':
            assert state['record'] == 162 and state['closed'] == 1
            start = address(listing,'IMAGE')
            assert cpu.mem[start:start+20480] == package[128:]
    print('PASS: 10 package magic/version/size/base, length/EOF and readability cases; no destination activity')


if __name__ == '__main__': main()
