"""Compose SEARCH development modules with the existing shared selector code."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def selector_source():
    common = ROOT/'src/utilities/common'
    text = 'DU_MAP: DS 64\nDU_WORK: DS 12\n'
    for name in ('duselect.inc', 'filespec.inc', 'operandqual.inc'):
        text += (common/name).read_text()+'\n'
    attr = (common/'attrselect.inc').read_text()
    text += attr[:attr.index('; Destination modification list:')]
    text += (common/'rcpselect.inc').read_text()+'\n'
    # Reuse precisely the same FCB builder as TYPE/REN; no new 8.3 parser.
    rcp = (ROOT/'src/cpx/rcp.mac').read_text()
    start = rcp.index('BC_PFCB:')
    text += rcp[start:rcp.index('; ================================================================================', start)]
    text += '\nBC_ALL: DB \'*.*\'\nBC_INPTR: DW 0\nBC_INLEN: DB 0\nBC_FCBPTR: DW 0\n'
    return text


def development_source():
    directory = ROOT/'src/utilities/search'
    return ''.join((directory/name).read_text()+'\n'
                   for name in ('parser.inc', 'matcher.inc', 'state.inc', 'scan.inc')) + selector_source()


def qualification_driver():
    """Small native-BDOS integration probe, deliberately not SEARCH.COM."""
    tail = '"4142" B0:FIX.DAT'
    expected = b''.join(n.to_bytes(8, 'little') for n in (1, 1, 3, 1, 4))
    return ('        JP QENTRY\n' + development_source() + f'''
RHOOK: RET
QENTRY:
        LD (QOLDSP),SP
        LD SP,QSTACK
        LD HL,QTAIL
        LD B,{len(tail)}
        LD D,1
        LD E,0
        CALL PCOMMAND
        JR C,QBAD
        OR A
        JR NZ,QBAD
        CALL RRUN
        JR C,QBAD
        LD HL,RCOUNTS
        LD DE,QEXPECT
        LD B,40
QCHECK:
        LD A,(DE)
        CP (HL)
        JR NZ,QBAD
        INC HL
        INC DE
        DJNZ QCHECK
        LD HL,(STSTART)
        LD DE,0FFFFH
        OR A
        SBC HL,DE
        JR NZ,QBAD
        LD HL,(STSTART+2)
        LD A,H
        OR L
        JR NZ,QBAD
        LD A,(STLINE)
        CP 2
        JR NZ,QBAD
        LD C,25
        CALL RBDOS
        CP 1
        JR NZ,QBAD
        LD C,32
        LD E,255
        CALL RBDOS
        OR A
        JR NZ,QBAD
        LD DE,QPASS
        JR QPRINT
QBAD:
        LD HL,RCOUNTS
        LD B,40
QDEBUG:
        LD A,(HL)
        CALL QHEX
        INC HL
        DJNZ QDEBUG
        LD A,(RERROR)
        CALL QHEX
        LD DE,QFAIL
QPRINT:
        LD C,9
        CALL RBDOS
        LD SP,(QOLDSP)
        RET
QHEX:
        PUSH AF
        RRCA
        RRCA
        RRCA
        RRCA
        CALL QNIB
        POP AF
QNIB:
        AND 15
        ADD A,'0'
        CP '9'+1
        JR C,QDIGIT
        ADD A,7
QDIGIT:
        LD E,A
        LD C,2
        JP RBDOS
QTAIL: DB '{tail}'
QEXPECT: DB {','.join(str(b) for b in expected)}
QPASS: DB 13,10,'SEARCH BDOS PASS',13,10,'$'
QFAIL: DB 13,10,'SEARCH BDOS FAIL',13,10,'$'
QOLDSP: DW 0
        DS 512
QSTACK:
        END
''')
