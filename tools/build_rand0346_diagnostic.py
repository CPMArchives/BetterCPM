#!/usr/bin/env python3
"""Build a separately named, instrumented copy of pinned RANDTEST case 0346.

This is a diagnostic instrument, never a replacement conformance result.
The input suite is read only. Run R346DBG /0346 on disposable scratch media.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def instrument(source, every_write=False):
    start = source.index('RUN0346:')
    end = source.index('\nRUN0347:', start)
    original = source[start:end]
    assert original.count('CALL    BDOS') == 1
    changed = original.replace('        CALL    RWPREP',
        '        LD      DE,D346PREP\n        CALL    PUTS\n        CALL    RWPREP', 1)
    changed = changed.replace('R346LP:LD      DE,TESTFCB',
        'R346LP:CALL    D346PROGRESS\n        LD      DE,TESTFCB', 1)
    changed = changed.replace('        LD      (NEWOBS2),A\n        CP      2',
        '        LD      (NEWOBS2),A\n        CALL    D346RESULT\n        LD      A,(NEWOBS2)\n        CP      2', 1)
    if every_write:
        changed = changed.replace('        CALL    BDOS\n        OR      A',
            '        CALL    BDOS\n        CALL    D346RETURN\n        OR      A', 1)
    helpers = '''
; Diagnostic only: checkpoint BEFORE each 128-record boundary write.
; Preserve every caller register and flags; console output does not change DMA.
; A missing next checkpoint bounds a stall to the intervening 128 writes.
D346PROGRESS:
        PUSH    AF
        PUSH    BC
        PUSH    DE
        PUSH    HL
        LD      A,(TESTFCB+33)
        AND     7FH
        JP      NZ,D346RESTORE
        LD      DE,D346WRITE
        CALL    PUTS
        CALL    D346RECORD
        LD      DE,D346NL
        CALL    PUTS
D346RESTORE:
        POP     HL
        POP     DE
        POP     BC
        POP     AF
        RET
D346RECORD:
        LD      A,(TESTFCB+35)
        CALL    HEXBYTE
        LD      A,(TESTFCB+34)
        CALL    HEXBYTE
        LD      A,(TESTFCB+33)
        JP      HEXBYTE
D346RESULT:
        LD      DE,D346STOP
        CALL    PUTS
        CALL    D346RECORD
        LD      DE,D346CODE
        CALL    PUTS
        LD      A,(NEWOBS2)
        CALL    HEXBYTE
        LD      DE,D346NL
        JP      PUTS
D346PREP: DB 13,10,'0346 DIAGNOSTIC: preparing temporary file',13,10,'$'
D346WRITE: DB '0346 next random record (hex)=','$'
D346STOP: DB '0346 stopped at random record (hex)=','$'
D346CODE: DB ' BDOS 34 return (hex)=','$'
D346NL: DB 13,10,'$'
'''
    if every_write:
        helpers = helpers.replace(
            '; Diagnostic only: checkpoint BEFORE each 128-record boundary write.',
            '; Diagnostic only: checkpoint BEFORE and AFTER every record write.')
        helpers = helpers.replace(
            '; A missing next checkpoint bounds a stall to the intervening 128 writes.',
            '; Each before/after pair identifies the record and its return status.')
        helpers = helpers.replace('        LD      A,(TESTFCB+33)\n        AND     7FH\n        JP      NZ,D346RESTORE\n', '')
        helpers += '''
; Fine-grained follow-up: preserve BDOS result and all loop state.
D346RETURN:
        PUSH    AF
        PUSH    BC
        PUSH    DE
        PUSH    HL
        LD      (D346RET),A
        LD      DE,D346RM
        CALL    PUTS
        CALL    D346RECORD
        LD      DE,D346CODE
        CALL    PUTS
        LD      A,(D346RET)
        CALL    HEXBYTE
        LD      DE,D346NL
        CALL    PUTS
        JP      D346RESTORE
D346RM: DB '0346 returned record (hex)=','$'
D346RET: DB 0
'''
    # Host assembler needs an explicit origin; ZSM4/LINK normally supplies it.
    return '        ORG 0100H\n' + source[:start] + changed + helpers + source[end:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--assembler', type=Path, default=Path.home()/'bin/z80asm')
    parser.add_argument('--every-write', action='store_true',
                        help='print before and after every write to localize a stall')
    args = parser.parse_args()
    source = args.source.read_bytes()
    args.output.mkdir(parents=True, exist_ok=True)
    staged = args.output/'R346DBG.ASM'
    staged.write_text(instrument(source.decode('ascii'), args.every_write), encoding='ascii')
    binary = args.output/'R346DBG.COM'
    subprocess.run([str(args.assembler), '-fb', '-o'+str(binary.resolve()),
                    '-l'+str((args.output/'R346DBG.lst').resolve()),
                    str(staged.resolve())], check=True)
    assert args.source.read_bytes() == source
    assert 0 < binary.stat().st_size < 53*1024
    report = {'original_source': str(args.source.resolve()),
              'original_sha256': hashlib.sha256(source).hexdigest(),
              'diagnostic_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
              'bytes': binary.stat().st_size, 'command': 'R346DBG /0346',
              'checkpoint_records': 1 if args.every_write else 128,
              'report_every_return': args.every_write,
              'scope': 'Diagnostic only; does not qualify unchanged RANDTEST.'}
    (args.output/'diagnostic-build.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
