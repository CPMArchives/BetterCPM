#!/usr/bin/env python3
"""Execute PATH.COM edits against protected state with a recording BDOS."""
from pathlib import Path
from build_ccp import assemble
from system_layout import LAYOUT
from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'build/compatibility/path-edits'
WORK.mkdir(parents=True, exist_ok=True)
provider = assemble(Path.home() / 'bin/z80asm', '''
        ORG 07000H
        LD A,C
        CP 9
        JR Z,STRING
        CP 2
        RET NZ
        LD A,E
        JR EMIT
STRING: LD A,(DE)
        CP '$'
        RET Z
        PUSH DE
        CALL EMIT
        POP DE
        INC DE
        JR STRING
EMIT:   LD HL,(07200H)
        LD (HL),A
        INC HL
        LD (07200H),HL
        RET
        END
''', WORK / 'bdos.bin', WORK / 'bdos.lst', 0x7000)
image = (ROOT / 'build/utilities/PATH.COM').read_bytes()
address = LAYOUT['EXTENSIONS'] - 16


def run(tail, entries, expected, message, flags=5):
    m = Z80(b'')
    m.mem[0x100:0x100+len(image)] = image
    m.mem[0x7000:0x7000+len(provider)] = provider
    m.mem[0:3] = bytes((0xC3, 0xFF, 0xFF))
    m.setword(1, LAYOUT['BIOS'] + 3)
    # WBOOT vector doubles as the runtime compatibility signature; terminate
    # at that target after PATH has checked it.
    target = LAYOUT['BIOS'] + 3
    m.mem[target:target+3] = bytes((0xC3, 0xFF, 0xFF))
    m.mem[5:8] = bytes((0xC3, 0, 0x70))
    m.setword(0x7200, 0x7300)
    m.mem[LAYOUT['PDS_DESCRIPTOR']:LAYOUT['PDS_DESCRIPTOR']+4] = b'BM\x01' + bytes([flags])
    record = bytes([len(entries)] + [v for pair in entries for v in pair]).ljust(13, b'\x00')
    m.mem[address:address+13] = record
    tail = tail.encode('ascii')
    m.mem[0x80] = len(tail)
    m.mem[0x81:0x81+len(tail)] = tail
    m.run(0x100, limit=100000)
    output = bytes(m.mem[0x7300:m.word(0x7200)]).decode('ascii')
    count = m.mem[address]
    actual = list(zip(m.mem[address+1:address+1+2*count:2],
                      m.mem[address+2:address+1+2*count:2]))
    assert actual == expected, (tail, actual, expected, output)
    assert message in output, (tail, output, message)
    if expected == entries:
        assert bytes(m.mem[address:address+13]) == record, tail


default = [(0, 255), (1, 0)]
base = [(2, 3), (1, 0)]
for alias in ('/A', '/ADD', '/a', '/add'):
    run(f'{alias} C7:', base, base+[(3, 7)], 'PATH: B3: | A0: | C7:')
    run(f'{alias} B03:', base, base, 'Duplicate PATH entry')
    run(f'{alias} B3: C7:', base, base, 'Use PATH')
    run(alias, base, base, 'Use PATH')
for alias in ('/D', '/DEL', '/d', '/del'):
    run(f'{alias} B03:', base, [(1, 0)], 'PATH: A0:')
    run(f'{alias} A0:', base, [(2, 3)], 'PATH: B3:')
    run(f'{alias} C7:', base, base, 'PATH entry not found')
    run(f'{alias} B3: A0:', base, base, 'Use PATH')
    run(alias, base, base, 'Use PATH')
run('$$ $0 A$ P31', base, [(0, 255), (0, 0), (1, 255), (16, 31)], 'PATH: $$: | $0: | A$: | P31:')
run('$$: $00: a$: p31:', base, [(0, 255), (0, 0), (1, 255), (16, 31)], 'PATH: $$: | $0: | A$: | P31:')
run('/ADD $0', base, base+[(0, 0)], 'PATH: B3: | A0: | $0:')
run('/DEL $00:', [(0, 0), (1, 255)], [(1, 255)], 'PATH: A$:')
run('/ADD $00', [(0, 0)], [(0, 0)], 'Duplicate PATH entry')
for tail in ('.', '$', '$:', '$32', 'A$$', '$0X'):
    run(tail, base, base, 'Invalid PATH')
run('/ADD B3:', [], default+[(2, 3)], 'PATH: $$: | A0: | B3:')
run('/DEL $$', [], [(1, 0)], 'PATH: A0:')
run('/DEL A0:', [], [(0, 255)], 'PATH: $$:')
run('/DEL B3:', [(2, 3)], [(2, 3)], 'Cannot delete the last')
run('/ADD $$', base, base+[(0, 255)], 'PATH: B3: | A0: | $$:')
run('/DEL B3:', [(1, 0), (2, 3), (3, 7)], [(1, 0), (3, 7)], 'PATH: A0: | C7:')
full = [(n, 0) for n in range(1, 7)]
run('/ADD G0:', full, full, 'up to six')
run('/DEL C0:', full, [x for x in full if x != (3, 0)], 'PATH: A0: | B0: | D0: | E0: | F0:')
for tail in ('/AD B3:', '/ADDX B3:', '/DE B3:', '/DEFAULT B3:', '/ADD C32:', '/DEL B3:X'):
    run(tail, base, base, 'PATH')
run('C7: A0:', base, [(3, 7), (1, 0)], 'PATH: C7: | A0:')
run('/DEFAULT', base, [], 'PATH: $$: | A0:')
run('/H', base, base, '/A /ADD')
run('/VER', base, base, 'Numeric Command Search Path')
run('/ADD $0', base, base, 'PATH requires a matching', flags=3)
print('PASS PATH edit aliases, ordering, defaults, rejection atomicity, capacity, help and version')
