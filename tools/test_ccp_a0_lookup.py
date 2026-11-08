#!/usr/bin/env python3
"""Record actual CCP Open calls, including first match and resolved duplicates."""
from pathlib import Path
from build_ccp import assemble
from test_ccp import cpu, symbol, call, install_bdos
from system_layout import LAYOUT

work = Path(__file__).resolve().parents[1] / 'build/compatibility/a0-lookup'
work.mkdir(parents=True, exist_ok=True)
provider = assemble(Path.home() / 'bin/z80asm', '''
        ORG %d
        LD A,C
        CP 32
        JR Z,USER
        CP 25
        JR Z,DRIVE
        CP 15
        JR Z,OPEN
        XOR A
        RET
USER:   LD A,E
        CP 0FFH
        JR Z,QUERY
        LD (07500H),A
        RET
QUERY:  LD A,(07500H)
        RET
DRIVE:  LD A,(07501H)
        RET
OPEN:   LD HL,(07504H)
        LD A,(DE)
        LD (HL),A
        INC HL
        LD A,(07500H)
        LD (HL),A
        INC HL
        LD (07504H),HL
        LD HL,07502H
        INC (HL)
        LD A,(07503H)
        CP (HL)
        LD A,0FFH
        RET NZ
        XOR A
        SCF                            ; carry is unrelated to public Open success
        RET
        END
''' % LAYOUT['BDOS'], work / 'provider.bin', work / 'provider.lst', LAYOUT['BDOS'])

# Drive zero in the log denotes the current drive in an FCB, A=1, B=2, etc.
current = (0, 7)
default = [current, (1, 0)]
custom = [(2, 3), (0, 255), (3, 7), (1, 0), (2, 1), (4, 31)]
resolved = [current, (2, 3), (1, 0), (2, 1), (4, 31)]

for command, entries, hit, expected in [
    ('HELLO', [], 1, default[:1]), ('HELLO', [], 2, default),
    ('HELLO', [], 0, default), (':DIR', [], 2, default), ('.DIR', [], 2, default),
    ('B:HELLO', custom, 0, [(2, 7)]), ('B3:HELLO', custom, 0, [(2, 3)]),
    ('5:HELLO', custom, 0, [(0, 5)]), (':B3:HELLO', custom, 0, [(2, 3)]),
    ('FOO', custom, 1, resolved[:1]), ('FOO', custom, 5, resolved),
    ('FOO', custom, 0, resolved), ('FOO', [(3, 7), (0, 255)], 0, [current]),
    ('FOO', [(0, 255), (3, 7)], 0, [current]),
    ('FOO', [(2, 3), (1, 0)], 0, [current, (2, 3), (1, 0)]),
    ('PATH', [(4, 0)], 1, [current]),
    ('FOO', [(0, 0)], 0, [current, (3, 0)]),
    ('FOO', [(1, 255)], 0, [current, (1, 7)]),
    ('FOO', [(0, 255)], 0, [current]),
    ('FOO', [(0, 7), (3, 255)], 0, [current]),
    ('FOO', [(0, 0), (1, 255)], 2, [current, (3, 0)]),
    ('FOO', [(4, 0)], 0, [current, (4, 0)]),
    (':FOO', [(4, 0)], 1, [current]),
    ('.FOO', [(4, 0)], 0, [current, (4, 0)]),
    ('FOO', [(2, 3), (1, 0)], 2, [current, (2, 3)]),
]:
    m = cpu()
    install_bdos(m, provider)
    m.mem[0x7500:0x7504] = bytes((7, 2, 0, hit))  # caller C7
    m.setword(0x7504, 0x7510)
    path = LAYOUT['EXTENSIONS'] - 16
    record = bytes([len(entries)] + [v for pair in entries for v in pair])
    m.mem[path:path + len(record)] = record
    m.mem[symbol('CCP_COUNT')] = len(command)
    start = symbol('CCP_DATA')
    m.mem[start:start + len(command)] = command.encode()
    call(m, symbol('CCP_LQUAL'))
    call(m, symbol('CCP_LOPEN'))
    assert bool(m.z) == (hit == 0), command
    attempts = list(zip(m.mem[0x7510:m.word(0x7504):2], m.mem[0x7511:m.word(0x7504):2]))
    assert attempts == expected, (command, attempts, expected)
    call(m, symbol('CCP_LURST'))
    assert tuple(m.mem[0x7500:0x7502]) == (7, 2), command
    assert bytes(m.mem[path:path+len(record)]) == record
print('PASS default and numeric PATH, exact qualifiers, Open order/count, DU restoration')
