#!/usr/bin/env python3
"""Measure an isolated IOBYTE router; never publish production system images.

The table prototype models unavailable devices with EOF/not-ready/no-output.
It is a size experiment, not authorization to enable PIP physical aliases.
"""
from pathlib import Path
import argparse
import json
import re
from audit_monitor_memory import assemble
from system_layout import LAYOUT, expand_layout

ROOT = Path(__file__).resolve().parents[1]


def router(source: str, host: bool) -> str:
    source = source.replace('JP      PL_CONOT', 'JP      BIOCONOT', 1)
    start = source.index('BIOCONST:')
    end = source.index('; ================================================================================', start)
    bodies = []
    # Rotate the selected IOBYTE pair to bits 0..1, then dispatch through a table.
    for label, shift, table in [('BIOCONST', 0, 'IO_CS'), ('BIOCONIN', 0, 'IO_CI'),
                                ('BIOCONOT', 0, 'IO_CO'), ('BIOREADR', 2, 'IO_RI'),
                                ('BIOPUNCH', 4, 'IO_PO'), ('BIOLIST', 6, 'IO_LO')]:
        bodies.append(f'{label}:\n        LD A,(0003H)\n' + '        RRCA\n' * shift
                      + f'        LD HL,{table}\n        JP IO_JUMP\n')
    bodies.append('''IO_JUMP:
        AND 3
        ADD A,A
        LD E,A
        LD D,0
        ADD HL,DE
        LD E,(HL)
        INC HL
        LD D,(HL)
        EX DE,HL
        JP (HL)
IO_NONE:
        XOR A
        RET
IO_EOF:
        LD A,01AH
        RET
IO_READY:
        LD A,0FFH
        RET
IO_STAT:
        CALL PL_CONST
        OR A
        RET Z
        JP IO_READY
IO_INPUT:
        CALL PL_CONIN
        AND 07FH
        RET
''')
    tty_s, tty_i, tty_o = ('IO_STAT', 'IO_INPUT', 'PL_CONOT') if host else ('IO_NONE', 'IO_EOF', 'IO_NONE')
    reader, punch, printer, ready = ('IO_AUXIN', 'IO_AUXOT', 'IO_PRINT', 'IO_LSTAT') if host else ('IO_EOF', 'IO_NONE', 'IO_NONE', 'IO_NONE')
    # BAT input uses the logical reader, output the logical list; no recursion
    # into CON. No reader-ready API exists, so its status policy remains open.
    tables = {'IO_CS': [tty_s, 'IO_STAT', 'IO_NONE', 'IO_NONE'],
              'IO_CI': [tty_i, 'IO_INPUT', 'BIOREADR', 'IO_EOF'],
              'IO_CO': [tty_o, 'PL_CONOT', 'BIOLIST', 'IO_NONE'],
              'IO_RI': [tty_i, reader, 'IO_EOF', 'IO_EOF'],
              'IO_PO': [tty_o, punch, 'IO_NONE', 'IO_NONE'],
              'IO_LO': [tty_o, 'PL_CONOT', printer, 'IO_NONE'],
              'IO_LS': [ 'IO_READY' if host else 'IO_NONE', 'IO_READY', ready, 'IO_NONE']}
    bodies.extend(f'{name}: DW ' + ','.join(targets) + '\n' for name, targets in tables.items())
    if host:
        bodies.append('''IO_AUXIN:
        IN A,(5)
        RET
IO_AUXOT:
        LD A,C
        OUT (5),A
        RET
IO_PRINT:
        LD A,C
        OUT (3),A
        RET
IO_LSTAT:
        IN A,(2)
        RET
''')
    source = source[:start] + '\n'.join(bodies) + source[end:]
    return re.sub(r'BIOLSTST:[^\n]*\n\s*XOR\s+A\n\s*RET', '''BIOLSTST:
        LD A,(0003H)
        RRCA
        RRCA
        RRCA
        RRCA
        RRCA
        RRCA
        LD HL,IO_LS
        JP IO_JUMP''', source, count=1)


def compact_model4(source: str) -> str:
    """Model 4 has CRT only: omit dispatch tables for unavailable endpoints."""
    if "IOBYTE_ROUTING_V1" in source:
        return source
    source = source.replace('JP      PL_CONOT', 'JP      BIOCONOT', 1)
    start = source.index('BIOCONST:')
    end = source.index('; ================================================================================', start)
    source = source[:start] + """BIOCONST:
        CALL IO_CON
        JR Z,IO_STAT
        XOR A
        RET
IO_STAT:
        CALL PL_CONST
        OR A
        RET Z
IO_READY:
        LD A,0FFH
        RET
BIOCONIN:
        CALL IO_CON
        JR Z,IO_INPUT
        JP BIOREADR
IO_INPUT:
        CALL PL_CONIN
        AND 07FH
        RET
BIOCONOT:
        CALL IO_CON
        JP Z,PL_CONOT
        CP 2
        RET NZ
        JP BIOLIST
IO_CON:
        LD A,(0003H)
        AND 3
        CP 1
        RET
BIOLIST:
        LD A,(0003H)
        AND 0C0H
        CP 040H
        RET NZ
        JP PL_CONOT
BIOPUNCH:
        RET
BIOREADR:
        LD A,01AH
        RET
""" + source[end:]
    return re.sub(r'BIOLSTST:[^\n]*\n\s*XOR\s+A\n\s*RET', """BIOLSTST:
        LD A,(0003H)
        AND 0C0H
        CP 040H
        JP Z,IO_READY
        XOR A
        RET""", source, count=1)


def monitor_hooks(source: str) -> str:
    """Compose the existing multiplex monitor prototype with CRT routing.

    Hook only the CRT paths. Raw backend access cannot re-enter IOBYTE or
    monitor dispatch. Provider publication/lifecycle remains outside this audit.
    """
    replacements = [('JP Z,PL_CONOT', 'JP Z,MH_OUT'),
                    ('JP PL_CONOT', 'JP MH_OUT'),
                    ('CALL PL_CONST', 'LD A,1\n        CALL MC_CALL'),
                    ('CALL PL_CONIN', 'LD A,2\n        CALL MC_CALL'),
                    ('JP      PL_CURSOR', 'JP      MH_CUR')]
    for old, new in replacements:
        assert source.count(old) == 1, old
        source = source.replace(old, new, 1)
    source = source.replace('BIOBOOT:',
        'MONCALL: JP MC_CALL\nMONRAW: JP MC_RAW\nMONBASE: JP MC_BASE\n\nBIOBOOT:', 1)
    source = source.replace('        CALL    PL_INIT',
                            '        CALL MC_BASE\n        CALL    PL_INIT', 1)
    return source.replace('        .DEPHASE', """
MH_OUT:
        XOR A
        JP MC_CALL
MH_CUR:
        LD A,3
MC_CALL:
        LD HL,(MP_MON)
        JP (HL)
MC_RAW:
        OR A
        JP Z,PL_CONOT
        DEC A
        JP Z,PL_CONST
        DEC A
        JP Z,PL_CONIN
        DEC A
        JP Z,PL_CURSOR
        DEC A
        JR Z,MC_CLEAR
        DEC A
        RET Z
        LD A,0FFH
        RET
MC_CLEAR:
        LD C,01CH
        JP PL_CONOT
MC_BASE:
        LD HL,MC_RAW
        LD (MP_MON),HL
        RET
MP_MON: DW 0
        .DEPHASE""", 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler', type=Path, default=Path('/Users/nathanael/bin/z80asm'))
    parser.add_argument('--output', type=Path, default=ROOT / 'build/audit/iobyte')
    args = parser.parse_args()
    original = (ROOT / 'src/bios/bios.mac').read_text()
    rows = []
    for host in (False, True):
        name = 'z80pack' if host else 'trs80m4'
        source = original
        if host:
            a, b = source.index('BIOREAD:'), source.index('; LISTST', source.index('BIOREAD:'))
            source = source[:a] + (ROOT / 'src/platform/z80pack/recordio.inc').read_text() + source[b:]
            source = source.replace('        INCLUDE biosplat.inc', (ROOT / 'src/platform/z80pack/biosplat.inc').read_text())
        sizes = []
        for routed in ((False, True) if host else (False, True, 'compact', 'combined')):
            stage = args.output / name / (routed if isinstance(routed, str) else 'router' if routed else 'baseline')
            stage.mkdir(parents=True, exist_ok=True)
            if not host:
                for file in ('m4cons.inc', 'm4scroll.inc', 'reload.inc'):
                    (stage / file).write_text(expand_layout((ROOT / 'src/platform/trs80m4' / file).read_text()))
                (stage / 'biosplat.inc').write_text((ROOT / 'src/bios/biosplat.inc').read_text())
            sizes.append(len(assemble(monitor_hooks(compact_model4(source)) if routed == 'combined' else compact_model4(source) if routed == 'compact' else router(source, host) if routed else source, 'bios', LAYOUT['BIOS'], stage, args.assembler)))
        rows.append(dict(platform=name, baseline=sizes[0], prototype=sizes[1], growth=sizes[1]-sizes[0], allocation=LAYOUT["FILE"]-LAYOUT["BIOS"], compact=sizes[2] if not host else None, combined=sizes[3] if not host else None))
    (args.output / 'sizes.json').write_text(json.dumps(rows, indent=2)+'\n')
    for row in rows:
        print(f"{row['platform']}: {row['baseline']} -> {row['prototype']} bytes (+{row['growth']}); allocation {row['allocation']}; compact {row['compact']}; combined {row['combined']}")


if __name__ == '__main__':
    main()
