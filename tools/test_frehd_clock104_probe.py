#!/usr/bin/env python3
"""Bounded Model 4/FreHD clock-adapter probe or full lifecycle campaign."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from add_cpm_file_to_dmk import extract_raw, add_file
from build_montezuma_extended_790k import build, SECTOR_SIZE
from build_trs80_boot import FILESYSTEM_FIRST_SECTOR, DIRECTORY_ENTRIES
from build_ccp import assemble
from run_trs80_command import DEFAULT_EMULATOR, key_args
from trs80gp_launch import run
from test_z80pack_clock104 import source
from test_z80pack_clock_lifecycle import PROBE

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / 'build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', choices=('T104C3', 'T104Z8'), required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--lifecycle', action='store_true')
    args = parser.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    text = source(args.profile == 'T104C3')
    (report / 'clk104.mac').write_text(text)
    probe = report / 'CLK104.COM'
    assemble(Path.home() / 'bin/z80asm', text, probe, report / 'clk104.lst', 0x100)
    p2 = report / 'CLKPROB.COM'
    (report / 'clkprob.mac').write_text(PROBE)
    assemble(Path.home() / 'bin/z80asm', PROBE, p2, report / 'clkprob.lst', 0x100)
    raw = extract_raw(IMAGE.read_bytes())
    directory = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE
    replacements = {b'R3COORD RSX', b'BDOSPRB COM', b'STATTST COM',
                    b'RSXTEST COM', b'RSX2TST COM', b'SVCTEST COM',
                    b'CLK104  COM', b'CLKPROB COM', b'T104C3  RSX', b'T104Z8  RSX'}
    for index in range(DIRECTORY_ENTRIES):
        offset = directory + index * 32
        name = bytes(value & 0x7F for value in raw[offset+1:offset+12])
        if raw[offset] == 0 and name in replacements:
            raw[offset] = 0xE5
    artifacts = [probe, p2, ROOT / 'build/system/R3COORD.RSX',
                 ROOT / 'build/rsx/T104C3.RSX', ROOT / 'build/rsx/T104Z8.RSX']
    for path in artifacts:
        add_file(raw, path.name, path.read_bytes())
    disk = report / 'clock.dmk'
    disk.write_bytes(build(bytes(raw)))
    frehd = report / 'frehd'
    frehd.mkdir()
    commands = [
        ('RSX LOAD FREHDCLK', None), ('RSX LOAD P2DOS', None),
        ('RSX LOAD ' + args.profile, None), ('CLK104 0', 'abi')]
    if args.lifecycle:
        opposite = 'T104Z8' if args.profile == 'T104C3' else 'T104C3'
        commands += [('WARM', None), ('CLK104 0', 'abi'),
                     ('RSX LOAD ' + opposite, 'conflict'),
                     ('RSX UNLOAD FREHDCLK', None), ('CLK104 1', 'abi'),
                     ('RSX LOAD FREHDCLK', None), ('CLK104 0', 'abi'),
                     ('CLKPROB 0', 'abi'), ('RSX UNLOAD ' + args.profile, None),
                     ('RSX UNLOAD P2DOS', None), ('RSX UNLOAD FREHDCLK', None),
                     ('RSX LIST', 'empty')]
    invocation = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo',
                  '-frehd_dir', str(frehd), '-d0', str(disk), '-id', '5000']
    for command, _ in commands:
        invocation += key_args(command + '\r')
        delay = 8000 if command.startswith(('RSX LOAD', 'RSX UNLOAD')) or command == 'WARM' else 3000
        if command.startswith(('RSX LOAD', 'RSX UNLOAD')) or command == 'WARM':
            delay = 16000
        invocation += ['-id', str(delay), '-it']
    invocation += ['-ix']
    (report / 'invocation.json').write_text(json.dumps(invocation, indent=2) + '\n')
    run(invocation, cwd=report, timeout=450 if args.lifecycle else 180, check=True)
    for index, (command, check) in enumerate(commands):
        capture = (report / f'trs80-text-{index}.bin').read_bytes()[:1920]
        lines = [capture[at:at+80].strip() for at in range(0, 1920, 80)
                 if capture[at:at+80].strip()]
        (report / f'screen-{index}.txt').write_text('\n'.join(line.decode('ascii', errors='replace') for line in lines))
        if check == 'abi':
            assert len(lines) >= 2 and lines[-2] == b'CLOCK ABI PASS' and lines[-1].startswith(b'A0>'), (command, lines)
            continue
        marker = b'A0>' + command.encode()
        assert marker in capture, (command, capture)
        block = capture[capture.rindex(marker):]
        if check == 'conflict':
            assert b'RSX module or profile error' in block, block
        elif check == 'empty':
            assert b'No RSXs loaded' in block and b'53K' in block, block
        else:
            assert b'error' not in block.lower(), (command, block)
    (report / 'evidence.json').write_text(json.dumps({
        'result': 'PASS', 'profile': args.profile, 'case': 'lifecycle' if args.lifecycle else 'load-probe', 'commands': commands,
        'artifact_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in artifacts},
        'image_sha256': hashlib.sha256(IMAGE.read_bytes()).hexdigest(),
        'simulator_sha256': hashlib.sha256(DEFAULT_EMULATOR.read_bytes()).hexdigest()
    }, indent=2) + '\n')
    print('PASS: Model 4/FreHD ' + args.profile + (' lifecycle' if args.lifecycle else ' load/ABI timing probe'))


if __name__ == '__main__':
    main()
