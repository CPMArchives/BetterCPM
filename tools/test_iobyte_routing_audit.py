#!/usr/bin/env python3
"""Execute the compact Model 4 routing prototype with physical endpoints stubbed."""
from pathlib import Path
from test_monitor_profiles import load

ROOT = Path(__file__).resolve().parents[1]
cpu, labels = load(ROOT / 'build/audit/iobyte/trs80m4/compact')
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
        assert (cpu.a == 0x77) == emitted, (byte, entry, cpu.a, emitted)
        assert cpu.c == ord('X')
        assert cpu.mem[3] == byte
        count += 1
print(f'PASS {count} compact Model 4 routing cases; physical endpoints stubbed')
