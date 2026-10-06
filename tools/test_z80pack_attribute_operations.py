#!/usr/bin/env python3
"""Qualify rename and file read-only enforcement on disposable native media."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from build_ccp import assemble
from test_z80pack_attributes import directory
from test_z80pack_sysgen_install import session

ROOT = Path(__file__).resolve().parents[1]
PROBE = """        ASEG
        ORG 100H
        LD SP,4000H
        LD A,(80H)
        LD L,A
        LD H,0
        LD DE,80H
        ADD HL,DE
        LD A,(HL)
        LD (OP),A
        LD DE,FCB
        LD C,15
        CALL 5
        CP 0FFH
        JP Z,BAD
        LD A,(FCB+9)
        AND 80H
        JR Z,WRITABLE
        LD A,0FFH
WRITABLE:
        LD (EXPECTED),A
        LD A,(OP)
        CP 'N'
        JR Z,RENAME
        CP 'D'
        JR Z,DELETE
        LD DE,DMA
        LD C,26
        CALL 5
        LD A,(OP)
        LD C,21
        CP 'W'
        JR Z,WRITE
        LD C,34
        CP 'R'
        JR Z,WRITE
        LD C,40
WRITE:  LD DE,FCB
        CALL 5
        JP BAD
RENAME: LD HL,NEWNAME
        LD DE,FCB+16
        LD BC,12
        LDIR
        LD C,23
        JR MUTATE
DELETE: LD C,19
MUTATE: LD DE,FCB
        CALL 5
        LD HL,EXPECTED
        CP (HL)
        JR NZ,BAD
        LD DE,OK
        JR PRINT
BAD:    LD DE,FAIL
PRINT:  LD C,9
        CALL 5
        JP 0
OP:     DB 0
EXPECTED: DB 0
OK:     DB 'ATTRIBUTE OP PASS',13,10,'$'
FAIL:   DB 'ATTRIBUTE OP FAIL',13,10,'$'
NEWNAME: DB 2,'NEW     BIN'
FCB:    DB 2,'ATTR    DAT'
        REPT 24
        DB 0
        ENDM
DMA:    REPT 128
        DB 0A5H
        ENDM
        END
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    (report / 'attrop.mac').write_text(PROBE)
    binary = report / 'ATROP.COM'
    assemble(Path.home() / 'bin/z80asm', PROBE, binary, report / 'attrop.lst', 0x100)
    simulator = Path.home() / 'projects/git/z80pack/cpmsim/cpmsim'
    observations = []
    cases = [(mask, 'N') for mask in range(8)] + [(mask, op) for mask in (1, 7) for op in 'DWRZ']
    for mask, op in cases:
        work = report / f'mask-{mask}-{op}'
        shutil.copytree(args.runtime, work)
        a, b = (work / 'disks' / f'drive{d}.dsk' for d in 'ab')
        def cpm(tool, *arguments):
            subprocess.run([tool, '-T', 'raw', '-f', 'bettercpm-default',
                            *map(str, arguments)], cwd=work, check=True)
        cpm('cpmrm', a, '0:WARM.COM')
        cpm('cpmcp', a, binary, '0:ATROP.COM')
        out = session(simulator, work / 'disks',
                      [(f'ATTRPROB {mask}\r'.encode(), b'A0>_ ', 15)], work / 'set.txt')
        assert b'ATTRIBUTE PASS' in out
        before = b.read_bytes()
        (work / 'before.dsk').write_bytes(before)
        raw = directory(b, work / 'diskdefs')
        old = next(raw[i:i+32] for i in range(0,len(raw),32)
                   if raw[i] == 0 and bytes(x & 127 for x in raw[i+1:i+12]) == b'ATTR    DAT')
        out = session(simulator, work / 'disks',
                      [(f'ATROP {op}\r'.encode(), b'A0>_ ', 15)], work / 'operation.txt')
        assert b'ATTRIBUTE OP FAIL' not in out, out
        if op in 'WRZ':
            assert b'File R/O' in out and b'ATTRIBUTE OP PASS' not in out, out
        else:
            assert b'ATTRIBUTE OP PASS' in out, out
        after = b.read_bytes()
        if mask & 1:
            assert after == before, 'rejected mutation changed media'
            resulting = old
        else:
            raw = directory(b, work / 'diskdefs')
            resulting = next(raw[i:i+32] for i in range(0,len(raw),32)
                             if raw[i] == 0 and bytes(x & 127 for x in raw[i+1:i+12]) == b'NEW     BIN')
            expected = bytes(ord(c) | (128 if mask & (1 << n) else 0)
                             for n,c in enumerate('BIN'))
            assert resulting[9:12] == expected
            assert resulting[12:] == old[12:], 'rename changed extent/allocation metadata'
            extracted = work / 'renamed.dat'
            cpm('cpmcp', b, '0:NEW.BIN', extracted)
            assert extracted.read_bytes() == bytes(range(128))
        observations.append({'mask': mask, 'operation': op, 'entry': resulting.hex(),
                             'before_sha256': hashlib.sha256(before).hexdigest(),
                             'after_sha256': hashlib.sha256(after).hexdigest()})
    (report / 'evidence.json').write_text(json.dumps({'result': 'PASS',
        'probe_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
        'simulator_sha256': hashlib.sha256(simulator.read_bytes()).hexdigest(),
        'cases': observations}, indent=2) + '\n')
    print('PASS: eight rename attribute cases; read-only delete, sequential/random/zero-fill writes reject without media changes')


if __name__ == '__main__':
    main()
