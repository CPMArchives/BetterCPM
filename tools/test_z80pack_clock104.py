#!/usr/bin/env python3
"""Bounded native lifecycle qualification of optional 104/105 adapters."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from build_ccp import assemble
from test_z80pack_clock_lifecycle import PROBE
from test_z80pack_sysgen_install import session

ROOT = Path(__file__).resolve().parents[1]


def source(four: bool) -> str:
    text = PROBE.replace("        LD C,200", "        LD C,105").replace(
        "        LD C,201", "        LD C,104")
    # Availability is selected by mode, not A: successful four-byte GET
    # returns nonzero seconds and must not enter the failed-GET atomicity check.
    text = text.replace("        LD A,(EXPECT)\n        OR A\n        JR Z,SETTEST",
                        "        LD A,(MODE)\n        OR A\n        JR Z,SETTEST")
    # This probe uses mode 0 for available and mode 1 for missing provider.
    # Four-byte GET returns seconds in A, while HL still reports success zero.
    if four:
        text = text.replace("        CALL INVOKE\n        CALL CHECK", """        CALL INVOKE
        LD A,(MODE)
        OR A
        JR NZ,GETCHECK
        LD A,(RET_A)
        CP 60H
        JP NC,BAD
        AND 0FH
        CP 10
        JP NC,BAD
        LD A,(RET_A)
        LD (EXPECT),A
GETCHECK:
        CALL CHECK""", 1)
    text = text.replace("        LD E,A\n        LD D,0\n        LD HL,(RET_HL)", """        LD DE,0
        CP 0FEH
        JR NZ,HLZERO
        LD E,A
HLZERO:
        LD HL,(RET_HL)""")
    text = text.replace("SETTEST:\n", """SETTEST:
        LD A,(BEFORE)
        CP 0C3H
        JP NZ,BAD
        LD A,(AFTER)
        CP 3CH
        JP NZ,BAD
""")
    if four:
        text = text.replace("SETTEST:\n", """SETTEST:
        LD A,(BUFFER+4)
        CP 0A5H
        JP NZ,BAD
""")
    text = text.replace("        LD DE,OK\n", '''        LD A,(BEFORE)
        CP 0C3H
        JP NZ,BAD
        LD A,(AFTER)
        CP 3CH
        JP NZ,BAD
        LD DE,OK
''' )
    text = text.replace("BUFFER: DB", "BEFORE: DB 0C3H\nBUFFER: DB")
    text = text.replace("RECORD: DB", "AFTER:  DB 3CH\nRECORD: DB")
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--image-dir', type=Path, default=ROOT / 'build/z80pack')
    parser.add_argument('--simulator', type=Path,
                        default=Path.home() / 'projects/git/z80pack/cpmsim/cpmsim')
    parser.add_argument('--report', type=Path,
                        default=ROOT / 'build/test-results/z80pack-clock104')
    args = parser.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    work = report / 'runtime'
    work.mkdir()
    shutil.copytree(args.image_dir / 'disks', work / 'disks')
    shutil.copy2(args.image_dir / 'diskdefs', work / 'diskdefs')
    disk = work / 'disks/drivea.dsk'
    # Free directory entries in the disposable copy, retaining all runtime
    # components. These older probes are unrelated to this campaign.
    subprocess.run(['cpmrm', '-T', 'raw', '-f', 'bettercpm-default', str(disk),
                    '0:bdosprb.com', '0:rsx2tst.com', '0:rsxtest.com',
                    '0:stattst.com', '0:svctest.com', '0:r3coord.rsx'], cwd=work, check=True)
    artifacts = []
    for name, four in (('CLK4', True), ('CLK5', False)):
        text = source(four)
        (report / (name.lower() + '.mac')).write_text(text)
        path = report / (name + '.COM')
        assemble(Path.home() / 'bin/z80asm', text, path,
                 report / (name.lower() + '.lst'), 0x100)
        artifacts.append(path)
    historical = report / 'CLKPROB.COM'
    (report / 'clkprob.mac').write_text(PROBE)
    assemble(Path.home() / 'bin/z80asm', PROBE, historical,
             report / 'clkprob.lst', 0x100)
    artifacts.append(historical)
    artifacts.extend(ROOT / 'build/rsx' / name for name in ('T104C3.RSX', 'T104Z8.RSX'))
    artifacts.append(ROOT / 'build/system/R3COORD.RSX')
    for path in artifacts:
        subprocess.run(['cpmcp', '-T', 'raw', '-f', 'bettercpm-default',
                        str(disk), str(path), '0:' + path.name], cwd=work, check=True)
    commands = [
        ('RSX LOAD ZPRTC', None), ('RSX LOAD P2DOS', None),
        ('RSX LOAD T104C3', 'load'), ('CLK4 0', 'abi'), ('CLKPROB 0', 'abi'),
        ('RSX LOAD T104Z8', 'conflict'), ('RSX LIST', 'four'),
        ('WARM', None), ('CLK4 0', 'abi'),
        ('RSX UNLOAD ZPRTC', None), ('CLK4 1', 'abi'), ('CLKPROB 1', 'abi'),
        ('RSX LOAD ECHO', None), ('RSX LOAD ZPRTC', None),
        ('CLK4 0', 'abi'), ('RSX UNLOAD ECHO', None),
        ('RSX UNLOAD T104C3', None), ('RSX LOAD T104Z8', 'load'),
        ('CLK5 0', 'abi'), ('CLKPROB 0', 'abi'), ('RSX LOAD T104C3', 'conflict'),
        ('RSX LIST', 'five'), ('WARM', None), ('CLK5 0', 'abi'),
        ('RSX UNLOAD ZPRTC', None), ('CLK5 1', 'abi'),
        ('RSX LOAD ECHO', None), ('RSX LOAD ZPRTC', None),
        ('CLK5 0', 'abi'), ('RSX UNLOAD ECHO', None),
        ('RSX UNLOAD T104Z8', None), ('RSX UNLOAD P2DOS', None),
        ('RSX UNLOAD ZPRTC', None), ('RSX LIST', 'empty'), ('VER', 'version')]
    output = session(args.simulator.resolve(), work / 'disks',
                     [(cmd.encode() + b'\r', b'A0>_ ', 20) for cmd, _ in commands],
                     report / 'transcript.txt')
    cursor = 0
    for command, check in commands:
        start = output.index(command.encode(), cursor)
        end = output.index(b'A0>_ ', start)
        block = output[start:end]
        cursor = end
        if check == 'abi':
            assert b'CLOCK ABI PASS' in block and b'CLOCK ABI FAIL' not in block, block
        elif check == 'conflict':
            assert b'RSX module or profile error' in block, block
        elif check == 'load':
            assert b'error' not in block.lower(), block
        elif check in ('four', 'five'):
            wanted, absent = ((b'T104C3', b'T104Z8') if check == 'four'
                              else (b'T104Z8', b'T104C3'))
            assert wanted in block and absent not in block and b'P2DOS' in block, block
        elif check == 'empty':
            assert b'53K' in block and b'T104' not in block and b'P2DOS' not in block, block
        elif check == 'version':
            assert b'BetterCP/M' in block, block
    evidence = {
        'result': 'PASS', 'commands': commands,
        'artifacts': {str(path.relative_to(ROOT)) if path.is_relative_to(ROOT)
                      else path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in artifacts},
        'simulator_sha256': hashlib.sha256(args.simulator.read_bytes()).hexdigest(),
        'boot_image_sha256': hashlib.sha256((args.image_dir / 'disks/drivea.dsk').read_bytes()).hexdigest(),
        'scope': 'cpmsim actual load, provider absence/replacement, WBOOT, conflict orders, P2DOS coexistence and TPA restoration; historical clients and Model 4 remain separate'
    }
    (report / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print('PASS: native 104/105 lifecycle, mutual exclusion, guarded ABI and restored 53K TPA')


if __name__ == '__main__':
    main()
