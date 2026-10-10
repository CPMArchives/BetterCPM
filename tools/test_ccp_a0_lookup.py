#!/usr/bin/env python3
"""Execute the CCP fixed A0 fallback against a recording BDOS provider."""
from pathlib import Path
from build_ccp import assemble
from test_ccp import cpu, symbol, call, install_bdos
from system_layout import LAYOUT

work = Path(__file__).resolve().parents[1] / 'build/compatibility/a0-lookup'
work.mkdir(parents=True, exist_ok=True)
provider = assemble(Path('/Users/nathanael/bin/z80asm'), '''
        ORG %d
        LD A,C
        CP 32
        JR Z,USER
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
OPEN:   LD HL,07501H
        INC (HL)
        LD A,(HL)
        CP 1
        JR NZ,SECOND
        LD A,(DE)
        LD (07502H),A
        LD A,(07500H)
        LD (07503H),A
        LD A,(07506H)
        SCF                            ; carry is not a public Open result
        RET
SECOND: LD A,(DE)
        LD (07504H),A
        LD A,(07500H)
        LD (07505H),A
        LD A,(07507H)
        RET
        END
''' % LAYOUT['BDOS'], work / 'provider.bin', work / 'provider.lst', LAYOUT['BDOS'])

for command, first, second, count, drive, user in (
    (b'HELLO', 0, 0, 1, 0, 7),
    (b'HELLO', 255, 0, 2, 0, 7),
    (b'HELLO', 255, 255, 2, 0, 7),
    (b':DIR', 255, 0, 2, 0, 7),
    (b'.DIR', 255, 0, 2, 0, 7),
    (b'B:HELLO', 255, 0, 1, 2, 7),
    (b'B3:HELLO', 255, 0, 1, 2, 3),
    (b'5:HELLO', 255, 0, 1, 0, 5),
    (b':B3:HELLO', 255, 0, 1, 2, 3),
):
    m = cpu()
    install_bdos(m, provider)
    m.mem[0x7500] = 7
    m.mem[0x7506:0x7508] = bytes((first, second))
    m.mem[symbol('CCP_COUNT')] = len(command)
    start = symbol('CCP_DATA')
    m.mem[start:start + len(command)] = command
    call(m, symbol('CCP_LQUAL'))
    call(m, symbol('CCP_LOPEN'))
    assert m.mem[0x7501] == count, command
    assert tuple(m.mem[0x7502:0x7504]) == (drive, user), command
    if count == 2:
        assert tuple(m.mem[0x7504:0x7506]) == (1, 0), command
    assert bool(m.z) == (first == 255 and (count == 1 or second == 255)), command
    call(m, symbol('CCP_LURST'))
    assert m.mem[0x7500] == 7, command
print('Nine current-DU/A0 lookup, prefix, exact-qualifier and restoration cases passed')
