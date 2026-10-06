#!/usr/bin/env python3
"""Run one bounded FreHD/P2DOS lifecycle with per-command screen evidence."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw, add_file
from build_montezuma_extended_790k import build, SECTOR_SIZE
from build_trs80_boot import FILESYSTEM_FIRST_SECTOR, DIRECTORY_ENTRIES
from build_ccp import assemble
from run_trs80_command import DEFAULT_EMULATOR, key_args
from trs80gp_launch import run
from test_z80pack_clock_lifecycle import PROBE

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / 'build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk'


def verify_screens(report: Path, commands) -> None:
    for index, (command, check) in enumerate(commands):
        capture = (report / f'trs80-text-{index}.bin').read_bytes()[:1920]
        text = '\n'.join(capture[at:at+80].decode('ascii', errors='replace').rstrip()
                         for at in range(0, 1920, 80))
        (report / f'screen-{index}.txt').write_text(text)
        # Evaluate only output after the latest command, not older screen text.
        if check == 'abi':
            lines = [capture[at:at+80].strip() for at in range(0, 1920, 80)
                     if capture[at:at+80].strip()]
            # The probe's return redraws the command line. Require fresh result
            # directly before the prompt, never an older PASS farther upscreen.
            assert len(lines) >= 2 and lines[-2] == b'CLOCK ABI PASS', (command, lines)
            assert lines[-1].startswith(b'A0>'), lines
            continue
        marker = b'A0>' + command.encode()
        assert marker in capture, (command, capture)
        block = capture[capture.rindex(marker):]
        if check == 'absent':
            assert b'No TIME provider is loaded' in block, block
        elif check == 'resident':
            assert b'P2DOS' in block and b'FREHDCLK' not in block, block
        elif check == 'provider':
            assert b'Provider: FREHDCLK' in block, block
        elif check == 'get':
            assert re.search(rb'20[0-9]{2}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}', block), block


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path,
                        default=ROOT / 'build/test-results/frehd-clock-lifecycle')
    parser.add_argument('--case', choices=('recovery', 'warm'), default='recovery')
    args = parser.parse_args()
    report = args.report.resolve()
    report.mkdir(parents=True, exist_ok=False)
    probe = report / 'CLKPROB.COM'
    (report / 'clkprob.mac').write_text(PROBE)
    assemble(Path.home() / 'bin/z80asm', PROBE, probe, report / 'clkprob.lst', 0x100)
    raw = extract_raw(IMAGE.read_bytes())
    directory = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE
    for index in range(DIRECTORY_ENTRIES):
        offset = directory + index * 32
        name = bytes(value & 0x7F for value in raw[offset+1:offset+12])
        if raw[offset] == 0 and name in (b'TIME    COM', b'BDOSPRB COM'):
            raw[offset] = 0xE5
    add_file(raw, 'TIME.COM', (ROOT / 'build/utilities/TIME.COM').read_bytes())
    add_file(raw, 'CLKPROB.COM', probe.read_bytes())
    disk = report / 'clock.dmk'
    disk.write_bytes(build(bytes(raw)))
    frehd = report / 'frehd'
    frehd.mkdir()
    if args.case == 'warm':
        commands = [('RSX LOAD FREHDCLK', None), ('RSX LOAD P2DOS', None),
                    ('WARM', None), ('CLKPROB 0', 'abi')]
    else:
        commands = [('RSX LOAD FREHDCLK', None), ('RSX LOAD P2DOS', None),
                    ('RSX UNLOAD FREHDCLK', None), ('CLKPROB 1', 'abi'),
                    ('RSX LIST', 'resident'), ('RSX LOAD FREHDCLK', None),
                    ('CLKPROB 0', 'abi'), ('TIME /PROVIDER', 'provider')]
    invocation = [str(DEFAULT_EMULATOR), '-m4', '-batch', '-turbo',
                  '-frehd_dir', str(frehd), '-d0', str(disk), '-id', '5000']
    for command, _ in commands:
        invocation += key_args(command + '\r')
        # Layout transitions need the timing measured by the focused load probe.
        delay = 8000 if command.startswith('RSX LOAD') or command.startswith('RSX UNLOAD') or command == 'WARM' else 3000
        invocation += ['-id', str(delay), '-it']
    invocation += ['-ix']
    (report / 'invocation.json').write_text(json.dumps(invocation, indent=2) + '\n')
    run(invocation, cwd=report, timeout=180, check=True)
    verify_screens(report, commands)
    (report / 'evidence.json').write_text(json.dumps({
        'result': 'PASS', 'case': args.case, 'commands': commands,
        'probe_sha256': hashlib.sha256(probe.read_bytes()).hexdigest(),
        'utility_sha256': hashlib.sha256((ROOT / 'build/utilities/TIME.COM').read_bytes()).hexdigest(),
        'source_image_sha256': hashlib.sha256(IMAGE.read_bytes()).hexdigest(),
        'simulator_sha256': hashlib.sha256(DEFAULT_EMULATOR.read_bytes()).hexdigest()
    }, indent=2) + '\n')
    print(f'PASS: FreHD/P2DOS {args.case}, registers and failed-GET atomicity')


if __name__ == '__main__':
    main()
