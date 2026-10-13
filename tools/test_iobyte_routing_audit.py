#!/usr/bin/env python3
"""Execute the compact Model 4 routing prototype with physical endpoints stubbed."""
from pathlib import Path
from test_monitor_profiles import load

ROOT = Path(__file__).resolve().parents[1]

def check(profile, provider=False):
    cpu, labels = load(ROOT / 'build/audit/iobyte/trs80m4' / profile)
    if profile == 'combined':
        cpu.run(labels['MONBASE'])
    if provider:
        # Multiplex callback: status=ready, input=C1h, output tag=66h.
        cpu.mem[0x9000:0x900E] = bytes([0xFE, 1, 0x28, 7, 0xFE, 2, 0x28, 6, 0x3E, 0x66, 0xC9, 0x3E, 1, 0xC9])
        cpu.mem[0x900E:0x9011] = bytes([0x3E, 0xC1, 0xC9])
        cpu.setword(labels['MP_MON'], 0x9000)
    output_tag = 0x66 if provider else 0x77
    for name, value in [('PL_CONST', 1), ('PL_CONIN', 0xC1), ('PL_CONOT', 0x77)]:
        # Model 4 uses equates for its physical interface; resolve those aliases
        # from the vector or actual driver label when absent from the listing map.
        aliases = {'PL_CONST': 'M4_STAT', 'PL_CONIN': 'M4_IN', 'PL_CONOT': 'M4_SCROLL_OUT'}
        address = labels.get(name, labels.get(aliases[name]))
        assert address is not None, name
        cpu.mem[address:address+3] = bytes([0x3E, value, 0xC9])
    count = 0
    for byte in range(256):
        cpu.mem[3] = byte
        con, lst = byte & 3, byte >> 6
        cases = [('BIOCONST', 0xFF if con == 1 else 0),
                 ('BIOCONIN', 0x41 if con == 1 else 0x1A),
                 ('BIOREADR', 0x1A),
                 ('BIOLSTST', 0xFF if lst == 1 else 0)]
        for entry, expected in cases:
            cpu.run(labels[entry])
            assert cpu.a == expected, (byte, entry, cpu.a, expected)
            assert cpu.mem[3] == byte
            count += 1
        # Observe calls to the output endpoint using its tag. Every other route
        # must return without emitting output. BAT delegates to logical LST.
        for entry, emitted in [('BIOCONOT', con == 1 or (con == 2 and lst == 1)),
                               ('BIOLIST', lst == 1), ('BIOPUNCH', False)]:
            cpu.c = ord('X')
            cpu.a = 0
            cpu.run(labels[entry])
            assert (cpu.a == output_tag) == emitted, (byte, entry, cpu.a, emitted)
            assert cpu.c == ord('X')
            assert cpu.mem[3] == byte
            count += 1
    if profile == 'combined':
        for selector, expected in [(0, 0x77), (1, 1), (2, 0xC1)]:
            cpu.a = selector
            cpu.run(labels['MONRAW'])
            assert cpu.a == expected, (selector, cpu.a, expected)
    print(f'PASS {count} {profile} routing cases; provider={provider}; physical endpoints stubbed')


if __name__ == '__main__':
    check('compact')
    check('combined')
    check('combined', provider=True)
