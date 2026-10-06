#!/usr/bin/env python3
"""Bounded actual P2DOS/provider lifecycle and historical register qualification."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from build_ccp import assemble
from test_z80pack_sysgen_install import session

ROOT = Path(__file__).resolve().parents[1]
PROBE = """        ASEG
        ORG 100H
        LD SP,4000H
        LD A,(80H)
        LD C,A
        LD B,0
        LD HL,80H
        ADD HL,BC
        LD A,(HL)
        SUB '0'
        LD (MODE),A
        CP 2
        LD A,0FFH
        JR Z,GOODGET
        LD A,(MODE)
        OR A
        LD A,0FEH
        JR NZ,GOODGET
        XOR A
GOODGET:
        LD (EXPECT),A
        LD C,200
        CALL INVOKE
        CALL CHECK
        LD A,(EXPECT)
        OR A
        JR Z,SETTEST
        LD HL,BUFFER
        LD B,5
ATOMIC:
        LD A,(HL)
        CP 0A5H
        JP NZ,BAD
        INC HL
        DJNZ ATOMIC
SETTEST:
        LD HL,RECORD
        LD DE,BUFFER
        LD BC,5
        LDIR
        LD A,(MODE)
        CP 2
        LD A,0FEH
        JR NZ,SETEXP
        LD A,0FFH
SETEXP:
        LD (EXPECT),A
        LD C,201
        CALL INVOKE
        CALL CHECK
        LD HL,BUFFER
        LD DE,RECORD
        LD B,5
UNCHANGED:
        LD A,(DE)
        CP (HL)
        JP NZ,BAD
        INC HL
        INC DE
        DJNZ UNCHANGED
        LD DE,OK
        JR PRINT
INVOKE:
        LD IX,1357H
        LD IY,2468H
        LD DE,BUFFER
        CALL 5
        LD (RET_A),A
        LD (RET_HL),HL
        LD (RET_DE),DE
        LD (RET_SP),SP
        PUSH IX
        POP HL
        LD (RET_IX),HL
        PUSH IY
        POP HL
        LD (RET_IY),HL
        RET
CHECK:
        LD A,(EXPECT)
        LD HL,RET_A
        CP (HL)
        JP NZ,BAD
        LD E,A
        LD D,0
        LD HL,(RET_HL)
        OR A
        SBC HL,DE
        JP NZ,BAD
        LD HL,(RET_DE)
        LD DE,BUFFER
        OR A
        SBC HL,DE
        JP NZ,BAD
        LD HL,(RET_SP)
        LD DE,3FFEH
        OR A
        SBC HL,DE
        JP NZ,BAD
        LD HL,(RET_IX)
        LD DE,1357H
        OR A
        SBC HL,DE
        JP NZ,BAD
        LD HL,(RET_IY)
        LD DE,2468H
        OR A
        SBC HL,DE
        JP NZ,BAD
        RET
BAD:
        LD DE,FAIL
PRINT:
        LD C,9
        CALL 5
        JP 0
OK:     DB 'CLOCK ABI PASS',13,10,'$'
FAIL:   DB 'CLOCK ABI FAIL',13,10,'$'
MODE:   DB 0
EXPECT: DB 0
RET_A:  DB 0
RET_HL: DW 0
RET_DE: DW 0
RET_SP: DW 0
RET_IX: DW 0
RET_IY: DW 0
BUFFER: DB 0A5H,0A5H,0A5H,0A5H,0A5H
RECORD: DB 1,0,12H,34H,56H
        END
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--image-dir', type=Path, default=ROOT / 'build/z80pack')
    parser.add_argument('--simulator', type=Path,
                        default=Path.home() / 'projects/git/z80pack/cpmsim/cpmsim')
    parser.add_argument('--report', type=Path,
                        default=ROOT / 'build/test-results/z80pack-clock-lifecycle')
    args = parser.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    work = report / 'runtime'
    work.mkdir()
    shutil.copytree(args.image_dir / 'disks', work / 'disks')
    shutil.copy2(args.image_dir / 'diskdefs', work / 'diskdefs')
    probe = report / 'CLKPROB.COM'
    (report / 'clkprob.mac').write_text(PROBE)
    assemble(Path.home() / 'bin/z80asm', PROBE, probe, report / 'clkprob.lst', 0x100)
    disk = work / 'disks/drivea.dsk'
    subprocess.run(['cpmrm', '-T', 'raw', '-f', 'bettercpm-default', str(disk),
                    '0:bdosprb.com', '0:time.com'], cwd=work, check=True)
    for path, name in [(probe, 'CLKPROB.COM'), (ROOT / 'build/utilities/TIME.COM', 'TIME.COM')]:
        subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default', str(disk),
                        str(path), '0:' + name], cwd=work, check=True)
    # Probe modes: 0 successful GET/read-only SET; 1 claimed failures;
    # 2 frontend absent. Check both historical A/HL and DE/SP/IX/IY.
    commands = [
        ('CLKPROB 2', 'abi'),
        ('RSX LOAD ZPRTC', None), ('RSX LOAD P2DOS', None),
        ('CLKPROB 0', 'abi'), ('TIME', 'get'),
        ('WARM', None), ('CLKPROB 0', 'abi'), ('TIME', 'get'),
        ('RSX UNLOAD ZPRTC', None), ('CLKPROB 1', 'abi'), ('TIME', 'absent'),
        ('RSX LIST', 'resident'),
        ('RSX LOAD ECHO', None), ('RSX LOAD ZPRTC', None),
        ('CLKPROB 0', 'abi'), ('TIME /PROVIDER', 'provider'),
        ('RSX UNLOAD P2DOS', None), ('CLKPROB 2', 'abi'), ('TIME', 'get'),
        ('RSX UNLOAD ZPRTC', None), ('TIME', 'absent'),
        ('RSX LOAD ZPRTC', None), ('RSX LOAD P2DOS', None), ('CLKPROB 0', 'abi'),
        ('VER', 'prompt')]
    output = session(args.simulator.resolve(), work / 'disks',
                     [(command.encode() + b'\r', b'A0>_ ', 20) for command, _ in commands],
                     report / 'transcript.txt')
    cursor = 0
    for command, check in commands:
        start = output.index(command.encode(), cursor)
        end = output.index(b'A0>_ ', start)
        block = output[start:end]
        cursor = end
        if check == 'abi':
            assert b'CLOCK ABI PASS' in block and b'CLOCK ABI FAIL' not in block, (command, block)
        elif check == 'get':
            assert re.search(rb'20[0-9]{2}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}', block), block
        elif check == 'absent':
            assert b'No TIME provider is loaded' in block, block
        elif check == 'resident':
            assert b'P2DOS' in block and b'ZPRTC' not in block, block
        elif check == 'provider':
            assert b'Provider: ZPRTC' in block, block
        elif check == 'prompt':
            assert b'BetterCP/M' in block, block
    (report / 'evidence.json').write_text(json.dumps({
        'result': 'PASS', 'commands': commands,
        'probe_sha256': hashlib.sha256(probe.read_bytes()).hexdigest(),
        'simulator_sha256': hashlib.sha256(args.simulator.read_bytes()).hexdigest(),
        'replacement': 'new ZPRTC instance after changed RSX layout; not a different hardware provider'
    }, indent=2) + '\n')
    print('PASS: P2DOS/provider unload, replacement instance, WBOOT, ABI registers and failed-GET atomicity')


if __name__ == '__main__':
    main()
