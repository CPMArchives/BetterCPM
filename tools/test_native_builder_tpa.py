#!/usr/bin/env python3
"""Execute native builder startup at active TPA boundaries (BCPM-AUD-002).

Uses the emitted COMs, an indirect page-zero gateway and protected-memory
canaries. No disk is opened: accepted cases stop at their first file call.
Run tools/build_disk_utilities.py first.
"""
from pathlib import Path
from test_bios import Z80, require

ROOT = Path(__file__).resolve().parents[1]


class FileAccess(Exception):
    pass


def run(name, ceiling, tail=''):
    image = (ROOT / 'build/utilities' / (name + '.COM')).read_bytes()
    require(0x100 + len(image) < 0x2F00, 'test caller stack overlaps COM')
    cpu = Z80(b'')
    cpu.mem[:] = b'\xA5' * 65536
    cpu.mem[0:3] = b'\xC3\xFF\xFF'  # existing query contract warm-boots
    cpu.mem[0x100:0x100 + len(image)] = image
    cpu.mem[5] = 0xC3
    cpu.setword(6, ceiling)
    cpu.mem[ceiling:ceiling + 3] = b'\xC3\x00\xF8'
    cpu.mem[0xF800:0xF803] = b'\xD3\x00\xC9'
    cpu.mem[0x80] = len(tail)
    cpu.mem[0x81:0x81 + len(tail)] = tail.encode('ascii')
    cpu.mem[0x81 + len(tail)] = 13
    cpu.sp = 0x3000
    output, calls = [], []

    def bdos(port, value):
        calls.append(cpu.c)
        if cpu.c != 9:
            raise FileAccess()
        end = cpu.mem.index(ord('$'), cpu.de)
        output.append(bytes(cpu.mem[cpu.de:end]).decode('ascii'))

    cpu.port_write = bdos
    protected = bytes(cpu.mem[ceiling:0xF800])
    workspace = bytes(cpu.mem[0x3E00:0xF800])
    file_access = False
    try:
        cpu.run(0x100, limit=200000)
    except FileAccess:
        file_access = True
    require(bytes(cpu.mem[ceiling:0xF800]) == protected,
            f'{name} damaged protected memory at {ceiling:04X}')
    text = ''.join(output)
    if tail or 'insufficient active TPA' in text:
        require(not file_access and all(c == 9 for c in calls),
                f'{name} accessed files on an early exit')
        if not tail:
            require(cpu.sp == 0x3000, f'{name} did not restore caller stack')
        require(bytes(cpu.mem[0x3E00:0xF800]) == workspace,
                f'{name} touched private stack/workspace on an early exit')
    return file_access, text


def main():
    count = 0
    for name, minimum in (('SYSBUILD', 0x9000), ('RLMBUILD', 0x8600)):
        # Include the audited gateway values and both sides of the exact
        # exclusive workspace end. Equality supplies all required bytes.
        for ceiling in (0x7001, 0x7801, 0x8001, minimum - 1, minimum, minimum + 1, 0xD501):
            access, text = run(name, ceiling)
            require(access == (ceiling >= minimum),
                    f'{name}: incorrect admission at {ceiling:04X}: {text!r}')
            if not access:
                require('insufficient active TPA' in text,
                        f'{name}: missing low-memory diagnostic')
            count += 1
        for tail in ('/VER', '/HELP', '/H', '/ver /help'):
            access, text = run(name, 0x7001, tail)
            require(not access and 'insufficient active TPA' not in text and text,
                    f'{name}: low-memory query failed: {tail}')
            count += 1
    print(f'PASS: {count} native builder TPA/query cases; protected memory intact')


if __name__ == '__main__':
    main()
