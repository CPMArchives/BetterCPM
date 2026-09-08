#!/usr/bin/env python3
"""Exercise unclosed random writes and zero fill on a private emulator disk."""
from pathlib import Path
import subprocess
import tempfile
from build_ccp import assemble
from add_cpm_file_to_dmk import extract_raw, add_file, build
from run_trs80_command import ROOT


def main():
    code = ['        ORG 0100H', '        LD SP,09000H']
    step = 0

    def invoke(function):
        nonlocal step
        step += 1
        code.extend([f'        LD A,{step}', '        LD (STEP),A',
                     '        LD DE,FCB', f'        LD C,{function}',
                     '        CALL 0005H'])
        code.extend(['        CP 0FFH' if function in (15, 16, 22) else '        OR A',
                     '        JP Z,FAIL' if function in (15, 16, 22) else '        JP NZ,FAIL'])

    def fill(value):
        code.extend([f'        LD A,{value}', '        LD HL,DMA', '        LD B,128',
                     '        CALL FILL'])

    def position(record):
        code.extend([f'        LD HL,{record}', '        LD (FCB+33),HL',
                     '        XOR A', '        LD (FCB+35),A'])

    def verify(record, value):
        position(record)
        invoke(33)
        code.extend([f'        LD A,{value}', '        LD HL,DMA', '        LD B,128',
                     '        CALL CHECK'])

    code.extend(['        LD DE,DMA', '        LD C,26', '        CALL 0005H'])
    invoke(22)
    fill(165)
    position(2)
    invoke(40)
    for record, value in ((0, 0), (1, 0), (2, 165)):
        verify(record, value)
    # Change extent without Close; both extents must retain their own data.
    for record, value in ((128, 90), (129, 60)):
        fill(value)
        position(record)
        invoke(34)
    for record, value in ((2, 165), (128, 90), (129, 60)):
        verify(record, value)
    invoke(16)
    code.extend(['        LD HL,INITIAL', '        LD DE,FCB', '        LD BC,36', '        LDIR'])
    invoke(15)
    for record, value in ((2, 165), (128, 90), (129, 60)):
        verify(record, value)
    invoke(35)
    code.extend(['        LD HL,(FCB+33)', '        LD DE,130', '        OR A',
                 '        SBC HL,DE', '        JP NZ,FAIL'])
    invoke(19)
    code.extend(['        LD DE,OK', '        JR PRINT',
                 'FAIL:   PUSH AF', '        LD A,(STEP)', '        ADD A,64', '        LD E,A', '        LD C,2', '        CALL 0005H', '        POP AF', '        ADD A,48', '        LD E,A', '        LD C,2', '        CALL 0005H', '        LD DE,BAD', 'PRINT:  LD C,9', '        CALL 0005H', '        JP 0000H',
                 'FILL:   LD (HL),A', '        INC HL', '        DJNZ FILL', '        RET',
                 'CHECK:  CP (HL)', '        JP NZ,FAIL', '        INC HL', '        DJNZ CHECK', '        RET',
                 "OK:     DB 'Random I/O persistence and zero-fill passed',13,10,'$'",
                 "BAD:    DB 'Random I/O regression FAILED',13,10,'$'",
                 "INITIAL: DB 0,'RANREG  ','TMP'", '        DB '+','.join(['0']*24),
                 "FCB:    DB 0,'RANREG  ','TMP'", '        DB '+','.join(['0']*24),
                 'STEP:   DB 0', 'DMA:    DEFS 128', '        END'])
    with tempfile.TemporaryDirectory(prefix='bettercpm-random-regression-') as temporary:
        work = Path(temporary)
        program = work / 'RANREG.COM'
        data = assemble(Path('/Users/nathanael/bin/z80asm'), '\n'.join(code)+'\n',
                        program, work / 'ranreg.lst', 0x100)
        evidence = ROOT / 'build/random-regression'
        evidence.mkdir(exist_ok=True)
        (evidence/'probe.asm').write_text('\n'.join(code))
        (evidence/'probe.bin').write_bytes(data)
        (evidence/'probe.lst').write_bytes((work/'ranreg.lst').read_bytes())
        original = ROOT / 'build/compatibility/BetterCPM-Compatibility-Final.dmk'
        raw = extract_raw(original.read_bytes())
        add_file(raw, 'RANREG.COM', data)
        disk = work / 'random.dmk'
        disk.write_bytes(build(raw))
        result = subprocess.run(['python3', str(ROOT/'tools/run_trs80_command.py'),
                                 'RANREG', '--image', str(disk), '--boot-delay', '3500',
                                 '--run-delay', '20000'], text=True, capture_output=True, check=True)
        assert 'Random I/O persistence and zero-fill passed' in result.stdout, result.stdout + result.stderr
        print('Real disk: zero-filled records, requested payload, unclosed extent switches, reopen and size passed')


if __name__ == '__main__':
    main()
